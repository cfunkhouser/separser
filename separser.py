#!/usr/bin/python
import hashlib
import re
from sqlalchemy import create_engine, Table, Column, Integer, String, MetaData, ForeignKey
from sqlalchemy.exc import IntegrityError, OperationalError
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

	def startElement(self, name, attrs):
		if name == "row":
			model = {}
			keys = []
			for attr in attrs.getNames():
				model[attrToColumnName(attr)] = unicode(attrs.getValue(attr))
				keys.append(attr)
			keys = hashlib.md5("".join(keys)).hexdigest()
			if not keys in self.data:
				self.data[keys] = [model]
				print "Key \"%s\" added" % keys
			else:
				self.data[keys].append(model)
				if len(self.data[keys]) >= self.batchSize:
					self.commit(self.data[keys])
					print "Key \"%s\" committed and removed." % keys
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
				print "Flushing %d entries for key \"%s\"" % (len(self.data[key]), key)
				self.commit(self.data[key])
		
	def initTable(self, table_name):
		self.table = Table(table_name, self.meta, autoload=True)

class ErrorFinderHandler(ContentHandler):

	def __init__(self):
		self.rowCount = 0

	def startElement(self, name, attrs):
		if name == "row": self.rowCount += 1

if __name__ == "__main__":
	import sys
	
	if len(sys.argv) < 3:
		print >> sys.stderr, "Usage:\t%s <xmlfile> <dburi>" % sys.argv[0]
	else:
		f = open(sys.argv[1], "r")
		sexchange_parser = ErrorFinderHandler() #StackExchangeMySQLHandler(sys.argv[2])
		parse(f, sexchange_parser)
		f.close()
