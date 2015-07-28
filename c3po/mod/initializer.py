__author__ = 'frank'

import argparse
import sys

from c3po.conf import settings
from c3po.mod import communicator


def start():
    parser = argparse.ArgumentParser(description='Please enter arguments')

    group = parser.add_mutually_exclusive_group()

    group.add_argument('-download', help='Downloads GDoc and converts to .po files', action='store_true')
    group.add_argument('-upload', help='Converts .po files and uploads it to GDoc', action='store_true')
    group.add_argument('-clear', help='Clears the GDoc', action='store_true')

    parser.add_argument('-e', '--email', help='GoogleDocs email address', metavar='')
    parser.add_argument('-p', '--password', help='GoogleDocs password', metavar='')
    parser.add_argument('-u', '--url', help='Spreadsheet URL', metavar='')
    parser.add_argument('-l', '--locale', help='Locale directory to path', metavar='')
    parser.add_argument('-P', '--po_path', help='Path from concrete lang dir to .po file', metavar='')
    parser.add_argument('-a', '--auto', help='Translating automatically with GoogleTranslate', metavar='')
    parser.add_argument('-d', '--default', help='Default language', metavar='')

    args = parser.parse_args()

    parser.print_help()

    return parser


def manage_options(parser, com):
    args = parser.parse_args()
    if args.email:
        settings.EMAIL = args.email
    if args.password:
        settings.PASSWORD = args.password
    if args.url:
        settings.URL = args.url
    if args.locale:
        settings.LOCALE_ROOT = args.locale
    if args.po_path:
        settings.PO_FILES_PATH = args.po_path
    if args.auto:
        settings.AUTO_TRANSLATE = True
    if args.default:
        settings.DEFAULT_LANGUAGE = args.default
    if args.download:
        com.download()
    if args.upload:
        com.upload()
    if args.clear:
        com.clear()

def initialize():
    parser = start()

    if len(sys.argv) == 1:
        sys.exit()

    com = communicator.Communicator()

    manage_options(parser, com)
