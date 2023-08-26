# SPDX-FileCopyrightText: 2023 Phu Hung Nguyen <phuhnguyen@outlook.com>
# SPDX-License-Identifier: LGPL-2.1-or-later

import inspect
from typing import Sequence, MutableMapping, List

import pygments.token
import yaml
from markdown_it.renderer import RendererProtocol
from markdown_it.token import Token
from markdown_it.utils import OptionsDict
from pygments import lexers, util

from .extraction_utils import I18NEnv
from .i18n_object import i12ize_object
from .. import utils


def _link_ref(env: MutableMapping, i18n_env: I18NEnv):
    refs = env.get('references', {}).items()
    if len(refs) == 0:
        return
    for ref, details in refs:
        if title := details.get('title', ''):
            # TODO: line number?
            i18n_env.add_entry(env['l10n_func'](title), 0)


class RendererMarkdownI18N(RendererProtocol):
    def __init__(self, _):
        self.rules = {
            k: v
            for k, v in inspect.getmembers(self, predicate=inspect.ismethod)
            if not (k.startswith("render") or k.startswith("_"))
        }

    def render(self, tokens: Sequence[Token], options: OptionsDict, env: MutableMapping):
        i18n_env = I18NEnv.from_env(env)

        for i, token in enumerate(tokens):
            if token.type in self.rules:
                r = self.rules[token.type](tokens, i, i18n_env)
                if r == -1:
                    break

        _link_ref(env, i18n_env)

    @classmethod
    def front_matter(cls, tokens: Sequence[Token], idx: int, i18n_env: I18NEnv):
        token = tokens[idx]

        fm = yaml.safe_load(token.content)

        # TODO support i12izing front matter as markdown
        i18n_env.mdi = None
        i12ize_object(fm, i18n_env)

    @classmethod
    def inline(cls, tokens: Sequence[Token], idx: int, i18n_env: I18NEnv):
        token = tokens[idx]
        # when there's no relevant config, ignore the whole shortcode
        if len(token.children) == 1 and (sc := token.children[0]).type == 'shortcode':
            if sc.meta['name'] == utils.HG_STOP:
                return -1
            sc_params_config = i18n_env.hg_config.shortcodes.get('params', {})
            sc_params_to_i12ize: List = sc_params_config.get(sc.meta['name'], [])
            sc_params_to_i12ize.extend(sc_params_config.get('*', []))
            sc_params_used = sc.meta['params']
            for param in sc_params_to_i12ize:
                if param in sc_params_used:
                    content: str = sc_params_used[param]
                    if content[0] in utils.SHORTCODE_QUOTES:
                        # keep newlines in raw string parameters (passed with ``)
                        if content[0] == '"':
                            content = utils.SPACES_PATTERN.sub(' ', content)
                        content = content[1:-1]
                    i18n_env.add_entry(content, token.map[0] + 1)
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
            content = utils.SPACES_PATTERN.sub(' ', token.content.replace('\n', ' '))
            if content and not utils.SPACES_PATTERN.fullmatch(content):
                i18n_env.add_entry(content, token.map[0] + 1)

    @classmethod
    def fence(cls, tokens: Sequence[Token], idx: int, i18n_env: I18NEnv):
        token = tokens[idx]
        try:
            lexer = lexers.get_lexer_by_name(token.info)
        except util.ClassNotFound:
            lexer = lexers.guess_lexer(token.content)
        code_toks = lexer.get_tokens(token.content)

        # temporary content of the comment being parsed
        # also indicates whether we are parsing a comment or not
        comment = ''
        # number of the line where the comment starts
        comment_line_num = 0
        # number of the last line with a comment token
        last_comment_line_num = 0
        # the token starts with one line of the fence, then the content. +1: 0-base -> 1-base
        line_num = token.map[0] + 1 + 1

        # concatenate comment tokens until either a non-comment token or a blank line or end of token stream
        for tok_type, tok_val in code_toks:
            if tok_type == pygments.token.Token.Comment.Single:
                # when another comment is already being parsed and there's a blank line
                if comment and line_num - last_comment_line_num > 1:
                    i18n_env.add_entry(comment, comment_line_num)
                    comment = ''
                    comment_line_num = 0
                comment_match = utils.SINGLE_COMMENT_PATTERN.match(tok_val)
                if comment != '':
                    comment += ' '
                comment += comment_match.group(2).strip()
                if comment_line_num == 0:
                    comment_line_num = line_num
                last_comment_line_num = line_num
            elif tok_val.strip() and comment:
                i18n_env.add_entry(comment, comment_line_num)
                comment = ''
                comment_line_num = 0
            line_num += tok_val.count('\n')
        if comment:
            i18n_env.add_entry(comment, comment_line_num)

    @classmethod
    def html_block(cls, tokens: Sequence[Token], idx: int, i18n_env: I18NEnv):
        token = tokens[idx]
        i18n_env.add_entry(token.content, token.map[0] + 1)
