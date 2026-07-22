#!/usr/bin/env python
#
#    The high-throughput toolkit (httk)
#    Copyright (C) 2012-2020 Rickard Armiento
#
#    This program is free software: you can redistribute it and/or modify
#    it under the terms of the GNU Affero General Public License as
#    published by the Free Software Foundation, either version 3 of the
#    License, or (at your option) any later version.
#
#    This program is distributed in the hope that it will be useful,
#    but WITHOUT ANY WARRANTY; without even the implied warranty of
#    MERCHANTABILITY or FITNESS FOR A PARTICULAR PURPOSE.  See the
#    GNU Affero General Public License for more details.
#
#    You should have received a copy of the GNU Affero General Public License
#    along with this program.  If not, see <http://www.gnu.org/licenses/>.

import json, time, codecs

try:
    from urllib2 import urlopen, HTTPError, URLError, Request
except ImportError:
    from urllib.request import urlopen, HTTPError, URLError, Request

class RequestError(Exception):
    def __init__(self, msg, code):
        super(RequestError, self).__init__(msg)
        self.code = code

def request(url,headers=None):
    retry = 5
    lasterr = None
    while retry > 0:
        try:
            if headers is not None:                
                req = Request(url)
                for header in headers:
                    req.add_header(header, headers[header])
            else:
                req = url
            uo = urlopen(req)
            reader = codecs.getreader("utf-8")
            output = json.load(reader(uo))
            headers = uo.info()
            return {'response':output, 'headers':headers, 'code':uo.code}
        except HTTPError as e:
            raise RequestError("Could not fetch resource: "+str(e), e.code)
        except URLError as e:
            lasterr = e
            retry-=1
            time.sleep(1.0)
    raise RequestError("Could not fetch resource: "+str(lasterr),None)

    
