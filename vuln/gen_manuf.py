#!/usr/bin/env python
# -*- coding: utf-8 -*-

# Copyright (c) 2013, Mario Vilas
# All rights reserved.
#
# Redistribution and use in source and binary forms, with or without
# modification, are permitted provided that the following conditions are met:
#
#     * Redistributions of source code must retain the above copyright notice,
#       this list of conditions and the following disclaimer.
#     * Redistributions in binary form must reproduce the above copyright
#       notice,this list of conditions and the following disclaimer in the
#       documentation and/or other materials provided with the distribution.
#     * Neither the name of the copyright holder nor the names of its
#       contributors may be used to endorse or promote products derived from
#       this software without specific prior written permission.
#
# THIS SOFTWARE IS PROVIDED BY THE COPYRIGHT HOLDERS AND CONTRIBUTORS "AS IS"
# AND ANY EXPRESS OR IMPLIED WARRANTIES, INCLUDING, BUT NOT LIMITED TO, THE
# IMPLIED WARRANTIES OF MERCHANTABILITY AND FITNESS FOR A PARTICULAR PURPOSE
# ARE DISCLAIMED. IN NO EVENT SHALL THE COPYRIGHT OWNER OR CONTRIBUTORS BE
# LIABLE FOR ANY DIRECT, INDIRECT, INCIDENTAL, SPECIAL, EXEMPLARY, OR
# CONSEQUENTIAL DAMAGES (INCLUDING, BUT NOT LIMITED TO, PROCUREMENT OF
# SUBSTITUTE GOODS OR SERVICES; LOSS OF USE, DATA, OR PROFITS; OR BUSINESS
# INTERRUPTION) HOWEVER CAUSED AND ON ANY THEORY OF LIABILITY, WHETHER IN
# CONTRACT, STRICT LIABILITY, OR TORT (INCLUDING NEGLIGENCE OR OTHERWISE)
# ARISING IN ANY WAY OUT OF THE USE OF THIS SOFTWARE, EVEN IF ADVISED OF THE
# POSSIBILITY OF SUCH DAMAGE.

# Example entry:
# 00:00:01	Xerox                  # XEROX CORPORATION

import re
r = re.compile(

    # MAC address prefix (3 octets).
    r"([0-9A-Fa-f][0-9A-Fa-f][\:\-\.]"
    r"[0-9A-Fa-f][0-9A-Fa-f][\:\-\.]"
    r"[0-9A-Fa-f][0-9A-Fa-f])"

    # Separator.
    r"[ \t]+"

    # 8-char short manufacturer name.
    r"([^ \t]+)"

    # Separator.
    r"[ \t]+\#[ \t]"

    # Full manufacturer name.
    r"(.+)"
)

import os.path
if not os.path.exists("manuf.txt"):
    import shutil
    import urllib2
    url = "https://code.wireshark.org/review/gitweb?p=wireshark.git;a=blob_plain;f=manuf;hb=HEAD"
    print "Downloading from: %s" % url
    req = urllib2.Request(url)
    req.add_header("User-Agent", "Mozilla/5.0 (X11; Ubuntu; Linux x86_64; rv:79.0) Gecko/20100101 Firefox/79.0")
    src = urllib2.urlopen(req)
    with open("manuf.txt", "wb") as dst:
        shutil.copyfileobj(src, dst)

import codecs
d = {}
with codecs.open("manuf.txt", "rU", "utf-8") as f:
    for line in f:
        line = line.encode("utf-8")
        for m in r.finditer(line):
            prefix, code, name = m.groups()
            d[prefix] = (code, name)

from pprint import pformat
with open("manuf.py", "w") as f:
    f.write("#!/usr/bin/env python\n")
    f.write("# -*- coding: utf-8 -*-\n\n")
    f.write("MAC_PREFIX_TO_MANUFACTURER = ")
    f.write(pformat(d))
    f.write("\n")

import cPickle
with open("manuf.pickle", "wb") as f:
    cPickle.dump(d, f, -1)

import marshal
with open("manuf.marshal", "wb") as f:
    marshal.dump(d, f)

import anydbm
db = anydbm.open("manuf.dbm", 'c')
for k,v in d.iteritems():
    db[k] = ",".join(v)
db.close()

import sqlite3
import os, os.path
if os.path.exists("manuf.db"):
    os.unlink("manuf.db")
db = sqlite3.connect("manuf.db")
try:
    c = db.cursor()
    try:
        c.execute(
            "CREATE TABLE `manufacturer` ("
            "    `prefix` CHAR(8) PRIMARY KEY NOT NULL,"
            "    `code` VARCHAR(8) NOT NULL,"
            "    `name` TEXT NOT NULL"
            ");"
        )
        for prefix in d:
            code, name = d[prefix]
            code = code.decode("utf-8")
            name = name.decode("utf-8")
            c.execute(
                "INSERT INTO `manufacturer` VALUES (?, ?, ?);",
                (prefix, code, name)
            )
    finally:
        db.commit()
        c.close()
finally:
    db.close()

del d

from time import time
from random import randint

import pickle

td = []
for i in xrange(30):
    t1 = time()
    with open("manuf.pickle", "rb") as f:
        d = pickle.load(f)
    t2 = time()
    td.append(t2 - t1)
import numpy
print "Pickle: %s seconds to load." % numpy.mean(td)
del d

import cPickle

td = []
for i in xrange(100):
    t1 = time()
    with open("manuf.pickle", "rb") as f:
        d = cPickle.load(f)
    t2 = time()
    td.append(t2 - t1)
import numpy
print "C Pickle: %s seconds to load." % numpy.mean(td)
del d

import marshal

td = []
for i in xrange(100):
    t1 = time()
    with open("manuf.marshal", "rb") as f:
        d = marshal.load(f)
    t2 = time()
    td.append(t2 - t1)
import numpy
print "Marshal: %s seconds to load." % numpy.mean(td)
td = []
for i in xrange(100000):
    a = randint(0, 16)
    b = randint(0, 16)
    c = randint(0, 16)
    x = "%.2x:%.2x:%.2x" % (a, b, c)
    t1 = time()
    try:
        d[x][1]
    except KeyError:
        pass
    t2 = time()
    td.append(t2 - t1)
print "Dict: %s to access." % numpy.mean(td)
del d

import anydbm

td = []
for i in xrange(1000):
    t1 = time()
    d = anydbm.open("manuf.dbm")
    t2 = time()
    td.append(t2 - t1)
import numpy
print "AnyDBM: %s seconds to load." % numpy.mean(td)
td = []
for i in xrange(100000):
    a = randint(0, 16)
    b = randint(0, 16)
    c = randint(0, 16)
    x = "%.2x:%.2x:%.2x" % (a, b, c)
    t1 = time()
    try:
        d[x][1]
    except KeyError:
        pass
    t2 = time()
    td.append(t2 - t1)
print "AnyDBM: %s to access." % numpy.mean(td)
del d

import sqlite3
td = []
for i in xrange(1000):
    t1 = time()
    db = sqlite3.connect("manuf.db")
    t2 = time()
    db.close()
    td.append(t2 - t1)
import numpy
print "SQLite3: %s seconds to load." % numpy.mean(td)
td = []
db = sqlite3.connect("manuf.db")
for i in xrange(100000):
    a = randint(0, 16)
    b = randint(0, 16)
    c = randint(0, 16)
    x = "%.2x:%.2x:%.2x" % (a, b, c)
    t1 = time()
    c = db.cursor()
    c.execute(
        "SELECT `code`, `name` FROM `manufacturer` WHERE `prefix` = ?;",
        (x,)
    )
    c.close()
    t2 = time()
    td.append(t2 - t1)
db.close()
print "SQLite3: %s to access." % numpy.mean(td)
td = []
for i in xrange(1000):
    a = randint(0, 16)
    b = randint(0, 16)
    c = randint(0, 16)
    x = "%.2x:%.2x:%.2x" % (a, b, c)
    t1 = time()
    db = sqlite3.connect("manuf.db")
    c = db.cursor()
    c.execute(
        "SELECT `code`, `name` FROM `manufacturer` WHERE `prefix` = ?;",
        (x,)
    )
    c.close()
    db.close()
    t2 = time()
    td.append(t2 - t1)
print "SQLite3: %s to access from scratch." % numpy.mean(td)

"""
Results on my machine (2013):

Pickle: 0.103633332253 seconds to load.
C Pickle: 0.030119998455 seconds to load.
Marshal: 0.02375 seconds to load.
Dict: 1.48000478745e-06 to access.
AnyDBM: 0.000647000074387 seconds to load.
AnyDBM: 1.64299988747e-05 to access.
SQLite3: 0.000156000137329 seconds to load.
SQLite3: 4.49900174141e-05 to access.
SQLite3: 0.00040499997139 to access from scratch.

1,173,504 manuf.db
1,343,488 manuf.dbm
1,004,757 manuf.marshal
  776,393 manuf.pickle
  938,882 manuf.py
1,335,564 manuf.txt

------------------------------------------------------------------------------

Results again in 2020, before updating manuf.txt:

Pickle: 0.0336551427841 seconds to load.
C Pickle: 0.0095471739769 seconds to load.
Marshal: 0.00561310052872 seconds to load.
Dict: 6.17473125458e-07 to access.
AnyDBM: 9.07230377197e-05 seconds to load.
AnyDBM: 5.89835643768e-06 to access.
SQLite3: 2.39644050598e-05 seconds to load.
SQLite3: 9.15317058563e-06 to access.
SQLite3: 9.27138328552e-05 to access from scratch.

-rw-r--r-- 1 mario mario 1150976 ago 11 15:21 manuf.db
-rw-r--r-- 1 mario mario 1306624 ago 11 15:21 manuf.dbm
-rw-r--r-- 1 mario mario 1004757 ago 11 15:21 manuf.marshal
-rw-r--r-- 1 mario mario  776393 ago 11 15:21 manuf.pickle
-rw-r--r-- 1 mario mario  921067 ago 11 15:21 manuf.py
-rw-r--r-- 1 mario mario 1335564 ene  9  2020 manuf.txt

Python marshalling got somewhat better but database support went horribly wrong...

After updating manuf.txt from here:
    https://gitlab.com/wireshark/wireshark/raw/master/manuf

Pickle: 1.41302744548e-05 seconds to load.
C Pickle: 7.3504447937e-06 seconds to load.
Marshal: 5.3596496582e-06 seconds to load.
Dict: 5.85944652557e-07 to access.
AnyDBM: 8.98447036743e-05 seconds to load.
AnyDBM: 5.99348783493e-06 to access.
SQLite3: 2.36549377441e-05 seconds to load.
SQLite3: 8.59124422073e-06 to access.
SQLite3: 9.4655752182e-05 to access from scratch.

-rw-r--r-- 1 mario mario   12288 ago 11 15:26 manuf.db
-rw-r--r-- 1 mario mario 1306624 ago 11 15:26 manuf.dbm
-rw-r--r-- 1 mario mario      91 ago 11 15:26 manuf.marshal
-rw-r--r-- 1 mario mario      89 ago 11 15:26 manuf.pickle
-rw-r--r-- 1 mario mario     174 ago 11 15:26 manuf.py
-rw-r--r-- 1 mario mario 1734797 ago 11 15:26 manuf.txt

It's interesting to see how each method scales differently as the database grows larger :)
"""
