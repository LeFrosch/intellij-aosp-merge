import argparse
import subprocess
import tempfile
import sys

from unidiff import PatchSet

from ._patch import patch_process as aosp_process_diff
from ._git import git_add_aosp, git_fetch_aosp, git_log
from ._util import log, log_error


def get_aosp_commit(repo: str, commit: str) -> str:
    body = git_log(repo, commit, '%b')
    line = body.splitlines()[-1]

    if (not line.startswith('AOSP: ')):
        log_error('commit body does not contain a aosp reference')

    return line[6:]


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


def execute(args: argparse.Namespace):
    repo = args.repo

    git_add_aosp(repo)
    git_fetch_aosp(repo)

    repo_commit = git_log(repo, args.commit, '%H')
    aosp_commit = get_aosp_commit(repo, args.commit)

    log('genreating repo diff for %s' % repo_commit)
    repo_diff = str(generate_diff(repo, repo_commit))

    log('genreating aosp diff for %s' % aosp_commit)
    aosp_diff = aosp_process_diff(generate_diff(repo, aosp_commit))

    log('diff between applied patch and aosp patch')
    show_diff_diff(repo, repo_diff, aosp_diff)

    log('end of diff')
