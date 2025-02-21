import argparse
import subprocess
import tempfile
import sys

from unidiff import PatchSet

from ._git import (
    git_setup_aosp,
    git_setup_intellij,
    git_log,
    git_read_aosp_commit,
    git_parse_rev,
)

from ._patch import patch_process as aosp_process_diff
from ._consts import INTELLIJ_ORIGIN
from ._util import log, log_error


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

        for hunk in file:
            hunk.source_start = 0
            hunk.source_length = 0
            hunk.target_start = 0
            hunk.target_length = 0

    return patch


def generate_stat(repo: str, repo_commit: str, aosp_commit: str) -> (int, int):
    """
    Similar to show_diff_diff but only calculates the different insertions and
    deletions from the diff. Useful for a quick overview how many mnuall
    changes have been made to a patch.
    """

    repo_diff = str(generate_diff(repo, repo_commit))
    aosp_diff = aosp_process_diff(generate_diff(repo, aosp_commit))

    repo_file = tempfile.NamedTemporaryFile(mode='wt')
    aosp_file = tempfile.NamedTemporaryFile(mode='wt')

    try:
        repo_file.write(repo_diff)
        repo_file.flush()
        aosp_file.write(aosp_diff)
        aosp_file.flush()

        result = subprocess.run(
            [
                'git',
                'diff',
                '--numstat',
                '--no-index',
                aosp_file.name,
                repo_file.name,
            ],
            capture_output=True,
            text=True,
            check=False,
        )

        # diff returns 0 when there are no changes
        if result.returncode == 0:
            return (0, 0)

        # diff returns 1 when there are changes
        if result.returncode != 1:
            return None

        diff = result.stdout.splitlines()
        if len(diff) == 0:
            return None

        insertions, deletions = diff[0].split('\t')[0:2]
        return (int(insertions), int(deletions))

    finally:
        repo_file.close()
        aosp_file.close()


def show_diff_diff(repo: str, repo_commit: str, aosp_commit: str):
    """
    Creates a diff from the changes applied to our repository and the changes
    applied to the AOSP repository. Adjusts the diffs to reduce the noise,
    stripping filenames and line numbers.
    """

    repo_diff = str(generate_diff(repo, repo_commit))
    aosp_diff = aosp_process_diff(generate_diff(repo, aosp_commit))

    repo_file = tempfile.NamedTemporaryFile(mode='wt')
    aosp_file = tempfile.NamedTemporaryFile(mode='wt')

    try:
        repo_file.write(repo_diff)
        repo_file.flush()
        aosp_file.write(aosp_diff)
        aosp_file.flush()

        subprocess.call(
            [
                'git',
                'diff',
                '--no-index',
                aosp_file.name,
                repo_file.name,
            ],
            stderr=sys.stdout,
            stdout=sys.stdout,
        )

    finally:
        repo_file.close()
        aosp_file.close()


def show_range_diff(repo: str, repo_commit: str, aosp_commit: str):
    """
    Uses git range diff to compar the changes between our repository and the
    AOSP repository. Should be considered the default for reviewing patches.
    """

    subprocess.call(
        [
            'git',
            'range-diff',
            '-b',
            '%s^..%s' % (aosp_commit, aosp_commit),
            '%s^..%s' % (repo_commit, repo_commit),
        ],
        cwd=repo,
        stderr=sys.stdout,
        stdout=sys.stdout,
    )


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

    parser.add_argument(
        '--mode',
        choices=['diff', 'range', 'stat'],
        help='review mode (diff, range, stat)',
        default='range',
    )


def execute(args: argparse.Namespace):
    repo = args.repo
    git_setup_aosp(repo)
    git_setup_intellij(repo)

    if args.pr:
        commit = git_fetch_pr(repo, args.pr)
    else:
        commit = args.commit

    repo_commit = git_log(repo, commit, '%H')
    log('reviewing: %s' % git_log(repo, repo_commit, '%s'))

    aosp_commit = git_read_aosp_commit(repo, commit)

    if args.mode == 'diff':
        show_diff_diff(repo, repo_commit, aosp_commit)
    elif args.mode == 'range':
        show_range_diff(repo, repo_commit, aosp_commit)
    elif args.mode == 'stat':
        insertions, deletions = generate_stat(repo, repo_commit, aosp_commit)
        log('STAT: %d insertions(+), %d deletion(-)' % (insertions, deletions))
    else:
        log_error('unknonw diff mode: %s' % args.mode)
