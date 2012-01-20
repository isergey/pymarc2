# encoding: utf-8
from lxml import etree as ET

from record import Record, UnimarcRecord
from field import ControlField, LinkedSubfield

XSI_NS = "http://www.w3.org/2001/XMLSchema-instance"
MARC_XML_NS = "http://www.loc.gov/MARC21/slim"
MARC_XML_SCHEMA = "http://www.loc.gov/MARC21/slim http://www.loc.gov/standards/marcxml/schema/MARC21slim.xsd"



def record_to_marc_xml(record, namespace=False):
    """
    To Marc21slim
    """
    root = ET.Element('record')
    if namespace:
        root.set('xmlns', MARC_XML_NS)
        root.set('xmlns:xsi', XSI_NS)
        root.set('xsi:schemaLocation', MARC_XML_SCHEMA)

    leader = ET.SubElement(root, 'leader')
    leader.text = record.leader.tostring()

    for key in sorted(record.fields.iterkeys()):
        for field in record.fields[key]:
            if isinstance(field, ControlField):
                control_field = ET.SubElement(root, 'controlfield')
                control_field.set('tag', field.tag)
                control_field.text = field.data
            else:
                data_field = ET.SubElement(root, 'datafield')
                data_field.set('tag', field.tag)
                data_field.set('ind1', field.ind1)
                data_field.set('ind2', field.ind2)
                for sf_key in sorted(field.subfields.iterkeys()):
                    for subfield in field.subfields[sf_key]:
                        data_subfield = ET.SubElement(data_field, 'subfield')
                        data_subfield.set('code', subfield.code)
                        data_subfield.text = subfield.data

    return root






UNIMARC_XSI_NS = "http://www.w3.org/2001/XMLSchema"
UNIMARC_MARC_XML_NS = "http://www.loc.gov/MARC21/slim"
UNIMARC_MARC_XML_SCHEMA = "http://www.rusmarc.ru/shema/UNISlim.xsd"





def record_to_unimarc_xml(record, namespace=False):
    """
    To UNISlim
    """
    root = ET.Element('record')
    if namespace:
        root.set('xmlns', UNIMARC_MARC_XML_NS)
        root.set('xmlns:xsi', UNIMARC_XSI_NS)
        root.set('xsi:schemaLocation', UNIMARC_MARC_XML_SCHEMA)

    leader = ET.SubElement(root, 'leader')
    leader.text = record.leader.tostring()

    for key in sorted(record.fields.iterkeys()):
        for field in record.fields[key]:
            if isinstance(field, ControlField):
                control_field = ET.SubElement(root, 'controlfield')
                control_field.set('tag', field.tag)
                control_field.text = field.data
            else:
                data_field = ET.SubElement(root, 'datafield')
                data_field.set('tag', field.tag)
                data_field.set('ind1', field.ind1)
                data_field.set('ind2', field.ind2)
                for sf_key in sorted(field.subfields.iterkeys()):
                    for subfield in field.subfields[sf_key]:
                        if isinstance(subfield, LinkedSubfield):
                            linked_subfield = ET.SubElement(data_field, 's1')
                            if  isinstance(subfield.field, ControlField):
                                linked_control_field = ET.SubElement(linked_subfield, 'controlfield')
                                linked_control_field.set('tag', subfield.field.tag)
                                linked_control_field.text = subfield.field.data
                            else:
                                linked_data_field = ET.SubElement(linked_subfield, 'datafield')
                                linked_data_field.set('tag', subfield.field.tag)
                                linked_data_field.set('ind1', subfield.field.ind1)
                                linked_data_field.set('ind2', subfield.field.ind2)

                                # глубже! еще глубже!
                                for sf_key in sorted(subfield.field.subfields.iterkeys()):
                                    for lsubfield in subfield.field.subfields[sf_key]:
                                        linkeddata_subfield = ET.SubElement(linked_data_field, 'subfield')
                                        linkeddata_subfield.set('code', lsubfield.code)
                                        linkeddata_subfield.text = lsubfield.data

                        else:
                            data_subfield = ET.SubElement(data_field, 'subfield')
                            data_subfield.set('code', subfield.code)
                            data_subfield.text = subfield.data

    return root





def record_to_rustam_xml(record, syntax='1.2.840.10003.5.28', namespace=False):
    """
    default syntax rusmarc
    """
    string_leader = record.leader.tostring()

    root = ET.Element('record')
    root.set('syntax', syntax)
    leader = ET.SubElement(root, 'leader')



    length = ET.SubElement(leader, 'length')
    length.text = string_leader[0:5]

    status = ET.SubElement(leader, 'status')
    status.text = string_leader[5]

    type = ET.SubElement(leader, 'status')
    type.text = string_leader[6]

    leader07 = ET.SubElement(leader, 'leader07')
    leader07.text = string_leader[7]

    leader08 = ET.SubElement(leader, 'leader08')
    leader08.text = string_leader[8]

    leader09 = ET.SubElement(leader, 'leader09')
    leader09.text = string_leader[9]

    indicator_count = ET.SubElement(leader, 'indicatorCount')
    indicator_count.text = string_leader[10]

    indicator_length = ET.SubElement(leader, 'identifierLength')
    indicator_length.text = string_leader[11]

    data_base_address = ET.SubElement(leader, 'dataBaseAddress')
    data_base_address.text = string_leader[12:17]

    leader17 = ET.SubElement(leader, 'leader17')
    leader17.text = string_leader[17]

    leader18 = ET.SubElement(leader, 'leader18')
    leader18.text = string_leader[18]

    leader19 = ET.SubElement(leader, 'leader19')
    leader19.text = string_leader[19]

    entry_map = ET.SubElement(leader, 'entryMap')
    entry_map.text = string_leader[20:23]

    for key in sorted(record.fields.iterkeys()):
        for field in record.fields[key]:
            if isinstance(field, ControlField):
                control_field = ET.SubElement(root, 'field')
                control_field.set('id', field.tag)
                control_field.text = field.data
            else:
                data_field = ET.SubElement(root, 'field')
                data_field.set('id', field.tag)

                ind1 = ET.SubElement(data_field, 'indicator')
                ind1.set('id', '1')
                ind1.text = field.ind1

                ind2 = ET.SubElement(data_field, 'indicator')
                ind2.set('id', '2')
                ind2.text = field.ind2


                for sf_key in sorted(field.subfields.iterkeys()):
                    for subfield in field.subfields[sf_key]:
                        if isinstance(subfield, LinkedSubfield):
                            linked_subfield = ET.SubElement(data_field, 'subfield')
                            linked_subfield.set('id', '1')

                            if  isinstance(subfield.field, ControlField):
                                linked_control_field = ET.SubElement(linked_subfield, 'field')
                                linked_control_field.set('id', subfield.field.tag)
                                linked_control_field.text = subfield.field.data
                            else:
                                linked_data_field = ET.SubElement(linked_subfield, 'field')
                                linked_data_field.set('id', subfield.field.tag)

                                linked_ind1 = ET.SubElement(linked_data_field, 'indicator')
                                linked_ind1.set('id', '1')
                                linked_ind1.text = subfield.field.ind1

                                linked_ind2 = ET.SubElement(linked_data_field, 'indicator')
                                linked_ind2.set('id', '2')
                                linked_ind2.text = subfield.field.ind2


                                # глубже! еще глубже!
                                for sf_key in sorted(subfield.field.subfields.iterkeys()):
                                    for lsubfield in subfield.field.subfields[sf_key]:
                                        linkeddata_subfield = ET.SubElement(linked_data_field, 'subfield')
                                        linkeddata_subfield.set('id', lsubfield.code)
                                        linkeddata_subfield.text = lsubfield.data

                        else:
                            data_subfield = ET.SubElement(data_field, 'subfield')
                            data_subfield.set('id', subfield.code)
                            data_subfield.text = subfield.data
    return root


# xml decoders

def record_to_xml(record):
    if isinstance(record, UnimarcRecord):
        #xml_record = record_to_unimarc_xml(record)
        xml_record = record_to_rustam_xml(record)
    elif isinstance(record, Record):
        xml_record = record_to_marc_xml(record)

    return xml_record
