# SPDX-FileCopyrightText: 2021 Phu Hung Nguyen <phuhnguyen@outlook.com>
# SPDX-License-Identifier: LGPL-2.1-or-later

import os
from typing import Set, Tuple, List, Optional

import yaml
from markdown_gettext.domain_generation import gettext_func
from markdown_it import MarkdownIt
from mdit_py_i18n import utils
from mdit_py_i18n.utils import L10NFunc, L10NResult

from ..utils import HugoLangGProtocol

DEFAULT_RATE_THRESHOLD = 0.75


class HugoDomainG:
    """
    Implements `HugoDomainGProtocol`
    """
    def __init__(self, lang_g: HugoLangGProtocol, l10n_func: L10NFunc):
        self.lang_g = lang_g
        self.l10n_func = l10n_func

    def localize_object_string(self, s: str, mdi: Optional[MarkdownIt]) -> L10NResult:
        """Localize `s` as Markdown using `mdi` if it's provided, otherwise, using `l10n_func`.
        :param s: the string to localize
        :param mdi: `MarkdownIt` object used to localize string as Markdown if provided
        :return: an `L10NResult` whose `total_count` is always considered `1`, as this is only "one" string.
        """
        if mdi:
            env = {
                'domain_generation': self
            }
            _, content_result = mdi.render(s, env)
        else:
            localized_s = self.l10n_func(s)
            # in front matters only count translations that are different from source messages
            l10n_count = 1 if s != localized_s else 0
            content_result = L10NResult(localized_s, 1, l10n_count)
        return content_result

    def localize_object(self,
                        o,
                        excluded_keys: Set[str],
                        mdi: Optional[MarkdownIt] = None) -> L10NResult:
        """Localize an object, either in front matters or in data files.
        :param o: the object being processed
        :param excluded_keys: a set of keys whose values are not processed
        :param mdi: `MarkdownIt` object used to localize string as Markdown if provided
        :return: an `L10NResult`. Translations are made in-place.
        """
        total_count, l10n_count = 0, 0
        if isinstance(o, str) and o and not utils.SPACES_PATTERN.fullmatch(o):
            if (obj_str_result := self.localize_object_string(o, mdi)).l10n_count > 0:
                return L10NResult(obj_str_result.localized, 1, 1)
            return L10NResult(o, 1, 0)
        if isinstance(o, list) or isinstance(o, dict):
            for key, value in (enumerate(o) if isinstance(o, list) else o.items()):
                if key in excluded_keys:
                    if key == 'aliases':
                        localized_urls = []
                        for url in value:
                            if url.startswith('/'):
                                localized_urls.append(f'/{self.lang_g.hugo_lang_code}{url}')
                            else:
                                localized_urls.append(url)
                        o[key] = localized_urls
                    continue
                item_result = self.localize_object(value, excluded_keys, mdi)
                total_count += item_result.total_count
                l10n_count += item_result.l10n_count
                o[key] = item_result.localized
            return L10NResult(o, total_count, l10n_count)
        return L10NResult(o, total_count, l10n_count)

    def _process_fm_conditions(self, fm):
        hg_config = self.lang_g.g.hg_config
        l10n_results = self.lang_g.l10n_results
        src_strings = self.lang_g.g.src_strings
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
                    strings_result = self.lang_g.localize_strings()
                    rate = strings_result.rate
                else:
                    cond_fm_result, content_result = self.__class__(self.lang_g, l10n_func).render_content_file(item)
                    rate = (cond_fm_result + content_result).rate
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

    def render_front_matter(self, content: str, markup: str) -> L10NResult:
        fm = yaml.safe_load(content)

        fm_result = self.localize_object(fm, self.lang_g.g.hg_config.excluded_keys)
        self._process_fm_conditions(fm)

        rendered_localized_fm = yaml.dump(fm, default_flow_style=False, allow_unicode=True)
        fm_result.localized = f'{markup}\n{rendered_localized_fm}\n{markup}\n'
        return fm_result

    def render_content_file(self, path: str) -> Tuple[L10NResult, L10NResult]:
        if path in self.lang_g.l10n_results:
            results = self.lang_g.l10n_results[path]
            return results[0], results[1]
        with open(path) as f_content:
            env = {
                'domain_generation': self
            }
            fm_result, content_result = self.lang_g.g.mdi.render(f_content.read(), env)
            self.lang_g.l10n_results[path] = [fm_result, content_result]
            return fm_result, content_result

    def write_content_file(self, fm: str, content: str, src_path: str):
        hg_config = self.lang_g.g.hg_config
        hugo_lang_code = self.lang_g.hugo_lang_code
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

    def generate_content_domain(self, domain_paths: List[str]):
        file_l10n_count = 0
        for src_path in domain_paths:
            if os.path.isfile(src_path):
                fm_result, content_result = self.render_content_file(src_path)
                if fm_result.l10n_count > 0 or content_result.rate == -1 or content_result.rate > 0.5:
                    # print(f'{src_path}: {fm_result}; {content_result}')
                    self.write_content_file(fm_result.localized, content_result.localized, src_path)
                    file_l10n_count += 1
        return file_l10n_count
