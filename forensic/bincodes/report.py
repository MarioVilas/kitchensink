#!/usr/bin/env python

"""Extract all credit card numbers from a list of plain text files and produce a report.

@type mii: tuple(str)
@type brand: tuple of tuple(str, regexp)

@var mii: Array of credit card types.
    The index of the array is the first digit of the credit card number.
    See: U{http://www.merriampark.com/anatomycc.htm}

@var brand: Regular expressions to match each credit card issuer.
    Do not use them with the L{extract.extract} function, they are written for
    matching rather than searching.
    See: U{http://www.regular-expressions.info/creditcard.html}

@type header_row: list(str)
@var header_row: Default header row for report tables.
"""

__all__ = ['mii', 'brand', 'BincodesDB', 'Table', 'pretty', 'report', 'extract_and_report']

import glob
import re
import os
try:
    import sqlite3
except ImportError:
    from pysqlite2 import dbapi2 as sqlite3
import sys
import texttable
import HTML

from extract import listfiles, extract

# http://www.merriampark.com/anatomycc.htm
mii = (
    "ISO/TC 68 and other industry assignments",
    "Airlines",
    "Airlines and other industry assignments",
    "Travel and entertainment",
    "Banking and financial",
    "Banking and financial",
    "Merchandizing and banking",
    "Petroleum",
    "Telecommunications and other industry assignment",
    "National assignment",
)

# http://www.regular-expressions.info/creditcard.html
brand = (
    ("Visa"                      ,   re.compile("^4[0-9]{12}(?:[0-9]{3})?$")),
    ("MasterCard"                ,   re.compile("^5[1-5][0-9]{14}$")),
    ("American Express"          ,   re.compile("^3[47][0-9]{13}$")),
    ("Diner's Club/Carte Blanche",   re.compile("^3(?:0[0-5]|[68][0-9])[0-9]{11}$")),
    ("Discover"                  ,   re.compile("^6(?:011|5[0-9]{2})[0-9]{12}$")),
    ("JCB"                       ,   re.compile("^(?:2131|1800|35\d{3})\d{11}$")),
)

header_row=[
    'Number',
    'Issuer',
    'Brand',
    'Industry',
    'Country',
    'Contact',
]

class Table:
    """Text or HTML table.
    @type html: bool
    @type table: texttable.Texttable or HTML.Table
    @ivar html: C{True} for HTML, C{False} for plain text.
    @ivar table: Actual table object.
    """

    def __init__(self, html=False, header_row=None):
        """
        @type html: bool
        @type header_row: list(str)
        @param html: C{True} for HTML, C{False} for plain text.
        @param header_row: Optional header row.
        """
        self.html = html
        if html:
            if header_row:
                self.table = HTML.Table(header_row=header_row)
            else:
                self.table = HTML.Table()
        else:
            self.table = texttable.Texttable(max_width=140)
            if header_row:
                self.table.add_row(['*%s*' % x for x in header_row])

    def add_row(self, row):
        """Add a row to the table.
        @type row: list(str)
        @param row: Row of text.
        """
        if self.html:
            self.table.rows.append(row)
        else:
            self.table.add_row(row)

    def draw(self):
        """Dump the resulting table as a text string.
        @rtype: str
        @return: Text or HTML table.
        """
        if self.html:
            return str(self.table)
        return self.table.draw()

    __str__ = draw

class BincodesDB:
    """Bincodes database.
    @type db: sqlite3.Connection
    @type cursor: sqlite3.Cursor
    @type filename: str
    @ivar db: SQLite connection object.
    @ivar cursor: SQLite cursor object.
    @ivar filename: SQLite databse filename.
    """

    def __init__(self, filename=None):
        """
        @type filename: str
        @param filename: Database filename.
        """
        if not filename:
            filename = os.path.split(__file__)[0]
            if not filename:
                filename = '.'
            filename = os.path.join(filename, 'bincodes.db')
        self.filename = filename
        self.db = sqlite3.connect(filename)
        self.db.text_factory = str
        self.cursor = self.db.cursor()

    def __del__(self):
        try:
            self.close()
        except Exception:
            pass

    def __enter__(self):
        return self

    def __exit__(self, type, value, traceback):
        return False

    def close(self):
        "Close the database."
        try:
            self.cursor.close()
        finally:
            self.db.close()

    def fetch(self, cc):
        """Fetch relevant information from the credit card number.
        @type cc: str
        @param cc: Credit card number.
        @rtype: tuple(str, str, str, str, str, str)
        @return:
            Some or all of the following:
             - Credit card number, sanitized with L{pretty}.
             - Issuer entity.
             - Card brand (see L{brand}).
             - Card industry type (see L{mii}).
             - Country of origin.
             - Bank's customer support telephone number.
            Missing fields are returned as C{None}.
        """
        industria = mii[int(cc[0])]
        marca = None
        for b, rb in brand:
            if rb.match(cc):
                marca = b
                break
        bincode = int(cc[0:6])
        self.cursor.execute("select * from bincodes where bincode=?", (bincode,))
        result = self.cursor.fetchall()
        if result:
            bincode, entidad, pais, telefono = result[0]
        else:
            entidad  = None
            pais     = None
            telefono = None
        return pretty(cc), entidad, marca, industria, pais, telefono

def pretty(cc):
    """Sanitize a credit card number for user display.
    @type cc: str
    @param cc: Credit card number.
    @rtype: str
    @return: Credit card number.
    """
    return '-'.join([cc[i:i+4] for i in xrange(0, len(cc), 4)])

def report(cclist, html=False):
    """Produce a report for a list of credit card numbers.
    @see: L{BincodesDB.fetch}
    @type cclist: list(str)
    @type html: bool
    @param cclist: List of credit card numbers.
    @param html: C{True} for an HTML report, C{False} for a plain text report.
    @rtype: Table
    @return: Text or HTML table.
    """
    bincodes = BincodesDB()
    try:
        table = Table(html, header_row)
        for cc in cclist:
            table.add_row(list(bincodes.fetch(cc)))
    finally:
        bincodes.close()
    return table

def extract_and_report(argv, html=False, matching_only=True):
    """Extract all credit card numbers from a list of plain text files
    and produce a report.
    @see: L{BincodesDB.fetch}
    @type argv: list(str)
    @type html: bool
    @type matching_only: bool
    @param argv: List of filenames, glob wildcards, or the special value "-".
        See: L{extract.listfiles}
    @param html: C{True} for an HTML report, C{False} for a plain text report.
    @param matching_only: C{True} to show only credit cards that match known
        bincodes, C{False} to show all credit cards.
    @rtype: iterator of (str, Table)
    @return: Yields tuples with the filename and the report for that file.
    """
    found = set()
    bincodes = BincodesDB()
    try:
        for filename in listfiles(argv):
            if filename != '-':
                data = open(filename, 'r').read()
            else:
                data = sys.stdin.read()
            table = Table(html, header_row)
            for cc in extract(data):
                if cc not in found:
                    row = list(bincodes.fetch(cc))
                    if not matching_only or row[1] is not None:
                        table.add_row(row)
                    found.add(cc)
            yield (filename, table)
    finally:
        bincodes.close()

def main():
    "This function is called when the module is run as a command line script."
    argv = sys.argv[1:]
    if not argv:
        import os
        print "Credit card number extractor + bincode analysis"
        print "%s <text file> [text file...]" % os.path.basename(sys.argv[0])
        return
    for (filename, table) in extract_and_report(argv):
        print "Results for %s:" % filename
        print table.draw()
        print

if __name__ == "__main__":
    try:
        import psyco
        psyco.full()
    except ImportError:
        pass
    main()
