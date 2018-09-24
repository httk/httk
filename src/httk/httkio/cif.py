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

import os, string, re
from collections import OrderedDict

import httk

from httk.core import *


def _read_cif_rewind_if_needed(f, row, done_fields):
    splitstr = row.lstrip().split(None, done_fields)
    if len(splitstr) > 1:
        rest = splitstr[-1]
        if rest.strip() != "":
            f.rewind(rest)
            return True
        return False
    else:
        return False


def _read_cif_loop(f, pragmatic=True, use_types=False):
    #print "Read cif loop"
    noteol = False
    loop_data = OrderedDict()
    header = []
    for row in f:
        striprow = row.strip()
        lowrow = striprow.lower()        
        if lowrow.startswith("_"):
            loop_data[lowrow[1:]] = []
            header += [lowrow[1:]]
            noteol = _read_cif_rewind_if_needed(f, row, 1)
        else:
            f.rewind()
            break

    while True:
        for i in range(len(loop_data)):
            try:
                row = f.next()
            except StopIteration:
                break
            if row.isspace():
                continue
            striprow = row.strip()
            lowrow = striprow.lower()
            if not row or row.startswith("_") or lowrow.startswith("data_") or lowrow.startswith("loop_"):
                f.rewind()
                break
            f.rewind()
            val, noteol = _read_cif_data_value(f, noteol, pragmatic, use_types, inloop=True)
            loop_data[header[i]].append(val)
        else:
            continue
        break
    return loop_data


def _read_cif_data_value(f, noteol, pragmatic=True, use_types=False, inloop=False):
    #print "Read cif data value"
    data_value = None
    for row in f:
        #print "read_cif_data_value_row:",row
        striprow = row.strip()
        if striprow == "":
            noteol = False
            continue
        elif (not noteol) and row.startswith(';'):
            folded = False
            newline = False
            data_value = ""
            if row[1] == "\\" and row[2:].rstrip("\r\n") == "":
                folded = True
            elif row[1:].isspace():
                if not pragmatic:
                    data_value = row.lstrip().rstrip('\r\n')
                    newline = True
            else:
                data_value = row.lstrip()[1:].rstrip('\r\n')
                newline = True
            stripirow = ""
            for irow in f:
                stripirow = irow.strip()
                if irow.startswith(';'):
                    break
                if newline:
                    data_value += '\n'
                    newline = True
                if folded and irow.rstrip('\r\n').endswith("\\"):
                    data_value += irow.rstrip('\r\n').rstrip("\\")
                    newline = False
                else:
                    data_value += irow.rstrip('\r\n')
                    newline = True
            if len(stripirow) > 1:
                f.rewind(stripirow[1:])
                noteol = True
            else:
                noteol = False
            break
        elif striprow.startswith("'") or striprow.startswith('"'):
            # The cif quoting rules are ... weird. Quotes are "escaped" if they are not followed by whitespace.
            quote = striprow[0] 
            starti = 1
            for chari in range(1, len(striprow)-1):
                if striprow[chari] == quote and str(striprow[chari+1]).isspace():
                    endi = chari
                    endq = chari+1
                    break
            else:
                if striprow[-1] != quote:
                    starti = 0
                    endi = len(striprow)
                    endq = len(striprow)
                else:
                    endi = len(striprow)-1
                    endq = len(striprow)
            data_value = striprow[starti:endi]
            if endq != len(striprow):
                f.rewind(striprow[endq:])
                noteol = True
            else:
                noteol = False
            break
        else:
            # Unquoted string
            if pragmatic and not inloop:
                # In pragmatic mode, if we are not in a loop and there is more than one data value
                # separated by whitespace, read all of it. This should always be ok to do, since 
                # multiple data values in this situation would be an
                # error in the file otherwise, but if there is whitespace + underscore/data_/loop_ we parse that
                # as a new symbol, since otherwise we COULD misread valid files (with very weird formatting...).
                splitstr = re.split("\s+_|\s+data_|\s+loop_", striprow, maxsplit=1)                    
            else:
                splitstr = striprow.split(None, 1)
            data_value = splitstr[0].strip()
            rightside = ""
            if len(splitstr) > 1:
                rightside = splitstr[1].strip()
            if rightside != "":
                f.rewind(rightside)
                noteol = True
            else:
                noteol = False
            break
            if use_types:
                if _cif_is_int(data_value):
                    data_value = int(data_value.replace("(", "").replace(")", ""))
                elif _cif_is_float(data_value):
                    data_value = float(data_value.replace("(", "").replace(")", ""))
            
    return data_value, noteol


def _read_cif_data_block(f, pragmatic=True, use_types=False):
    #print "Read cif data block"
    data_items = OrderedDict()
    loops = 0
    for row in f:
        #print "Read data block read:",row
        striprow = row.strip()
        lowrow = striprow.lower()
        if striprow.startswith("#"):
            continue
        elif lowrow.startswith("data_"):
            f.rewind()
            return data_items
        elif lowrow.startswith("loop_"):
            _read_cif_rewind_if_needed(f, row, 1)
            loopdata = _read_cif_loop(f, pragmatic, use_types)
            data_items['loop_'+str(loops)] = loopdata.keys()
            loops += 1
            data_items.update(loopdata)
        elif striprow.startswith(";"):
            # Multi-line string that we've failed to tie to a name, lets just skip it, maybe we should warn
            for irow in f:
                if irow.rstrip() == ";":
                    break 
        elif striprow.startswith("_"):
            lowsplit = lowrow.split()
            data_name = lowsplit[0][1:]
            if len(lowsplit) > 1:
                noteol = True
                rightside = striprow.split(None, 1)[1].strip()
                f.rewind(rightside)
            else:
                noteol = False
            data_value, noteol = _read_cif_data_value(f, noteol, pragmatic, use_types, inloop=False)
            data_items[data_name] = data_value
    return data_items


def read_cif(ioa, pragmatic=True, use_types=False):
    """
    Generic cif reader, given a filename / ioadapter it places all data in a python dictionary.

    It returns a tuple: (header, list) 
    Where list are pairs of data blocks names and data blocks
     
    Each data block is a dictionary with tag_name:value
    
    For loops, value is another dictionary with format column_name:value

    The optional parameter pragmatic regulates handling of some counter-intuitive aspects of the cif specification, where
    the default pragmatic=True handles these features the way people usually use them, whereas pragmatic=False means 
    to read the cif file precisely according to the spec. For example, in a multiline text field::

        ;
        some text
        ;

    Means the string '\\nsome text'. For this specific case pragmatic=True removes the leading newline. 

    set use_types to True to convert things that look like floats and integers to those respective types
    """
    ioa = IoAdapterFileReader.use(ioa)
    f = basic.rewindable_iterator(ioa.file)
    header = ""
    datalist = []
    for row in f:
        if row.strip().startswith("#"):
            header += row
        else:
            f.rewind()
            break

    for row in f:
        lowrow = row.strip().lower()
        if lowrow.startswith("data_"):
            data_block_name = lowrow.partition('_')[2].split()[0].strip()
            _read_cif_rewind_if_needed(f, row, 1)
            data_block = _read_cif_data_block(f, pragmatic, use_types)
            datalist += [(data_block_name, data_block)]

    ioa.close()
    return datalist, header
    
_cif_ordinary_char = "!%&()*+,-./0123456789:<=>?@ABCDEFGHIHJKLMNOPQRSTUVWXYZ\^`abcdefghijklmnopqrstuvwxyz{|}~"
_cif_non_blank_char = _cif_ordinary_char+'"'+"#$"+"'"+"_"+";[]"
_cif_text_lead_char = _cif_ordinary_char+'"'+"#$"+"'"+"_ \t[]"
_cif_any_print_char = _cif_ordinary_char+'"'+"#$"+"'"+"_ \t;[]"

_cif_non_blank_char_table = string.maketrans(_cif_non_blank_char, ' ' * len(_cif_non_blank_char))
_cif_helper_table = string.maketrans('', '')

_cif_integer_regex = re.compile('^[+-]?[0-9]+$')
_cif_float_regex = re.compile('^[+-]?[0-9]+[eE][+-]?[0-9]+|([+-]?[0-9]*\.[0-9]+|[+-]?[0-9]\.)([eE][+-]?[0-9]+)?$')
_cif_simplestring_regex = re.compile('^[A-Za-z0-9()][A-Za-z0-9()+-]*$')


def _cif_validate_name(name_unfiltered, context=None):
    if context is not None:
        context = context+": "+name_unfiltered
    name = _cif_validate_non_blank_char(name_unfiltered, context)
    if len(name) > 75:
        sys.stderr.write("***Warning: write_cif: name length > 75, surplus characters removed in "+context+": "+name_unfiltered)
        name = name[:75]
    return name


def _cif_is_float(data_value):
    return (_cif_float_regex.match(data_value) is not None)


def _cif_is_simplestring(data_value):
    return (_cif_simplestring_regex.match(data_value) is not None)


def _cif_is_int(data_value):
    return (_cif_integer_regex.match(data_value) is not None)


def _cif_validate_non_blank_char(s, context=None):
    out = s.translate(_cif_helper_table, _cif_non_blank_char_table)
    if out != s:
        if context is not None:
            sys.stderr.write("***Warning: write_cif: non-permitted characters in "+context+" removed.")
        else:
            sys.stderr.write("***Warning: write_cif: non-permitted characters removed.")
    return out


def _cif_write_semicolontextfield(f, lines, noteol, max_line_length):
    if noteol:
        f.write("\n")
        noteol = False
    for i in range(len(lines)):            
        lines[i] = lines[i].rstrip("\r\n")
        if lines[i][0] == ';':
            sys.stderr.write("***Warning: write_cif: had to insert space before semicolon at the start of a line of a multi-line string to fulfill arcane quoting rules.")
            lines[i] = ' '+lines[i]
        if len(lines[i]) > max_line_length:
            f.write(";\\"+"\n")            
            break
    else:
        f.write(";")
    for line in lines:            
        if len(line) > max_line_length:
            sublines = [line[i:i+max_line_length-2] for i in range(0, len(line), max_line_length-2)]
            # Handle a wonderful corner case: the line splitting for length creates lines that start with one, or more, semi-colons..., sigh...
            for i in range(1, len(sublines)):                
                if sublines[i][0] == ";":
                    if len(sublines[i]) > 1 and sublines[i][1] != ";":
                        # If its just a single semi-colon, move it to the previous line, which we saved space for by splitting at max_line_length-2
                        sublines[i-1] += ";"
                        sublines[i] = sublines[i][1:]
                    else:
                        # Multiple semi-colons in a row, or a semi-colon + newline, this is a possibly unresolvable case (think long string of only semi-colons)
                        # fudge a solution by inserting a space
                        sys.stderr.write("***Warning: write_cif: had to insert space before semicolon in a long string to fulfill arcane quoting rules.")
                        sublines[i] = " "+sublines[i]
            for subline in sublines:
                f.write(subline+"\\"+"\n")
        else:
            f.write(line+"\n")

    f.write(";\n")
    return False


def _cif_write_data_value(f, orig_data_value, noteol, max_line_length, use_types, inloop):
    if orig_data_value is None:
        data_value = ""
    else:
        data_value = str(orig_data_value)
    has_whitespace = len(data_value.split()) > 1
    lines = data_value.splitlines()
    has_lines = len(lines) > 1
    has_single_quote = data_value.find("'") != -1
    has_double_quote = data_value.find('"') != -1
    too_long = len(data_value) + 2 > max_line_length
    if has_lines or (has_single_quote and has_double_quote) or too_long:
        noteol = _cif_write_semicolontextfield(f, lines, noteol, max_line_length)
        return noteol
    elif has_double_quote or (has_whitespace and not has_single_quote) or data_value == "":
        f.write("'"+data_value+"'")
        return True
    elif has_single_quote or (has_whitespace and not has_double_quote):
        f.write('"'+data_value+'"')
        return True
    elif not use_types:
        # Skip quotes if it looks like a number or is a simple string used in a loop
        if _cif_is_float(data_value):
            f.write(data_value)
            return True
        elif _cif_is_int(data_value):
            f.write(data_value)
            return True
        elif inloop and _cif_is_simplestring(data_value):
            f.write(data_value)
            return True
        else:
            f.write("'"+data_value+"'")
            return True
    else:
        # Always quote when a string, never quote otherwise
        if isinstance(orig_data_value, basestring):
            f.write("'"+data_value+"'")
        else:
            f.write(data_value)
        return True    


def _cif_write_data_block(f, data_block, max_line_length, use_types):
    for key in data_block:
        val = data_block[key]
        if key.startswith("loop_"):
            f.write("loop_\n")
            outdata_columns = []
            for unfiltered_column in val:
                column = _cif_validate_non_blank_char(unfiltered_column, "column name: "+unfiltered_column)
                f.write("_"+column+"\n")
                outdata_columns += [data_block[unfiltered_column]]
            if len(outdata_columns) > 0:
                noteol = False
                for i in range(len(outdata_columns[0])):
                    column_count = 0
                    for j in range(len(outdata_columns)):
                        column_count += len(str(outdata_columns[j][i]))+2
                        if column_count > max_line_length and noteol:
                            f.write("\n")
                            column_count = 0
                            noteol = False
                        noteol = _cif_write_data_value(f, outdata_columns[j][i], noteol, max_line_length, use_types, inloop=True)
                        if noteol:
                            f.write(" ")
                            column_count += 1
                        else:
                            column_count = 0
                    if noteol:
                        noteol = False
                        f.write("\n")
        elif basic.is_sequence(val):
            continue
        else:
            data_name = _cif_validate_name(key)
            # Do we have space _ + key + space + quote + the whole data value + quote?, if not, preemptively break line
            f.write("_"+data_name+" ")
            if len(data_name)+len(str(val))+4 > max_line_length:
                f.write("\n")
                noteol = False
            else:
                noteol = True
            noteol = _cif_write_data_value(f, val, noteol, max_line_length, use_types, inloop=False)
            if noteol:
                f.write("\n")
                noteol = False
    

def write_cif(ioa, data, header=None, max_line_length=80, use_types=False):
    """
    Generic cif writer, given a filename / ioadapter 
    
    data = the cif data to write as an (ordered) dictionary of tag_name:value
    
    header = the header (comment) segment
    
    max_line_length = the maximum number of characters allowed on each line. This should not be set < 80
    (there is no point, and the length calculating algorithm breaks down at some small line length)
    
    use_types = 
    
       if True: always quote values that are of string type. Numeric values are put in the file unquoted (as they should)
       if False (default): also strings that look like cif numbers are put in the file unquoted
    
    For loops, value is another dictionary with format column_name:value
    
    The optional parameter pragmatic regulates handling of some counter-intuitive aspects of the cif specification, where
    the default pragmatic=True handles these features the way people usually use them, whereas pragmatic=False means 
    to read the cif file precisely according to the spec. For example, in a multiline text field::
    
      ;
      some text
      ;

    Means the string '\\nsome text'. For this specific case pragmatic=True removes the leading newline.
    
    set use_types to True to convert things that look like floats and integers to those respective types

    
    """

    ioa = IoAdapterFileWriter.use(ioa)
    f = ioa.file

    if header is not None:
        lines = header.splitlines()
        for line in lines:            
            if len(line) > max_line_length:
                header = "#\n" + header
                break            
        for line in lines:            
            if len(line) > max_line_length:
                sublines = [line[i:i+79] for i in range(0, len(line), 79)]
                for subline in sublines:
                    f.write(subline+"\\"+"\n")
            else:
                f.write(line+"\n")

    data_block_count = -1
    for data_block in data:
        data_block_count += 1
        data_block_name_unfiltered = data_block[0]
        if data_block_name_unfiltered is None:
            data_block_name = "data_"+str(data_block_count)
        else:
            data_block_name = _cif_validate_name(data_block_name_unfiltered, "data block name")
            if data_block_name == "":
                data_block_name = "data_"+str(data_block_count)
                    
        f.write("data_"+data_block_name+"\n")
        _cif_write_data_block(f, data_block[1], max_line_length, use_types)
    ioa.close()

        
def main():
    gurk = open("/tmp/gurk.cif", "r")
    datalist, header = read_cif(gurk)
    
    gurk = open("/tmp/gurk2.cif", "w")
    write_cif(gurk, datalist, header)
    gurk.close()

    datalist2, header2 = read_cif("/tmp/gurk2.cif")

    print "MATCH1", header == header2
    print "MATCH2", datalist == datalist2
    
    exit(0)

if __name__ == "__main__":
    main()
