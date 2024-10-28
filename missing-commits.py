import git
import pathlib
import subprocess
from datetime import datetime

url = 'https://github.com/bazelbuild/intellij/commit/'
dir = '/home/daniel_brauner/Projects/bazel/intellij'


def collect_missing_commits() -> list[str]:
    output = subprocess.check_output(['git', 'cherry', '-v', 'master', 'google'], cwd=dir)
    lines = output.decode().splitlines()

    return [it.split(' ')[1] for it in lines if it[0] == '+']


if __name__ == '__main__':
    missing = collect_missing_commits()

    csv = open('out.csv', 'wt')

    repo = git.Repo(dir)
    for commit_hash in missing:
        commit = repo.commit(commit_hash)
        row = '=HYPERLINK("%s%s", "%s");%s;%s;%d;%s\n' % (
            url,
            commit.hexsha,
            commit.hexsha,
            commit.message.partition('\n')[0],
            datetime.fromtimestamp(commit.committed_date).date(),
            commit.size,
            ', '.join({pathlib.Path(it).parts[0] for it in commit.stats.files})
        )

        csv.write(row)

    csv.close()
