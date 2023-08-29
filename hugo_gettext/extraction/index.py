# SPDX-FileCopyrightText: 2023 Phu Hung Nguyen <phuhnguyen@outlook.com>
# SPDX-License-Identifier: LGPL-2.1-or-later

import os

from .i18n_content import i12ize_content_domain
from .i18n_data_others import i12ize_data_others
from .extraction_utils import make_pot
from .renderer_md_i18n import RendererMarkdownI18N
from .. import utils


def extract(args):
    """Extract messages from source files
    :param args: arguments passed in command line, containing
        - pot: path of the directory containing the target pot file(s)
        - customs (optional): path to Python file containing custom functions
    :return: None. Data, config fields, and strings are extracted to the default domain,
    while content files are extracted to configured domains.
    """
    hg_config, mdi = utils.initialize(args.customs, RendererMarkdownI18N)
    dest = args.pot
    default_entries = []
    i12ize_data_others(default_entries, mdi)
    os.makedirs(dest, exist_ok=True)
    for domain, domain_paths in hg_config.content.items():
        if domain == 'default':
            i12ize_content_domain(domain_paths, default_entries, mdi)
        else:
            domain_entries = []
            i12ize_content_domain(domain_paths, domain_entries, mdi)
            make_pot(domain_entries, f'{dest}/{domain}.pot')
    make_pot(default_entries, f'{dest}/{hg_config.default_domain_name}.pot')
