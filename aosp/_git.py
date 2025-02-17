import subprocess
import sys
import os

from ._consts import (
    AOSP_REMOTE,
    AOSP_ORIGIN,
    AOSP_BRANCH,
    INTELLIJ_REMOTE,
    INTELLIJ_ORIGIN,
    INTELLIJ_BRANCH,
)

from ._util import log, log_error


def git_add_remote(repo: str, origin: str, remote: str):
    """
    Adds a remote to the repository or checks that the remote points to the
    right URL if it exists.
    """

    try:
        output = subprocess.check_output(
            ['git', 'remote', 'get-url', origin],
            cwd=repo,
        )

        if (output.decode().strip() == remote):
            return

        log_error(
            'remote %s exists but does not point to %s' % (origin, remote)
        )

    except subprocess.CalledProcessError:
        # get url failed, most likely because remote does not exist
        subprocess.check_call(
            ['git', 'remote', 'add', origin, remote],
            cwd=repo,
            stderr=subprocess.DEVNULL,
            stdout=subprocess.DEVNULL,
        )
        log('added %s remote' % origin)


def git_fetch_remote(repo: str, origin: str, branch: str):
    """
    Fetches a branch from the origin.
    """

    subprocess.check_call(
        ['git', 'fetch', origin, branch],
        cwd=repo,
        stderr=sys.stdout,
        stdout=sys.stdout,
    )
    log('%s up to date' % origin)


def git_setup_aosp(repo: str):
    """
    Adds the aosp remote to the repository and fetches the main branch.
    """

    git_add_remote(repo, AOSP_ORIGIN, AOSP_REMOTE)
    git_fetch_remote(repo, AOSP_ORIGIN, AOSP_BRANCH)


def git_setup_intellij(repo: str):
    """
    Adds the intelli remote to the repository and fetches the main branch.
    """

    git_add_remote(repo, INTELLIJ_ORIGIN, INTELLIJ_REMOTE)
    git_fetch_remote(repo, INTELLIJ_ORIGIN, INTELLIJ_BRANCH)


def git_log(repo: str, commit: str, format: str) -> str:
    """
    Runs git log for the specified commit and uses the format specifier.

    Formats:
        %s   Commit subject
        %b   Commit body
        %ad  Author data
        %H   Commit hash
    """

    output = subprocess.check_output(
        ['git', 'log', '--pretty=format:' + format, '-n 1', commit],
        cwd=repo,
    )
    return output.decode()


def git_rebase_in_progress(repo: str) -> bool:
    """
    Checks if the .git/rebase-apply directory exists. Simple heuristic if a git
    am is in progress.
    """

    return os.path.isdir(os.path.join(repo, '.git', 'rebase-apply'))


def git_try_read_aosp_commit(repo: str, commit: str) -> str | None:
    """
    Finds the `AOSP: ...` line in the commit body and returns the AOSP commit
    hash or None if there is no such line.
    """

    body = git_log(repo, commit, '%b')
    aosp_lines = [line for line in body.splitlines()
                  if line.startswith('AOSP: ')]

    if len(aosp_lines) == 0:
        return None

    if len(aosp_lines) > 1:
        return None

    return aosp_lines[0][6:]


def git_read_aosp_commit(repo: str, commit: str) -> str:
    """
    Finds the `AOSP: ...` line in the commit body and returns the AOSP commit
    hash or errors if there is no such line.
    """

    aosp_commit = git_try_read_aosp_commit(repo, commit)

    if aosp_commit is None:
        log_error(
            'commit body contains more than one aosp reference:\n %s' % commit
        )

    return aosp_commit


def git_branch_contains(repo: str, origin: str, branch: str, commit: str) -> bool:
    """
    Checks if a branch contains the specific commit.
    """

    result = subprocess.run(
        [
            'git',
            'merge-base',
            '--is-ancestor',
            commit,
            '%s/%s' % (origin, branch),
        ],
        cwd=repo,
    )

    if result.returncode not in [0, 1]:
        log_error('git contains check failed: %d' % result.returncode)

    return result.returncode == 0


def git_list_files(repo: str, commit: str) -> list[str]:
    """
    Gets all files modified by this commit.
    """

    output = subprocess.check_output(
        ['git', 'diff-tree', '--no-commit-id', '--name-only', commit, '-r'],
        cwd=repo,
    )

    files = output.decode().splitlines()

    # if the commit from the aosp brnach, the file paths need to be remapped
    if not git_branch_contains(repo, AOSP_ORIGIN, AOSP_BRANCH, commit):
        return files

    return [file.removeprefix('aswb/') for file in files]


def git_parse_rev(repo: str, rev: str) -> str:
    """
    Gets the hash of a revision like HEAD.
    """

    return subprocess.check_output(
        ['git', 'rev-parse', rev],
        cwd=repo,
    ).decode().strip()
