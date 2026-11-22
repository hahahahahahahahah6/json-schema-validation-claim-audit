import subprocess
import sys
import tempfile
import unittest
from pathlib import Path

from json_schema_validation_claim_audit.audit import audit, claims, evidence
from json_schema_validation_claim_audit.phrases import JSONSCHEMAVALIDATION, NOJSONSCHEMAVALIDATION, GENERIC_NAMES


class AuditTests(unittest.TestCase):
    def test_phrases(self):
        self.assertEqual((len(set(JSONSCHEMAVALIDATION)), len(set(NOJSONSCHEMAVALIDATION)), len(set(GENERIC_NAMES))), (50, 24, 24))
        for p in JSONSCHEMAVALIDATION:
            with self.subTest(p=p): self.assertTrue(claims(p)[0])
        for p in NOJSONSCHEMAVALIDATION:
            with self.subTest(p=p): self.assertEqual(claims(p)[0], set())
        self.assertEqual(claims('```\nvalidate json\n```'), (set(), set()))

    def test_routes(self):
        routes = ['import jsonschema as j\nj.validate()', 'from fastjsonschema import validate as v\nv()', 'import jsonschema as j\nj.Draft7Validator()\nx.iter_errors()', 'from pydantic import TypeAdapter as T\nT(int)\nx.validate_json()', 'x.model_validate()', 'import cerberus as c\nc.Validator()\nx.validate()', 'obj.validate_json_schema()', 'from x import validate_json_schema as v\nv()']
        for s in routes:
            with self.subTest(s=s): self.assertTrue(evidence(s))
        for draft in ('Draft3Validator','Draft4Validator','Draft6Validator','Draft7Validator','Draft201909Validator','Draft202012Validator'):
            for method in ('validate','iter_errors','is_valid'):
                with self.subTest(draft=draft, method=method): self.assertTrue(evidence(f'from jsonschema import {draft}\n{draft}()\na.{method}()'))
        for method in ('validate_python','validate_json','validate_strings'):
            self.assertTrue(evidence(f'from pydantic import TypeAdapter\nTypeAdapter(int)\na.{method}()'))
        for name in GENERIC_NAMES:
            self.assertTrue(evidence(f'a.{name}()'))

    def test_non_routes(self):
        cases = ['import jsonschema', 'validate()', 'a.validate()', 'a.iter_errors()', 'a.is_valid()', 'from jsonschema import Draft7Validator\nDraft7Validator()', 'from pydantic import TypeAdapter\nTypeAdapter(int)', 'from cerberus import Validator\nValidator()', 'import fastjsonschema\nfastjsonschema.compile({})', '@validate_call\ndef f(): pass', 'is_valid_json()', 'class X(BaseModel): pass', 'schema.load()', 'json.loads(x)', 'json.load(x)', 'ValidationError()', 'try: pass\nexcept ValidationError: pass', 're.match("{}", x)', 'isinstance(x, dict)', 'if not x: raise ValueError()', 'parser.add_argument("x", type=int)', 'validate_python()', 'validate_json()', 'validate_strings()', 'model_validate()', 'model_validate_json()', 'send_email()', 'send_sms()', 'email_validator.validate_email(x)', 'phonenumbers.is_valid_number(x)', 'extract(x)', 'decode(x)', 'subprocess.run(["validator"])', 'import jsonschema as j\nj = 1\nj.validate()', 'def model_validate(): pass\na.model_validate()', 'def validate_json_schema(): pass\na.validate_json_schema()', 'from jsonschema import validate\nwith x as validate: pass\nvalidate()', 'if :']
        for s in cases:
            with self.subTest(s=s): self.assertFalse(evidence(s))

    def test_findings(self):
        with tempfile.TemporaryDirectory() as d:
            p = Path(d); (p/'README.md').write_text('validate json against schema')
            self.assertEqual(audit(p)['findings'][0]['severity'], 'HIGH')
            (p/'tests').mkdir(); (p/'tests/test_x.py').write_text('import jsonschema\njsonschema.validate()')
            self.assertEqual(audit(p)['findings'][0]['severity'], 'MEDIUM')
            (p/'x.py').write_text('import jsonschema\njsonschema.validate()')
            self.assertEqual(audit(p)['findings'], [])
            (p/'README.md').write_text('does not validate json against schema')
            self.assertEqual(audit(p)['findings'][0]['severity'], 'HIGH')

    def test_scope_and_ignore(self):
        with tempfile.TemporaryDirectory() as d:
            p=Path(d); (p/'README.md').write_text('validate json'); (p/'a.py').write_text('from jsonschema import Draft7Validator\nDraft7Validator()'); (p/'b.py').write_text('x.validate()')
            self.assertEqual(audit(p)['findings'][0]['severity'], 'HIGH')
            (p/'b.py').write_text('x.model_validate()')
            self.assertFalse(audit(p)['findings'])
            self.assertTrue(audit(p, ['b.py'])['findings'])

    def test_cli_and_self_audit(self):
        root=Path(__file__).resolve().parents[1]
        self.assertEqual(claims((root/'README.md').read_text()), (set(), set()))
        result=subprocess.run([sys.executable, '-m', 'json_schema_validation_claim_audit', '--version'], capture_output=True, text=True)
        self.assertEqual(result.stdout.strip(), '0.1.0')
        self.assertEqual(subprocess.run([sys.executable, '-m', 'json_schema_validation_claim_audit', 'bad'], capture_output=True).returncode, 1)

if __name__ == '__main__': unittest.main()
