from time import time as t
from record import Record, UnimarcRecord
from reader import Reader
from marcxml import record_to_xml
#source = open('/home/sergey/PycharmProjects/pymarc2/tmp/ruslan22.mrc', 'r')
source = open('/home/sergey/PycharmProjects/pymarc2/tmp/wrong.mrc', 'r')
#source = open('/home/sergey/projects/PycharmProjects/ermapp/appdata/rusmarc_ebsco.mrc', 'r')
#out = open('tmp/rusmarc_ebsco_out.mrc', 'w')
s = t()
import pprint
pp = pprint.PrettyPrinter(indent=4)
reader = Reader(UnimarcRecord, source, raw_encoding='utf-8')
for record in reader:
    print record
    #record_to_xml(record)
    #print pp.pprint(record.to_dict())
    #out.write(UnimarcRecord(record.as_marc()).as_marc())


print 'time:', t() - s

