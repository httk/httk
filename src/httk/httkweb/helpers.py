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

def setup_template_helpers(global_data):
    
    def first_value(*vals):
        for val in vals:
            if val:
                return val
    
    def getitem(a,i):
        #try:
        #    return global_data[a][i]
        #except TypeError:
        #    return global_data[a][int(i)]
        try:
            return a[i]
        except TypeError:
            return a[int(i)]
        
    global_data['first_value'] = first_value
    global_data['getitem'] = getitem
