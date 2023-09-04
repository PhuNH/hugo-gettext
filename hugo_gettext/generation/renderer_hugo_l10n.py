# SPDX-FileCopyrightText: 2023 Phu Hung Nguyen <phuhnguyen@outlook.com>
# SPDX-License-Identifier: LGPL-2.1-or-later

from typing import List, Dict, Sequence, Tuple

from markdown_it.token import Token
from markdown_it.utils import EnvType, OptionsDict
from mdit_py_i18n import utils
from mdit_py_i18n.renderer_l10n import MdCtx, RendererMarkdownL10N, SETEXT_HEADING_MARKUPS
from mdit_py_i18n.utils import L10NResult

from ..utils import HugoDomainGProtocol, HG_STOP, SHORTCODE_QUOTES


class HugoMdCtx(MdCtx):
    def __init__(self, env: EnvType):
        super().__init__(env)
        self.domain_g: HugoDomainGProtocol = env['domain_generation']
        self.heading_attrs: List[Dict] = []


class RendererHugoL10N(RendererMarkdownL10N):
    def render(self, tokens: Sequence[Token], _options: OptionsDict, env: EnvType) -> Tuple[L10NResult, L10NResult]:
        """
        :param tokens: list of block tokens to render
        :param _options: properties of parser instance
        :param env: containing 'domain_generation' an object compatible with `HugoDomainGProtocol`
        :return: an `L10NResult`
        """
        md_ctx = HugoMdCtx(env)

        if (token := tokens[0]).type == 'front_matter':
            fm_result = md_ctx.domain_g.render_front_matter(token.content, token.markup)
            tokens = tokens[1:]
        else:
            fm_result = L10NResult('', 0, 0)

        content_result = L10NResult('', 0, 0)
        for i, token in enumerate(tokens):
            if token.type in self.rules:
                r = self.rules[token.type](tokens, i, md_ctx, content_result)
                if r == -1:
                    break
        self._link_ref(env, md_ctx, content_result)

        return fm_result, content_result

    @classmethod
    def _shortcode(cls, token: Token, sc_params_to_localize: List, md_ctx: HugoMdCtx, content_result: L10NResult):
        opening = token.meta['markup']
        closing = opening if opening == '%' else '>'
        opening = '{{' + opening
        closing = closing + '}}'
        args = ''
        sc_params = token.meta['params']
        for param in sc_params:
            content: str = sc_params[param]
            quote = content[0]
            if quote in SHORTCODE_QUOTES:
                # keep newlines in raw string parameters (passed with ``)
                if quote == '"':
                    content = utils.SPACES_PATTERN.sub(' ', content)
                content = content[1:-1]
            else:
                quote = ''
            if param in sc_params_to_localize:
                localized_content = md_ctx.domain_g.l10n_func(content)
                if localized_content is not content:
                    content_result.l10n_count += 1
                content_result.total_count += 1
            else:
                localized_content = content
            param_name_part = '' if token.meta['is_positional'] else f'{param}='
            args += f' {param_name_part}{quote}{localized_content}{quote}'
        # keep no space after the opening to take advantage of HTML highlighting
        content_result.localized += f"{md_ctx.get_line_indent()}{opening}{token.meta['name']}{args} {closing}"

    @staticmethod
    def _attribute_block(attrs: Dict):
        s = ''
        for k, v in attrs.items():
            if k == 'class':
                for c in v.split(' '):
                    s += f'.{c} '
            elif k == 'id':
                s += f'#{v} '
            else:
                s += f'{k}="{v}" '
        return '{' + s + '}'

    @classmethod
    def _attributes(cls, token: Token, md_ctx: MdCtx, content_result: L10NResult):
        if token.attrs:
            attrs_s = cls._attribute_block(token.attrs)
            content_result.localized += f'{md_ctx.line_indent}{attrs_s}\n'

    @classmethod
    def inline(cls, tokens: Sequence[Token], idx: int, md_ctx: HugoMdCtx, content_result: L10NResult):
        token = tokens[idx]
        if len(token.children) == 1 and (sc := token.children[0]).type == 'shortcode':
            if sc.meta['name'] == HG_STOP:
                return -1
            sc_params_config = md_ctx.domain_g.lang_g.g.hg_config.shortcodes.get('params', {})
            sc_params_to_localize: List = sc_params_config.get(sc.meta['name'], [])
            sc_params_to_localize.extend(sc_params_config.get('*', []))
            cls._shortcode(sc, sc_params_to_localize, md_ctx, content_result)
        else:
            super().inline(tokens, idx, md_ctx, content_result)

    @classmethod
    def blockquote_close(cls, tokens: Sequence[Token], idx: int, md_ctx: MdCtx, content_result: L10NResult):
        token = tokens[idx]
        # unindent before adding the rendered attributes
        md_ctx.line_indent = md_ctx.line_indent[:-2]
        cls._attributes(token, md_ctx, content_result)
        content_result.localized += f'{md_ctx.line_indent}\n'

    @classmethod
    def heading_open(cls, tokens: Sequence[Token], idx: int, md_ctx: HugoMdCtx, _content_result: L10NResult):
        super().heading_open(tokens, idx, md_ctx, _content_result)
        token = tokens[idx]
        if token.attrs:
            md_ctx.heading_attrs.append(token.attrs)

    @classmethod
    def heading_close(cls, _tokens: Sequence[Token], _idx: int, md_ctx: HugoMdCtx, content_result: L10NResult):
        # for headings, put rendered attributes on the same line
        if md_ctx.heading_attrs:
            attrs_s = cls._attribute_block(md_ctx.heading_attrs.pop())
            content_result.localized += attrs_s
        super().heading_close(_tokens, _idx, md_ctx, content_result)

    @classmethod
    def hr(cls, tokens: Sequence[Token], idx: int, md_ctx: MdCtx, content_result: L10NResult):
        # just put rendered attributes below the hr
        super().hr(tokens, idx, md_ctx, content_result)
        cls._attributes(tokens[idx], md_ctx, content_result)

    @classmethod
    def bullet_list_close(cls,
                          tokens: Sequence[Token],
                          idx: int,
                          md_ctx: MdCtx,
                          content_result: L10NResult):
        # things are ready after list_item_close so here put rendered attributes in and close the list
        # the same with ordered_list_close
        cls._attributes(tokens[idx], md_ctx, content_result)
        super().bullet_list_close(tokens, idx, md_ctx, content_result)

    # paragraph
    @classmethod
    def paragraph_close(cls, tokens: Sequence[Token], idx: int, md_ctx: MdCtx, content_result: L10NResult):
        token = tokens[idx]
        content_result.localized += '\n'
        # rendered attributes should be after a newline, so we can't call the super method
        cls._attributes(token, md_ctx, content_result)
        if idx < len(tokens) - 1:
            next_token = tokens[idx + 1]
            # add a blank line when next token is a setext heading_open, an indented code block, a paragraph open,
            # or a definition list open
            if (next_token.type == 'heading_open' and next_token.markup in SETEXT_HEADING_MARKUPS) \
                    or next_token.type in {'code_block', 'paragraph_open', 'dl_open'}:
                content_result.localized += f'{md_ctx.line_indent}\n'

    @classmethod
    def table_close(cls, tokens: Sequence[Token], idx: int, md_ctx: MdCtx, content_result: L10NResult):
        # things are ready after tr_close so here put rendered attributes in and close the table
        cls._attributes(tokens[idx], md_ctx, content_result)
        super().table_close(tokens, idx, md_ctx, content_result)

    @classmethod
    def dd_close(cls, tokens: Sequence[Token], idx: int, md_ctx: MdCtx, content_result: L10NResult):
        latest_len = md_ctx.indents.pop()
        # unindent before adding the rendered attributes
        md_ctx.line_indent = md_ctx.line_indent[:-latest_len]
        # but only at the last dd_close
        if idx + 1 < len(tokens) and (token := tokens[idx+1]).type == 'dl_close':
            cls._attributes(token, md_ctx, content_result)
        content_result.localized += f'{md_ctx.line_indent}\n'
