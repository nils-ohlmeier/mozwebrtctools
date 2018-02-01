#!/usr/bin/env python
import csv
import sys

if len(sys.argv) != 2:
    sys.exit('missing input csv file name')

filename = sys.argv[1]

components = {}

with open(filename, 'rb') as csvfile:
    reader = csv.DictReader(csvfile)
    try:
        for row in reader:
            compname = row['Component']
            bugid = row['Bug ID']
            summary = row['Summary']
            if not compname in components:
                components[compname] = {}
            comp = components[compname]
            comp[bugid] = summary
    except csv.Error as e:
        sys.exit('file %s, line: %d: %s' % (filename, reader.line_num, e))
    csvfile.close()

for compname in sorted(components):
    comp = components[compname]
    print
    print '===%s:===' % (compname)
    for bugnr in sorted(comp):
        title = comp[bugnr]
        print
        print '{{Bug|%s}} %s' % (bugnr, title)
