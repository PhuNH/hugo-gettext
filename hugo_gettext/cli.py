# SPDX-FileCopyrightText: 2023 Phu Hung Nguyen <phuhnguyen@outlook.com>
# SPDX-License-Identifier: LGPL-2.1-or-later

import logging
from argparse import ArgumentParser, RawTextHelpFormatter

from .extraction import extract
from .generation import generate
from .compilation import compile_po


def main():
    parser = ArgumentParser(description='I18n tool with gettext for Hugo projects')
    parser.add_argument('-q', '--quiet', action='store_true', help='stop showing INFO or lower logs')
    subparsers = parser.add_subparsers(description="used in the process from extracting source files' messages "
                                                   'to generating target files')

    extract_cmd = subparsers.add_parser('extract', help='extract messages from source files',
                                        formatter_class=RawTextHelpFormatter)
    extract_cmd.add_argument('pot', help='path of the directory containing the target pot file(s)')
    extract_cmd.add_argument('-c', '--customs', help='path to Python file containing custom functions')
    extract_cmd.set_defaults(func=extract)

    generate_cmd = subparsers.add_parser('generate', help='generate target messages and files',
                                         formatter_class=RawTextHelpFormatter)
    generate_cmd.add_argument('-c', '--customs', help='path to Python file containing custom functions')
    generate_cmd.add_argument('-k', '--keep-locale', action='store_true', help='do not delete locale folder')
    generate_cmd.set_defaults(func=generate)

    compile_po_cmd = subparsers.add_parser('compile', help='compile translated messages to binary format',
                                           formatter_class=RawTextHelpFormatter)
    compile_po_cmd.add_argument('dir', help='path of the directory containing subdirectories with PO files inside,\n'
                                            'in the form of {dir}/{lang}/*.po')
    compile_po_cmd.set_defaults(func=compile_po)

    args = parser.parse_args()
    level = logging.WARNING if args.quiet else logging.INFO
    logging.basicConfig(format='%(levelname)s: %(message)s', level=level)
    args.func(args)
