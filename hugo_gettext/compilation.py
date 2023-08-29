# SPDX-FileCopyrightText: 2023 Phu Hung Nguyen <phuhnguyen@outlook.com>
# SPDX-License-Identifier: LGPL-2.1-or-later

import logging
import os
import subprocess


def compile_po(args):
    """Compile translated messages to binary format stored in 'locale/{lang}/LC_MESSAGES' directory
    :param args: arguments passed in command line, containing
        - dir: path of the directory containing subdirectories with PO files inside, in the form of {dir}/{lang}/*.po
    :return: None
    """
    po_dir = args.dir
    for lang in os.listdir(po_dir):
        target_path = f'locale/{lang}/LC_MESSAGES'
        os.makedirs(target_path, exist_ok=True)
        src_path = f'{po_dir}/{lang}'

        for po in os.listdir(src_path):
            po_path = f'{src_path}/{po}'
            mo_path = f'{target_path}/{po[:-2]}mo'
            command = f'msgfmt {po_path} -o {mo_path}'
            subprocess.run(command, shell=True, check=True)
        logging.info(f'Compiled {lang}')
