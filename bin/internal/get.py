#!/usr/bin/env python
import sys, urllib, urllib2, os, mimetools, mimetypes, itertools, httplib


url = sys.argv[1]
fields = {}

for i in range(2,len(sys.argv),2):
    fields[sys.argv[i]] = sys.argv[i+1]

data = urllib.urlencode(fields)
req = urllib2.Request(url, data)
response = urllib2.urlopen(req)
the_page = response.read().strip()
if the_page=="OK":
    exit(0)
else:
    print(the_page)
    exit(1)
