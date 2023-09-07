# SPDX-FileCopyrightText: 2023 Phu Hung Nguyen <phuhnguyen@outlook.com>
# SPDX-License-Identifier: LGPL-2.1-or-later

import os
import re
from enum import Enum
from typing import Dict, Protocol, Any, List

import tomlkit
import yaml
from markdown_it import MarkdownIt
from mdit_py_i18n.utils import DomainGenerationProtocol, DomainExtractionProtocol

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


class TextFormat(Enum):
    ELSE = -1
    YAML = 0
    TOML = 1

    @classmethod
    def decide_by_path(cls, path: str) -> 'TextFormat':
        if (ext := os.path.splitext(path)[1]) in {'.yaml', '.yml'}:
            return cls.YAML
        elif ext == '.toml':
            return cls.TOML
        else:
            return cls.ELSE

    def load_str(self, content: str):
        if self == TextFormat.YAML:
            return yaml.safe_load(content)
        elif self == TextFormat.TOML:
            return tomlkit.loads(content)
        else:
            return {}

    def dump_obj(self, obj):
        if self == TextFormat.YAML:
            return yaml.dump(obj, default_flow_style=False, allow_unicode=True)
        elif self == TextFormat.TOML:
            return tomlkit.dumps(obj)
        else:
            return ''


def read_file(file_path: str):
    text_format = TextFormat.decide_by_path(file_path)
    with open(file_path) as f:
        return text_format.load_str(f.read())


def write_file(file_path: str, obj):
    text_format = TextFormat.decide_by_path(file_path)
    with open(file_path, 'w+') as f:
        f.write(text_format.dump_obj(obj))


def read_data_files(file_paths: List[str]) -> Dict:
    src_data = {}
    for path in file_paths:
        if not os.path.isfile(path):
            continue
        src_data[path] = read_file(path)
    return src_data


def read_strings() -> Dict:
    try:
        with open("i18n/en.yaml", 'r') as f_i18n:
            src_strings = yaml.safe_load(f_i18n)
    except FileNotFoundError:
        src_strings = {}

    return src_strings
