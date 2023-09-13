# SPDX-FileCopyrightText: 2023 Phu Hung Nguyen <phuhnguyen@outlook.com>
# SPDX-License-Identifier: LGPL-2.1-or-later

import json
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
HG_STOP = 'hg_stop'


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
    ELSE = ''
    YAML = '.yaml'
    TOML = '.toml'
    JSON = '.json'

    @classmethod
    def decide_by_path(cls, path: str) -> 'TextFormat':
        if (ext := os.path.splitext(path)[1]) == cls.YAML.value or ext == '.yml':
            return cls.YAML
        elif ext == cls.TOML.value:
            return cls.TOML
        elif ext == cls.JSON.value:
            return cls.JSON
        else:
            return cls.ELSE

    def load_content(self, content: str):
        if self == TextFormat.YAML:
            return yaml.safe_load(content)
        elif self == TextFormat.TOML:
            return tomlkit.loads(content)
        elif self == TextFormat.JSON:
            return json.loads(content)
        else:
            return {}

    def dump_obj(self, obj):
        if self == TextFormat.YAML:
            return yaml.dump(obj, default_flow_style=False, allow_unicode=True)
        elif self == TextFormat.TOML:
            return tomlkit.dumps(obj)
        elif self == TextFormat.JSON:
            return json.dumps(obj, ensure_ascii=False, indent=4)
        else:
            return ''


def read_file(file_path: str):
    text_format = TextFormat.decide_by_path(file_path)
    with open(file_path) as f:
        return text_format.load_content(f.read())


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
