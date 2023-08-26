# SPDX-FileCopyrightText: 2023 Phu Hung Nguyen <phuhnguyen@outlook.com>
# SPDX-License-Identifier: LGPL-2.1-or-later

import logging
from typing import List

from markdown_it import MarkdownIt

from .extraction_utils import Entry, Occurrence, I18NEnv
from .i18n_object import i12ize_object
from .. import utils
from ..config import Config


def i12ize_data_files(entries: List[Entry], hg_config: Config, mdi: MarkdownIt):
    for path, data in utils.read_data_files(hg_config).items():
        i12ize_object(data, I18NEnv(path, entries, hg_config, mdi))
        logging.info(path)


def i12ize_data_others(entries: List[Entry], hg_config: Config, mdi: MarkdownIt):
    # config fields
    path = 'config.yaml'
    default_language_config = hg_config.hugo_config.get('languages', {}).get('en', {})
    if hg_config.do_title:
        if 'title' not in default_language_config:
            logging.warning(f"Default language config section doesn't have a `title` field.")
        else:
            entries.append(Entry(default_language_config['title'], Occurrence(path, 0)))
    if hg_config.do_description:
        if 'params' not in default_language_config or 'description' not in default_language_config['params']:
            logging.warning(f"Default language config section doesn't have a `params.description` field.")
        else:
            entries.append(Entry(default_language_config['params']['description'], Occurrence(path, 0)))
    if hg_config.do_menu:
        for menu_entry in default_language_config['menu']['main']:
            entries.append(Entry(menu_entry['name'], Occurrence(path, 0)))
    # data
    if hg_config.data:
        i12ize_data_files(entries, hg_config, mdi)
    # strings
    if hg_config.do_strings:
        path = 'i18n/en.yaml'
        src_strings = utils.read_strings()
        for _, string in src_strings.items():
            entries.append(Entry(string['other'], Occurrence(path, 0), string.get('comment', '')))
