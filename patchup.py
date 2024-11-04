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


def is_rename(file: PatchedFile) -> bool:
    if (file.patch_info is None):
        return False

    for line in file.patch_info:
        if (line.startswith('rename to')):
            return True

    return False


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
        ['git', 'diff', '-U5', '--binary', '-p', commit + '~1', commit],
        cwd=repo,
    )
    return PatchSet(output.decode())


def patch_process_info(info: list[str], reject: bool):
    """
    Processes the patch info. It is mutated in place.
    """

    # process a single info line
    def process(line: str) -> str:
        # strip aswb from diff target
        line = line.replace(' b/aswb/', ' b/')

        # only strip aswb from source for `--reject`
        if (reject):
            line = line.replace(' a/aswb/', ' a/')

        # fix renames for `--reject`
        if (reject):
            line = line.replace('rename to aswb/', 'rename to ')
            line = line.replace('rename from aswb/', 'rename from ')

        return line

    for i in range(len(info)):
        info[i] = process(info[i])


def patch_process_file(file: PatchedFile, reject: bool) -> str | None:
    """
    Processes a patched file. Returns either the diff for the file or none if
    the file is not relevant for the patch.

    If reject is true the patch is prepared for `--reject` otherwiese it is
    prepared for `--3way`.
    """

    # if the file is a rename, generate a reject diff
    if (not reject and is_rename(file)):
        return patch_process_file(file, reject=True)

    # only keep changes to the aswb subfolder
    source_aswb = file.source_file.startswith('a/aswb')
    target_aswb = file.target_file.startswith('b/aswb')

    # for newly add files source is /dev/null and visversa for removed files
    if (not source_aswb and not target_aswb):
        return None

    # strip the aswb subfolder
    file.target_file = file.target_file.replace('b/aswb/', 'b/')

    # only strip aswb from source for `--reject` or file deletions
    if (reject or file.target_file == '/dev/null'):
        file.source_file = file.source_file.replace('a/aswb/', 'a/')

    # same for patch info if present
    if (file.patch_info is not None):
        patch_process_info(file.patch_info, reject)

    for hunk in file:
        for line in hunk:
            line.value = deaosp(line.value)

    return str(file)


def patch_process(diff: PatchSet, reject: bool) -> str:
    """
    Processes every file in the commit and concatenates the result to on patch.
    """

    files = (patch_process_file(file, reject) for file in diff)
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


def patch_apply(patch: str, reject: bool) -> bool:
    """
    Applies the commit to the current branch. Uses a 3 way merge to handle any
    conflicts if reject is false or reject any conflicts.
    """

    result = subprocess.run(
        ['git', 'am', '--reject', '--no-3way']
        if reject else ['git', 'am', '--3way'],
        cwd=repo,
        input=bytes(patch, encoding='utf-8'),
        stderr=sys.stdout,
        stdout=sys.stdout,
    )

    print(result)
    return result.returncode == 0


def patch_generate(commit: str, reject: bool) -> str:
    """
    Generates a patch from the aosp commit for the idea repository.

    If reject is true the patch is prepared for `--reject` otherwiese it is
    prepared for `--3way`.
    """

    header = patch_generate_header(commit)
    diff = patch_generate_diff(commit)
    patch = patch_process(diff, reject)

    if (reject):
        print('-> patch generated for reject')
    else:
        print('-> patch generated for 3way merge')

    return '%s\n%s' % (header, patch)


def abort_am():
    """
    Aborts an am merge. Used after 3way merge failed.
    """

    subprocess.check_call(
        ['git', 'am', '--abort'],
        cwd=repo,
    )


def main():
    commit = sys.argv[1]

    aosp_remote()
    aosp_fetch()

    patch = patch_generate(commit, reject=False)
    success = patch_apply(patch, reject=False)

    if (success):
        print('-> patch applied')
        return

    answer = input('-> 3way merge failed, fallback to no-3way? [y/n]')
    if (answer != 'y'):
        print('-> patch failed')
        return

    abort_am()

    patch = patch_generate(commit, reject=True)
    success = patch_apply(patch, reject=True)

    if (success):
        print('-> patch applied')
    else:
        print('-> patch applied with rejects')


if __name__ == '__main__':
    main()
