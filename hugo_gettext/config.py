# SPDX-FileCopyrightText: 2023 Phu Hung Nguyen <phuhnguyen@outlook.com>
# SPDX-License-Identifier: LGPL-2.1-or-later

import glob
import importlib.util
import os
from typing import List, Dict

import yaml


def _read_domain_config(domain_config) -> List[str]:
    """
    Get files of a domain
    :param domain_config: config of the domain to read
    :return: list of files of the domain
    """
    if 'files' not in domain_config and 'globs' not in domain_config:
        raise ValueError("Domain config contains neither 'files' nor 'globs' field. At least one is required.")
    domain_files = set()
    if 'files' in domain_config:
        domain_files |= set([os.path.normpath(p) for p in domain_config['files']])
    if 'globs' in domain_config:
        for g in domain_config['globs']:
            domain_files |= set([os.path.normpath(p) for p in glob.glob(g)])
    if 'excludedFiles' in domain_config:
        domain_files -= set([os.path.normpath(p) for p in domain_config['excludedFiles']])
    if 'excludedGlobs' in domain_config:
        excluded_files = set()
        for g in domain_config['excludedGlobs']:
            excluded_files |= set([os.path.normpath(p) for p in glob.glob(g)])
        domain_files -= excluded_files
    return sorted(domain_files)


def _read_data_config(i18n_config) -> List[str]:
    """
    Retrieve a list of data files to extract
    :param i18n_config: the i18n config section
    :return: a list of file paths
    """
    return _read_domain_config(i18n_config['data']) if 'data' in i18n_config else []


def _read_content_config(i18n_config) -> Dict[str, List[str]]:
    """
    Retrieve lists of content files, grouped by domains
    :param i18n_config: the i18n config section
    :return: a dict with domain names as keys and file lists as values
    """
    if 'content' not in i18n_config:
        return {'default': []}

    content_config = i18n_config['content']
    content_files: Dict[str, List[str]] = {}
    for domain in content_config:
        content_files[domain] = _read_domain_config(content_config[domain])
    return content_files


excluded_keys = {'aliases', 'date',
                 'i18n_configs', 'layout',
                 'publishDate',
                 'type', 'url'}
# TODO how to customize this?
custom_excluded_keys = {'appstream', 'authors', 'background', 'cdnJsFiles', 'cssFiles', 'flatpak_exp',
                        'forum', 'jsFiles', 'hl_class', 'hl_video', 'konqi', 'minJsFiles', 'parent',
                        'sassFiles', 'screenshot', 'scssFiles', 'SPDX-License-Identifier', 'src_icon',
                        'userbase'}


def _load_lang_names() -> Dict:
    return {}


def _get_default_domain_name(package: str) -> str:
    return package


def _convert_lang_code(lang_code) -> str:
    hugo_lang_code = lang_code
    return hugo_lang_code


class Config:
    def __init__(self, customs_path: str):
        with open('config.yaml') as f:
            hugo_config = yaml.safe_load(f)
            if 'i18n' not in hugo_config:
                return

        i18n_config = hugo_config['i18n']
        self.package = os.environ.get('PACKAGE', '') or i18n_config.get('package', '')
        if not self.package:
            raise ValueError('Neither a PACKAGE env. var nor an i18n.package config exists. At least one is required.')

        if customs_path:
            spec = importlib.util.spec_from_file_location('hugo_gettext_customs', customs_path)
            customs = importlib.util.module_from_spec(spec)
            spec.loader.exec_module(customs)
            self.load_lang_names = customs.load_lang_names
            self.get_default_domain_name = customs.get_default_domain_name
            self.convert_lang_code = customs.convert_lang_code
        else:
            self.load_lang_names = _load_lang_names
            self.get_default_domain_name = _get_default_domain_name
            self.convert_lang_code = _convert_lang_code

        self.gen_to_other_dir = i18n_config.get('genToOtherDir', False)
        self.src_dir = i18n_config.get('srcDir', 'content')
        self.gen_dir = i18n_config.get('genDir', 'content-trans')
        self.do_title = 'others' in i18n_config and 'title' in i18n_config['others']
        self.do_description = 'others' in i18n_config and 'description' in i18n_config['others']
        self.do_menu = 'others' in i18n_config and 'menu' in i18n_config['others']
        self.do_strings = 'others' in i18n_config and 'strings' in i18n_config['others']
        self.data = _read_data_config(i18n_config)
        self.content = _read_content_config(i18n_config)
        self.excluded_data_keys = set(i18n_config.get('excludedDataKeys', '').split())
        self.excluded_keys = excluded_keys | custom_excluded_keys | set(i18n_config.get('excludedKeys', '').split())
        self.langs = i18n_config.get('langs', '').split()

        goldmark_config = hugo_config.get('markup', {}).get('goldmark', {})
        extensions_config = goldmark_config.get('extensions', {})
        self.parse_definition_list = extensions_config.get('definitionList', True)
        self.parse_table = extensions_config.get('table', True)

        self.hugo_config = hugo_config
