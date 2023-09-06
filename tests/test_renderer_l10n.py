# SPDX-FileCopyrightText: 2023 Phu Hung Nguyen <phuhnguyen@outlook.com>
# SPDX-License-Identifier: LGPL-2.1-or-later

import importlib.resources as pkg_resources
import unittest

from markdown_it import MarkdownIt
from mdit_py_hugo.attribute import attribute_plugin
from mdit_py_hugo.shortcode import shortcode_plugin
from mdit_py_plugins.deflist import deflist_plugin
from mdit_py_plugins.front_matter import front_matter_plugin

from hugo_gettext.generation.g_domain import HugoDomainG
from hugo_gettext.generation.renderer_hugo_l10n import RendererHugoL10N


class RendererHugoL10NTestCase(unittest.TestCase):
    mdi = (MarkdownIt(renderer_cls=RendererHugoL10N).use(front_matter_plugin).use(shortcode_plugin)
           .enable('table').use(deflist_plugin).use(attribute_plugin))

    def _prep_test(self, f_obj):
        env = {
            'domain_generation': HugoDomainG(None, lambda s: s)
        }
        # skip front matter
        tokens = self.mdi.parse(f_obj.read(), env)[1:]
        _, content_result = self.mdi.renderer.render(tokens, self.mdi.options, env)
        localized_tokens = self.mdi.parse(content_result.localized)
        return tokens, content_result, localized_tokens

    def test_attributes(self):
        with pkg_resources.open_text('tests.resources', 'attributes.md') as f_obj:
            tokens, content_result, localized_tokens = self._prep_test(f_obj)
            self.assertEqual([token.attrs for token in tokens if token.type != 'heading_close'],
                             [token.attrs for token in localized_tokens if token.type != 'heading_close'])
