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

import datetime
import hashlib
import re
import io
from sqlalchemy import create_engine, Table, MetaData
from xml.sax import ContentHandler, parse

CCSplitRX = re.compile("([A-Z][a-z]+)")

def attrToColumnName(attr):
	global CamelCaseSplitRegex
	return "_".join(filter(lambda x: len(x) > 0, CCSplitRX.split(attr))).lower()

class StackExchangeMySQLHandler(ContentHandler):
	
	def __init__(self, dburi, batchSize=100):
		self.dbengine = create_engine(dburi, pool_recycle=7200)
		self.meta = MetaData()
		self.meta.bind = self.dbengine
		self.table = None
		self.batchSize = batchSize
		self.data = {}
		self.firstElement = False
		self.tableName = ""
		self.rowCount = 0

	def startElement(self, name, attrs):
		if name == "row":
			model = {}
			keys = []
			for attr in attrs.getNames():
				model[attrToColumnName(attr)] = unicode(attrs.getValue(attr))
				keys.append(attr)
			keys = hashlib.md5("".join(keys)).hexdigest()
			self.rowCount += 1
			if not keys in self.data:
				self.data[keys] = [model]
			else:
				self.data[keys].append(model)
				if len(self.data[keys]) >= self.batchSize:
					self.commit(self.data[keys])
					del self.data[keys]
		else:
			if not self.firstElement:
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
		self.table = Table(table_name, self.meta, autoload=True)

class PatternReplacementStream(file):

	def __init__(self, *args, **kwargs):
		super(PatternReplacementStream, self).__init__(*args, **kwargs)
		self._pattern = re.compile("$^")
		
	@property
	def pattern(self):
		return self._pattern

	@pattern.setter
	def pattern(self, pattern):
		if type(pattern) is str:
			self._pattern = re.compile(pattern)
		else: self._pattern = pattern

	def read(self, *args, **kwargs):
		return self.pattern.sub("", super(PatternReplacementStream, self).read(*args, **kwargs))
	
	def readline(self, *args, **kwargs):
		return self.pattern.sub("", super(PatternReplacementStream, self).readline(*args, **kwargs))

if __name__ == "__main__":
	import sys
	
	if len(sys.argv) < 3:
		print >> sys.stderr, "Usage:\t%s <xmlfile> <dburi>" % sys.argv[0]
	else:
		f = PatternReplacementStream(sys.argv[1], "r")
		f.pattern = "&#x([0-8B-Cb-cEe]|1[0-9A-Fa-f]|[dD][89][0-9A-Fa-f]{2}|[fF]{3}[EF]);"
		sexchange_parser = StackExchangeMySQLHandler(sys.argv[2])
		print "Parsing %s ..." % sys.argv[1] ,
		sys.stdout.flush()
		start_time = datetime.datetime.now()
		parse(f, sexchange_parser)
		end_time = datetime.datetime.now()
		print "Done.\nStored %d rows in %f seconds." % (sexchange_parser.rowCount, (end_time - start_time).total_seconds())
		f.close()
