import sys
import subprocess
import argparse
import os

from unidiff import PatchSet, PatchedFile

from ._git import git_add_aosp, git_fetch_aosp, git_log
from ._deaosp import process as deaosp
from ._util import log, log_error, filter_none, choose

MAGIC_DATE = 'From %s Mon Sep 17 00:00:00 2001'
AUTHOR = 'Googler <intellij-github@google.com>'

repo = '/Volumes/Projects/bazel/intellij'


def patch_generate_diff(repo: str, commit: str) -> PatchSet:
    """
    Generates and parsed the git diff for the patch.
    """

    output = subprocess.check_output(
        ['git', 'diff', '-U8', '--binary', '-p', commit + '~1', commit],
        cwd=repo,
    )
    return PatchSet(output.decode())


def patch_process_info(info: list[str]):
    """
    Processes the patch info. It is mutated in place.
    """

    # process a single info line
    def process(line: str) -> str:
        # strip aswb from diff target
        line = line.replace(' a/aswb/', ' a/')
        line = line.replace(' b/aswb/', ' b/')

        # strip aswb from rename targets
        line = line.replace('rename to aswb/', 'rename to ')
        line = line.replace('rename from aswb/', 'rename from ')

        return line

    for i in range(len(info)):
        info[i] = process(info[i])


def patch_process_file(file: PatchedFile) -> str | None:
    """
    Processes a patched file. Returns either the diff for the file or none if
    the file is not relevant for the patch.

    If reject is true the patch is prepared for `--reject` otherwiese it is
    prepared for `--3way`.
    """

    # only keep changes to the aswb subfolder
    source_aswb = file.source_file.startswith('a/aswb')
    target_aswb = file.target_file.startswith('b/aswb')

    # for newly add files source is /dev/null and visversa for removed files
    if (not source_aswb and not target_aswb):
        return None

    # strip the aswb subfolder
    file.source_file = file.source_file.replace('a/aswb/', 'a/')
    file.target_file = file.target_file.replace('b/aswb/', 'b/')

    # same for patch info if present
    if (file.patch_info is not None):
        patch_process_info(file.patch_info)

    for hunk in file:
        for line in hunk:
            line.value = deaosp(line.value)

    return str(file)


def patch_process(diff: PatchSet) -> str:
    """
    Processes every file in the commit and concatenates the result to on patch.
    """

    files = (patch_process_file(file) for file in diff)
    return ''.join(filter_none(files))


def patch_generate_header(repo: str, commit: str) -> str:
    """
    Generates the header for the patch. Copies evertying from the original
    commit but overrides the author and adds the aosp commit id.
    """

    date = MAGIC_DATE % commit
    author = 'From: %s' % AUTHOR
    author_date = 'Data: %s' % git_log(repo, commit, '%ad')
    subject = 'Subject: [PATCH] %s' % git_log(repo, commit, '%s')
    body = git_log(repo, commit, '%b')
    aosp = 'AOSP: %s' % commit

    return '\n'.join([date, author, author_date, subject, '', body, aosp])


def patch_apply(repo: str, patch: str, reject: bool) -> bool:
    """
    Applies the commit to the current branch. Uses a 3 way merge to handle any
    conflicts if reject is false or reject any conflicts.
    """

    result = subprocess.run(
        ['git', 'am', '--reject', '--no-3way', '-C3']
        if reject else ['git', 'am', '--3way', '-C3'],
        cwd=repo,
        input=bytes(patch, encoding='utf-8'),
        stderr=sys.stdout,
        stdout=sys.stdout,
    )

    return result.returncode == 0


def patch_generate(repo: str, commit: str) -> str:
    """
    Generates a patch from the aosp commit for the idea repository.

    If reject is true the patch is prepared for `--reject` otherwiese it is
    prepared for `--3way`.
    """

    header = patch_generate_header(repo, commit)
    diff = patch_generate_diff(repo, commit)
    patch = patch_process(diff)

    log('patch generated')

    return '%s\n%s' % (header, patch)


def git_am_continue(repo: str):
    """
    Runs a git am --coninue command
    """

    subprocess.check_call(
        ['git', 'am', '--continue'],
        cwd=repo,
    )


def git_am_abort(repo: str):
    """
    Runs a git am --abort command
    """

    subprocess.check_call(
        ['git', 'am', '--abort'],
        cwd=repo,
    )


def git_rebase_in_progress(repo: str) -> bool:
    """
    Checks if the .git/rebase-apply directory exists. Simple heuristic if a git
    am is in progress.
    """

    return os.path.isdir(os.path.join(repo, '.git', 'rebase-apply'))


def delete_reject_files(repo: str) -> bool:
    """
    Deletes all reject files that might be left over.
    """

    for dir, _, files in os.walk(repo):
        for name in files:
            if name.endswith('.rej'):
                os.remove(os.path.join(dir, name))


def try_3way_merge(repo: str, patch: str) -> bool:
    success = patch_apply(repo, patch, reject=False)

    if success:
        log('patch applied')
        return True

    # if the patch failed but a rebase is in progress, there are conflicts
    if not git_rebase_in_progress(repo):
        log('patch failed')
        return False

    result = choose(
        title='patch could not be applied automaticaly',
        options=[
            '[c] resolved conflicts, continue',
            '[a] abort',
        ],
    )

    if result == 'a':
        git_am_abort(repo)
        log('patch aborted')
        return False

    git_am_continue(repo)
    log('patch applied')

    return True


def try_reject_merge(repo: str, patch: str) -> bool:
    success = patch_apply(repo, patch, reject=True)

    if success:
        log('patch applied')
        return True

    result = choose(
        title='patch could not be applied automaticaly',
        options=[
            '[c] resolved conflicts, continue',
            '[a] abort',
        ],
    )

    delete_reject_files(repo)

    if result == 'a':
        git_am_abort(repo)
        log('patch aborted')
        return False

    git_am_continue(repo)
    log('patch applied')

    return True


def configure(parser: argparse.ArgumentParser):
    parser.add_argument(
        'commit',
        type=str,
        help='hash of the commit to pick'
    )


def execute(args: argparse.Namespace):
    if git_rebase_in_progress(args.repo):
        log_error('a rebase is in progress')

    repo = args.repo

    git_add_aosp(repo)
    git_fetch_aosp(repo)

    patch = patch_generate(repo, args.commit)
    return try_3way_merge(repo, patch) or try_reject_merge(repo, patch)
