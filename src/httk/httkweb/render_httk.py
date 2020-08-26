#
#    The high-throughput toolkit (httk)
#    Copyright (C) 2012-2018 Rickard Armiento
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

from __future__ import print_function
import os, sys, re, pprint, unicodedata, codecs

# Retain python2 compatibility without a dependency on httk.core
if sys.version[0] == "2":
    # Note:
    # The "html" module is not a builtin in Python 2.
    # If it happens to be installed, we still do not
    # want to use it since it is old (last updated in 2011,
    # version 1.16). Use the builtin cgi module to get the
    # escape funtion instead.

    from cgi import escape
    unicode_type=unicode

    from StringIO import StringIO
    import ConfigParser as configparser
else:
    from html import escape
    unicode_type=str

    from io import StringIO
    import configparser


class RenderHttk(object):

    left_punctuation_chars = "'[({<:\"; -"
    right_punctuation_chars = "]')}>:,!.?\"; -"

    #left_punctuation_chars_quotes = "\\'\\(\\[\\{\\<:-\\\"; "
    #right_punctuation_chars_quotes = "'\\)\\]\\}\\>:,-\\!\\.\\?\\\"; "

    adornment_chars = ['!','"','#','$','%','&',"'",'(',')','*','+',',','-','.','/',':',';','<','=','>','?','@','[',"\\",']','^','_','`','{','|','}','~']
    bullet_item_markers = ['- ', '* ', '+ ']
    option_list_characters = ['-','/']

    def __init__(self, render_dir, render_filename, global_data):

        self.render_dir = render_dir
        self.render_filename = render_filename
        self.filename = os.path.join(render_dir, render_filename)

        with codecs.open(self.filename, 'r', encoding='utf-8') as f:
            source = f.read()

        self.global_data = global_data

        if render_dir != '':
            owd = os.getcwd()
            os.chdir(render_dir)
        try:
            self.split_content(source)
        finally:
            if render_dir != '':
                os.chdir(owd)

    def make_id(self, s):
        s = unicodedata.normalize('NFKD', s).encode('ascii','ignore').decode('utf-8')
        s = s.lower()
        s = s.replace(' ', '_')
        #s = re.sub('[^0-9a-zA-Z_]', '', s)
        #s = re.sub('^[^a-zA-Z_]+', '', s)
        return s

    def rst_light_html_renderer(self, content):
        outstr = ''
        for entry in content:
            if entry['type'] == 'section':
                modifiers = [x['name'] for x in entry['modifiers']]
                modifiers += ['section']
                outstr += '<div id="'+self.make_id(entry['title'])+'" class="'+(' '.join(modifiers))+'">'
                end_div_tag = '</div>\n'
                outstr += '<h'+str(entry['level']+1)+'>'+entry['title']+'</h'+str(entry['level']+1)+">\n"
                outstr += self.rst_light_html_renderer(entry['content'])
                outstr += end_div_tag
            elif entry['type'] == 'transition':
                outstr += '<hr class="docutils"/>'
            elif entry['type'] == 'textblock':
                modifiers = [x['name'] for x in entry['modifiers']]
                if len(entry['modifiers'])>0:
                    outstr += '<p class="'+(' '.join(modifiers))+'">'
                    end_p_tag = '</p>\n'
                else:
                    outstr += '<p>'
                    end_p_tag = '</p>\n'
                for segment in entry['content']:
                    endtag = '\n'
                    modifiers = [x['name'] for x in segment['modifiers']]
                    if 'literal' in modifiers:
                        modifiers.remove('literal')
                        outstr += '<tt class="docutils literal">'
                        outstr +=  segment['content']
                        outstr += '</tt>'
                        continue
                    if 'strong' in modifiers:
                        modifiers.remove('strong')
                        outstr += '<strong>'
                        endtag = '</strong>' + endtag
                    if 'emphasis' in modifiers:
                        modifiers.remove('emphasis')
                        outstr += '<em>'
                        endtag = '</em>' + endtag
                    if 'link' in modifiers:
                        modifiers.remove('link')
                        outstr += '<a class="reference external" href="'+segment['url']+'">'
                        endtag = '</a>'+endtag
                    if 'anchor' in modifiers:
                        modifiers.remove('anchor')
                        outstr += '<a class="reference internal" href="#'+segment['anchor']+'">'
                        endtag = '</a>'+endtag
                    if len(modifiers)>0:
                        if 'role' in modifiers:
                            modifiers.remove('role')
                            outstr += '<span class="'+(' '.join(modifiers + [segment['role']]))+'">'
                        else:
                            outstr += '<span class="'+(' '.join(modifiers))+'">'
                        endtag = '</span>' + endtag
                    outstr +=  escape(segment['content']).encode('ascii',
                            'xmlcharrefreplace').decode('utf-8')
                    outstr += endtag
                outstr += end_p_tag
        return outstr

    def rst_light_parse_textstyle(self, content, start_marker, end_marker, style, allow_nested = False, unescape=True, handle_roles = False, handle_hyperlinks = False):

        # Quote
        start_marker = re.escape(start_marker)
        end_marker = re.escape(end_marker)

        outcontent = []
        for segment in content:
            segment_text = segment['content']
            if len(segment['modifiers'])==0 or allow_nested:
                role = False
                link = False

                #try:
                #print("REGEX",segment_text)
                found = re.finditer('(?P<start>['+self.left_punctuation_chars+']|^)(?P<role>:[^:]+:)?'+start_marker+'(?P<content>.+?)(?P<url> +<[^>]+>)?'+end_marker+'(?P<link>_?)(?P<end>['+self.right_punctuation_chars+']|$)',segment_text)
                #except Exception:
                #    print("RE ERROR",repr('(['+self.left_punctuation_chars+']|^)(:[^:]+:)?'+start_marker+'(.+?)(
                #    +<[^>]+>)?'+end_marker+'(_?)(['+self.right_punctuation_chars+']|$)'))
                #    print("STRING",segment_text)
                #    raise
                end_idx = 0
                for m in found:
                    start = m.group('start') if m.group('start') is not None else ''
                    role = m.group('role')[1:-1] if m.group('role') is not None else ''
                    content = m.group('content') if m.group('content') is not None else ''
                    url = m.group('url').lstrip(" <").rstrip(">") if m.group('url') is not None else ''
                    link = m.group('link') if m.group('link') is not None else ''
                    end = m.group('end') if m.group('end') is not None else ''

                    #print("MATCH:",start,'|',role,'|',content,'|',url,'|',link,'|',end)
                    start_idx = m.start()
                    # Text role
                    if handle_roles and role != '' and link == '':
                        #print("TEXT ROLE")
                        before_text = segment_text[end_idx:start_idx]+start
                        outcontent += [{'content':before_text,'modifiers':segment['modifiers'],'unescape':segment['unescape']}]

                        outcontent += [{'content':content+url,'role':role,'modifiers':segment['modifiers'] + [{'name':'role'}], 'unescape':unescape and segment['unescape']}]
                    # Hyperlink
                    elif handle_hyperlinks and role == '' and link != '':
                        #print("HYPERLINK")
                        before_text = segment_text[end_idx:start_idx]+start+role
                        outcontent += [{'content':before_text,'modifiers':segment['modifiers'],'unescape':segment['unescape']}]
                        if url == '':
                            outcontent += [{'content':content,'anchor':self.make_id(content),'modifiers':segment['modifiers'] + [{'name':'anchor'}], 'unescape':unescape and segment['unescape']}]
                        else:
                            outcontent += [{'content':content,'url':url,'modifiers':segment['modifiers'] + [{'name':'link'}], 'unescape':unescape and segment['unescape']}]
                    # Error condition, if it isn't a hyperlink but ends with _, reject the m
                    elif handle_hyperlinks and role != '' and link != '':
                        #print("ERROR")
                        continue
                    # Other markup
                    else:
                        #print("OTHER MARKUP", m.start(), start, start,role)
                        before_text = segment_text[end_idx:start_idx]+start+role
                        #print("BEFORE TEXT", before_text)
                        outcontent += [{'content':before_text,'modifiers':segment['modifiers'],'unescape':segment['unescape']}]
                        outcontent += [{'content':content + url,'modifiers':segment['modifiers'] + [style], 'unescape':unescape and segment['unescape']}]

                    end_idx = m.end()-len(end)

                after_text = segment_text[end_idx:]
                if len(after_text) > 0:
                    outcontent += [{'content':after_text,'modifiers':segment['modifiers'],'unescape':segment['unescape']}]

            else:
                outcontent += [{'content':segment['content'], 'modifiers':segment['modifiers'], 'unescape':segment['unescape']}]

        return outcontent

    def rst_light_parser(self, source):
        adornment_levels = []
        fifo = []
        content = []
        section_hierarcy = []
        context = content
        block_modifiers = []

        align_hierarcy = []
        last_align = 0
        align = 0
        last_list_index = None

        # Divide text into sections, add an empty line to make sure last textblock is terminated
        for line in source.splitlines() + [""]:
            fifo += [line]
            section_title = None
            adornment = None

            # Detect section header with over and underline
            if len(fifo) == 3:
                line1, line2, line3 = fifo[0].rstrip(), fifo[1].rstrip(), fifo[2].rstrip()
                if len(line1) == len(line3) and len(line1) > 0 and line1 == len(line1) * line1[0] and line3 == len(line1) * line1[0] and line1[0] in self.adornment_chars:
                    section_title = line2.strip()
                    adornment = line1[0] + line1[0]

            # Detect section header with over and underline
            elif len(fifo) == 2:
                line1, line2 = fifo[-2].rstrip(), fifo[-1].rstrip()
                if len(line1) == len(line2) and len(line2) > 0 and line2 == len(line2) * line2[0]:
                    section_title = line1.rstrip()
                    adornment = line2[0]

            # Handle titles
            if section_title is not None:
                if adornment not in adornment_levels:
                    adornment_levels += [adornment]
                level = adornment_levels.index(adornment)
                #section_hierarcy = section_hierarcy[:-(len(section_hierarcy)-level)]
                context = []
                section = {'type':'section','level':level, 'title':section_title, 'content':context, 'modifiers':block_modifiers}
                block_modifiers = []
                while len(section_hierarcy) > 0 and section_hierarcy[-1]['level'] >= level:
                    section_hierarcy = section_hierarcy[:-1]
                if len(section_hierarcy) > 0:
                    section_hierarcy[-1]['content'] += [section]
                else:
                    content += [section]
                section_hierarcy += [section]
                fifo = []
                continue

            # Handle other blocks
            last_align = align
            if len(fifo[-1].strip()) > 0:
                align = len(fifo[-1]) - len(fifo[-1].lstrip(' '))

            if align > last_align:
                skip = False
                # Class
                if fifo[0][:3] == ".. ":
                    skip = True
                # Bullet item
                if fifo[0][:2] in self.bullet_item_markers:
                    skip = True
                # Numbered list item
                if fifo[0][:2] == '#. ' or (fifo[0][0].isdigit() and fifo[0].lstrip("0123456789") == '. '):
                    list_index = int(fifo[0].partition('. ')[0])
                    if last_list_index != None:
                        if list_index == last_list_index+1:
                            skip = True
                    else:
                        skip = True
                if len(fifo) == 2:
                    # Field list
                    if fifo[0][0] == ':' and fifo[0][-1] == ':':
                        skip = True
                    # Definition list
                    else:
                        skip = True
                # Option lists not yet supported
                # Literal block not yet supported
                # Line blocks not yet supported
                # Doctest blocks not supported
                # Tables not supported
                # Footnotes not supported
                # Citations not supported
                # External separated hyperlinks not supported
                if skip:
                    continue

            if len(fifo) >= 2 and len(fifo[-1].strip())==0 or align < last_align:
                # Transition
                first_line_strp = fifo[0].strip()
                if len(fifo) == 2 and len(first_line_strp) >= 4 and first_line_strp == first_line_strp[0]*len(first_line_strp) and not first_line_strp.isalnum():
                    element = {'type':'transition','modifiers':block_modifiers,'align':align}
                    block_modifiers = []
                    context += [element]
                    fifo = []
                    continue
                # Class
                if fifo[0][:3] == ".. ":
                    modparts = fifo[0][3:].split("::")
                    modname = modparts[0]
                    if len(modparts) > 1:
                        modargs = modparts[1].split()
                    else:
                        modargs = []
                    modcontent = fifo[1:-1]
                    if modname != 'class':
                        block_modifiers += [{'name':modname,'args':modargs,'content':modcontent, 'align':align}]
                    else:
                        block_modifiers += [{'name':modargs[0],'args':modargs[1:],'content':modcontent, 'align':align}]
                    fifo = []
                    continue
                #elif fifo[0][0:2] in self.bullet_item_markers:
                #
                #    list_fifo += {}

                allcontent = (" ".join([x.strip() for x in fifo[:-1]])).strip()
                allcontent = [{'content':allcontent,'modifiers':[],'unescape':True}]
                allcontent = self.rst_light_parse_textstyle(allcontent,'``','``',{'name':'literal'},unescape=False)
                allcontent = self.rst_light_parse_textstyle(allcontent,'**','**',{'name':'strong'})
                allcontent = self.rst_light_parse_textstyle(allcontent,'*','*',{'name':'emphasis'})
                # Roles and hyperlinks
                allcontent = self.rst_light_parse_textstyle(allcontent,'`','`',{'name':'literal'}, handle_roles=True, handle_hyperlinks=True)

                # Unescape
                for segment in allcontent:
                    if segment['unescape']:
                        segment['content'] = "\\".join(["".join(y) for y in [x.replace("\\ ","").split("\\") for x in segment['content'].split("\\\\")]])
                element = {'type':'textblock','content':allcontent,'modifiers':block_modifiers,'align':align}
                block_modifiers = []
                context += [element]
                fifo = []
                continue

            # Empty block, just ignore
            if len(fifo) == 1 and len(fifo[-1].strip())==0:
                fifo = []
                continue

        #print("== RESULT")
        #pprint.pprint(content)
        #print("==")
        return content

    def split_content(self,source):
        if source.startswith("---"):
            alt1 = source[3:].find("---")
            alt2 = source[3:].find("...")
            if alt1 >= 0:
                if alt2 >= 0:
                    pos = min(alt1,alt2)
                else:
                    pos = alt1
            elif alt2 > 0:
                pos = alt2
            else:
                self.metadata_block = ''
                self.content_block = source
                return

            self.metadata_block = source[3:pos+3]
            self.content_block = self.rst_light_html_renderer(self.rst_light_parser(source[pos+6:]))

        else:
            self.metadata_block = ''
            self.content_block = self.rst_light_html_renderer(self.rst_light(source))

        return

    def content(self):
        return self.content_block

    def metadata(self):
        md = self.metadata_block
        buf = StringIO("[main]\n"+md)
        config = configparser.ConfigParser()
        config.readfp(buf)
        d = dict(config.items('main'))
        # In Python 3 d.keys() is not a list but an iterator,
        # which means that when we do the deleting of keys and values
        # below, something gets messed up with the iterator.
        # Making sure that d.keys() is a list seems to fix the problem.
        for i in list(d.keys()):
            if i.endswith("-list"):
                l = d[i]
                del d[i]
                newkey = i[:-len("-list")]
                d[newkey] = [x.strip() for x in l.split(",")]
        return d
