import argparse
import subprocess
import sys

from ._git import git_setup_intellij


def configure(parser: argparse.ArgumentParser):
    parser.add_argument(
        '--hard',
        action='store_true',
        help='hard reset the repository',
        default=False,
    )


def execute(args: argparse.Namespace):
    repo = args.repo

    # fetches latest intellij master and stroes it in FETCH_HEAD
    git_setup_intellij(repo)

    if args.hard:
        cmd = ['git', 'reset', 'FETCH_HEAD', '--hard']
    else:
        cmd = ['git', 'rebase', 'FETCH_HEAD', '--autostash']

    subprocess.check_call(
        cmd,
        cwd=repo,
        stderr=sys.stdout,
        stdout=sys.stdout,
    )
