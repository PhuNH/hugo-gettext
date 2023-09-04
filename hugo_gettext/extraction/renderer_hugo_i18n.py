# SPDX-FileCopyrightText: 2023 Phu Hung Nguyen <phuhnguyen@outlook.com>
# SPDX-License-Identifier: LGPL-2.1-or-later

from typing import Sequence, List

from markdown_it.token import Token
from markdown_it.utils import EnvType, OptionsDict
from mdit_py_i18n import utils
from mdit_py_i18n.renderer_i18n import MdCtx, RendererMarkdownI18N

from ..utils import HugoDomainEProtocol, HG_STOP, SHORTCODE_QUOTES


class HugoMdCtx(MdCtx):
    def __init__(self, env: EnvType):
        super().__init__(env)
        self.domain_e: HugoDomainEProtocol = env['domain_extraction']
        self.with_line: bool = env['with_line']

    def add_entry(self, msgid: str, line_number: int, comment: str = '', msgctxt: str = ''):
        line_number = line_number if self.with_line else 0
        self.domain_e.add_entry(self.path, msgid, line_number, comment, msgctxt)


class RendererHugoI18N(RendererMarkdownI18N):
    def render(self, tokens: Sequence[Token], _options: OptionsDict, env: EnvType):
        """
        :param tokens: list of block tokens to render
        :param _options: properties of parser instance
        :param env: containing:
            - 'path': path of the source file
            - 'domain_extraction': an object compatible with `HugoDomainEProtocol`
            - 'with_line': whether to include line number in the extraction
        :return: None
        """
        md_ctx = HugoMdCtx(env)

        for i, token in enumerate(tokens):
            if token.type in self.rules:
                r = self.rules[token.type](tokens, i, md_ctx)
                if r == -1:
                    break
        self._link_ref(env, md_ctx)

    @classmethod
    def inline(cls, tokens: Sequence[Token], idx: int, md_ctx: HugoMdCtx):
        token = tokens[idx]
        # when there's no relevant config, ignore the whole shortcode
        if len(token.children) == 1 and (sc := token.children[0]).type == 'shortcode':
            if sc.meta['name'] == HG_STOP:
                return -1
            sc_params_config = md_ctx.domain_e.e.hg_config.shortcodes.get('params', {})
            sc_params_to_i12ize: List = sc_params_config.get(sc.meta['name'], [])
            sc_params_to_i12ize.extend(sc_params_config.get('*', []))
            sc_params_used = sc.meta['params']
            for param in sc_params_to_i12ize:
                if param in sc_params_used:
                    content: str = sc_params_used[param]
                    if content[0] in SHORTCODE_QUOTES:
                        # keep newlines in raw string parameters (passed with ``)
                        if content[0] == '"':
                            content = utils.SPACES_PATTERN.sub(' ', content)
                        content = content[1:-1]
                    md_ctx.add_entry(content, token.map[0] + 1)
        else:
            # in case we want to parse shortcodes nested in inlines
            # content = ''
            # link = ''
            # for t in token.children:
            #     if t.type == 'softbreak':
            #         content += ' '
            #     elif t.type == 'link_open':
            #         content += '['
            #         link = t.attrs['href']
            #     elif t.type == 'link_close':
            #         content += f']({link})'
            #     elif t.type in {'em_open', 'em_close', 'strong_open', 'strong_close'}:
            #         content += t.markup
            #     elif t.type == 'image':
            #         content += f'![{t.content}]({t.attrs["src"]})'
            #     elif t.type == 'code_inline':
            #         content += f'{t.markup}{t.content}{t.markup}'
            #     else:
            #         content += t.content
            # content = utils.SPACES_PATTERN.sub(' ', content)
            super().inline(tokens, idx, md_ctx)
