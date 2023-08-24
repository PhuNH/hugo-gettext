# SPDX-FileCopyrightText: 2023 Phu Hung Nguyen <phuhnguyen@outlook.com>
# SPDX-License-Identifier: LGPL-2.1-or-later

import copy
import logging
import os
import shutil

from .generation_content import generate_content_domain
from .generation_data_others import generate_data_others, write_config
from .generation_utils import L10NResults, L10NEnv, gettext_func
from .. import utils


def generate(args):
    """
    Generate target messages and files
    :return: None
    """

    hg_config, mdi = utils.initialize(args.customs)
    src_strings = utils.read_strings()
    original_hugo_config = copy.deepcopy(hg_config.hugo_config)
    src_data = utils.read_data_files(hg_config)

    lang_names = hg_config.load_lang_names()
    file_total_count = sum([len(x) for _, x in hg_config.content.items()])
    os.makedirs('locale', exist_ok=True)
    for lang_code in os.listdir('locale'):
        os.environ["LANGUAGE"] = lang_code
        hugo_lang_code = hg_config.convert_lang_code(lang_code)
        file_l10n_count = 0
        default_func = None
        l10n_results: L10NResults = {}

        for domain in hg_config.content:
            domain_name = domain if domain != 'default' else hg_config.default_domain_name
            mo_path = f'locale/{lang_code}/LC_MESSAGES/{domain_name}.mo'
            if os.path.isfile(mo_path):
                l10n_func = gettext_func(domain_name)
            # ensure generate_content_domain is still called even when a language has no file for the domain,
            #   so that, for example, a language that only has string translations and no file translation
            #   can still be qualified if there are files with no content to be translated
            else:
                def l10n_func(x): return x
            if domain_name == hg_config.default_domain_name:
                default_func = l10n_func
            l10n_env = L10NEnv(l10n_results, hugo_lang_code, l10n_func, mdi, hg_config, src_strings)
            file_l10n_count += generate_content_domain(domain, l10n_env)
        if default_func is None:
            mo_path = f'locale/{lang_code}/LC_MESSAGES/{hg_config.default_domain_name}.mo'
            if os.path.isfile(mo_path):
                default_func = gettext_func(hg_config.default_domain_name)
            # ensure default_func is not None and thus generate_others is still called even when a language
            #   has no file for the default domain, so that the language can still be qualified
            else:
                def default_func(x): return x
        logging.info(f'{hugo_lang_code} [{file_l10n_count}/{file_total_count}]')

        if default_func is not None:
            l10n_env = L10NEnv(l10n_results, hugo_lang_code, default_func, mdi, hg_config, src_strings)
            generate_data_others(lang_code, file_total_count, file_l10n_count, l10n_env, lang_names, src_data)
    if not args.keep_locale:
        shutil.rmtree('locale')
    write_config(hg_config.hugo_config, original_hugo_config)
