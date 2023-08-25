# SPDX-FileCopyrightText: 2023 Phu Hung Nguyen <phuhnguyen@outlook.com>
# SPDX-License-Identifier: LGPL-2.1-or-later

import copy
import os
from typing import Set, MutableMapping, Tuple, Dict

import yaml
from markdown_it.token import Token

from .generation_data_others import localize_strings
from .generation_utils import L10NEnv, L10NFunc, L10NResult, gettext_func
from .l10n_object import localize_object
from ..config import Config

DEFAULT_RATE_THRESHOLD = 0.75


# TODO support localizing front matter as markdown
def localize_front_matter(o, excluded_keys: Set[str], hugo_lang_code: str, l10n_func: L10NFunc) -> L10NResult:
    """Localize the front matter
    :param o: the front matter object
    :param excluded_keys: values of these keys are not processed
    :param hugo_lang_code: only used to prepend language code to absolute aliases
    :param l10n_func: a `gettext.gettext` function
    :return: an `L10NResult`. Translations are made in-place.
    """
    return localize_object(o, excluded_keys, hugo_lang_code, l10n_func)


def render_content_file(path: str,
                        l10n_env: L10NEnv) -> Tuple[L10NResult, L10NResult]:
    if path in l10n_env.l10n_results:
        results = l10n_env.l10n_results[path]
        return results[0], results[1]

    with open(path) as f_content:
        # copy to a new object so that one file's env isn't carried over to that of another
        fm_result, content_result = l10n_env.mdi.render(f_content.read(), copy.copy(l10n_env.__dict__))
        l10n_env.l10n_results[path] = [fm_result, content_result]
        return fm_result, content_result


def process_fm_conditions(fm: Dict, l10n_env: L10NEnv):
    hg_config = l10n_env.hg_config
    l10n_results = l10n_env.l10n_results
    src_strings = l10n_env.src_strings
    i18n_conditions = fm.get('i18n_configs', {}).get('conditions', [])
    conditions_met = True
    for cond in i18n_conditions:
        if isinstance(cond, str):
            item, threshold = cond, DEFAULT_RATE_THRESHOLD
        else:
            item, threshold = list(cond.items())[0]

        if item not in l10n_results:
            domain = (
                next(
                    (domain for domain in hg_config.content if item in hg_config.content[domain]),
                    '') if item != 'strings' else hg_config.default_domain_name)
            if not domain:
                continue
            if domain == 'default':
                domain = hg_config.default_domain_name

            l10n_func = gettext_func(domain)
            if item == 'strings':
                if not hg_config.do_strings or not src_strings:
                    continue
                strings_result = localize_strings(src_strings, l10n_func, l10n_results)
                rate = strings_result.rate
            else:
                cond_l10n_env = L10NEnv(l10n_results, l10n_env.hugo_lang_code, l10n_func, l10n_env.mdi,
                                        hg_config, src_strings)
                cond_fm_result, content_result = render_content_file(item, cond_l10n_env)
                rate = cond_fm_result.sum_rate_with(content_result)
        else:
            if item == 'strings':
                rate = l10n_results[item][0].rate
            else:
                cond_fm_result = l10n_results[item][0]
                content_result = l10n_results[item][1]
                rate = cond_fm_result.sum_rate_with(content_result)
        if rate < threshold:
            fm['i18n_configs']['warning'] = True
            conditions_met = False
            break

    if conditions_met and 'i18n_configs' in fm and 'warning' in fm['i18n_configs']:
        del fm['i18n_configs']['warning']


def render_front_matter(token: Token, env: MutableMapping) -> L10NResult:
    l10n_env = L10NEnv.from_env(env)

    fm = yaml.safe_load(token.content)

    fm_result = localize_front_matter(fm,
                                      l10n_env.hg_config.excluded_keys,
                                      l10n_env.hugo_lang_code,
                                      l10n_env.l10n_func)
    process_fm_conditions(fm, l10n_env)

    rendered_localized_fm = yaml.dump(fm, default_flow_style=False, allow_unicode=True)
    fm_result.localized = f'''---
{rendered_localized_fm}
---
'''

    return fm_result


def write_content_file(fm: str, content: str, src_path: str, hugo_lang_code: str, hg_config: Config):
    if hg_config.gen_to_other_dir:
        target_path = src_path.replace(f'{hg_config.src_dir}/',
                                       f'{hg_config.gen_dir}/{hugo_lang_code}/')
    else:
        extension = os.path.splitext(src_path)[1]
        basename = os.path.splitext(src_path)[0].split('.')[0]
        target_path = f'{basename}.{hugo_lang_code}{extension}'
    os.makedirs(os.path.dirname(target_path), exist_ok=True)

    with open(target_path, 'w+') as f_target:
        f_target.write(fm)
        f_target.write(content)


def generate_content_domain(domain_name: str, l10n_env: L10NEnv):
    file_l10n_count = 0
    for src_path in l10n_env.hg_config.content[domain_name]:
        if os.path.isfile(src_path):
            fm_result, content_result = render_content_file(src_path, l10n_env)
            # TODO: when a localized content file is accepted
            if fm_result.l10n_count > 0 or content_result.rate == -1 or content_result.rate > 0.5:
                # print(f'{src_path}: {fm_result}; {content_result}')
                write_content_file(fm_result.localized, content_result.localized, src_path,
                                   l10n_env.hugo_lang_code, l10n_env.hg_config)
                file_l10n_count += 1
    return file_l10n_count
