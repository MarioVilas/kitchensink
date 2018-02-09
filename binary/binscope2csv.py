#!/usr/bin/env python

from csv import writer
from glob import glob
from os import walk, unlink, listdir
from os.path import isdir, isfile, join, abspath, splitext, commonprefix
from tempfile import mkdtemp
from shutil import rmtree
from subprocess import check_call
from traceback import print_exc
from sys import stdout, stderr
from collections import defaultdict

try:
    import xml.etree.cElementTree as ET
except ImportError:
    import xml.etree.ElementTree as ET

def main(argv):
    """Main function."""

    # Expand unresolved file masks (happens on Windows).
    # Convert all arguments to absolute file paths.
    reports = []
    for param in argv:
        if "*" in param or "?" in param:
            reports.extend(map(abspath, glob(param)))
        else:
            reports.append(abspath(param))

    # The first columns of the CSV are fixed, the rest depend on the plugins.
    default_columns = ['path', 'length', 'IsManaged', 'IsPureManaged', 'IsManagedResourceOnly',
                       'IsResourceOnly', 'IsInteropWrapper', 'IsKernelMode', 'Is64bit']

    # For each BinScope report create a CSV file.
    for report in reports:
        csvfile = splitext(report)[0] + '.csv'
        with open(csvfile, 'w') as outfile:
            csvwriter = writer(outfile, dialect='excel')

            # Parse the report file.
            results = defaultdict(dict)
            binaries = defaultdict(dict)
            plugins = set()
            with open(report, 'rU') as infile:
                xml = ET.fromstring(infile.read())
            for item in xml.iter('item'):
                x = item.find('result')
                if x is not None:
                    result = x.text
                    path = item.find('targetPath').text
                    plugin = item.find('issueType').text
                    results[path][plugin] = result
                    plugins.add(plugin)
                else:
                    x = item.find('path')
                    if x is not None:
                        path = x.text
                        for k in default_columns:
                            binaries[path][k] = item.find(k).text

            # Write a CSV row for each file.
            optional_columns = list(plugins)
            optional_columns.sort()
            csvwriter.writerow(default_columns + optional_columns)
            result_files = sorted(set(results.keys() + binaries.keys()))
            for result_file in result_files:
                row = []
                bin_item = binaries[result_file]
                res_item = results[result_file]
                for column in default_columns:
                    data = bin_item.get(column, '')
                    row.append(data)
                for column in optional_columns:
                    data = res_item.get(column, '')
                    row.append(data)
                csvwriter.writerow(row)

if __name__ == '__main__':
    from sys import argv
    main(argv[1:])
