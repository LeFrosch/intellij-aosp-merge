import argparse
import subprocess

from ._aosp import AOSP_URL, AOSP_REF
from ._git import git_add_aosp, git_fetch_aosp, git_log
from ._util import log


def collect_missing_commits(repo: str, from_hash: str) -> list[str]:
    output = subprocess.check_output(
        [
            'git',
            'log',
            '%s..%s' % (from_hash, AOSP_REF),
            '--pretty=format:"%H"',
            '--',
            'aswb',
        ],
        cwd=repo,
    )

    return [hash.strip('"') for hash in output.decode().splitlines()]


def format_commit(repo: str, commit: str) -> str:
    return '=HYPERLINK("%s%s", "%s");%s;%s;0' % (
        AOSP_URL,
        commit,
        commit,
        git_log(repo, commit, '%s'),
        git_log(repo, commit, '%as'),
    )


def configure(parser: argparse.ArgumentParser):
    parser.add_argument(
        'commit',
        type=str,
        help='commit hash of the last applied commit'
    )

    parser.add_argument(
        '-o',
        type=str,
        help='path to the output csv file',
        dest='output',
        default='missing.csv',
    )


def execute(args: argparse.Namespace):
    repo = args.repo

    git_add_aosp(repo)
    git_fetch_aosp(repo)

    log('collectting commits')
    missing = collect_missing_commits(repo, args.commit)

    log('found %d missing commits' % len(missing))
    content = '\n'.join(format_commit(repo, it) for it in reversed(missing))

    log('writing commits to %s' % args.output)
    with open(args.output, 'wt') as f:
        f.write(content)
