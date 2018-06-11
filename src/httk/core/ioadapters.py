# 
#    The high-throughput toolkit (httk)
#    Copyright (C) 2012-2015 Rickard Armiento
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

import os, tempfile, StringIO

try:
    import bz2
except ImportError:
    pass

try:
    import gzip
except ImportError:
    pass


def universal_opener(other):
    #if isinstance(other, file):
    if isinstance(other, StringIO.StringIO):
        return IoAdapterFileReader(other)
    elif hasattr(other, 'read'):
        return IoAdapterFileReader(other, name=other.name)
    elif isinstance(other, str):
        return IoAdapterFilename(other, name=other)
    raise Exception("universal_opener: do not know how to open, object is:"+str(other.__class__))

# This file contains a number of interoperable IoAdapter classes. See IoAdapterFileReader for more info.


class IoAdapterFileReader(object):

    """
    Io adapter for easy handling of io.
    """

    def __init__(self, f, name=None, deletefilename=None, close=False):
        self.file = f
        self.name = name
        self.deletefilename = deletefilename
        self.close_file = close

    def close(self):
        if self.file is not None and self.close_file:
            self.file.close()
            self.file = None
        if self.deletefilename is not None:
            os.unlink(self.deletefilename)
        
    @classmethod
    def use(cls, other):
        if isinstance(other, IoAdapterFileReader):
            return other
        if isinstance(other, IoAdapterString):
            f = StringIO.StringIO(other.string)
            return IoAdapterFileReader(f, name=other.name)
        if isinstance(other, IoAdapterFileWriter):
            return IoAdapterFileReader(other.fire, name=other.name, close=other.close_file)
        if isinstance(other, IoAdapterStringList):
            f = StringIO.StringIO("\n".join(other.stringlist))
            return IoAdapterFileReader(f, name=other.name)
        if isinstance(other, IoAdapterFilename):
            f = cleveropen(other.filename, 'r')
            return IoAdapterFileReader(f, name=other.name, close=True)
        return cls.use(universal_opener(other))

    def __iter__(self):
        try:
            for line in self.file:
                yield line
            self.close()
        except GeneratorExit:
            self.close()
        

class IoAdapterFileWriter(object):

    """
    Io adapter for access to data as a python file object
    """

    def __init__(self, f, name=None, close=False):
        self.file = f
        self.name = name
        self.close_file = close

    def close(self):
        if self.file and self.close_file:
            self.file.close()
            self.file = None
        
    @classmethod
    def use(cls, other):
        if isinstance(other, IoAdapterFileWriter):
            return other
        if isinstance(other, IoAdapterString):
            f = StringIO.StringIO(other.string)
            other._reroute = f
            return IoAdapterFileWriter(f, name=other.name)
        if isinstance(other, IoAdapterFileReader):
            return IoAdapterFileWriter(other.file, name=other.name, close=other.close_file)
        if isinstance(other, IoAdapterFilename):
            f = cleveropen(other.filename, 'w')
            return IoAdapterFileReader(f, name=other.name, close=True)
        return cls.use(universal_opener(other))


class IoAdapterFileAppender(object):

    """
    Io adapter for access to data as a python file object
    """

    def __init__(self, f, name=None):
        self.file = f
        self.name = name

    def close(self):
        if self.file:
            self.file.close()
            self.file = None
        
    @classmethod
    def use(cls, other):
        if isinstance(other, IoAdapterFileWriter):
            return other
        if isinstance(other, IoAdapterString):
            f = StringIO.StringIO(other.string)
            return IoAdapterFileAppender(f, name=other.name)
        if isinstance(other, IoAdapterFilename):
            f = cleveropen(other.filename, 'a')
            return IoAdapterFileReader(f, name=other.name, close=True)
        return cls.use(universal_opener(other))


class IoAdapterString(object):

    """
    Universal io adapter, helps handling the passing of filenames, files, and strings to functions that deal with io    
    """

    def __init__(self, string=None, name=None):
        if string is None:
            self._string = ""
        else:
            self._string = string
        self.name = name
        self._reroute = None

    @property
    def string(self):
        if self._reroute is not None:
            return self._reroute.getvalue()
        return self._string

    @string.setter
    def string(self, new):
        if self._reroute is not None:
            self._reroute.seek(0)
            self._reroute.write(new)
        else:
            self._string = new

    def close(self):
        if self._reroute is not None:
            self._reroute.close()
        pass
        
    @classmethod
    def use(cls, other):
        if isinstance(other, IoAdapterString):
            return other
        if isinstance(other, IoAdapterFileReader):
            string = other.file.read()
            return IoAdapterString(string, name=other.name)
        if isinstance(other, IoAdapterFilename):
            with cleveropen(other.filename, 'r') as f:
                string = f.read()
            return IoAdapterString(string, name=other.name)
        return cls.use(universal_opener(other))

    def __iter__(self):
        new = IoAdapterFileReader.use(self)
        return new.__iter__()


class IoAdapterStringList(object):

    """
    Universal io adapter, helps handling the passing of filenames, files, and strings to functions that deal with io    
    """

    def __init__(self, stringlist, name=None):
        self.stringlist = stringlist
        self.name = name
        
    @classmethod
    def use(cls, other):
        if isinstance(other, IoAdapterStringList):
            return other
        if isinstance(other, IoAdapterString):
            return IoAdapterStringList(other.string.split('\n'))
        if isinstance(other, IoAdapterFileReader):
            stringlist = other.file.readlines()
            return IoAdapterStringList(stringlist, name=other.name)
        if isinstance(other, IoAdapterFilename):
            with cleveropen(other.filename) as f:
                stringlist = f.file.readlines()
            return IoAdapterStringList(stringlist, name=other.name)
        return cls.use(universal_opener(other))

    def __iter__(self):
        return self.stringlist.__iter__()


class IoAdapterFilename(object):

    """
    Universal io adapter, helps handling the passing of filenames, files, and strings to functions that deal with io    
    """

    def __init__(self, filename, name=None, deletefilename=None):
        self.filename = filename
        if name is None:
            self.name = filename
        else:
            self.name = name
        self.deletefilename = deletefilename

    def close(self):
        if self.deletefilename is not None:
            os.unlink(self.deletefilename)
        
    @classmethod
    def use(cls, other):
        if isinstance(other, IoAdapterFilename):
            return other
        if isinstance(other, IoAdapterFileReader):
            tmpfile = tempfile.NamedTemporaryFile(mode='w', bufsize=-1, delete=False)
            name = tmpfile.name
            tmpfile.write(other.file.read())
            tmpfile.close()
            other.close()
            return IoAdapterFilename(name, name=other.name, deletefilename=name)
        if isinstance(other, IoAdapterString):
            tmpfile = tempfile.NamedTemporaryFile(mode='w', bufsize=-1, delete=False)
            name = tmpfile.name
            tmpfile.write(other.string)
            tmpfile.close()
            return IoAdapterFilename(name, name=other.name, deletefilename=name)
        if isinstance(other, IoAdapterStringList):
            tmpfile = tempfile.NamedTemporaryFile(mode='w', bufsize=-1, delete=False)
            name = tmpfile.name
            tmpfile.write("\n".join(other.stringlist))
            tmpfile.close()
            return IoAdapterFilename(name, name=other.name, deletefilename=name)
        return cls.use(universal_opener(other))

    def __iter__(self):
        new = IoAdapterFileReader.use(self)
        return new.__iter__()


def zdecompressor(f, mode, *args):
    """
    Read a classic unix compress .Z type file.
    """
    # Note: there is no python library for reading .Z files. zlib is not it.
    # We have to call out to gunzip, which the user hopefully has...
    import subprocess

    if not os.path.exists(f):
        raise IOError("zlibdecompressor: File not found found:"+str(f))

    #print "Opening: "+f
    
    if mode != 'r' and mode != 'rb':
        raise Exception("Cannot write inside zlib compressed files.")

    p = subprocess.Popen(["gunzip", "-c", f], stdout=subprocess.PIPE)
    result = p.communicate()
    if p.returncode != 0:
        raise Exception('zdecompressor needed to call out to gunzip binary, which failed with error:'+str(result[1]))
    return StringIO.StringIO(result[0])
    

def cleveropen(filename, mode, *args):
    basename_no_ext, ext = os.path.splitext(filename)
    if ext.lower() == '.bz2':
        return bz2.BZ2File(filename, mode, *args)
    elif ext.lower() == '.gz':
        return gzip.GzipFile(filename, mode, *args)
    elif ext.lower() == '.z':
        return gzip.GzipFile(filename, mode, *args)
    else:
        try:
            return open(filename, mode, *args)
        except IOError:
            pass
        try:
            return bz2.BZ2File(filename+".bz2", mode, *args)
        except (IOError, NameError):
            pass
        try:
            return bz2.BZ2File(filename+".BZ2", mode, *args)
        except (IOError, NameError):
            pass
        try:
            return gzip.GzipFile(filename+".gz", mode, *args)
        except (IOError, NameError):
            pass
        try:
            return gzip.GzipFile(filename+".GZ", mode, *args)
        except (IOError, NameError):
            pass
        try:
            return zdecompressor(filename+".z", mode, *args)
        except (IOError, NameError):
            pass
        try:
            return zdecompressor(filename+".Z", mode, *args)
        except (IOError, NameError):
            pass
        if not os.path.exists(filename):
            raise Exception("IOAdapters.cleveropen: file not found: "+str(filename))
        else:
            raise Exception("IOAdapters.cleveropen: Do not know how to open:"+str(filename))


