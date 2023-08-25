# SPDX-FileCopyrightText: 2021 Carl Schwan <carlschwan@kde.org>
# SPDX-FileCopyrightText: 2021 Phu Hung Nguyen <phuhnguyen@outlook.com>
# SPDX-License-Identifier: LGPL-2.1-or-later

import copy

from .extraction_utils import I18NEnv


def i12ize_object(o, i18n_env: I18NEnv):
    """Internationalize an object, either in front matter or in data files.
    :param o: the object being processed
    :param i18n_env: the I18NEnv object. Values of keys in i18n_env.hg_config.excluded_keys are not processed
    :return: None. Messages are added to the `i18n_env.entries` list.
    """
    if isinstance(o, str):
        if i18n_env.mdi:
            env = copy.copy(i18n_env.__dict__)
            env['with_line'] = False
            i18n_env.mdi.render(o, env)
        else:
            i18n_env.add_entry(o, 0)
    elif isinstance(o, list):
        for item in o:
            i12ize_object(item, i18n_env)
    elif isinstance(o, dict):
        for key in o:
            if key not in i18n_env.hg_config.excluded_keys:
                i12ize_object(o[key], i18n_env)
