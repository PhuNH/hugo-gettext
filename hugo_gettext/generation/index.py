# SPDX-FileCopyrightText: 2023 Phu Hung Nguyen <phuhnguyen@outlook.com>
# SPDX-License-Identifier: LGPL-2.1-or-later

import copy
import os
import shutil
from typing import Dict

from markdown_it import MarkdownIt

from .g_lang import HugoLangG
from .renderer_hugo_l10n import RendererHugoL10N
from .. import utils
from ..config import Config, initialize


class Generation:
    """
    Implements `HugoGProtocol`
    """
    def __init__(self,
                 src_strings: Dict,
                 src_data: Dict,
                 hg_config: Config,
                 mdi: MarkdownIt):
        self.src_strings = src_strings
        self.src_data = src_data
        self.hg_config = hg_config
        self.lang_names = self.hg_config.load_lang_names()
        self.file_total_count: int = sum([len(x) for _, x in self.hg_config.content.items()])
        self.mdi = mdi

    def generate(self, keep_locale):
        os.makedirs('locale', exist_ok=True)
        for lang_code in os.listdir('locale'):
            HugoLangG(self, lang_code).generate_lang()
        if not keep_locale:
            shutil.rmtree('locale')


def generate(args):
    """Generate target messages and files
    :param args: arguments passed in command line, containing
        - customs (optional): path to Python file containing custom functions
        - config (optional): path to config file
        - keep_locale (optional): do not delete locale folder, default False
    :return: None
    """
    hg_config, mdi = initialize(RendererHugoL10N, args.customs, args.config)
    if hg_config.do_strings and hg_config.string_file_path:
        src_strings = utils.read_file(hg_config.string_file_path)
    else:
        src_strings = {}
    original_hugo_config = copy.deepcopy(hg_config.hugo_config)
    src_data = utils.read_data_files(hg_config.data)

    Generation(src_strings, src_data, hg_config, mdi).generate(args.keep_locale)

    if hg_config.hugo_config != original_hugo_config:
        utils.write_file(hg_config.config_path, hg_config.hugo_config)
