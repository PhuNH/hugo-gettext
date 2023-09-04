# SPDX-FileCopyrightText: 2023 Phu Hung Nguyen <phuhnguyen@outlook.com>
# SPDX-License-Identifier: LGPL-2.1-or-later

import logging
import os

from markdown_it import MarkdownIt

from .e_domain import HugoDomainE
from .renderer_hugo_i18n import RendererHugoI18N
from .. import utils
from ..config import Config


class Extraction:
    """
    Implements `HugoEProtocol`
    """
    def __init__(self, hg_config: Config, mdi: MarkdownIt):
        self.hg_config = hg_config
        self.mdi = mdi
        self.default_domain_e = HugoDomainE(self)

    def i12ize_data_files(self):
        for path, data in utils.read_data_files(self.hg_config).items():
            self.default_domain_e.i12ize_object(data, self.hg_config.excluded_data_keys, path, self.mdi)
            logging.info(path)

    def i12ize_data_others(self):
        hg_config = self.hg_config
        # config fields
        path = 'config.yaml'
        default_language_config = hg_config.hugo_config.get('languages', {}).get('en', {})
        if hg_config.do_title:
            if 'title' not in default_language_config:
                logging.warning(f"Default language config section doesn't have a `title` field.")
            else:
                self.default_domain_e.add_entry(path, default_language_config['title'], 0)
        if hg_config.do_description:
            if 'params' not in default_language_config or 'description' not in default_language_config['params']:
                logging.warning(f"Default language config section doesn't have a `params.description` field.")
            else:
                self.default_domain_e.add_entry(path, default_language_config['params']['description'], 0)
        if hg_config.do_menu:
            for menu_entry in default_language_config['menu']['main']:
                self.default_domain_e.add_entry(path, menu_entry['name'], 0)
        # data
        if hg_config.data:
            self.i12ize_data_files()
        # strings
        if hg_config.do_strings:
            path = 'i18n/en.yaml'
            src_strings = utils.read_strings()
            for _, string in src_strings.items():
                self.default_domain_e.add_entry(path, string['other'], 0, string.get('comment', ''))

    def extract(self, target_dir: str):
        os.makedirs(target_dir, exist_ok=True)
        self.i12ize_data_others()
        for domain, domain_paths in self.hg_config.content.items():
            if domain == 'default':
                self.default_domain_e.i12ize_content_domain(domain_paths)
            else:
                domain_e = HugoDomainE(self)
                domain_e.i12ize_content_domain(domain_paths)
                domain_e.to_pot(f'{target_dir}/{domain}.pot')
        self.default_domain_e.to_pot(f'{target_dir}/{self.hg_config.default_domain_name}.pot')


def extract(args):
    """Extract messages from source files
    :param args: arguments passed in command line, containing
        - pot: path of the directory containing the target pot file(s)
        - customs (optional): path to Python file containing custom functions
    :return: None. Data, config fields, and strings are extracted to the default domain,
    while content files are extracted to configured domains.
    """
    hg_config, mdi = utils.initialize(args.customs, RendererHugoI18N)
    Extraction(hg_config, mdi).extract(args.pot)
