__author__ = 'frank'

import ast

import polib
import os
import re

from c3po.conf import settings

METADATA_EMPTY = "{'comment': '', 'previous_msgctxt': None, " + \
                 "'encoding': 'utf-8', 'obsolete': 0, 'msgid_plural': '', " + \
                 "'msgstr_plural': {}, 'occurrences': [], 'msgctxt': None, " + \
                 "'flags': [], 'previous_msgid': None, " + \
                 "'previous_msgid_plural': None}"


def _write_header(po_path, lang, header=''):
    """
    Write header into po file for specific lang.
    Metadata are read from settings file.
    """
    po_file = open(po_path, 'w')
    po_file.write(header + '\n')
    content = '{}{}{}{}{}{}{}{}{}{}{}{}'.format(
        'msgid ""', '\nmsgstr ""', '\n"MIME-Version: ', settings.METADATA['MIME-Version'], r'\n"''\n"Content-Type: ',
        settings.METADATA['Content-Type'], r'\n"''\n"Content-Transfer-Encoding: ',
        settings.METADATA['Content-Transfer-Encoding'], r'\n"''\n"Language: ', lang, r'\n"', '\n')
    po_file.write(content)
    po_file.close()


def _get_all_po_filenames(locale_root, lang, po_files_path):
    """
    Get all po filenames from locale folder and return list of them.
    Assumes a directory structure:
    <locale_root>/<lang>/<po_files_path>/<filename>.
    """
    all_files = os.listdir(os.path.join(locale_root, lang, po_files_path))
    return filter(lambda s: s.endswith('.po'), all_files)


def _prepare_locale_dirs(languages, locale_root):
    """
    Prepare locale dirs for writing po files.
    Create new directories if they doesn't exist.
    """
    for lang in enumerate(languages):
        lang_path = locale_root + "/" + lang[1]
        if not os.path.exists(lang_path):
            os.makedirs(lang_path)


def _prepare_polib_files(files_dict, filename, languages,
                         locale_root, po_files_path, header):
    """
    Prepare polib file object for writing/reading from them.
    Create directories and write header if needed. For each language,
    ensure there's a translation file named "filename" in the correct place.
    Assumes (and creates) a directory structure:
    <locale_root>/<lang>/<po_files_path>/<filename>.
    """
    files_dict[filename] = {}
    for lang in languages:
        file_path = os.path.join(locale_root, lang, po_files_path)
        if not os.path.exists(file_path):
            os.makedirs(file_path)

        _write_header(os.path.join(file_path, filename), lang, header)
        files_dict[filename][lang] = polib.pofile(
            os.path.join(file_path, filename), encoding="UTF-8")


def _write_entries(po_files, languages, msgid, msgstrs, metadata, comment):
    """
    Write msgstr for every language with all needed metadata and comment.
    Metadata are parser from string into dict, so read them only from gdocs.
    """
    start = re.compile(r'^[\s]+')
    end = re.compile(r'[\s]+$')
    for i, lang in enumerate(languages):
        meta = ast.literal_eval(metadata)
        entry = polib.POEntry(**meta)
        entry.tcomment = comment
        entry.msgid = msgid
        if msgstrs[i]:
            start_ws = start.search(msgid)
            end_ws = end.search(msgid)
            entry.msgstr = str(start_ws.group() if start_ws else '') + \
                           unicode(msgstrs[i].strip()) + \
                           str(end_ws.group() if end_ws else '')
        else:
            entry.msgstr = ''
        po_files[lang].append(entry)


def po_to_list(trans, meta, languages, locale_root, po_files_path):
    """
    Finds all .po files in locale_root directory and converts them into gspread.Cell list.
    """
    po_files = _get_all_po_filenames(locale_root, languages[0], po_files_path)

    last_row = 0
    for po_file in po_files:
        po = polib.pofile(locale_root + "/" + languages[0] + "/" + po_files_path + "/" + po_file)
        for entry_no, entry in enumerate(po):
            curr_row = entry_no + 1 + last_row
            trans[0][curr_row].value = entry.tcomment
            trans[1][curr_row].value = entry.msgid
            meta[0][curr_row].value = po_file
            meta[1][curr_row].value = METADATA_EMPTY
        last_row += entry_no + 1

    for col in range(2, len(trans)):
        trans[col][0].value = languages[col - 2]
        last_row = 0
        for po_file in po_files:
            po = polib.pofile(locale_root + "/" + trans[col][0].value + "/" + po_files_path + "/" + po_file)
            for entry_no, entry in enumerate(po):
                curr_row = entry_no + last_row + 1
                if not settings.AUTO_TRANSLATE:
                    trans[col][entry_no + 1 +last_row].value = entry.msgstr
                else:
                    value = "=GoogleTranslate(B{}{}{}{}{}{}{}{}".format(str(curr_row + 1), ", \"", settings.DEFAULT_LANGUAGE, "\", ", "\"", trans[col][0].value, "\"", ")")
                    trans[col][curr_row].value = value
            last_row += entry_no + 1

    return trans, meta


def list_to_po(trans, meta, locale_root, po_files_path, languages, header='# translated with c3po\n'):
    """
    Takes gspread.Cell list save data from that list in .po files
    """
    # deleting previous files
    pattern = "^\w+.*po$"
    for root, dirs, files in os.walk(locale_root):
        for f in filter(lambda x: re.match(pattern, x), files):
            os.remove(os.path.join(root, f))

    _prepare_locale_dirs(languages, locale_root)

    po_files = {}

    for row in range(1, len(trans[0])):  # from because of column titles
        filename = meta[0][row].value
        if filename != '':
            metadata = meta[1][row].value.rstrip() if meta[1][row].value else METADATA_EMPTY  # if meta[1] else - before
            msgid = trans[1][row].value
            comment = trans[0][row].value
            new_row = []
            new_row.append([trans[col][row].value for col in range(2, len(trans))])

            if filename not in po_files:
                _prepare_polib_files(po_files, filename, languages,
                                     locale_root, po_files_path, header)

            _write_entries(po_files[filename], languages, msgid, new_row, metadata, comment)

            for filename in po_files:
                for lang in po_files[filename]:
                    po_files[filename][lang].save()








