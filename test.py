from time import time as t
import constants
from record import Record, UnimarcRecord
import exc



class Reader(object):
    def __init__(self, record_cls, source, raw_encoding='utf-8'):
        """
        record_cls - record class
        source - file or StringIO
        raw_encoding - encoding of raw records
        """
        self.__record_cls = record_cls
        self.__source = source
        self.__raw_encoding = raw_encoding
        self.__index = []
        self.__indexed = False
        self.__next = -1

    def __len__(self):
        if not self.__indexed:
            self.__index_source()
        return len(self.__index)

    def __index_source(self):
        offset = 0
        while True:
            first5 = source.read(5)

            if not first5:
                break
            if len(first5) < 5:
                raise exc.RecordLengthInvalid

            length = int(first5)
            self.__index.append((offset, length))
            offset += length
            source.seek(offset)

        self.__indexed = True

    def next(self):
        self.__next +=1
        return self[self.__next]


    def __getitem__(self, item):
        if not self.__indexed:
            self.__index_source()
        offset, length = self.__index[item]
        source.seek(offset)
        chunk = source.read(length)
        return  self.__record_cls(chunk, self.__raw_encoding)

#source = open('/home/sergey/PycharmProjects/pymarc2/tmp/ruslan22.mrc', 'r')
source = open('tmp/rusmarc_ebsco.mrc', 'r')
out = open('tmp/rusmarc_ebsco_out.mrc', 'w')
s = t()

reader = Reader(UnimarcRecord, source, raw_encoding='utf-8')
for record in reader:
    out.write(UnimarcRecord(record.as_marc()).as_marc())


print 'time:', t() - s

