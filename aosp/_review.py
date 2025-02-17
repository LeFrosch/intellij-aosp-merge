import argparse
import subprocess
import tempfile
import sys

from unidiff import PatchSet

from ._patch import patch_process as aosp_process_diff
from ._git import git_setup_aosp, git_log, git_read_aosp_commit, git_parse_rev
from ._consts import INTELLIJ_ORIGIN
from ._util import log


def git_fetch_pr(repo: str, pr: str) -> str:
    """
    Fetches the head of the pull request from GitHub and resolves the commit
    hash for the head.
    """

    subprocess.check_call(
        ['git', 'fetch', INTELLIJ_ORIGIN, 'pull/%s/head' % pr],
        cwd=repo,
    )
    log('pr %s up to date' % pr)

    return git_parse_rev(repo, 'FETCH_HEAD')


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


def show_diff_diff(repo: str, repo_diff: str, aosp_diff: str):
    repo_file = tempfile.NamedTemporaryFile(mode='wt')
    aosp_file = tempfile.NamedTemporaryFile(mode='wt')

    try:
        repo_file.write(repo_diff)
        aosp_file.write(aosp_diff)

        subprocess.call(
            [
                'git',
                '--no-pager',
                'diff',
                '--no-index',
                aosp_file.name,
                repo_file.name,
            ],
            cwd=repo,
            stderr=sys.stdout,
            stdout=sys.stdout,
        )

    finally:
        repo_file.close()
        aosp_file.close()


def configure(parser: argparse.ArgumentParser):
    group = parser.add_mutually_exclusive_group(required=True)

    group.add_argument(
        '--commit',
        type=str,
        help='hash of the commit to review'
    )
    group.add_argument(
        '--pr',
        type=str,
        help='number of the pull request to review'
    )


def execute(args: argparse.Namespace):
    repo = args.repo
    git_setup_aosp(repo)

    if (args.pr):
        commit = git_fetch_pr(repo, args.pr)
    else:
        commit = args.commit

    repo_commit = git_log(repo, commit, '%H')
    aosp_commit = git_read_aosp_commit(repo, commit)

    log('genreating repo diff for %s' % repo_commit)
    repo_diff = str(generate_diff(repo, repo_commit))

    log('genreating aosp diff for %s' % aosp_commit)
    aosp_diff = aosp_process_diff(generate_diff(repo, aosp_commit))

    log('diff between applied patch and aosp patch')
    show_diff_diff(repo, repo_diff, aosp_diff)

    log('end of diff')
