# SPDX-FileCopyrightText: 2021 Carl Schwan <carlschwan@kde.org>
# SPDX-FileCopyrightText: 2023 Phu Hung Nguyen <phuhnguyen@outlook.com>
# SPDX-License-Identifier: LGPL-2.1-or-later

import copy
import logging
import os
from typing import List, Dict

import yaml
from markdown_gettext.domain_generation import gettext_func
from mdit_py_i18n.utils import L10NResult

from .g_domain import HugoDomainG
from ..utils import HugoGProtocol

L10NResults = Dict[str, List[L10NResult]]
# TODO: how to handle this?
RTL_LANGUAGES = {'ar', 'he'}


class HugoLangG:
    """
    Implements `HugoLangGProtocol`
    """
    def __init__(self, g: HugoGProtocol, lang_code: str):
        self.g = g
        self.lang_code = lang_code
        self.hugo_lang_code = self.g.hg_config.convert_lang_code(self.lang_code)
        self.lang_prefix = '' if self.hugo_lang_code == 'en' else f'/{self.hugo_lang_code}'
        self.l10n_results: L10NResults = {}
        self.file_l10n_count = 0
        self.default_domain_g = None

    def localize_strings(self) -> L10NResult:
        l10n_results = self.l10n_results
        src_strings = self.g.src_strings
        if 'strings' in l10n_results:
            return l10n_results['strings'][0]

        target_strings = {}
        total_count = len(src_strings)
        l10n_count = 0
        for key, string in src_strings.items():
            if (localized_string := self.default_domain_g.l10n_func(string['other'])) is not string['other']:
                target_strings[key] = {'other': localized_string}
                l10n_count += 1
        result = L10NResult(target_strings, total_count, l10n_count)
        l10n_results['strings'] = [result]
        return result

    def write_strings(self, target_strings):
        if len(target_strings) > 0:
            i18n_path = f'i18n/{self.hugo_lang_code}.yaml'
            with open(i18n_path, 'w+') as f_target_i18n:
                logging.info(i18n_path)
                f_target_i18n.write(yaml.dump(target_strings, default_flow_style=False, allow_unicode=True))

    def localize_languages(self):
        hg_config = self.g.hg_config
        hugo_config = hg_config.hugo_config
        hugo_lang_code = self.hugo_lang_code
        if hugo_lang_code not in hugo_config['languages']:
            hugo_config['languages'][hugo_lang_code] = {}
        hugo_config['languages'][hugo_lang_code]['languageCode'] = self.lang_code
        hugo_config['languages'][hugo_lang_code]['weight'] = 2

        if hugo_lang_code in self.g.lang_names:
            hugo_config['languages'][hugo_lang_code]['languageName'] = self.g.lang_names[hugo_lang_code]

        if hugo_lang_code in RTL_LANGUAGES:
            hugo_config['languages'][hugo_lang_code]['languagedirection'] = 'rtl'

        if hg_config.gen_to_other_dir:
            hugo_config['languages'][hugo_lang_code]['contentDir'] = f'{hg_config.gen_dir}/{hugo_lang_code}'

    def localize_menu(self):
        menu = {'main': []}
        hugo_config = self.g.hg_config.hugo_config
        for menu_item in hugo_config['languages']['en']['menu']['main']:
            target_menu_item = copy.deepcopy(menu_item)
            target_menu_item['name'] = self.default_domain_g.l10n_func(target_menu_item['name'])
            menu['main'].append(target_menu_item)
        hugo_config['languages'][self.hugo_lang_code]['menu'] = menu

    def localize_description(self):
        hugo_config = self.g.hg_config.hugo_config
        hugo_config['languages'][self.hugo_lang_code]['params'] = {
            'description': self.default_domain_g.l10n_func(hugo_config['languages']['en']['params']['description'])
        }

    def localize_title(self):
        hugo_config = self.g.hg_config.hugo_config
        hugo_config['languages'][self.hugo_lang_code]['title'] = (
            self.default_domain_g.l10n_func(hugo_config['languages']['en']['title']))

    def generate_data_files(self):
        for path, data in self.g.src_data.items():
            # make a copy because other languages need to use this too
            data = copy.deepcopy(data)
            src_sub_path = path.split('/', 1)[1]
            target_path = f'data{self.lang_prefix}/{src_sub_path}'
            os.makedirs(os.path.dirname(target_path), exist_ok=True)

            o_result = self.default_domain_g.localize_object(data, self.g.hg_config.excluded_data_keys, self.g.mdi)
            if o_result.l10n_count > 0:
                with open(target_path, 'w+') as f_target:
                    f_target.write(yaml.dump(data, default_flow_style=False, allow_unicode=True))

    def generate_data_others(self):
        """Generate strings file and data files, and localize config fields.
        Strings file will be generated even if the language doesn't meet requirements.
        Config fields and data files won't.
        """
        hg_config = self.g.hg_config
        src_strings = self.g.src_strings
        file_total_count = self.g.file_total_count
        file_l10n_count = self.file_l10n_count
        strings_ok = True
        if hg_config.do_strings and src_strings is not None:
            strings_result = self.localize_strings()
            self.write_strings(strings_result.localized)
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

        self.localize_languages()
        if hg_config.do_menu:
            self.localize_menu()
        if hg_config.do_description:
            self.localize_description()
        if hg_config.do_title:
            self.localize_title()
        if self.g.src_data:
            self.generate_data_files()

    def generate_lang(self):
        os.environ["LANGUAGE"] = self.lang_code
        hg_config = self.g.hg_config
        for domain, domain_paths in hg_config.content.items():
            domain_name = domain if domain != 'default' else hg_config.default_domain_name
            mo_path = f'locale/{self.lang_code}/LC_MESSAGES/{domain_name}.mo'
            if os.path.isfile(mo_path):
                l10n_func = gettext_func(domain_name)
            # ensure generate_content_domain is still called even when a language has no file for the domain,
            #   so that, for example, a language that only has string translations and no file translation
            #   can still be qualified if there are files with no content to be translated
            else:
                def l10n_func(x): return x
            domain_g = HugoDomainG(self, l10n_func)
            if domain_name == hg_config.default_domain_name:
                self.default_domain_g = domain_g
            self.file_l10n_count += domain_g.generate_content_domain(domain_paths)
        if self.default_domain_g is None:
            mo_path = f'locale/{self.lang_code}/LC_MESSAGES/{hg_config.default_domain_name}.mo'
            if os.path.isfile(mo_path):
                default_func = gettext_func(hg_config.default_domain_name)
            # ensure default_func is not None and thus generate_others is still called even when a language
            #   has no file for the default domain, so that the language can still be qualified
            else:
                def default_func(x): return x
            self.default_domain_g = HugoDomainG(self, default_func)
        logging.info(f'{self.hugo_lang_code} [{self.file_l10n_count}/{self.g.file_total_count}]')

        if self.default_domain_g is not None:
            self.generate_data_others()
