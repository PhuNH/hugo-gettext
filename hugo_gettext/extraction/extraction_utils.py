# SPDX-FileCopyrightText: 2023 Phu Hung Nguyen <phuhnguyen@outlook.com>
# SPDX-License-Identifier: LGPL-2.1-or-later

from dataclasses import dataclass
from datetime import datetime
from typing import List, MutableMapping

import polib
from markdown_it import MarkdownIt

from ..config import Config


@dataclass
class Occurrence:
    src_path: str
    line_num: int

    # this is used with tuple()
    def __iter__(self):
        for field in self.__dict__:
            # polib requires an int for line number, but number 0 passed to it would be lost, so we use string
            yield str(self.__getattribute__(field))


@dataclass
class Entry:
    msgid: str
    occurrence: Occurrence
    comment: str = ''

    def to_poentry(self) -> polib.POEntry:
        return polib.POEntry(msgid=self.msgid,
                             msgstr='',
                             occurrences=[tuple(self.occurrence)],
                             comment=self.comment)

    def add_to_pot(self, pot: polib.POFile):
        if self.msgid:
            if old_entry := pot.find(self.msgid):
                old_entry.occurrences.append(tuple(self.occurrence))
            else:
                try:
                    pot.append(self.to_poentry())
                except ValueError:
                    pass


def make_pot(entries: List[Entry], dest_path: str, hg_config: Config):
    pot = polib.POFile(check_for_duplicates=True)
    pot.metadata = {
        'Project-Id-Version': f'{hg_config.package} 1.0',
        'Report-Msgid-Bugs-To': hg_config.report_address,
        'POT-Creation-Date': datetime.now().astimezone().strftime('%Y-%m-%d %H:%M%z'),
        'PO-Revision-Date': 'YEAR-MO-DA HO:MI+ZONE',
        'Last-Translator': 'FULL NAME <EMAIL@ADDRESS>',
        'Language-Team': f'LANGUAGE <{hg_config.team_address}>',
        'MIME-Version': '1.0',
        'Content-Type': 'text/plain; charset=utf-8',
        'Content-Transfer-Encoding': '8bit',
    }
    for e in entries:
        e.add_to_pot(pot)
    pot.save(dest_path)


@dataclass
class I18NEnv:
    src_path: str
    entries: List[Entry]
    hg_config: Config
    mdi: MarkdownIt
    with_line: bool = True

    @classmethod
    def from_env(cls, env: MutableMapping):
        return cls(env['src_path'], env['entries'], env['hg_config'], env['mdi'], env['with_line'])

    def add_entry(self, msgid: str, line_num: int, comment: str = ''):
        line_num = line_num if self.with_line else 0
        occ = Occurrence(self.src_path, line_num)
        self.entries.append(Entry(msgid, occ, comment))
