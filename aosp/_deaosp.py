import os
import argparse

from ._util import log


def repo(label):
    """
    Creates two replacements for a repository label. One for trailing `/` and
    one for `:`.
    """

    return {
        f'{label}/': '//',
        f'{label}:': '//:',
    }


def path(value):
    """
    Creates two replacements for a path. One for trailing `/` and without.
    """

    return {
        f'{value}/': '',
        f'{value}': '',
    }


REPLACEMENTS = {
    # remap aosp relative labels
    **repo('//tools/adt/idea/aswb'),
    **repo('//tools/vendor/google/aswb'),
    **repo('//tools/vendor/google3/aswb'),
    **repo('//third_party/intellij/bazel/plugin'),
    **repo('//third_party/intellij/plugin'),
    '//third_party/java/auto_value': '//third_party/java/auto_value',
    '//third_party/java/auto:auto_value': '//third_party/java/auto_value',
    '//third_party/java/jetbrains:build_defs.bzl': '//intellij_platform_sdk:build_defs.bzl',
    '//third_party/java/junit': '//third_party/java/junit',
    '//third_party/java/truth': '//third_party/java/truth',
    '//third_party/java/flogger': '//third_party/java/flogger',
    '//third_party/java/jetbrains/python': '//third_party/python',
    '//prebuilts/tools/common/m2:jsr305-2.0.1': '@jsr305_annotations//jar',

    # remap plugin api
    '//plugin_api:guava_for_external_binaries': '//intellij_platform_sdk:guava',
    '//plugin_api:jsr305': '//intellij_platform_sdk:jsr305',
    '//plugin_api:test_libs': '//intellij_platform_sdk:test_libs',
    '//plugin_api:plugin_api_for_tests': '//intellij_platform_sdk:plugin_api_for_tests',
    '//plugin_api:coverage_for_tests': '//intellij_platform_sdk:coverage_for_tests',
    '//plugin_api:truth': '//intellij_platform_sdk:truth',
    '//plugin_api:juint': '//intellij_platform_sdk:juint',
    '//plugin_api:kotlin_for_tests': '//intellij_platform_sdk:kotlin_for_tests',
    '//plugin_api:kotlin': '//intellij_platform_sdk:kotlin',
    '//plugin_api:terminal': '//intellij_platform_sdk:terminal',
    '//plugin_api:devkit': '//intellij_platform_sdk:plugin_api:devkit',
    '//plugin_api': '//intellij_platform_sdk:plugin_api',

    # remap to old maven import style
    '@maven//:com.google.guava.guava': '@com_google_guava_guava//jar',
    '@maven//:io.grpc.grpc-protobuf-lite': '@protobuf//:protobuf_java',
    '@maven//:io.grpc.grpc-protobuf': '@protobuf//:protobuf_java',
    '@maven//:com.google.protobuf.protobuf-java': '@protobuf//:protobuf_java',
    '@maven//:org.mockito.mockito-core': '@mockito//jar',
    '@maven//:com.google.code.gson.gson': '@gson//jar',
    '@maven//:com.google.errorprone.error_prone_annotations': '@error_prone_annotations//jar',

    # remap to rules
    '//:android.bzl': '@rules_android//rules:rules.bzl',
    '//tools/base/bazel:kotlin.bzl': '@rules_kotlin//kotlin:jvm.bzl',

    # remap aosp paths
    **path('tools/adt/idea/aswb'),
    **path('tools/vendor/google3/aswb/third_party/intellij/bazel/plugin'),

    # other fixes
    '@com_google_protobuf//:protobuf_java': '@protobuf//:protobuf_java',
}


def process(text: str) -> str:
    """
    Processes one text line. Applies all defined replacements.
    """

    for src, dst in REPLACEMENTS.items():
        text = text.replace(src, dst)

    return text


def walk(path):
    """
    Walks a directory and processes every file in the directory.
    """

    for dir, _, files in os.walk(path):
        for name in files:
            file = os.path.join(dir, name)

            try:
                with open(file, 'r') as f:
                    text = f.read()
            except Exception:
                log('skipping file: ' + file)
                continue

            text = process(text)

            with open(file, 'w') as f:
                f.write(text)


def configure(parser: argparse.ArgumentParser):
    parser.add_argument(
        'path',
        type=str,
        help='path of the directory to convert'
    )


def execute(args: argparse.Namespace):
    log('walking directory %s' % args.path)
    walk(args.path)
