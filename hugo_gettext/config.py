# SPDX-FileCopyrightText: 2023 Phu Hung Nguyen <phuhnguyen@outlook.com>
# SPDX-License-Identifier: LGPL-2.1-or-later

import glob
import importlib.util
import inspect
import logging
import os
from typing import List, Dict, Callable, Set, Type, Tuple

from markdown_it import MarkdownIt
from markdown_it.renderer import RendererProtocol
from mdit_py_hugo.attribute import attribute_plugin
from mdit_py_hugo.shortcode import shortcode_plugin
from mdit_py_plugins.deflist import deflist_plugin
from mdit_py_plugins.front_matter import front_matter_plugin

from . import utils


def _read_domain_config(domain_config) -> List[str]:
    """Get files of a domain
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
    """Retrieve a list of data files to extract
    :param i18n_config: the i18n config section
    :return: a list of file paths
    """
    return _read_domain_config(i18n_config['data']) if 'data' in i18n_config else []


def _read_content_config(i18n_config) -> Dict[str, List[str]]:
    """Retrieve lists of content files, grouped by domains
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


def _find_string_file(default_lang: str) -> str:
    if not os.path.isdir('i18n'):
        return ''
    possible_paths = [f'i18n/{default_lang}.toml',
                      f'i18n/{default_lang}.yaml',
                      f'i18n/{default_lang}.json']
    for path in possible_paths:
        if os.path.isfile(path):
            return path
    return ''


def _find_config_file() -> str:
    possible_paths = ['hugo.toml', 'hugo.yaml', 'hugo.json',
                      'config.toml', 'config.yaml', 'config.json']
    for path in possible_paths:
        if os.path.isfile(path):
            return path
    return ''


excluded_keys = {'aliases', 'date',
                 'i18n_configs', 'layout',
                 'publishDate',
                 'type', 'url'}


def _get_customs_functions(customs_path: str) -> Dict[str, Callable]:
    if not customs_path:
        return {}
    spec = importlib.util.spec_from_file_location('hugo_gettext_customs', customs_path)
    if not spec:
        return {}
    customs = importlib.util.module_from_spec(spec)
    spec.loader.exec_module(customs)
    functions = inspect.getmembers(customs, inspect.isfunction)
    return {f[0]: f[1] for f in functions}


def _load_lang_names() -> Dict[str, str]:
    return {}


def _get_default_domain_name(package: str) -> str:
    return package


def _convert_lang_code(lang_code: str) -> str:
    hugo_lang_code = lang_code
    return hugo_lang_code


def _get_custom_excluded_keys() -> Set[str]:
    return set()


def _get_pot_fields() -> Dict[str, str]:
    return {
        'report_address': '',
        'team_address': ''
    }


def _get_rtl_langs() -> List[str]:
    return []


class Config:
    def __init__(self, hugo_config, config_path: str = '', customs_path: str = ''):
        if 'i18n' not in hugo_config:
            return

        i18n_config = hugo_config['i18n']
        self.config_path = config_path
        # env. var. > config value
        self.package = os.environ.get('PACKAGE', '') or i18n_config.get('package', '')
        if not self.package:
            raise ValueError('Neither a PACKAGE env. var nor an i18n.package config exists. At least one is required.')

        # command line arg. > config value
        customs_path = customs_path or i18n_config.get('customs', '')
        customs_functions = _get_customs_functions(customs_path)
        # value directly set in config file > value gotten by calling custom function
        #   default_domain_name
        if default_domain_name := i18n_config.get('defaultDomain', ''):
            self.default_domain_name = default_domain_name
        else:
            get_default_domain_name = customs_functions.get('get_default_domain_name', _get_default_domain_name)
            self.default_domain_name = get_default_domain_name(self.package)
        #   report_address and team_address
        get_pot_fields = customs_functions.get('get_pot_fields', _get_pot_fields)
        pot_fields = get_pot_fields()
        if report_address := i18n_config.get('reportAddress', ''):
            self.report_address = report_address
        else:
            self.report_address = pot_fields.get('report_address', '')
        if team_address := i18n_config.get('teamAddress', ''):
            self.team_address = team_address
        else:
            self.team_address = pot_fields.get('team_address', '')
        #   rtl_langs
        get_rtl_langs = customs_functions.get('get_rtl_langs', _get_rtl_langs)
        if rtl_langs := i18n_config.get('rtlLangs', []):
            self.rtl_langs = rtl_langs
        else:
            self.rtl_langs = get_rtl_langs()

        # custom functions with no corresponding config fields
        get_custom_excluded_keys = customs_functions.get('get_custom_excluded_keys', _get_custom_excluded_keys)
        custom_excluded_keys = get_custom_excluded_keys()
        self.load_lang_names = customs_functions.get('load_lang_names', _load_lang_names)
        self.convert_lang_code = customs_functions.get('convert_lang_code', _convert_lang_code)

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
        self.shortcodes = i18n_config.get('shortcodes', {})

        self.default_lang = hugo_config.get('defaultContentLanguage', 'en')
        self.string_file_path = _find_string_file(self.default_lang)
        if self.do_strings and not self.string_file_path:
            logging.warning('Strings specified as an i18n target, but no string file in the default language found')

        goldmark_config = hugo_config.get('markup', {}).get('goldmark', {})
        extensions_config = goldmark_config.get('extensions', {})
        self.parse_definition_list = extensions_config.get('definitionList', True)
        self.parse_table = extensions_config.get('table', True)
        attribute_config = goldmark_config.get('parser', {}).get('attribute', {})
        self.parse_attribute_block = attribute_config.get('block', False)
        self.parse_attribute_title = attribute_config.get('title', True)

        self.hugo_config = hugo_config

    @classmethod
    def from_config_file(cls, config_path: str, customs_path: str = ''):
        if not config_path:
            config_path = _find_config_file()
        hugo_config = utils.read_file(config_path)
        return cls(hugo_config, config_path, customs_path)


def initialize(renderer_cls: Type[RendererProtocol],
               customs_path: str = '',
               config_path: str = '') -> Tuple[Config, MarkdownIt]:
    hg_config = Config.from_config_file(config_path, customs_path)
    mdi = MarkdownIt(renderer_cls=renderer_cls).use(front_matter_plugin).use(shortcode_plugin)
    if hg_config.parse_table:
        mdi = mdi.enable('table')
    if hg_config.parse_definition_list:
        mdi = mdi.use(deflist_plugin)
    if hg_config.parse_attribute_title or hg_config.parse_attribute_block:
        mdi = mdi.use(attribute_plugin, block=hg_config.parse_attribute_block, title=hg_config.parse_attribute_title)
    return hg_config, mdi
