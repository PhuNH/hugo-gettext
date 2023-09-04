# SPDX-FileCopyrightText: 2023 Phu Hung Nguyen <phuhnguyen@outlook.com>
# SPDX-License-Identifier: LGPL-2.1-or-later

import os
import re
from typing import Tuple, Dict, Type, Protocol, Any

import yaml
from markdown_it import MarkdownIt
from markdown_it.renderer import RendererProtocol
from mdit_py_hugo.attribute import attribute_plugin
from mdit_py_hugo.shortcode import shortcode_plugin
from mdit_py_i18n.utils import DomainGenerationProtocol, DomainExtractionProtocol
from mdit_py_plugins.deflist import deflist_plugin
from mdit_py_plugins.front_matter import front_matter_plugin

from .config import Config

SINGLE_COMMENT_PATTERN = re.compile('(// *)(.*)')
SHORTCODE_QUOTES = {'"', '`'}
HG_STOP = 'hg-stop'


class HugoEProtocol(Protocol):
    hg_config: Any
    mdi: MarkdownIt


class HugoGProtocol(Protocol):
    src_strings: Dict
    src_data: Dict
    lang_names: Dict
    file_total_count: int
    hg_config: Any
    mdi: MarkdownIt


class HugoLangGProtocol(Protocol):
    g: HugoGProtocol
    hugo_lang_code: str
    l10n_results: Dict

    def localize_strings(self):
        ...


class HugoDomainEProtocol(DomainExtractionProtocol):
    e: HugoEProtocol


class HugoDomainGProtocol(DomainGenerationProtocol):
    lang_g: HugoLangGProtocol


def initialize(customs_path: str, renderer_cls: Type[RendererProtocol]) -> Tuple[Config, MarkdownIt]:
    hg_config = Config(customs_path)
    mdi = MarkdownIt(renderer_cls=renderer_cls).use(front_matter_plugin).use(shortcode_plugin)
    if hg_config.parse_table:
        mdi = mdi.enable('table')
    if hg_config.parse_definition_list:
        mdi = mdi.use(deflist_plugin)
    if hg_config.parse_attribute_title or hg_config.parse_attribute_block:
        mdi = mdi.use(attribute_plugin, block=hg_config.parse_attribute_block, title=hg_config.parse_attribute_title)
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
