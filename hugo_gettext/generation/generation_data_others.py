# SPDX-FileCopyrightText: 2021 Carl Schwan <carlschwan@kde.org>
# SPDX-FileCopyrightText: 2023 Phu Hung Nguyen <phuhnguyen@outlook.com>
# SPDX-License-Identifier: LGPL-2.1-or-later

import copy
import logging
import os
from typing import Dict, Set

import yaml
from markdown_it import MarkdownIt

from .generation_utils import L10NEnv, L10NResult, L10NResults, L10NFunc
from .l10n_object import localize_object
from ..config import Config

# TODO: how to handle this?
RTL_LANGUAGES = {'ar', 'he'}


def generate_data_files(src_data: Dict,
                        excluded_data_keys: Set[str],
                        hugo_lang_code: str,
                        l10n_func: L10NFunc,
                        mdi: MarkdownIt):
    lang_prefix = '' if hugo_lang_code == 'en' else f'/{hugo_lang_code}'
    for path, data in src_data.items():
        # make a copy because other languages need to use this too
        data = copy.deepcopy(data)
        src_sub_path = path.split('/', 1)[1]
        target_file = f'data{lang_prefix}/{src_sub_path}'
        os.makedirs(os.path.dirname(target_file), exist_ok=True)

        o_result = localize_object(data, excluded_data_keys, hugo_lang_code, l10n_func, mdi)
        if o_result.l10n_count > 0:
            with open(target_file, 'w+') as f_target:
                f_target.write(yaml.dump(data, default_flow_style=False, allow_unicode=True))


def localize_strings(src_strings, l10n_func: L10NFunc, l10n_results: L10NResults = None) -> L10NResult:
    if l10n_results is None:
        l10n_results = {}

    if 'strings' in l10n_results:
        return l10n_results['strings'][0]

    target_strings = {}
    total_count = len(src_strings)
    l10n_count = 0
    for key, string in src_strings.items():
        if (localized_string := l10n_func(string['other'])) is not string['other']:
            target_strings[key] = {'other': localized_string}
            l10n_count += 1
    result = L10NResult(target_strings, total_count, l10n_count)
    l10n_results['strings'] = [result]
    return result


def write_strings(target_strings, hugo_lang_code):
    if len(target_strings) > 0:
        i18n_path = f'i18n/{hugo_lang_code}.yaml'
        with open(i18n_path, 'w+') as f_target_i18n:
            logging.info(i18n_path)
            f_target_i18n.write(yaml.dump(target_strings, default_flow_style=False, allow_unicode=True))


def localize_languages(hg_config: Config, lang_names: Dict, lang_code: str, hugo_lang_code: str):
    hugo_config = hg_config.hugo_config
    if hugo_lang_code not in hugo_config['languages']:
        hugo_config['languages'][hugo_lang_code] = {}
    hugo_config['languages'][hugo_lang_code]['languageCode'] = lang_code
    hugo_config['languages'][hugo_lang_code]['weight'] = 2

    if hugo_lang_code in lang_names:
        hugo_config['languages'][hugo_lang_code]['languageName'] = lang_names[hugo_lang_code]

    if hugo_lang_code in RTL_LANGUAGES:
        hugo_config['languages'][hugo_lang_code]['languagedirection'] = 'rtl'

    if hg_config.gen_to_other_dir:
        hugo_config['languages'][hugo_lang_code]['contentDir'] = f'{hg_config.gen_dir}/{hugo_lang_code}'


def localize_menu(hugo_config, hugo_lang_code: str, l10n_func: L10NFunc):
    menu = {'main': []}
    for menu_item in hugo_config['languages']['en']['menu']['main']:
        target_menu_item = copy.deepcopy(menu_item)
        target_menu_item['name'] = l10n_func(target_menu_item['name'])
        menu['main'].append(target_menu_item)
    hugo_config['languages'][hugo_lang_code]['menu'] = menu


def localize_description(hugo_config, hugo_lang_code: str, l10n_func: L10NFunc):
    hugo_config['languages'][hugo_lang_code]['params'] = {
        'description': l10n_func(hugo_config['languages']['en']['params']['description'])
    }


def localize_title(hugo_config, hugo_lang_code: str, l10n_func: L10NFunc):
    hugo_config['languages'][hugo_lang_code]['title'] = l10n_func(hugo_config['languages']['en']['title'])


def generate_data_others(lang_code: str, file_total_count: int, file_l10n_count: int, l10n_env: L10NEnv,
                         lang_names: Dict, src_data: Dict):
    """Generate strings file and data files, and localize config fields.
    Strings file will be generated even if the language doesn't meet requirements.
    Config fields and data files won't.
    """
    hugo_lang_code = l10n_env.hugo_lang_code
    l10n_func = l10n_env.l10n_func
    hg_config = l10n_env.hg_config
    src_strings = l10n_env.src_strings
    strings_ok = True
    if hg_config.do_strings and src_strings is not None:
        strings_result = localize_strings(src_strings, l10n_func, l10n_env.l10n_results)
        write_strings(strings_result.localized, hugo_lang_code)
        strings_ok = strings_result.l10n_count > 0

    # Only generate the config section and data files for the language if conditions are met
    # X = 'languages' in hugo_config and (
    #       (file_total_count <= 0 and strings_ok) or (file_total_count > 0 and file_l10n_count > 0))
    # X_ = 'languages' not in hugo_config or (
    #       (file_total_count > 0 or not strings_ok) and (file_total_count <= 0 or file_l10n_count <= 0))
    # A = file_total_count > 0
    # B = not strings_ok
    # C = file_l10n_count <= 0
    # X_ = 'languages' not in hugo_config or ((A or B) and (A_ or C))
    # (A or B) and (A_ or C) = ((A or B) and A_) or ((A or B) and C)
    #                        = (A and A_) or (B and A_) or (A and C) or (B and C)
    #                        = (B and A_) or (A and C) or (B and C)
    # X_ = 'languages' not in hugo_config or (
    #       (not strings_ok and file_total_count <= 0) or (file_total_count > 0 and file_l10n_count <= 0) or
    #       (not strings_ok and file_l10n_count <= 0))
    if (file_total_count <= 0 and not strings_ok) or (file_total_count > 0 and file_l10n_count <= 0) \
            or (not strings_ok and file_l10n_count <= 0) or 'languages' not in hg_config.hugo_config:
        return

    localize_languages(hg_config, lang_names, lang_code, hugo_lang_code)
    if hg_config.do_menu:
        localize_menu(hg_config.hugo_config, hugo_lang_code, l10n_func)
    if hg_config.do_description:
        localize_description(hg_config.hugo_config, hugo_lang_code, l10n_func)
    if hg_config.do_title:
        localize_title(hg_config.hugo_config, hugo_lang_code, l10n_func)
    if src_data:
        generate_data_files(src_data, hg_config.excluded_data_keys,
                            hugo_lang_code, l10n_func, l10n_env.mdi)


def write_config(current, original):
    if current != original:
        with open('config.yaml', 'w+') as f_config:
            f_config.write(yaml.dump(current, default_flow_style=False, allow_unicode=True))
