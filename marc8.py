# encoding: utf-8
# see http://www.loc.gov/marc/specifications/speccharmarc8.html
"pymarc marc8.py file."

import sys
import unicodedata
import marc8_mapping


def marc8_to_unicode(marc8, hide_utf8_warnings=False):
    """
    Pass in a string, and get back a Unicode object.

      print marc8_to_unicode(record.title())

    """
    # XXX: might be good to stash away a converter somehow
    # instead of always re-creating it
    converter = MARC8ToUnicode(quiet=hide_utf8_warnings)
    return converter.translate(marc8)


class MARC8ToUnicode:
    """
    Converts MARC-8 to Unicode.  Note that currently, unicode strings
    aren't normalized, and some codecs (e.g. iso8859-1) will fail on
    such strings.  When I can require python 2.3, this will go away.

    Warning: MARC-8 EACC (East Asian characters) makes some
    distinctions which aren't captured in Unicode.  The LC tables give
    the option of mapping such characters either to a Unicode private
    use area, or a substitute character which (usually) gives the
    sense.  I've picked the second, so this means that the MARC data
    should be treated as primary and the Unicode data used for display
    purposes only.  (If you know of either of fonts designed for use
    with LC's private-use Unicode assignments, or of attempts to
    standardize Unicode characters to allow round-trips from EACC,
    or if you need the private-use Unicode character translations,
    please inform me, asl2@pobox.com.
    """
    basic_latin = 0x42
    ansel = 0x45
    def __init__(self, G0=basic_latin, G1=ansel, quiet=False):
        self.g0 = G0
        self.g0_set = set(['(', ',', '$'])
        self.g1 = G1
        self.g1_set = set([')', '-', '$'])
        self.quiet = quiet

    def translate(self, marc8_string):
        # don't choke on empty marc8_string
        if not marc8_string:
            return u''
        uni_list = []
        combinings = []
        pos = 0
        while pos < len(marc8_string):
            # http://www.loc.gov/marc/specifications/speccharmarc8.html
            if marc8_string[pos] == '\x1b':
                next = marc8_string[pos+1]
                if (next in self.g0_set):
                    if len(marc8_string) >= pos + 3:
                        if marc8_string[pos+2] == ',' and next == '$':
                            pos += 1
                        self.g0 = ord(marc8_string[pos+2])
                        pos = pos + 3
                        continue
                    else:
                        # if there aren't enough remaining characters, readd
                        # the escape character so it doesn't get lost; may
                        # help users diagnose problem records
                        uni_list.append(marc8_string[pos])
                        pos += 1
                        continue

                elif next in self.g1_set:
                    if marc8_string[pos+2] == '-' and next == '$':
                        pos += 1
                    self.g1 = ord(marc8_string[pos+2])
                    pos = pos + 3
                    continue

            def is_multibyte(charset):
                return charset == 0x31

            mb_flag = is_multibyte(self.g0)

            if mb_flag:
                code_point = (ord(marc8_string[pos]) * 65536 +
                              ord(marc8_string[pos+1]) * 256 +
                              ord(marc8_string[pos+2]))
                pos += 3
            else:
                code_point = ord(marc8_string[pos])
                pos += 1

            if (code_point < 0x20 or
                (code_point > 0x80 and code_point < 0xa0)):
                uni = unichr(code_point)
                continue

            try:
                if code_point > 0x80 and not mb_flag:
                    (uni, cflag) = marc8_mapping.CODESETS[self.g1][code_point]
                else:
                    (uni, cflag) = marc8_mapping.CODESETS[self.g0][code_point]
            except KeyError:
                try:
                    uni = marc8_mapping.ODD_MAP[code_point]
                    uni_list.append(unichr(uni))
                    # we can short circuit because we know these mappings
                    # won't be involved in combinings.  (i hope?)
                    continue
                except KeyError:
                    pass
                if not self.quiet:
                    sys.stderr.write("couldn't find 0x%x in g0=%s g1=%s\n" %
                                     (code_point, self.g0, self.g1))
                uni = ord(' ')
                cflag = False

            if cflag:
                combinings.append(unichr(uni))
            else:
                uni_list.append(unichr(uni))
                if len(combinings) > 0:
                    uni_list.extend(combinings)
                    combinings = []

        # what to do if combining chars left over?
        uni_str = u"".join(uni_list)

        # unicodedata.normalize not available until Python 2.3
        if hasattr(unicodedata, 'normalize'):
            uni_str = unicodedata.normalize('NFC', uni_str)

        return uni_str