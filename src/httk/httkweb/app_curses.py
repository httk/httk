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

# Note: this is a placeholder, this does not yet work

try:
    from html.parser import HTMLParser
except ImportError:
    # Python 2 compatibility
    from HTMLParser import HTMLParser

try:
    from urllib.request import urlopen
except ImportError:
    # Python 2 compatibility    
    from urllib2 import urlopen

from curses import wrapper

    
from re import sub
from sys import stderr

class MyHTMLParser(HTMLParser):

    ignore_close_tags = ['meta', 'link', 'br', 'img', 'input']    
    ignore_content = ['script','style']
    
    def __init__(self):
        HTMLParser.__init__(self)
        self.content = []
        self.ignore = False
        self.taglist = []
        
    def handle_data(self, data):
        if not self.ignore:
            text = data.strip().encode('utf-8')
            if len(text) > 0:
                text = sub('[ \t\r\n]+', ' ', text)
                self.content.append(text + ' ')
                #print("  "*len(self.taglist) + text)

    def handle_starttag(self, tag, attrs):
        if tag not in self.ignore_close_tags:
            #print("  "*len(self.taglist) + "<"+tag+">")
            self.taglist.append(tag)
        else:
            #print("  "*len(self.taglist) + "<"+tag+"/>")
            pass
        if tag == 'p':
            self.content.append('\n\n')
        elif tag == 'br':
            self.content.append('\n')
        elif tag in self.ignore_content:
            self.ignore = True

    def handle_startendtag(self, tag, attrs):
        #print("  "*len(self.taglist) + "<" + tag + "/>")
        if tag == 'br':
            self.content.append('\n\n')
        elif tag in self.ignore_content:
            self.ignore = False

    def handle_endtag(self, tag):
        if tag in self.ignore_close_tags:
            return
        oldtag = self.taglist.pop()
        if tag != oldtag:
            #print("  "*len(self.taglist) + "</"+tag + "!=" + oldtag +">")
            raise Exception("Badly formed html")
        else:
            #print("  "*len(self.taglist) + "</"+tag+">")
            pass
        if tag in self.ignore_content:
            self.ignore = False
            
    def text(self):
        return ''.join(self.content).strip()

ESC = 27
next_url = None

def render_page(stdscr):
    global next_url
    
    stdscr.clear()
    stdscr.refresh()
    curses.nl()
    curses.noecho()
    stdscr.timeout(0)

    stdscr.nodelay(0)
    curidx = 0
    entries = ["test", "test2" ]
    pending_click = False
    
    while 1:
        stdscr.clear()
        curses.init_pair(1, curses.COLOR_WHITE, curses.COLOR_BLUE)
        line = 0
        offset = max(0, curidx - curses.LINES + 3)
        
        for i in range(len(entries)):
            if line == curidx:
                if pending_click:
                    next_url = line
                    return
                stdscr.attrset(curses.color_pair(1) | curses.A_BOLD)        
            else:
                stdscr.attrset(curses.color_pair(0))
            if 0 <= line - offset < curses.LINES - 1:
                stdscr.addstr(line - offset, 0, entries[i])
            line +=1
            
        stdscr.refresh()
        
        ch = stdscr.getch()
        if ch == curses.KEY_UP: curidx -= 1
        elif ch == curses.KEY_DOWN: curidx += 1
        elif ch == curses.KEY_PPAGE:
            curidx -= curses.LINES
            if curidx < 0: curidx = 0
        elif ch == curses.KEY_NPAGE:
            curidx += curses.LINES
            if curidx >= line: curidx = line - 1
        elif ch == curses.KEY_RIGHT: curidx += 1
        elif ch == curses.KEY_LEFT: curidx -= 1
        elif ch == ESC: return
        elif ch == ord('\n'): pending_click = True
        curidx %= line



class WebviewCurses(object):

    def __init__(self,appdir):
        self.appdir = appdir
    
    def open_url(self, url):
        global next_url
        
        #creating an object of the overridden class
        parser = MyHTMLParser()

        resource = urllib2.urlopen("http://www.google.com")
        if 'charset' in resource.headers.getparamnames():
            charset = resource.headers.getparam("charset")
        else:
            charset = 'utf-8'
        content =  resource.read().decode(charset)
            
        #Feeding the content
        parser.feed(content)
        parser.close()

        print(parser.text())

        wrapper(render_page)
        print("Next url:",next_url)

