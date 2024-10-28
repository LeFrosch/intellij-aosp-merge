import sys
import subprocess

from unidiff import PatchSet, PatchedFile


dir = '/home/daniel_brauner/Projects/bazel/idea'


def filter_none(generator):
    return (x for x in generator if x is not None)


def generate_diff(commit: str) -> PatchSet:
    output = subprocess.check_output(
        ['git', 'diff', '-p', commit, commit + '~1'],
        cwd=dir,
    )
    return PatchSet(output.decode())


def process(file: PatchedFile) -> str | None:
    # only keep changes to the aswb subfolder
    if (not file.source_file.startswith('a/aswb')):
        return None

    # strip the aswb subfolder
    file.source_file = 'a/' + file.source_file[7:]
    file.target_file = 'b/' + file.target_file[7:]

    return str(file)


if __name__ == '__main__':
    diff = generate_diff(sys.argv[1])
    body = ''.join(filter_none(process(file) for file in diff))

    print(body)
