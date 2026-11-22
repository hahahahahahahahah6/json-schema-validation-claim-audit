"""Static documentation and source inspection."""
import ast
import os
import re
from pathlib import Path

from .phrases import JSONSCHEMAVALIDATION, NOJSONSCHEMAVALIDATION, GENERIC_NAMES

DRAFTS = {'Draft3Validator', 'Draft4Validator', 'Draft6Validator', 'Draft7Validator', 'Draft201909Validator', 'Draft202012Validator'}


def _pattern(phrases):
    return re.compile(r'(?<!\w)(?:' + '|'.join(re.escape(p) for p in sorted(phrases, key=lambda x: (-len(x), x))) + r')(?!\w)')

YES_RE = _pattern(JSONSCHEMAVALIDATION)
NO_RE = _pattern(NOJSONSCHEMAVALIDATION)


def claims(text):
    lines = []
    fence = None
    for line in text.splitlines():
        match = re.match(r'^ {0,3}(`{3,}|~{3,})', line)
        if fence:
            if match and match.group(1)[0] == fence[0] and len(match.group(1)) >= len(fence) and not line[match.end():].strip():
                fence = None
            continue
        if match:
            fence = match.group(1)
        else:
            lines.append(line)
    yes, no = set(), set()
    for paragraph in re.split(r'\n\s*\n', '\n'.join(lines)):
        normalized = re.sub(r'\s+', ' ', paragraph.lower().replace("n't", ' not').replace('-', ' '))
        no.update(m.group() for m in NO_RE.finditer(normalized))
        normalized = NO_RE.sub(' ', normalized)
        yes.update(m.group() for m in YES_RE.finditer(normalized))
    return yes, no


def evidence(source):
    try:
        tree = ast.parse(source)
    except (SyntaxError, ValueError):
        return False
    nodes = list(ast.walk(tree))
    definitions = {n.name for n in nodes if isinstance(n, (ast.FunctionDef, ast.AsyncFunctionDef, ast.ClassDef))}
    imports = {}
    bound = set()
    for n in nodes:
        if isinstance(n, ast.Import):
            for a in n.names:
                imports[a.asname or a.name.split('.')[0]] = a.name if a.asname else a.name.split('.')[0]
        elif isinstance(n, ast.ImportFrom) and n.module and not n.level:
            for a in n.names:
                if a.name != '*':
                    imports[a.asname or a.name] = n.module + '.' + a.name
        elif isinstance(n, (ast.Assign, ast.AnnAssign, ast.NamedExpr, ast.AugAssign)):
            targets = n.targets if isinstance(n, ast.Assign) else [n.target]
            for target in targets:
                bound.update(x.id for x in ast.walk(target) if isinstance(x, ast.Name) and isinstance(x.ctx, ast.Store))
        elif isinstance(n, (ast.With, ast.AsyncWith)):
            for item in n.items:
                if item.optional_vars:
                    bound.update(x.id for x in ast.walk(item.optional_vars) if isinstance(x, ast.Name) and isinstance(x.ctx, ast.Store))
    shadowed = definitions | bound
    def root(expr):
        while isinstance(expr, ast.Attribute):
            expr = expr.value
        return expr.id if isinstance(expr, ast.Name) else None
    def route(func, library, names):
        if isinstance(func, ast.Name):
            target = imports.get(func.id, '')
            return func.id not in shadowed and target in {library + '.' + name for name in names} and target.rsplit('.', 1)[-1] not in definitions
        if isinstance(func, ast.Attribute) and func.attr in names and func.attr not in definitions:
            base = root(func.value)
            return base in imports and base not in shadowed and (imports[base] == library or imports[base].startswith(library + '.'))
        return False
    constructions = set()
    methods = set()
    for node in nodes:
        if not isinstance(node, ast.Call):
            continue
        f = node.func
        if route(f, 'jsonschema', {'validate'}) or route(f, 'fastjsonschema', {'validate'}):
            return True
        for library, names, label in [('jsonschema', DRAFTS, 'draft'), ('pydantic', {'TypeAdapter'}, 'adapter'), ('cerberus', {'Validator'}, 'cerberus')]:
            if route(f, library, names):
                constructions.add(label)
        if isinstance(f, ast.Attribute):
            base = root(f.value)
            if base in imports and base in shadowed:
                continue
            if f.attr in definitions:
                continue
            methods.add(f.attr)
            if f.attr in GENERIC_NAMES or f.attr in {'model_validate', 'model_validate_json'}:
                return True
        elif isinstance(f, ast.Name) and f.id not in shadowed:
            target = imports.get(f.id, '').rsplit('.', 1)[-1]
            if target in GENERIC_NAMES and target not in definitions:
                return True
    return bool(('draft' in constructions and methods & {'validate', 'iter_errors', 'is_valid'}) or ('adapter' in constructions and methods & {'validate_python', 'validate_json', 'validate_strings'}) or ('cerberus' in constructions and 'validate' in methods))


def audit(root, ignores=()):
    root = Path(root)
    if not root.is_dir() or not os.access(root, os.R_OK | os.X_OK):
        raise OSError('root is not a readable directory')
    yes, no, production, tests = [], [], [], []
    prefixes = [p.replace('\\', '/').strip('/') for p in ignores]
    for directory, dirs, files in os.walk(root, followlinks=False, onerror=lambda e: (_ for _ in ()).throw(e)):
        base = Path(directory)
        def ignored(path):
            rel = path.relative_to(root).as_posix()
            return any(rel == p or rel.startswith(p + '/') for p in prefixes)
        dirs[:] = sorted(d for d in dirs if not (base / d).is_symlink() and not ignored(base / d))
        for name in sorted(files):
            path = base / name
            if path.is_symlink() or ignored(path):
                continue
            rel = path.relative_to(root)
            parts = rel.parts
            isdoc = rel.as_posix() == 'README.md' or ('docs' in parts[:-1] and path.suffix == '.md')
            istest = 'tests' in parts[:-1] or name.startswith('test_') or name.endswith('_test.py')
            iscode = path.suffix == '.py' and not any(x in parts[:-1] for x in ('fixtures', 'docs', 'examples'))
            if isdoc:
                a, b = claims(path.read_text(encoding='utf-8'))
                yes.extend((rel.as_posix(), p) for p in sorted(a))
                no.extend((rel.as_posix(), p) for p in sorted(b))
            if iscode and evidence(path.read_text(encoding='utf-8')):
                (tests if istest else production).append(rel.as_posix())
    findings = []
    if yes and not production:
        findings.append({'id': 'documented-json-schema-validation-claim-false', 'severity': 'MEDIUM' if tests else 'HIGH', 'claims': yes, 'evidence': tests})
    if no and production:
        findings.append({'id': 'documented-no-json-schema-validation-claim-false', 'severity': 'HIGH', 'claims': no, 'evidence': production})
    return {'findings': findings, 'claims': {'positive': yes, 'negative': no}, 'production_evidence': production, 'test_evidence': tests}
