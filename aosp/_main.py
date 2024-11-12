import argparse
import os

from . import _patch as patch, _deaosp as deaosp, _missing as missing

from .__about__ import __version__, __description__


def parse_arguments() -> argparse.Namespace:
    parser = argparse.ArgumentParser(description=__description__)

    parser.add_argument(
        '--version',
        action='version',
        version=__version__,
    )

    parser.add_argument(
        '--repo',
        type=str,
        help='path to the git repository (env: REPO)',
        default=os.environ.get('REPO'),
    )

    commands = parser.add_subparsers(
        required=True,
        help='available subcommands',
    )

    patch_parser = commands.add_parser(
        'patch',
        help='create a patch from an AOSP commit',
    )
    patch_parser.set_defaults(execute=patch.execute)
    patch.configure(patch_parser)

    deaosp_parser = commands.add_parser(
        'remap',
        help='remap AOSP specific references',
    )
    deaosp_parser.set_defaults(execute=deaosp.execute)
    deaosp.configure(deaosp_parser)

    missing_parser = commands.add_parser(
        'missing',
        help='collect missing commits',
    )
    missing_parser.set_defaults(execute=missing.execute)
    missing.configure(missing_parser)

    return parser.parse_args()


def main():
    args = parse_arguments()
    args.execute(args)
