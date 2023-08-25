# SPDX-FileCopyrightText: 2021 Carl Schwan <carlschwan@kde.org>
# SPDX-FileCopyrightText: 2021 Phu Hung Nguyen <phuhnguyen@outlook.com>
# SPDX-License-Identifier: LGPL-2.1-or-later

from typing import Set

from markdown_it import MarkdownIt

from .generation_utils import L10NFunc, L10NResult


def localize_object_string(s: str, l10n_func: L10NFunc, mdi: MarkdownIt) -> L10NResult:
    """Localize `s` as Markdown using `mdi` if it's provided, otherwise, using `l10n_func`.
    :param s: the string to localize
    :param l10n_func: a `gettext.gettext` function
    :param mdi: `MarkdownIt` object used to localize string as Markdown if provided
    :return: an `L10NResult` whose `total_count` is always considered `1`, as this is only "one" string.
    """
    if mdi:
        env = {
            'l10n_func': l10n_func
        }
        _, content_result = mdi.render(s, env)
    else:
        localized_s = l10n_func(s)
        # in front matter only count translations that are different from source messages
        l10n_count = 1 if s != localized_s else 0
        content_result = L10NResult(localized_s, 1, l10n_count)
    return content_result


def localize_object(o,
                    excluded_keys: Set[str],
                    hugo_lang_code: str,
                    l10n_func: L10NFunc,
                    mdi: MarkdownIt = None) -> L10NResult:
    """Localize an object, either in front matter or in data files.
    :param o: the object being processed
    :param excluded_keys: values of these keys are not processed
    :param hugo_lang_code: only used to prepend language code to absolute aliases
    :param l10n_func: a `gettext.gettext` function
    :param mdi: `MarkdownIt` object used to localize string as Markdown if provided
    :return: an `L10NResult`. Translations are made in-place.
    """
    # TODO: handle aliases here or where?
    total_count, l10n_count = 0, 0

    # TODO: with parsing front matter as markdown
    # if isinstance(o, str):
    if isinstance(o, list):
        for index, item in enumerate(o):
            if isinstance(item, str):
                total_count += 1
                if (obj_string_result := localize_object_string(item, l10n_func, mdi)).l10n_count > 0:
                    l10n_count += 1
                    o[index] = obj_string_result.localized
            else:
                more = localize_object(item, excluded_keys, hugo_lang_code, l10n_func, mdi)
                total_count += more.total_count
                l10n_count += more.l10n_count
    elif isinstance(o, dict):
        for key, value in o.items():
            if key in excluded_keys:
                if key == 'aliases':
                    localized_urls = []
                    for url in value:
                        if url.startswith('/'):
                            localized_urls.append(f'/{hugo_lang_code}{url}')
                        else:
                            localized_urls.append(url)
                    o[key] = localized_urls
                continue
            if not value:
                o[key] = ''
            elif isinstance(value, str):
                total_count += 1
                if (obj_string_result := localize_object_string(value, l10n_func, mdi)).l10n_count > 0:
                    l10n_count += 1
                    o[key] = obj_string_result.localized
            else:
                more = localize_object(value, excluded_keys, hugo_lang_code, l10n_func, mdi)
                total_count += more.total_count
                l10n_count += more.l10n_count

    return L10NResult(o, total_count, l10n_count)
