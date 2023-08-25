# SPDX-FileCopyrightText: 2023 Phu Hung Nguyen <phuhnguyen@outlook.com>
# SPDX-License-Identifier: LGPL-2.1-or-later

import logging
from argparse import ArgumentParser, RawTextHelpFormatter

from .extraction import extract
from .generation import generate


def main():
    parser = ArgumentParser(description='I18n tool for Hugo projects, working in coordination with scripty')
    parser.add_argument('-q', '--quiet', action='store_true', help='stop showing INFO or lower logs')
    # TODO: is this only for generation or for something else too?
    parser.add_argument('-c', '--customs', help='path to Python file containing custom functions')
    subparsers = parser.add_subparsers(description="used in the process from extracting source files' messages "
                                                   'to generating target files')

    extract_cmd = subparsers.add_parser('extract', help='extract messages from source files',
                                        formatter_class=RawTextHelpFormatter)
    extract_cmd.add_argument('pot', help='either path of the only target pot file or path of the directory\n'
                                         'containing the target pot file(s)')
    extract_cmd.set_defaults(func=extract)

    generate_cmd = subparsers.add_parser('generate', help='generate target messages and files',
                                         formatter_class=RawTextHelpFormatter)
    generate_cmd.add_argument('-k', '--keep-locale', action='store_true', help='do not delete locale folder')
    generate_cmd.set_defaults(func=generate)

    args = parser.parse_args()
    level = logging.WARNING if args.quiet else logging.INFO
    logging.basicConfig(format='%(levelname)s: %(message)s', level=level)
    args.func(args)
