import sys
import subprocess
import argparse
import dataclasses

from ._util import log, choose, exit


@dataclasses.dataclass
class Case:
    target: str
    product: str
    flags: list[str] = dataclasses.field(default_factory=list)


TEST_CASES = [
    Case(
        target='//clwb:unit_tests',
        product='clion-oss-latest-stable',
    ),
    Case(
        target='//clwb:headless_tests',
        product='clion-oss-latest-stable',
        flags=['--test_tag_filters=bit_bazel_8_4_0'],
    ),
]


BUILD_CASES = [
    Case(
        target='//clwb:clwb_bazel_zip',
        product='clion-oss-latest-stable',
    ),
    Case(
        target='//:clwb_tests',
        product='clion-oss-latest-stable',
    ),
]


def bazel_test(repo: str, case: Case):
    """
    Runs a bazel test command for the given target and ij_product.
    """

    while True:
        log('executing test %s' % case.target)

        success = subprocess.run(
            [
                'bazel',
                'test',
                case.target,
                '--define=ij_product=%s' % case.product,
                '--disk_cache=/tmp/bazel_cache',
                *case.flags,
            ],
            cwd=repo,
            stderr=sys.stdout,
            stdout=sys.stdout,
        ).returncode == 0

        if success:
            log('test %s passed' % case.target)
            break

        result = choose(
            title='test %s failed, press enter to retry' % case.target,
            options=[
                '[r] retry',
                '[a] abort',
            ],
        )

        if result == "a":
            exit("test aborted")


def bazel_build(repo: str, case: Case):
    while True:
        log('executing build %s' % case.target)

        success = subprocess.run(
            [
                'bazel',
                'build',
                case.target,
                '--define=ij_product=%s' % case.product,
                '--disk_cache=/tmp/bazel_cache',
                *case.flags,
            ],
            cwd=repo,
            stderr=sys.stdout,
            stdout=sys.stdout,
        ).returncode == 0

        if success:
            log('build %s passed' % case.target)
            break

        result = choose(
            title='build %s failed, press enter to retry' % case.target,
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
        for case in BUILD_CASES:
            bazel_build(args.repo, case)
        log('all builds passed')

    else:
        for case in TEST_CASES:
            bazel_test(args.repo, case)
        log('all tests passed')
