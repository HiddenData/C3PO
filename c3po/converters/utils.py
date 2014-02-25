#!/usr/bin/env python
# -*- coding: utf-8 -*-

import codecs
import cStringIO
import csv


class UTF8Recoder(object):
    """
    Iterator that reads an encoded stream and reencodes the input to UTF-8
    """
    def __init__(self, fd, encoding):
        self.reader = codecs.getreader(encoding)(fd)

    def __iter__(self):
        return self

    def next(self):
        return self.reader.next().encode("utf-8")


class UnicodeReader(object):
    """
    A CSV reader which will iterate over lines in the CSV file "f",
    which is encoded in the given encoding.
    """

    def __init__(self, file_path, dialect=csv.excel,
                 encoding="utf-8", **kwargs):
        self.file = open(file_path, 'rb')
        recorder = UTF8Recoder(self.file, encoding)
        self.reader = csv.reader(recorder, dialect=dialect, **kwargs)

    def next(self):
        row = self.reader.next()
        return [unicode(s, "utf-8") for s in row]

    def __iter__(self):
        return self

    def close(self):
        self.file.close()


class UnicodeWriter(object):
    """
    A CSV writer which will write rows to CSV file "f",
    which is encoded in the given encoding.
    """

    def __init__(self, file_path, dialect=csv.excel,
                 encoding="utf-8", **kwargs):
        # Redirect output to a queue
        self.queue = cStringIO.StringIO()
        self.writer = csv.writer(self.queue, dialect=dialect, **kwargs)
        self.stream = open(file_path, 'wb')
        self.encoder = codecs.getincrementalencoder(encoding)()

    def writerow(self, row):
        self.writer.writerow([s.encode("utf-8") for s in row])
        # Fetch UTF-8 output from the queue ...
        data = self.queue.getvalue()
        data = data.decode("utf-8")
        # ... and reencode it into the target encoding
        data = self.encoder.encode(data)
        # write to the target stream
        self.stream.write(data)
        # empty queue
        self.queue.truncate(0)

    def writerows(self, rows):
        for row in rows:
            self.writerow(row)

    def close(self):
        self.stream.close()


def get_filename_from_context(context):
    return 'editor.po' if 'editor' in context else 'django.po'


def get_context_from_filename(po_filename, entry):
    if 'editor' in po_filename:
        context = 'editor'
    else:
        for occurrence, line in entry.occurrences:
            if 'dashboard' not in occurrence:
                context = 'e-commerce'
                break
        else:
            context = 'dashboard'
    return context
