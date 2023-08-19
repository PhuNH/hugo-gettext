# SPDX-FileCopyrightText: 2023 Phu Hung Nguyen <phuhnguyen@outlook.com>
# SPDX-License-Identifier: LGPL-2.1-or-later

from typing import Callable

L10NFunc = Callable[[str], str]


class L10NResult:
    """
    Localized content, total number of messages, number of translations
    If there are no messages, rate will be -1
    """
    def __init__(self, localized, total_count, l10n_count):
        self.localized = localized
        self.total_count = total_count
        self.l10n_count = l10n_count

    def __str__(self):
        return f'({self.l10n_count}/{self.total_count})'

    @property
    def rate(self):
        return self.l10n_count / self.total_count if self.total_count > 0 else -1
