# SPDX-FileCopyrightText: 2023 Phu Hung Nguyen <phuhnguyen@outlook.com>
# SPDX-License-Identifier: LGPL-2.1-or-later

import logging
import os
import subprocess

import polib


def compile_po(args):
    """Compile translated messages to binary format stored in 'locale/{lang}/LC_MESSAGES' directory
    :param args: arguments passed in command line, containing
        - dir: path of the directory containing subdirectories with PO files inside, in the form of {dir}/{lang}/*.po
    :return: None
    """
    po_dir = args.dir

    with_gettext = True
    test_gettext_cmd = 'msgfmt -V'
    try:
        # do not show the output of running test_gettext_cmd
        subprocess.run(test_gettext_cmd, shell=True, check=True, capture_output=True)
    except subprocess.CalledProcessError:
        with_gettext = False

    for lang in os.listdir(po_dir):
        target_path = f'locale/{lang}/LC_MESSAGES'
        os.makedirs(target_path, exist_ok=True)
        src_path = f'{po_dir}/{lang}'

        for po in os.listdir(src_path):
            po_path = f'{src_path}/{po}'
            mo_path = f'{target_path}/{po[:-2]}mo'
            if not with_gettext:
                polib.pofile(po_path).save_as_mofile(mo_path)
                continue

            command = f'msgfmt {po_path} -o {mo_path}'
            try:
                os.remove(mo_path)
                logging.info(f'Removed {mo_path}')
            except OSError:
                logging.info(f"{mo_path} doesn't exist or can't be removed")
                pass
            subprocess.run(command, shell=True, check=True)
            logging.info(f'Created {mo_path}')
        logging.info(f'Compiled {lang}')
