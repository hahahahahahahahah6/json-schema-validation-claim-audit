import argparse
import json
import sys
from . import __version__
from .audit import audit


class Parser(argparse.ArgumentParser):
    def error(self, message):
        self.print_usage(sys.stderr)
        self.exit(1, f'{self.prog}: error: {message}\n')


def main(argv=None):
    parser = Parser(description='Audit documentation claims against Python source.')
    parser.add_argument('--version', action='version', version=__version__)
    subs = parser.add_subparsers(dest='command', required=True, parser_class=Parser)
    sub = subs.add_parser('audit')
    sub.add_argument('repo', nargs='?', default='.')
    sub.add_argument('--json', action='store_true')
    sub.add_argument('--verbose', action='store_true')
    sub.add_argument('--ignore', action='append', default=[])
    sub.add_argument('--fail-on', choices=('high', 'medium'), default='high')
    args = parser.parse_args(argv)
    try:
        result = audit(args.repo, args.ignore)
    except (OSError, UnicodeError) as exc:
        print(f'error: {exc}', file=sys.stderr)
        return 1
    if args.json:
        print(json.dumps(result, indent=2))
    else:
        for item in result['findings']:
            print(f"{item['severity']} {item['id']}")
        if not result['findings']:
            print('PASS')
        if args.verbose:
            for category, values in result['claims'].items():
                for path, phrase in values:
                    print(f'{category}: {path}: {phrase}')
            for category in ('production_evidence', 'test_evidence'):
                for path in result[category]:
                    print(f'{category}: {path}')
    return 2 if any(x['severity'] == 'HIGH' or args.fail_on == 'medium' for x in result['findings']) else 0


if __name__ == '__main__':
    sys.exit(main())
