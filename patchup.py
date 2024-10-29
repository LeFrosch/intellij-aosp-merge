import sys
import os
import subprocess

from deaosp import process as deaosp

from unidiff import PatchSet, PatchedFile

AOSP_REMOTE = 'https://android.googlesource.com/platform/tools/adt/idea'
AOSP_BRANCH = 'mirror-goog-studio-main'

MAGIC_DATE = 'From %s Mon Sep 17 00:00:00 2001'
AUTHOR = 'Googler <intellij-github@google.com>'

repo = '/Volumes/Projects/bazel/intellij'


def log_error(message: str):
    print(message, file=sys.stderr)
    sys.exit(1)


def filter_none(generator):
    return (x for x in generator if x is not None)


def generate_log(commit: str, format: str) -> str:
    output = subprocess.check_output(
        ['git', 'log', '--pretty=format:' + format, '-n 1', commit],
        cwd=repo,
    )
    return output.decode()


def aosp_remote():
    """
    Adds the aosp remote to the repository. The remote is required to fetch the
    commit and for the 3-way merge.
    """

    try:
        output = subprocess.check_output(
            ['git', 'remote', 'get-url', 'aosp'],
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
            ['git', 'remote', 'add', 'aosp', AOSP_REMOTE],
            cwd=repo,
        )
        print('-> added aosp remote')


def aosp_fetch():
    """
    Fetches the main branch from the aosp repository.
    """

    subprocess.check_call(
        ['git', 'fetch', 'aosp', AOSP_BRANCH],
        cwd=repo,
        stderr=sys.stdout,
        stdout=sys.stdout,
    )
    print('-> aosp up to date')


def patch_generate_diff(commit: str) -> PatchSet:
    """
    Generates and parsed the git diff for the patch.
    """

    output = subprocess.check_output(
        ['git', 'diff', '--binary', '-p', commit + '~1', commit],
        cwd=repo,
    )
    return PatchSet(output.decode())


def patch_process_file(file: PatchedFile) -> str | None:
    """
    Processes a patched file. Returns either the diff for the file or none if
    the file is not relevant for the patch.
    """

    # only keep changes to the aswb subfolder
    source_aswb = file.source_file.startswith('a/aswb')
    target_aswb = file.target_file.startswith('b/aswb')

    # for newly add files source is /dev/null and visversa for removed files
    if (not source_aswb and not target_aswb):
        return None

    # strip the aswb subfolder, only from target to not confuse git
    file.target_file = file.target_file.replace('b/aswb/', 'b/')

    # same for patch info if present
    if (file.patch_info is not None):
        for i in range(len(file.patch_info)):
            file.patch_info[i] = file.patch_info[i].replace('b/aswb/', 'b/')

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


def patch_generate_header(commit: str) -> str:
    """
    Generates the header for the patch. Copies evertying from the original
    commit but overrides the author and adds the aosp commit id.
    """

    date = MAGIC_DATE % commit
    author = 'From: %s' % AUTHOR
    author_date = 'Data: %s' % generate_log(commit, '%ad')
    subject = 'Subject: [PATCH] %s' % generate_log(commit, '%s')
    body = generate_log(commit, '%b')
    aosp = 'AOSP: %s' % commit

    return '\n'.join([date, author, author_date, subject, '', body, aosp])


def patch_apply(patch: str):
    """
    Applies the commit to the current branch. Uses a 3 way merge to handle any
    conflicts.
    """

    subprocess.run(
        ['git', 'am', '-3'],
        cwd=repo,
        input=bytes(patch, encoding='utf-8'),
        stderr=sys.stdout,
        stdout=sys.stdout,
    )
    print('-> patch applied')


def patch_generate(commit: str) -> str:
    """
    Generates a patch from the aosp commit for the idea repository.
    """

    header = patch_generate_header(commit)
    diff = patch_generate_diff(commit)
    patch = patch_process(diff)

    print('-> patch generated')

    return '%s\n%s' % (header, patch)


if __name__ == '__main__':
    commit = sys.argv[1]

    aosp_remote()
    aosp_fetch()

    patch = patch_generate(commit)
    patch_apply(patch)
