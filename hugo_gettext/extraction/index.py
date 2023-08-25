# SPDX-FileCopyrightText: 2023 Phu Hung Nguyen <phuhnguyen@outlook.com>
# SPDX-License-Identifier: LGPL-2.1-or-later

import os

from .i18n_content import i12ize_content_domain
from .i18n_data_others import i12ize_data_others
from .extraction_utils import make_pot
from .renderer_md_i18n import RendererMarkdownI18N
from .. import utils


def extract(args):
    """
    Extract messages from source files
    :param args: arguments passed in command line, containing
        - pot: either path of the only target pot file or path of the directory containing the target pot file(s)
    :return: None
    """
    hg_config, mdi = utils.initialize(args.customs, RendererMarkdownI18N)
    dest = args.pot
    default_entries = []
    i12ize_data_others(default_entries, hg_config, mdi)
    os.makedirs(dest, exist_ok=True)
    for domain in hg_config.content:
        if domain == 'default':
            i12ize_content_domain(domain, default_entries, hg_config, mdi)
        else:
            domain_entries = []
            i12ize_content_domain(domain, domain_entries, hg_config, mdi)
            make_pot(domain_entries, f'{dest}/{domain}.pot', hg_config)
    make_pot(default_entries, f'{dest}/{hg_config.default_domain_name}.pot', hg_config)
