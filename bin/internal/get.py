#!/usr/bin/env python
import sys, urllib
import six

if sys.version_info[0] == 3:
    from urllib.parse import urlencode
    from urllib.request import Request, urlopen
else:
    from urllib import urlencode
    from urllib2 import Request, urlopen

url = sys.argv[1]
fields = {}

for i in range(2, len(sys.argv), 2):
    fields[sys.argv[i]] = sys.argv[i+1]

data = urlencode(fields).encode()
req = Request(url, data)
response = urlopen(req)
the_page = response.read().strip().decode('utf-8')
if the_page == "OK":
    sys.exit(0)
else:
    print(the_page)
    sys.exit(1)
