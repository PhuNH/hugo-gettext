---
authors:
- SPDX-FileCopyrightText: 2023 Phu Hung Nguyen <phuhnguyen@outlook.com>
SPDX-License-Identifier: CC0-1.0
---
* bullet 1
* bullet 2
bullet 2 second line
* bullet 3

1. ordered 1
2. ordered 2
3. ordered 3
4. ordered 4

* bullet 1
  * nested bullet 1
    * nested nested bullet 1
    * nested nested bullet 2
  * nested bullet 2
* bullet 2

1) ordered 1
   1) nested ordered 1
   2) nested ordered 2
      1) nested nested ordered 1
   3) nested ordered 3
2) ordered 2
   1) nested 2.1
   2) nested 2.2

1. mixed list
   - bullet inside 1
   - bullet 2 inside 1
     1. ordered inside bullet 2 inside 1
2. second item

1) ordered 1 with bullet list
    + bullet 1 inside 1
    + bullet 2 inside 1

1) ordered 2 after a blank line

1. 1. list right at beginning of an item
2. second item

1) list with blockquote
   > inside blockquote
   > 1. list inside blockquote
   > 2. another list item

1. list with code

       int main():
           return 0
2. fence in item

   ```python
   def main():
       return None
   ```

3. # can an atx heading be here?
   ---
   now a table

   | head | head2 |
   |------|-------|
   | body | body2 |
4. two paragraphs

   in one list item
5. term number 2
   : details number 2
   onto the next line, without indentation
6. can a setext heading be here?
   -
   [foo]: /url "title"

   this is a reference [foo]. and after the reference.