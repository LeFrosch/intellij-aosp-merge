import sys
import subprocess
import argparse

from ._util import log, choose, exit

TEST_CASES = [
    ('//:clwb_tests', 'clion-oss-latest-stable'),
    ('//:ijwb_ue_tests', 'intellij-ue-oss-latest-stable'),
    ('//querysync/...', 'intellij-ue-oss-latest-stable'),
]


BUILD_CASES = [
    ('//clwb:clwb_bazel_zip', 'clion-oss-latest-stable'),
    ('//ijwb:ijwb_bazel_zip', 'intellij-ue-oss-latest-stable'),
    ('//querysync', 'intellij-ue-oss-latest-stable'),
]


def bazel_test(repo: str, target: str, ij_product: str):
    """
    Runs a bazel test command for the given target and ij_product.
    """

    while True:
        log('executing test %s' % target)

        success = subprocess.run(
            [
                'bazel',
                'test',
                target,
                '--define=ij_product=%s' % ij_product,
                '--disk_cache=/tmp/bazel_cache',
            ],
            cwd=repo,
            stderr=sys.stdout,
            stdout=sys.stdout,
        ).returncode == 0

        if success:
            log('test %s passed' % target)
            break

        result = choose(
            title='test %s failed, press enter to retry' % target,
            options=[
                '[r] retry',
                '[a] abort',
            ],
        )

        if result == "a":
            exit("test aborted")


def bazel_build(repo: str, target: str, ij_product: str):
    while True:
        log('executing build %s' % target)

        success = subprocess.run(
            [
                'bazel',
                'build',
                target,
                '--define=ij_product=%s' % ij_product,
                '--disk_cache=/tmp/bazel_cache',
            ],
            cwd=repo,
            stderr=sys.stdout,
            stdout=sys.stdout,
        ).returncode == 0

        if success:
            log('build %s passed' % target)
            break

        result = choose(
            title='build %s failed, press enter to retry' % target,
            options=[
                '[r] retry',
                '[a] abort',
            ],
        )

        if result == "a":
            exit("test aborted")


def configure(parser: argparse.ArgumentParser):
    parser.add_argument(
        '--buildonly',
        action='store_true',
        help='run build the targets',
        default=False,
    )


def execute(args: argparse.Namespace):
    if (args.buildonly):
        for (target, product) in BUILD_CASES:
            bazel_build(args.repo, target, product)
        log('all builds passed')

    else:
        for (target, product) in TEST_CASES:
            bazel_test(args.repo, target, product)
        log('all tests passed')
