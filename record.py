# encoding: utf-8
from array import array
import exc
from marc8 import marc8_to_unicode
from field import ControlField, DataField, Subfield, LinkedSubfield
from constants import LEADER_LEN, DIRECTORY_ENTRY_LEN, SUBFIELD_INDICATOR, END_OF_FIELD, END_OF_RECORD

class Record(object):
    def __init__(self, raw='', raw_encoding='utf-8'):
        self._leader = array('c', '          22        4500')
        self._fields = {}
        self.raw = raw
        self.raw_encoding = raw_encoding

    def __getitem__(self, item):
        return self.fields[item]

    def _load(self):
        """
        for lazy load
        """
        if self.raw:
            self.decode(self.raw, self.raw_encoding)
            self.raw = None

    @property
    def leader(self):
        self._load()
        return self._leader


    @leader.setter
    def leader(self, value):
        self._leader = value


    @property
    def fields(self):
        self._load()
        return self._fields


    @fields.setter
    def fields(self, value):
        self._fields = value


    def to_dict(self):
        record_dict = {
            'leader': self.leader.tostring(),
            'controlfields': {},
            'datafields': {}
        }
        for key in sorted(self.fields.iterkeys()):
            for field in self._fields[key]:
                if isinstance(field, ControlField):
                    if field.tag not in record_dict['controlfields']:
                        record_dict['controlfields'][field.tag] = []
                    record_dict['controlfields'][field.tag].append(field.to_dict())
                else:
                    if field.tag not in record_dict['datafields']:
                        record_dict['datafields'][field.tag] = []
                    record_dict['datafields'][field.tag].append(field.to_dict())
        return record_dict


    def decode(self, raw, raw_encoding):
        """
        decode_marc() accepts a MARC record in transmission format as a
        a string argument, and will populate the object based on the data
        found. The Record constructor actually uses decode_marc() behind
        the scenes when you pass in a chunk of MARC data to it.

        """
        # extract record leader
        self._leader = array('c', raw[0:LEADER_LEN])
        if len(self._leader) != LEADER_LEN:
            raise exc.RecordLeaderInvalid

        # extract the byte offset where the record data starts
        base_address = int(raw[12:17])
        if base_address <= 0:
            raise exc.BaseAddressNotFound
        if base_address >= len(raw):
            raise exc.BaseAddressInvalid

        # extract directory, base_address-1 is used since the
        # director ends with an END_OF_FIELD byte
        directory = raw[LEADER_LEN:base_address - 1]

        # determine the number of fields in record
        if len(directory) % DIRECTORY_ENTRY_LEN != 0:
            raise exc.RecordDirectoryInvalid
        field_total = len(directory) / DIRECTORY_ENTRY_LEN

        # add fields to our record using directory offsets
        field_count = 0
        while field_count < field_total:
            entry_start = field_count * DIRECTORY_ENTRY_LEN
            entry_end = entry_start + DIRECTORY_ENTRY_LEN
            entry = directory[entry_start:entry_end]
            entry_tag = entry[0:3]
            entry_length = int(entry[3:7])
            entry_offset = int(entry[7:12])
            entry_data = raw[base_address + entry_offset:
            base_address + entry_offset + entry_length - 1]

            # assume controlfields are numeric; replicates ruby-marc behavior
            if entry_tag < '010' and entry_tag.isdigit():
                if raw_encoding == 'marc8':
                    data = marc8_to_unicode(entry_data)
                else:
                    data = entry_data.decode(raw_encoding)
                field = ControlField(tag=entry_tag, data=data)
            else:
                subfields = []
                subs = entry_data.split(SUBFIELD_INDICATOR)
                ind1 = subs[0][0]
                ind2 = subs[0][1]
                for subfield in subs[1:]:
                    if len(subfield) == 0:
                        continue
                    code = subfield[0]
                    data = subfield[1:]

                    if raw_encoding == 'marc8':
                        data = marc8_to_unicode(data)
                    else:
                        data = data.decode(raw_encoding)

                    subfields.append(Subfield(code=code, data=data))

                field = DataField(
                    tag=entry_tag,
                    ind1=ind1,
                    ind2=ind2,
                    subfields=subfields,
                )
            if field.tag not in self._fields:
                self._fields[field.tag] = []

            self._fields[field.tag].append(field)
            field_count += 1

        if field_count == 0:
            raise exc.NoFieldsFound

    def as_marc(self, to_encoding='utf-8'):
        """
        returns the record serialized as MARC21
        """
        self._load()

        fields = []
        directory = []
        offset = 0
        to_encoding = to_encoding.lower()
        if to_encoding == 'utf-8' or to_encoding == 'utf8':
            self._leader[9] = 'a'
            # build the directory
        # each element of the directory includes the tag, the byte length of
        # the field and the offset from the base address where the field data
        # can be found
        for key in sorted(self._fields.iterkeys()):
            for field in self._fields[key]:
                field_data = field.as_marc(to_encoding)
                fields.append(field_data)
                directory.append('%03d' % int(field.tag))
                directory.append('%04d%05d' % (len(field_data), offset))
                offset += len(field_data)


        # directory ends with an end of field
        directory.append(END_OF_FIELD)

        # field data ends with an end of record
        fields.append(END_OF_RECORD)

        # the base address where the directory ends and the field data begins
        directory = ''.join(directory)
        base_address = LEADER_LEN + len(directory)

        # figure out the length of the record
        fields = ''.join(fields)
        record_length = base_address + len(fields)

        # update the leader with the current record length and base address
        # the lengths are fixed width and zero padded
        self._leader = array('c', '%05d%s%05d%s' %\
                                 (record_length, self.leader[5:12].tostring(), base_address,
                                  self.leader[17:].tostring()))

        # return the encoded record
        return self._leader.tostring() + directory + fields

    def __unicode__(self):
        self._load()
        lines = [self._leader.tostring().replace(' ', '#')]
        for key in sorted(self._fields.iterkeys()):
            for field in self._fields[key]:
                lines.append(unicode(field))
        return u'\n'.join(lines)

    def __str__(self):
        return unicode(self).encode('utf-8')


class UnimarcRecord(Record):
    def __init__(self, raw='', raw_encoding='utf-8'):
        super(UnimarcRecord, self).__init__(raw, raw_encoding)

    def __unicode__(self):
        self._load()
        lines = [self._leader.tostring().replace(' ', '#')]
        for key in sorted(self._fields.iterkeys()):
            for field in self._fields[key]:
                lines.append(unicode(field))
        return u'\n'.join(lines)

    def __str__(self):
        return unicode(self).encode('utf-8')


    def decode(self, raw, raw_encoding):
        """
        decode_marc() accepts a MARC record in transmission format as a
        a string argument, and will populate the object based on the data
        found. The Record constructor actually uses decode_marc() behind
        the scenes when you pass in a chunk of MARC data to it.

        """
        # extract record leader
        self._leader = array('c', raw[0:LEADER_LEN])
        if len(self._leader) != LEADER_LEN:
            raise exc.RecordLeaderInvalid

        # extract the byte offset where the record data starts
        base_address = int(raw[12:17])
        if base_address <= 0:
            raise exc.BaseAddressNotFound
        if base_address >= len(raw):
            raise exc.BaseAddressInvalid

        # extract directory, base_address-1 is used since the
        # director ends with an END_OF_FIELD byte
        directory = raw[LEADER_LEN:base_address - 1]

        # determine the number of fields in record
        if len(directory) % DIRECTORY_ENTRY_LEN != 0:
            raise exc.RecordDirectoryInvalid
        field_total = len(directory) / DIRECTORY_ENTRY_LEN

        # add fields to our record using directory offsets
        field_count = 0
        while field_count < field_total:
            entry_start = field_count * DIRECTORY_ENTRY_LEN
            entry_end = entry_start + DIRECTORY_ENTRY_LEN
            entry = directory[entry_start:entry_end]
            entry_tag = entry[0:3]
            entry_length = int(entry[3:7])
            entry_offset = int(entry[7:12])
            entry_data = raw[base_address + entry_offset:
            base_address + entry_offset + entry_length - 1]

            # assume controlfields are numeric; replicates ruby-marc behavior
            if entry_tag < '010' and entry_tag.isdigit():
                if raw_encoding == 'marc8':
                    data = marc8_to_unicode(entry_data)
                else:
                    data = entry_data.decode(raw_encoding)
                field = ControlField(tag=entry_tag, data=data)
            else:
                subfields = []
                subs = entry_data.split(SUBFIELD_INDICATOR)
                ind1 = subs[0][0]
                ind2 = subs[0][1]

                #########################################################################
                if entry_tag > '399' and entry_tag < '500':
                    linked_subfield = None
                    start_linked_parse = False # flag of begining linked subfield parse
                    for subfield in subs[1:]:
                        code = subfield[0]
                        data = subfield[1:]
                        if code == '1':
                            start_linked_parse = True # begin parse linked subfield
                            if linked_subfield:
                                subfields.append(linked_subfield)

                            linked_subfield = LinkedSubfield(code=code)
                            linked_field_tag = data[0:3]
                            if linked_field_tag < '010':
                                if raw_encoding == 'marc8':
                                    data = marc8_to_unicode(data)
                                else:
                                    data = data.decode(raw_encoding)
                                linked_subfield.field = ControlField(linked_field_tag, data.decode(raw_encoding))
                            else:
                                linked_subfield.field = DataField(tag=linked_field_tag, ind1=data[3], ind2=data[4])

                        elif start_linked_parse: # if now parse linked subfield
                            if raw_encoding == 'marc8':
                                data = marc8_to_unicode(data)
                            else:
                                data = data.decode(raw_encoding)
                            linked_subfield.field.add_subfield(Subfield(code, data))
                        else: # if field with 4.. code but not have "1" linked subfield
                            if raw_encoding == 'marc8':
                                data = marc8_to_unicode(data)
                            else:
                                try:
                                    data = data.decode(raw_encoding)
                                except UnicodeDecodeError:
                                    data = u"Can't decode field data"
                            subfields.append(Subfield(code=code, data=data))

                    if start_linked_parse:
                        subfields.append(linked_subfield)
                        start_linked_parse = False # now set flag that linked field stop parse
                ##########################################################################
                else:
                    for subfield in subs[1:]:
                        if len(subfield) == 0:
                            continue
                        code = subfield[0]
                        data = subfield[1:]

                        if raw_encoding == 'marc8':
                            data = marc8_to_unicode(data)
                        else:
                            try:
                                data = data.decode(raw_encoding)
                            except UnicodeDecodeError:
                                data = u"Can't decode field data"
                        subfields.append(Subfield(code=code, data=data))

                field = DataField(
                    tag=entry_tag,
                    ind1=ind1,
                    ind2=ind2,
                    subfields=subfields,
                )
            if field.tag not in self._fields:
                self._fields[field.tag] = []

            self._fields[field.tag].append(field)
            field_count += 1

        if field_count == 0:
            raise exc.NoFieldsFound
