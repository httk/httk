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

import httk
from httk.atomistic import Structure
from httk.core import FracVector

class Result_AIMDResult(httk.Result):
    """
    TODO: document the variables here
    """
    @httk.httk_typed_init({
        'formula': str,
        'temperature': float,
        'VEC': float,
        'c11': float,
        'c12': float,
        'c44': float,
        'c111': float,
        'c112': float,
        'c123': float,
        'c144': float,
        'c166': float,
        'c456': float,
        'str_t001': float,
        'str_t110': float,
        'str_t111': float,
        'str_s001': float,
        'str_s110': float,
        'str_s111': float,
        'str_s211': float,
        't001': float,
        't110': float,
        't111': float,
        's001': float,
        's110': float,
        's111': float,
        's211': float,
        'ut001': float,
        'ut110': float,
        'ut111': float,
        'ur001': float,
        'ur110': float,
        'ur111': float,
        'elastr001': float,
        'elastr110': float,
        'elastr111': float,
        'plastr001': float,
        'plastr110': float,
        'plastr111': float,
        'frac001': float,
        'frac110': float,
        'frac111': float,
        'plaenede001': float,
        'plaenede110': float,
        'plaenede111': float,
        'crack001': float,
        'crack110': float,
        'crack111': float,
        'G110': float,
        'G111': float,
        'Gv': float,
        'B': float,
        'Ev': float,
        'G_over_B': float,
        # 'material_id': str,
        })
    def __init__(self,
        formula,
        temperature,
        VEC,
        c11,
        c12,
        c44,
        c111,
        c112,
        c123,
        c144,
        c166,
        c456,
        str_t001,
        str_t110,
        str_t111,
        str_s001,
        str_s110,
        str_s111,
        str_s211,
        t001,
        t110,
        t111,
        s001,
        s110,
        s111,
        s211,
        ut001,
        ut110,
        ut111,
        ur001,
        ur110,
        ur111,
        elastr001,
        elastr110,
        elastr111,
        plastr001,
        plastr110,
        plastr111,
        frac001,
        frac110,
        frac111,
        plaenede001,
        plaenede110,
        plaenede111,
        crack001,
        crack110,
        crack111,
        G110,
        G111,
        Gv,
        B,
        Ev,
        G_over_B,
        # material_id,
            ):
        self.formula = formula
        self.temperature = temperature
        self.VEC = VEC
        self.c11 = c11
        self.c12 = c12
        self.c44 = c44
        self.c111 = c111
        self.c112 = c112
        self.c123 = c123
        self.c144 = c144
        self.c166 = c166
        self.c456 = c456
        self.str_t001 = str_t001
        self.str_t110 = str_t110
        self.str_t111 = str_t111
        self.str_s001 = str_s001
        self.str_s110 = str_s110
        self.str_s111 = str_s111
        self.str_s211 = str_s211
        self.t001 = t001
        self.t110 = t110
        self.t111 = t111
        self.s001 = s001
        self.s110 = s110
        self.s111 = s111
        self.s211 = s211
        self.ut001 = ut001
        self.ut110 = ut110
        self.ut111 = ut111
        self.ur001 = ur001
        self.ur110 = ur110
        self.ur111 = ur111
        self.elastr001 = elastr001
        self.elastr110 = elastr110
        self.elastr111 = elastr111
        self.plastr001 = plastr001
        self.plastr110 = plastr110
        self.plastr111 = plastr111
        self.frac001 = frac001
        self.frac110 = frac110
        self.frac111 = frac111
        self.plaenede001 = plaenede001
        self.plaenede110 = plaenede110
        self.plaenede111 = plaenede111
        self.crack001 = crack001
        self.crack110 = crack110
        self.crack111 = crack111
        self.G110 = G110
        self.G111 = G111
        self.Gv = Gv
        self.B = B
        self.Ev = Ev
        self.G_over_B = G_over_B
        # self.material_id = material_id
