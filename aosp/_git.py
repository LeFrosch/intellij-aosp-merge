import subprocess
import sys

from ._util import log, log_error
from ._aosp import AOSP_REMOTE, AOSP_ORIGIN, AOSP_BRANCH


def git_add_aosp(repo: str):
    """
    Adds the aosp remote to the repository or checks that the remote points to
    the right URL if it exists.
    """

    try:
        output = subprocess.check_output(
            ['git', 'remote', 'get-url', AOSP_ORIGIN],
            cwd=repo,
        )

        if (output.decode().strip() == AOSP_REMOTE):
            return

        log_error(
            'remote aosp exists but does not point to %s' % AOSP_REMOTE
        )

    except subprocess.CalledProcessError:
        # get url failed, most likely because remote does not exist
        subprocess.check_call(
            ['git', 'remote', 'add', AOSP_ORIGIN, AOSP_REMOTE],
            cwd=repo,
        )
        log('added aosp remote')


def git_fetch_aosp(repo: str):
    """
    Fetches the main branch from the aosp repository.
    """

    subprocess.check_call(
        ['git', 'fetch', AOSP_ORIGIN, AOSP_BRANCH],
        cwd=repo,
        stderr=sys.stdout,
        stdout=sys.stdout,
    )
    log('aosp up to date')


def git_log(repo: str, commit: str, format: str) -> str:
    """
    Runs git log for the specified commit and uses the format specifier.

    Formats:
        %s   Commit subject
        %b   Commit body
        %ad  Author data
    """

    output = subprocess.check_output(
        ['git', 'log', '--pretty=format:' + format, '-n 1', commit],
        cwd=repo,
    )
    return output.decode()
