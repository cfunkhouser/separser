#!/usr/bin/python
#
# The GNU General Public License 3.0
#
# separser.py - Nov. 14, 2012 - Parse Stack Exchange data to various formats.
#
# Copyright (C) 2012 Christian Funkhouser
#
# This program is free software: you can redistribute it and/or modify
# it under the terms of the GNU General Public License as published by
# the Free Software Foundation, either version 3 of the License, or
# (at your option) any later version.
#
# This program is distributed in the hope that it will be useful,
# but WITHOUT ANY WARRANTY; without even the implied warranty of
# MERCHANTABILITY or FITNESS FOR A PARTICULAR PURPOSE.  See the
# GNU General Public License for more details.
#
# You should have received a copy of the GNU General Public License
# along with this program.  If not, see <http://www.gnu.org/licenses/>.

__author__ = 'christian.funkhouser@gmail.com (Christian Funkhouser)'

"""An importer to MySQL of Stack Exchange XML data files.

At the time of this writing, the creative-commons licensed dumps are found at:
http://blog.stackexchange.com/category/cc-wiki-dump/
"""

import datetime
import hashlib
import io
import logging
import re
import sys

from xml import sax

try:
  import sqlalchemy
except:
  logging.error('SQLAlchemy could not be found. Is it installed?')

CC_SPLIT_RX = re.compile('([A-Z][a-z]+)')
PARSE_PATTERN = (
    '&#x([0-8B-Cb-cEe]|1[0-9A-Fa-f]|[dD][89][0-9A-Fa-f]{2}|[fF]{3}[EF]);')


def _AttrToColumnName(attr):
  return '_'.join(filter(lambda x: len(x) > 0, CC_SPLIT_RX.split(attr))).lower()


class StackExchangeMySQLHandler(sax.ContentHandler):
  """An XML SAX parser which populates a database from a Stack Exchange dump."""

  def __init__(self, db_uri, batch_size=100):
    """Create a StackExchangeMySQLHandler.

    Args:
      db_uri: (str) A URI identifying the target database.
      batch_size: (str) Number of entries to buffer in memory before batch
          inserting into the database.
    """
    self.dbengine = sqlalchemy.create_engine(db_uri, pool_recycle=7200)
    self.meta = sqlalchemy.MetaData()
    self.meta.bind = self.dbengine
    self.table = None
    self.batch_size = batch_size
    self.data = {}
    self.firstElement = False
    self.tableName = ''
    self.rowCount = 0

  def startElement(self, name, attrs):
    if name == 'row':
      model = {}
      keys = []
      for attr in attrs.getNames():
        model[_AttrToColumnName(attr)] = unicode(attrs.getValue(attr))
        keys.append(attr)
      keys = hashlib.md5(''.join(keys)).hexdigest()
      self.rowCount += 1
      if not keys in self.data:
        self.data[keys] = [model]
      else:
        self.data[keys].append(model)
        if len(self.data[keys]) >= self.batch_size:
          self.commit(self.data[keys])
          del self.data[keys]
    elif not self.firstElement:
        self.initTable(name)
        self.firstElement = True
        self.tableName = name

  def commit(self, data):
    ins = self.table.insert()
    self.dbengine.connect().execute(ins, data)

  def endElement(self, name):
    if name == self.tableName:
      for key in self.data:
        self.commit(self.data[key])

  def initTable(self, table_name):
    self.table = sqlalchemy.Table(table_name, self.meta, autoload=True)

class PatternReplacementStream(file):
  """File object Wrapper which removes a pattern from a file during read.

  Only works with text data. Behavior is undefined on binary data.
  """

  def __init__(self, *args, **kwargs):
    super(PatternReplacementStream, self).__init__(*args, **kwargs)
    self._pattern = re.compile('$^')

  @property
  def pattern(self):
    return self._pattern

  @pattern.setter
  def pattern(self, pattern):
    if type(pattern) is str:
      self._pattern = re.compile(pattern)
    else: self._pattern = pattern

  def read(self, *args, **kwargs):
    return self.pattern.sub(
        '', super(PatternReplacementStream, self).read(*args, **kwargs))

  def readline(self, *args, **kwargs):
    return self.pattern.sub(
        '', super(PatternReplacementStream, self).readline(*args, **kwargs))


def ParseStackExchangeFile(xml_file_path, db_uri):
  """Parse the provided XML file into the Database.

  Args:
    xml_file_path: (str) Path to the XML file containing the SE data.
    db_uri: (str) The URI for the target database.
  """
  pattern_stream = PatternReplacementStream(xml_file_path, 'r')
  pattern_stream.pattern = PARSE_PATTERN

  sexchange_parser = StackExchangeMySQLHandler(db_uri)
  logging.info('Parsing %s', xml_file_path)
  start_time = datetime.datetime.now()

  # Parse the xml file
  sax.parse(pattern_stream, sexchange_parser)

  end_time = datetime.datetime.now()
  logging.info(
    'Stored %d rows in %f seconds.',
    (sexchange_parser.rowCount, (end_time - start_time).total_seconds()))
  pattern_stream.close()


if __name__ == '__main__':
  if len(sys.argv) < 3:
    print >> sys.stderr, 'Usage:\t%s <xmlfile> <dburi>' % sys.argv[0]
    sys.exit(1)
  ParseStackExchangeFile(sys.argv[1], sys.argv[2])
