#!/usr/bin/env python

"""Extract credit card numbers from plain text files.

@type rcc_strict: regexp
@type rcc_loose: regexp
@var rcc_strict: Strict credit card number matching. See: U{http://www.regular-expressions.info/creditcard.html}
@var rcc_loose: Relaxed credit card number matching. See: U{http://www.regular-expressions.info/creditcard.html}
"""

__all__ = ['rcc_strict', 'rcc_loose', 'is_luhn_valid', 'strip', 'extract', 'bruteforce', 'listfiles']

import glob
import re
import sys

# http://www.regular-expressions.info/creditcard.html
rcc_strict = re.compile('[^0-9](?:4[0-9]{12}(?:[0-9]{3})?|5[1-5][0-9]{14}|6(?:011|5[0-9][0-9])[0-9]{12}|3[47][0-9]{13}|3(?:0[0-5]|[68][0-9])[0-9]{11}|(?:2131|1800|35\\d{3})\\d{11})[^0-9]')
##rcc_loose  = re.compile('\\b(?:\d[ -]*?){13,16}\\b')
rcc_loose  = re.compile('\\b(?:\\d[ -;,\\.\\:\\t\\r\\n]*?){13,16}\\b')

# http://en.wikipedia.org/wiki/Luhn_algorithm
def is_luhn_valid(cc):
    """Validate a credit card number using the Luhn algorithm.
    @see: U{http://en.wikipedia.org/wiki/Luhn_algorithm}
    @type cc: str
    @param cc: Credit card number.
    @rtype: bool
    @return: C{True} if the credit card number appears to be valid.
    """
    num = map(int, cc)
    return not sum(num[::-2] + map(lambda d: sum(divmod(d * 2, 10)), num[-2::-2])) % 10

def strip(cc):
    """Strip all non numeric characters.
    @type cc: str
    @param cc: String.
    @rtype: str
    @return: Stripped string.
    """
    return ''.join([c for c in cc if c.isdigit()])

def extract(data, rcc=rcc_loose):
    """Extract credit card numbers from plain text data.
    @type data: str
    @type rcc: regexp
    @param data: Plain text to analyze.
    @param rcc: Regular expression to use.
        See L{rcc_strict} and L{rcc_loose}.
        Defaults to C{rcc_loose}.
    @rtype: iterator
    @return: Yields seemingly valid credit card numbers. See L{is_luhn_valid}.
        To get all results at once, for example to sort them, do the following::
            cc_list = list(extract(data))
            cc_list.sort()
        There may be repeated entries, so you can also do this to remove them::
            cc_set = set(extract(data))
    """
    for cc in rcc.findall(data):
        cc = strip(cc)
        if is_luhn_valid(cc):
            yield cc

# absolutely the dumbest brute force ever
# too many false positives, though :(
# they could be mitigated by checking the bincode too
def bruteforce(data):
    """Extract credit card numbers from plain text data by brute force.
    @warning: May yield a large number of false positives!
    @see: L{extract}
    @type data: str
    @param data: Plain text to analyze.
    @rtype: iterator
    @return: Yields seemingly valid credit card numbers.
    """
    data = strip(data)
    for i in xrange(len(data) - 20):
        for n in xrange(13, min(21, len(data) - i)):
            cc = data[i:i+n]
            if rcc_strict.match(' %s ' % cc) and is_luhn_valid(cc):
                yield cc

def listfiles(argv):
    """Yields all filenames, expanding glob wildcards.
    @warning: Filenames are not guaranteed to exist.
    @type argv: list(str)
    @param argv: List of filenames, glob wildcards, or the special value "-".
    @rtype: iterator
    @return: Filenames.
    """
    for filename in argv:
        if '*' in filename or '?' in filename:
            for filename in glob.glob(filename):
                yield filename
        else:
            yield filename

def main():
    "This function is called when the module is run as a command line script."
    argv = sys.argv[1:]
    if not argv:
        import os
        print "Credit card number extractor"
        print "%s <text file> [text file...]" % os.path.basename(sys.argv[0])
        return
    for filename in listfiles(argv):
        data = open(filename, 'r').read()
        result = list(set(extract(data)))
        result.sort()
        for cc in result:
            print cc

if __name__ == "__main__":
    try:
        import psyco
        psyco.full()
    except ImportError:
        pass
    main()
