import unittest
import shutil
import os
import polib
from c3po.converters.po_list import list_to_po, po_to_list, _get_all_po_filenames

TESTS_URL = 'https://docs.google.com/spreadsheet/ccc?key=0AnVOHClWGpLZdGFpQmpVUUx2eUg4Z0NVMGVQX3NrNkE#gid=0'

PO_CONTENT_LOCAL = [r'''# test
msgid ""
msgstr ""
"MIME-Version: 1.0\n"
"Content-Type: text/plain; charset=UTF-8\n"
"Content-Transfer-Encoding: 8bit\n"
"Language: %s\n"

#: tpl/base_site.html:44
msgid "Translation1"
msgstr "Str1 local"

#: tpl/base_site.html:44
msgid "Translation2"
msgstr ""

''', r'''# test
msgid ""
msgstr ""
"MIME-Version: 1.0\n"
"Content-Type: text/plain; charset=UTF-8\n"
"Content-Transfer-Encoding: 8bit\n"
"Language: %s\n"

#: tpl/base_site.html:44
msgid "Custom1"
msgstr "Str1 local"

#: tpl/base_site.html:44
msgid "Custom2"
msgstr ""

''']

PL_CUSTOM = [r'''# translated with c3po
msgid ""
msgstr ""
"MIME-Version: 1.0\n"
"Content-Type: text/plain; charset=UTF-8\n"
"Content-Transfer-Encoding: 8bit\n"
"Language: pl\n"

msgid "Translation1"
msgstr "Str1 local"

msgid "Translation2"
msgstr ""

''']

PL_DJANGO = [r'''# translated with c3po
msgid ""
msgstr ""
"MIME-Version: 1.0\n"
"Content-Type: text/plain; charset=UTF-8\n"
"Content-Transfer-Encoding: 8bit\n"
"Language: pl\n"

msgid "Custom1"
msgstr "Str1 local"

# komentarz
msgid "Custom2"
msgstr ""

''']

JA_CUSTOM = [r'''# translated with c3po
msgid ""
msgstr ""
"MIME-Version: 1.0\n"
"Content-Type: text/plain; charset=UTF-8\n"
"Content-Transfer-Encoding: 8bit\n"
"Language: ja\n"

msgid "Translation1"
msgstr "Str1 local"

msgid "Translation2"
msgstr ""

''']

JA_DJANGO = [r'''# translated with c3po
msgid ""
msgstr ""
"MIME-Version: 1.0\n"
"Content-Type: text/plain; charset=UTF-8\n"
"Content-Transfer-Encoding: 8bit\n"
"Language: ja\n"

msgid "Custom1"
msgstr "Str1 local"

# komentarz
msgid "Custom2"
msgstr ""

''']

EN_CUSTOM = [r'''# translated with c3po
msgid ""
msgstr ""
"MIME-Version: 1.0\n"
"Content-Type: text/plain; charset=UTF-8\n"
"Content-Transfer-Encoding: 8bit\n"
"Language: en\n"

msgid "Translation1"
msgstr "Str1 local"

msgid "Translation2"
msgstr ""

''']

EN_DJANGO = [r'''# translated with c3po
msgid ""
msgstr ""
"MIME-Version: 1.0\n"
"Content-Type: text/plain; charset=UTF-8\n"
"Content-Transfer-Encoding: 8bit\n"
"Language: en\n"

msgid "Custom1"
msgstr "Str1 local"

# komentarz
msgid "Custom2"
msgstr ""

''']


class Cell:
    def __init__(self, value):
        self.value = value


class TestConverters(unittest.TestCase):
    def setUp(self):
        self.temp_dir = 'temp-conf'
        if os.path.exists(self.temp_dir):
            shutil.rmtree(self.temp_dir)
        self.languages = ['en', 'pl', 'ja']
        self.po_filenames = ['custom.po', 'django.po']
        self.locale_root = os.path.join(self.temp_dir, 'locale')
        self.po_files_path = 'LC_MESSAGES'
        self.header = '# test\n'
        os.makedirs(self.locale_root)
        for lang in self.languages:
            lang_path = os.path.join(self.locale_root, lang, self.po_files_path)
            os.makedirs(lang_path)

            with open(os.path.join(lang_path, self.po_filenames[0]), 'wb') as po_file:
                po_file.write(PO_CONTENT_LOCAL[0] % lang)
            with open(os.path.join(lang_path, self.po_filenames[1]), 'wb') as po_file:
                po_file.write(PO_CONTENT_LOCAL[1] % lang)

    def prepare_trans_and_meta(self):
        trans = []
        meta = []
        meta_col1 = []
        meta_col2 = []
        for i in range(5):
            trans.append([Cell('') for _ in range(5)])
            meta_col1.append(Cell(''))
            meta_col2.append(Cell(''))
        meta.append(meta_col1)
        meta.append(meta_col2)
        trans[0][0].value = 'comment'
        trans[1][0].value = 'to_translate'
        trans[2][0].value = 'en'
        trans[3][0].value = 'pl'
        trans[4][0].value = 'ja'

        return trans, meta

    def test_po_to_list(self):

        result = self.prepare_result()
        trans, meta = self.prepare_trans_and_meta()

        trans, meta = po_to_list(trans, meta, self.languages, self.locale_root, self.po_files_path)

        func_result = self.cell_list_helper(trans)

        self.assertEqual(result, func_result)

    def cell_list_helper(self, cell_list):
        help_list = []
        for i in range(5):
            tmp = []
            help_list.append(tmp)
        for col in range(len(cell_list)):
            for row in range(len(cell_list[0])):
                help_list[col].append(cell_list[col][row].value)
        return help_list

    def prepare_result(self):
        result = [['comment', '', '', '', ''],
                  ['to_translate', 'Translation1', 'Translation2', 'Custom1', 'Custom2'],
                  ['en', 'Str1 local', '', 'Str1 local', ''],
                  ['pl', 'Str1 local', '', 'Str1 local', ''],
                  ['ja', 'Str1 local', '', 'Str1 local', '']]

        return result

    def test_list_to_po(self):

        result = self.prepare_result()

        trans, meta = self.prepare_trans_and_meta()

        list_to_po(trans, meta, self.locale_root, self.po_files_path, self.languages)

        po_files = _get_all_po_filenames(self.locale_root, self.languages[0], self.po_files_path)

        for k in range(len(trans)):  # for every language
            for po_file in po_files:
                po = polib.pofile(os.path.join(self.locale_root, self.languages[0], self.po_files_path, po_file))
                for i, entry in enumerate(po_file):
                    self.assertEqual(entry.tcomment, result[0][i + 1])
                    self.assertEqual(entry.msgid, result[1][i + 1])
                    self.assertEqual(entry.msgstr, result[k][i + 1])

    def tearDown(self):
        shutil.rmtree(self.temp_dir)


if __name__ == '__main__':
    unittest.main()
