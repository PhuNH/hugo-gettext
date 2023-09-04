<!--
SPDX-FileCopyrightText: 2023 Phu Hung Nguyen <phuhnguyen@outlook.com>
SPDX-License-Identifier: CC-BY-SA-4.0
-->

# hugo-gettext

I18n with gettext for Hugo.

## Install

```bash
pip install hugo-gettext
```

## Usage

There are three commands corresponding to three steps that _hugo-gettext_
supports:
- `hugo-gettext extract` extracts messages from source files (files in the
source language) to one or many POT files;
- `hugo-gettext compile` compiles PO files to binary MO files;
- `hugo-gettext generate` uses MO files to generate target files (files in
target languages).

These are types of text that _hugo-gettext_ can extract messages from and can
generate in target languages:
- Front matter and content in content files;
- Strings in string file (i.e. "translation table") in `i18n` folder
  - `other` keys
  - Support `comment`
- Menu item names, site title, and site description in site config file:
all in `languages.en` config key:
  - title: `title`
  - description: `params.description`
  - menu: `menu.main.<entry>.name`
- Data in data files: processed as Markdown (front matter text aren't
processed as Markdown).

Each project can specify multiple text domains to work with (i.e. messages are
extracted to multiple POT files and subsequently multiple PO files are
available to use for generation), however all types of text outside content
files always belong to a default domain which is derived from a name that each
project must have. Content files can be associated with the default domain or
custom domains.

### Compilation
- From a folder containing subdirectories with PO files inside,
in the form of `<dir>/<lang_code>/<domain>.po`
- To a `locale` folder
- Structure: `locale/<lang_code>/LC_MESSAGES/<domain>.po`

### Generation
- Conditions in front matter
- `hugo_lang_code`s are prepended to absolute links in `aliases` dict in front matter
- How data file generation works
- Requirement for a language to be qualified
(a config block is added and data files are generated, string file is generated anyway):
  - there's no content file to translate but string file is translated, or
  - there are content files to translate and some files are translated
- A content file is considered translated if
  - The front matter is translated, or
  - There's nothing in the content, or
  - The translation rate of the content is higher than 50%

### Markdown

CommonMark compliant. All core Markdown elements are supported, as well as
table, and definition list.

Some notes about how different elements are handled:
- Inlines: newlines and consecutive spaces are not kept;
- Content of each HTML block isn't parsed into finer tokens but processed
  as a whole;
- Fenced code blocks: only `//` single comments are processed;

#### Shortcodes
- If the string contains only one shortcode
- Newlines are kept for arguments quoted with backticks
- hg-stop shortcode to stop processing a content file

#### Attributes

## Configuration
- `package`: `Project-Id-Version` in POT metadata
- `report_address` and `team_address`: `Report-Msgid-Bugs-To` and `Language-Team` in POT metadata
- `excluded_keys`: in front matter
- `excluded_data_keys`: in data files
- `shortcodes`: can use `*` wildcard to indicate all shortcodes

### Custom functions
The path of the file should be passed as an argument to the command line with `-c` or `--customs` option,
or set in the config file with `customs` key.

The following functions are called to make `default_domain_name`, `excluded_keys`,
`report_address`, and `team_address` attributes of `Config`:
- `get_default_domain_name`: will be called with `package` as an argument, returns `package` by default
- `get_custom_excluded_keys`: returns an empty set by default
- `get_pot_fields`: returns a dictionary of `'report_address'` and `'team_address'` keys

Two functions are called during the generation step:
- `load_lang_names`: returns an empty dictionary by default
- `convert_lang_code`: function to convert gettext language codes to Hugo language codes,
returns gettext language codes by default

## Development

- With Conda

```bash
conda env create -f environment.yml
conda activate hg
poetry install
```