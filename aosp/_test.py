import sys
import subprocess
import argparse

from ._util import log, choose, exit

TEST_CASES = [
    ('//:clwb_tests', 'clion-oss-latest-stable'),
    ('//:ijwb_ue_tests', 'intellij-ue-oss-latest-stable'),
    ('//querysync/...', 'intellij-ue-oss-latest-stable'),
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


def configure(parser: argparse.ArgumentParser):
    pass


def execute(args: argparse.Namespace):
    for (target, product) in TEST_CASES:
        bazel_test(args.repo, target, product)

    log('all tests passed')
