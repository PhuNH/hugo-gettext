# SPDX-FileCopyrightText: 2023 Phu Hung Nguyen <phuhnguyen@outlook.com>
# SPDX-License-Identifier: LGPL-2.1-or-later

import logging
import os
from typing import Set, Optional, List

import yaml
from markdown_gettext.domain_extraction import DomainExtraction
from markdown_it import MarkdownIt
from mdit_py_i18n import utils

from ..utils import HugoEProtocol


class HugoDomainE(DomainExtraction):
    """
    Implements `HugoDomainEProtocol` and `DomainExtraction`
    """
    def __init__(self, e: HugoEProtocol):
        super().__init__()
        self.e = e

    def i12ize_object(self, o, excluded_keys: Set[str], path: str, mdi: Optional[MarkdownIt] = None):
        """Internationalize an object, either in front matters or in data files.
        :param o: the object being processed
        :param excluded_keys: a set of keys whose values are not processed
        :param path: path of the source file
        :param mdi: used to i12ize a string as Markdown if provided
        :return: None. Messages are added to the `entries` list.
        """
        if isinstance(o, str) and o and not utils.SPACES_PATTERN.fullmatch(o):
            if mdi:
                env = {
                    'path': path,
                    'domain_extraction': self,
                    'with_line': False
                }
                mdi.render(o, env)
            else:
                self.add_entry(path, o, 0)
        elif isinstance(o, list) or isinstance(o, dict):
            for key, value in (enumerate(o) if isinstance(o, list) else o.items()):
                if key not in excluded_keys:
                    self.i12ize_object(value, excluded_keys, path, mdi)

    def render_front_matter(self, path: str, content: str, markup: str):
        fm = yaml.safe_load(content)
        self.i12ize_object(fm, self.e.hg_config.excluded_keys, path)

    def i12ize_content_file(self, path: str):
        with open(path) as f_content:
            env = {
                'path': path,
                'domain_extraction': self,
                'with_line': True
            }
            self.e.mdi.render(f_content.read(), env)

    def i12ize_content_domain(self, domain_paths: List[str]):
        for path in domain_paths:
            if os.path.isfile(path):
                self.i12ize_content_file(path)
                logging.info(path)

    def to_pot(self, dest_path: str):
        super().make_pot(self.e.hg_config.package, self.e.hg_config.report_address, self.e.hg_config.team_address,
                         dest_path)
