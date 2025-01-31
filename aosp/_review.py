import argparse
import subprocess
import tempfile
import sys

from unidiff import PatchSet

from ._patch import patch_process as aosp_process_diff
from ._git import git_setup_aosp, git_log, git_read_aosp_commit
from ._util import log


def generate_diff(repo: str, commit: str) -> PatchSet:
    """
    Generates and parsed the git diff for the patch.
    """

    output = subprocess.check_output(
        ['git', 'diff', '-p', commit + '~1', commit],
        cwd=repo,
    )

    patch = PatchSet(output.decode())

    for file in patch:
        file.patch_info = None

    return patch


def configure(parser: argparse.ArgumentParser):
    parser.add_argument(
        'commit',
        type=str,
        help='hash of the commit to review'
    )


def show_diff_diff(repo: str, repo_commit: str, aosp_commit: str):
    try:
        subprocess.call(
            [
                'git',
                'range-diff',
                f'{aosp_commit}^..{aosp_commit}',
                f'{repo_commit}^..{repo_commit}',
            ],
            cwd=repo,
            stderr=sys.stdout,
            stdout=sys.stdout,
        )
    finally:
        pass


def execute(args: argparse.Namespace):
    repo = args.repo
    git_setup_aosp(repo)

    repo_commit = git_log(repo, args.commit, '%H')
    aosp_commit = git_read_aosp_commit(repo, args.commit)

    log('diff between applied patch and aosp patch')
    show_diff_diff(repo, repo_commit, aosp_commit)

    log('end of diff')
