#!/usr/bin/env python
import sys, urllib, urllib2, os, mimetools, mimetypes, itertools, httplib, urlparse

class form_wrapper(file):
    def __init__(self, path, mode, name, filename, fields=[], prepend_progress=""):
        file.__init__(self, path, mode)
        self.seek(0, os.SEEK_END)
        self._total = self.tell()
        self.seek(0)
        self._seen = 0
        self._fields = fields
        self._prepend_progress = prepend_progress
        self.boundary = mimetools.choose_boundary()

        self.predata = ""
        for field in fields:            
            self.predata += "--" + self.boundary + "\r\n"
            self.predata += 'Content-Disposition: form-data; name="%s"' % (field[0],) + "\r\n\r\n"
            self.predata += field[1] + "\r\n"
        self.predata += "--" + self.boundary + "\r\n"
        self.predata += 'Content-Disposition: file; name="%s"; filename="%s"' % (name, filename)
        #if path.endswith(".bz2"):
        #    self.predata += 'Content-Type: %s' % ('application/x-bzip2',) + "\r\n\r\n"      
        #else:
        self.predata += 'Content-Type: %s' % ('application/octet-stream',) + "\r\n\r\n"
        #self.predata += 'Content-Length: %d' % (self._total,) + "\r\n\r\n"

        self.postdata = "\r\n"
        self.postdata += '--' + self.boundary + '--' + "\r\n\r\n"

    def __len__(self):
        return len(self.predata) + self._total + len(self.postdata)

    def read(self, size):
        data = ""
        if self._seen < len(self.predata):
            newdata = self.predata[self._seen:self._seen + size]
            data += newdata
            size -= len(newdata)
            self._seen += len(newdata)
        if size > 0 and self._seen < len(self.predata) + self._total:
            newdata = file.read(self, size)
            data += newdata
            size -= len(newdata)
            self._seen += len(newdata)
        if size > 0 and self._seen >= len(self.predata) + self._total:
            newdata = self.postdata[self._seen - len(self.predata) - self._total:self._seen - len(self.predata) - self._total + size]
            data += newdata
            size -= len(newdata)
            self._seen += len(newdata)
            
        if len(data) > 0:
            progress = float((self._seen)) / len(self)
            sys.stdout.write('\r\033[K[{0}{1}] {2}%'.format('#'*int((100*progress/10)),' '*(10-int((100*progress/10))), int(100*progress))+" "+self._prepend_progress)
        return data

argcount=1
if sys.argv[argcount] == '-t':
    prepend_progress = sys.argv[argcount+1]
    argcount+=2
else:
    prepend_progress = ""

url = sys.argv[argcount]
path = sys.argv[argcount+1]
fields = []

for i in range(argcount+2,len(sys.argv),2):
    fields += [(sys.argv[i], sys.argv[i+1])]

#stream = form_wrapper(path, 'rb', 'file', path, fields)
#print stream.read(10000000)
stream = form_wrapper(path, 'rb', 'file', path, fields, prepend_progress)

# Build the request
request = urllib2.Request(url)
request.add_header('User-agent', 'httk-post')
request.add_header('Content-type', 'multipart/form-data; boundary='+str(stream.boundary))
request.add_header('Content-length', len(stream))
request.add_data(stream)
result = urllib2.urlopen(request).read()
if result=="OK":
    exit(0)
else:
    print "===="+result+"===="
    exit(1)

