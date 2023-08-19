# SPDX-FileCopyrightText: 2023 Phu Hung Nguyen <phuhnguyen@outlook.com>
# SPDX-License-Identifier: LGPL-2.1-or-later

import unittest

import importlib.resources as pkg_resources
from markdown_it import MarkdownIt
from mdit_py_plugins.deflist import deflist_plugin
from mdit_py_plugins.front_matter import front_matter_plugin

from hugo_gettext.renderer_localized_md import RendererLocalizedMd


class RendererLocalizedMdTestCase(unittest.TestCase):
    mdi = MarkdownIt(renderer_cls=RendererLocalizedMd).use(front_matter_plugin) \
        .enable('table').use(deflist_plugin)

    def _prep_test(self, f_obj):
        env = {
            'l10n_func': lambda s: s
        }
        tokens = self.mdi.parse(f_obj.read(), env)
        # skip the front matter token
        tokens = tokens[1:]
        _, content_result = self.mdi.renderer.render(tokens, self.mdi.options, env)
        localized_tokens = self.mdi.parse(content_result.localized)
        return tokens, content_result, localized_tokens

    def test_blockquotes(self):
        with pkg_resources.open_text('tests.resources', 'blockquotes.md') as f_obj:
            tokens, content_result, localized_tokens = self._prep_test(f_obj)
            self.assertEqual([token.type for token in tokens], [token.type for token in localized_tokens])

    def test_lists(self):
        with pkg_resources.open_text('tests.resources', 'lists.md') as f_obj:
            tokens, content_result, localized_tokens = self._prep_test(f_obj)
            self.assertEqual([token.type for token in tokens], [token.type for token in localized_tokens])

    def test_definition_list(self):
        with pkg_resources.open_text('tests.resources', 'definition_list.md') as f_obj:
            tokens, content_result, localized_tokens = self._prep_test(f_obj)
            self.assertEqual([token.type for token in tokens], [token.type for token in localized_tokens])

    def test_others(self):
        with pkg_resources.open_text('tests.resources', 'renderer.md') as f_obj:
            tokens, content_result, localized_tokens = self._prep_test(f_obj)
            self.assertEqual([token.type for token in tokens], [token.type for token in localized_tokens])


if __name__ == '__main__':
    unittest.main()
