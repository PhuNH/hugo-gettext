# SPDX-FileCopyrightText: 2023 Phu Hung Nguyen <phuhnguyen@outlook.com>
# SPDX-License-Identifier: LGPL-2.1-or-later

import os
from typing import Tuple, Dict

import yaml

from markdown_it import MarkdownIt
from mdit_py_plugins.deflist import deflist_plugin
from mdit_py_plugins.front_matter import front_matter_plugin

from .config import Config
from .generation.renderer_md_l10n import RendererMarkdownL10N


# TODO: use this in extraction?
def initialize(customs_path: str) -> Tuple[Config, MarkdownIt]:
    hg_config = Config(customs_path)
    mdi = MarkdownIt(renderer_cls=RendererMarkdownL10N).use(front_matter_plugin)
    if hg_config.parse_table:
        mdi = mdi.enable('table')
    if hg_config.parse_definition_list:
        mdi = mdi.use(deflist_plugin)
    return hg_config, mdi


def read_data_files(hg_config: Config) -> Dict:
    src_data = {}
    for path in hg_config.data:
        if not os.path.isfile(path):
            continue
        with open(path, 'r') as f_data:
            data = yaml.safe_load(f_data)
        src_data[path] = data
    return src_data


def read_strings() -> Dict:
    try:
        with open("i18n/en.yaml", 'r') as f_i18n:
            src_strings = yaml.safe_load(f_i18n)
    except FileNotFoundError:
        src_strings = {}

    return src_strings
