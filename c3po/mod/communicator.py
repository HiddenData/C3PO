#!/usr/bin/env python
# !/usr/bin/env python
# -*- coding: utf-8 -*

import os
import subprocess
import urlparse
from subprocess import Popen, PIPE
import polib

import gdata.spreadsheet.service
import gdata.docs.client
import gdata.docs.data
import gdata.data
import gdata.docs.service
import gdata.gauth
from gdata.client import RequestError

from c3po.conf import settings
from c3po.converters.po_list import po_to_list, list_to_po, _get_all_po_filenames

import gspread

LOCAL_ODS = 'local.ods'
GDOCS_TRANS_CSV = 'c3po_gdocs_trans.csv'
GDOCS_META_CSV = 'c3po_gdocs_meta.csv'
LOCAL_TRANS_CSV = 'c3po_local_trans.csv'
LOCAL_META_CSV = 'c3po_local_meta.csv'


class PODocsError(Exception):
    pass


class Communicator(object):
    """
    Client for communicating with GDocs. Providing log in on object
    creation and methods for synchronizing, uploading,
    downloading files and clearing GDoc.

    Needs to specify:
        locale_root, po_files_path
    For example in Django, where 'en' is language code:
        conf/locale/en/LC_MESSAGES/django.po
        conf/locale/en/LC_MESS AGES/custom.po
    locale_root='conf/locale/'
    po_files_path='LC_MESSAGES'
    """

    email = None
    password = None
    url = None
    source = None
    temp_path = None
    languages = None
    locale_root = None
    po_files_path = None
    header = None

    def __init__(self, email=None, password=None, url=None, source=None,
                 temp_path=None, languages=None, locale_root=None,
                 po_files_path=None, header=None):
        """
            Initialize object with all necessary client information and log in
        :param email: user gmail account address
        :param password: password to gmail account
        :param url: url to spreadsheet where translations are or will be placed
        :param temp_path: path where temporary files will be saved
        :param source: source information to show on web
        :param languages: list of languages
        :param locale_root: path to locale root folder containing directories
                            with languages
        :param po_files_path: path from lang directory to po file
        :param header: header which will be put on top of every po file when
                       downloading
        """
        construct_vars = ('email', 'password', 'url', 'source', 'temp_path',
                          'languages', 'locale_root', 'po_files_path', 'header')
        for cv in construct_vars:
            if locals().get(cv) is None:
                setattr(self, cv, getattr(settings, cv.upper()))
            else:
                setattr(self, cv, locals().get(cv))

        self.login()
        self._get_gdocs_key()
        self._ensure_temp_path_exists()

        self.sht = self.download_spreadsheet()
        self.trans = self.sht.get_worksheet(0)
        self.meta = self.sht.get_worksheet(1)

    def login(self):
        print 'starting logging...'
        client_id = '213287829843-ebhnnhb26rialaos1rl9jhjo50gc2lpo.apps.googleusercontent.com'
        client_secret = 'ddTqgfG4Z3kTKM3DH2Zz1kfQ'
        scope = 'https://spreadsheets.google.com/feeds/'
        user_agent = 'myself'
        self.token = gdata.gauth.OAuth2Token(client_id=client_id, client_secret=client_secret, scope=scope,
                                             user_agent=user_agent)
        token_url = self.token.generate_authorize_url(redirect_uri='urn:ietf:wg:oauth:2.0:oob', approval_prompt='auto',
                                                      response_type='code')
        import webbrowser
        webbrowser.open(token_url)  # automatically open browser
        code = raw_input("Code: ")  # reading the code
        print 'Your code: ', code
        self.token.get_access_token(code)
        print "Refresh token"
        print self.token.refresh_token
        print "Access Token"
        print self.token.access_token
        print '\n'

    def download_spreadsheet(self):
        gc = gspread.authorize(self.token)
        sht = gc.open_by_url(
            'https://docs.google.com/spreadsheets/d/1dZWnWcY9bswYocM64dPHaMWYVLLXO8-qEBAb1P8a6XE/edit#gid=0')
        return sht

    def get_the_right_size(self):
        trans_sheet = self.sht.get_worksheet(0)
        meta_sheet = self.sht.get_worksheet(1)
        po_files = _get_all_po_filenames(self.locale_root, self.languages[0], self.po_files_path)

        k = 0
        for po_file in po_files:
            po = polib.pofile(self.locale_root + "/" + self.languages[0] + "/" + self.po_files_path + "/" + po_file)
            for entry in po:
                k += 1

        if trans_sheet.row_count < k or meta_sheet.row_count < k:
            trans_sheet.resize(k + 1, trans_sheet.col_count)
            meta_sheet.resize(k + 1, trans_sheet.col_count)
            trans_sheet = self.sht.get_worksheet(0)
            meta_sheet = self.sht.get_worksheet(1)
        return trans_sheet, meta_sheet

    def prepare_upload(self):

        trans_sheet, meta_sheet = self.get_the_right_size()

        how_many = trans_sheet.row_count

        trans_comment = trans_sheet.range(chr(1 + 64) + str(1) + ":" + chr(1 + 64) + str(how_many))
        trans_comment[0].value = 'comment'

        to_translate = trans_sheet.range(chr(2 + 64) + str(1) + ":" + chr(2 + 64) + str(how_many))
        to_translate[0].value = 'to_translate'

        meta_file = meta_sheet.range(chr(1 + 64) + str(1) + ":" + chr(1 + 64) + str(how_many))
        meta_file[0].value = 'file'

        meta_data = meta_sheet.range(chr(2 + 64) + str(1) + ":" + chr(2 + 64) + str(how_many))
        meta_data[0].value = 'metadata'

        trans = []
        trans.append(trans_comment)
        trans.append(to_translate)

        meta = []
        meta.append(meta_file)
        meta.append(meta_data)

        for i, lang in enumerate(self.languages):
            col = trans_sheet.range(chr(1 + i + 64 + 2) + str(1) + ":" + chr(1 + i + 64 + 2) + str(how_many))
            col[0].value = lang
            trans.append(col)

        return trans, meta

    def upload(self):

        trans, meta = self.prepare_upload()

        trans, meta = po_to_list(trans, meta, self.languages, self.locale_root, self.po_files_path)
        trans_sheet = self.sht.get_worksheet(0)
        meta_sheet = self.sht.get_worksheet(1)
        for tra in trans:
            trans_sheet.update_cells(tra)
        for met in meta:
            meta_sheet.update_cells(met)

    def num_to_alphanum(self, column, row):
        return chr(column + 64) + str(row)

    def clear(self):
        no = 0
        how_many_trans = self.trans.row_count
        how_many_meta = self.meta.row_count
        for col in range(self.trans.col_count):
            no += 1
            trans_column = self.trans.range(
                self.num_to_alphanum(no, 1) + ":" + self.num_to_alphanum(no, how_many_trans))
            meta_column = self.meta.range(self.num_to_alphanum(no, 1) + ":" + self.num_to_alphanum(no, how_many_meta))
            for cell in trans_column:
                cell.value = ""
            for cell in meta_column:
                cell.value = ""
            self.trans.update_cells(trans_column)
            self.meta.update_cells(meta_column)

    def download(self):
        self.sht = self.download_spreadsheet()
        trans = self.sht.get_worksheet(0)
        meta = self.sht.get_worksheet(1)

        trans_list = []
        for i in range(len(self.languages) + 2):  # +1(comment) + 1(to_translate))
            trans_list.append(
                trans.range(self.num_to_alphanum(i + 1, 1) + ":" + self.num_to_alphanum(i + 1, trans.row_count)))

        meta_list = []
        meta_list.append(meta.range("A1:A" + str(meta.row_count)))
        meta_list.append(meta.range("B1:B" + str(meta.row_count)))

        list_to_po(trans_list, meta_list, self.locale_root, self.po_files_path, self.languages,
                   header='# translated with c3po\n')


    def _ensure_temp_path_exists(self):
        """
        Make sure temp directory exists and create one if it does not.
        """
        try:
            if not os.path.exists(self.temp_path):
                os.mkdir(self.temp_path)
        except OSError as e:
            raise PODocsError(e)

    def _clear_temp(self):
        """
        Clear temp directory from created csv and ods files during
        communicator operations.
        """
        temp_files = [LOCAL_ODS, GDOCS_TRANS_CSV, GDOCS_META_CSV,
                      LOCAL_TRANS_CSV, LOCAL_META_CSV]
        for temp_file in temp_files:
            file_path = os.path.join(self.temp_path, temp_file)
            if os.path.exists(file_path):
                os.remove(file_path)

    def _merge_local_and_gdoc(self, entry, local_trans_csv,
                              local_meta_csv, gdocs_trans_csv, gdocs_meta_csv):
        """
        Download csv from GDoc.
        :return: returns resource if worksheets are present
        :except: raises PODocsError with info if communication with GDocs
                 lead to any errors
        """
        try:
            new_translations = po_to_csv_merge(
                self.languages, self.locale_root, self.po_files_path,
                local_trans_csv, local_meta_csv,
                gdocs_trans_csv, gdocs_meta_csv)
            if new_translations:
                local_ods = os.path.join(self.temp_path, LOCAL_ODS)
                csv_to_ods(local_trans_csv, local_meta_csv, local_ods)
                media = gdata.data.MediaSource(
                    file_path=local_ods, content_type=
                    'application/x-vnd.oasis.opendocument.spreadsheet'
                )
                self.gd_client.UpdateResource(entry, media=media,
                                              update_metadata=True)
        except (IOError, OSError, RequestError) as e:
            raise PODocsError(e)

    def synchronize(self):
        """
        Synchronize local po files with translations on GDocs Spreadsheet.
        Downloads two csv files, merges them and converts into po files
        structure. If new msgids appeared in po files, this method creates
        new ods with appended content and sends it to GDocs.
        """
        gdocs_trans_csv = os.path.join(self.temp_path, GDOCS_TRANS_CSV)
        gdocs_meta_csv = os.path.join(self.temp_path, GDOCS_META_CSV)
        local_trans_csv = os.path.join(self.temp_path, LOCAL_TRANS_CSV)
        local_meta_csv = os.path.join(self.temp_path, LOCAL_META_CSV)

        try:
            entry = self._download_csv_from_gdocs(gdocs_trans_csv,
                                                  gdocs_meta_csv)
        except PODocsError as e:
            if 'Sheet 1 not found' in str(e) \
                    or 'Conversion failed unexpectedly' in str(e):
                self.upload()
            else:
                raise PODocsError(e)
        else:
            self._merge_local_and_gdoc(entry, local_trans_csv, local_meta_csv,
                                       gdocs_trans_csv, gdocs_meta_csv)

            try:
                csv_to_po(local_trans_csv, local_meta_csv,
                          self.locale_root, self.po_files_path, self.header)
            except IOError as e:
                raise PODocsError(e)

        self._clear_temp()


def git_push(git_message=None, git_repository=None, git_branch=None,
             locale_root=None):
    """
    Pushes specified directory to git remote
    :param git_message: commit message
    :param git_repository: repository address
    :param git_branch: git branch
    :param locale_root: path to locale root folder containing directories
                        with languages
    :return: tuple stdout, stderr of completed command
    """
    if git_message is None:
        git_message = settings.GIT_MESSAGE
    if git_repository is None:
        git_repository = settings.GIT_REPOSITORY
    if git_branch is None:
        git_branch = settings.GIT_BRANCH
    if locale_root is None:
        locale_root = settings.LOCALE_ROOT

    try:
        subprocess.check_call(['git', 'checkout', git_branch])
    except subprocess.CalledProcessError:
        try:
            subprocess.check_call(['git', 'checkout', '-b', git_branch])
        except subprocess.CalledProcessError as e:
            raise PODocsError(e)

    try:
        subprocess.check_call(['git', 'ls-remote', git_repository])
    except subprocess.CalledProcessError:
        try:
            subprocess.check_call(['git', 'remote', 'add', 'po_translator',
                                   git_repository])
        except subprocess.CalledProcessError as e:
            raise PODocsError(e)

    commands = 'git add ' + locale_root + \
               ' && git commit -m "' + git_message + '"' + \
               ' && git push po_translator ' + git_branch + ':' + git_branch
    proc = Popen(commands, shell=True, stdout=PIPE, stderr=PIPE)
    stdout, stderr = proc.communicate()

    return stdout, stderr


def git_checkout(git_branch=None, locale_root=None):
    """
    Checkouts branch to last commit
    :param git_branch: branch to checkout
    :param locale_root: locale folder path
    :return: tuple stdout, stderr of completed command
    """
    if git_branch is None:
        git_branch = settings.GIT_BRANCH
    if locale_root is None:
        locale_root = settings.LOCALE_ROOT

    proc = Popen('git checkout ' + git_branch + ' -- ' + locale_root,
                 shell=True, stdout=PIPE, stderr=PIPE)
    stdout, stderr = proc.communicate()

    return stdout, stderr
