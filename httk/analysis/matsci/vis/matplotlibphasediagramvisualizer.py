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

from pylab import *
from httk.graphics.matplotlib.polygonplot import PolygonPlot
from httk.graphics.matplotlib.arrowplot import arrowplot
from httk.core import FracVector


class MatplotlibPhaseDiagramVisualizer(object):

    def __init__(self, phasediagram):
        self.phasediagram = phasediagram
         
    def show(self, showunstable=True, labelunstable=False, avoid_overlap=True):
        print "Warning: graphical phase diagrams currently does not fill in *all* dividing lines."
        
        pd = self.phasediagram
        pp = PolygonPlot(labels=pd.coord_system, sides=len(pd.coord_system), label_offset=0.15)
                
        coords, ids = pd.hull_point_coords()
        coords = FracVector.use(coords).to_floats()        

        coords2, ids2 = pd.interior_point_coords()
        coords2 = FracVector.use(coords2).to_floats()                
        newdata2 = pp.translate_coords(coords2)

        allcoords, allids = pd.coords()
        allcoords = FracVector.use(allcoords).to_floats()                
        alldata = pp.translate_coords(allcoords)

        if showunstable and len(newdata2) > 0:
            pp.ax.scatter(newdata2[:, 0], newdata2[:, 1], s=50, color='purple', marker='o', facecolor='none')
        
        newdata = pp.translate_coords(coords)
        
        pp.ax.scatter(newdata[:, 0], newdata[:, 1], s=100, marker='o')

        labelpos = []        
        for i, txt in enumerate(ids):
            labelpos += [[newdata[i, 0], newdata[i, 1], newdata[i, 0]+0.04, newdata[i, 1]+0.01, txt, {'color': 'blue'}]]

        if showunstable and labelunstable:
            for i, txt in enumerate(ids2):
                labelpos += [[newdata2[i, 0], newdata2[i, 1], newdata2[i, 0]+0.04, newdata2[i, 1]+0.01, txt, {'color': 'purple'}]]

        # TODO: Replace with true spring framework instead
        if avoid_overlap:
            xoffset = 0.00
            yoffset = 0.02
            overlap = True
            maxiters = 100
            while overlap and maxiters > 0:
                overlap = False
                for i in range(len(labelpos)):
                    pos1 = labelpos[i]
                    if sqrt((pos1[0]-pos1[2])**2 + (pos1[1]-pos1[3])**2) < 0.02:
                        labelpos[i] = [pos1[0], pos1[1], pos1[2]+xoffset*(random.choice([+1, -1])), pos1[3]+yoffset*(random.choice([+1, -1]))]+pos1[4:]
                        overlap = True      
                        #print "OVERLAP1",i            
                    for j in range(i+1, len(labelpos)):
                        if (i == j):
                            continue
                        pos1 = labelpos[i]
                        pos2 = labelpos[j]
                        if sqrt((pos1[0]-pos1[2])**2 + (pos1[1]-pos1[3])**2) < 0.02:
                            labelpos[i] = [pos1[0], pos1[1], pos1[2]+xoffset*(random.choice([+1, -1])), pos1[3]+yoffset*(random.choice([+1, -1]))]+pos1[4:]
                            #labelpos[j] = [pos2[0],pos2[1],pos2[2]+xoffset*(random.choice([+1, -1])),pos2[3]+yoffset*(random.choice([+1, -1]))]+pos2[4:]
                            overlap = True
                            #print "OVERLAP2",i,j,abs(sqrt(pos1[2]**2 + pos1[3]**2) - sqrt(pos2[2]**2 + pos2[3]**2))      
                            print pos1
                            print pos2

                #print maxiters, labelpos
                maxiters -= 1

        for i, pos in enumerate(labelpos):
            if abs(sqrt(pos[0]**2 + pos[1]**2) - sqrt(pos[2]**2 + pos[3]**2)) > 0.04:
                pp.ax.annotate(pos[4],
                               xy=(pos[0], pos[1]), xycoords='data',
                               xytext=(pos[2], pos[3]), textcoords='data',
                               arrowprops=dict(arrowstyle="->",
                                               connectionstyle="arc3"), **pos[5])
                #pp.ax.annotate(pos[2], (pos[0],pos[1]))
            else:
                pp.ax.annotate(pos[4], (pos[2], pos[3]), **pos[5])

        lines = pd.interior_competing_phase_lines()
        for line in lines:
            arrowplot(pp.ax, [alldata[line[0]][0], alldata[line[1]][0]], [alldata[line[0]][1], alldata[line[1]][1]], c='purple')
            #pp.ax.plot([alldata[line[0]][0],alldata[line[1]][0]],[alldata[line[0]][1],alldata[line[1]][1]],'-',color='purple')
        
#         lines = pd.hull_to_interior_competing_phase_lines()
#         for line in lines:
#             arrowplot(pp.ax,[alldata[line[0]][0],alldata[line[1]][0]],[alldata[line[0]][1],alldata[line[1]][1]],c='blue')
#             #pp.ax.plot([alldata[line[0]][0],alldata[line[1]][0]],[alldata[line[0]][1],alldata[line[1]][1]],'b-')

#         lines = pd.hull_competing_phase_lines()
#         for line in lines:
#             #print "LINE",line[0],"->",line[1]
#             #arrowplot(pp.ax,[newdata[line[0]][0],newdata[line[1]][0]],[newdata[line[0]][1],newdata[line[1]][1]],c='black')            
#             pp.ax.plot([newdata[line[0]][0],newdata[line[1]][0]],[newdata[line[0]][1],newdata[line[1]][1]],'k-')

        lines = pd.phase_lines
        for line in lines:
            #print "LINE",line[0],"->",line[1]
            #arrowplot(pp.ax,[newdata[line[0]][0],newdata[line[1]][0]],[newdata[line[0]][1],newdata[line[1]][1]],c='black')            
            pp.ax.plot([newdata[line[0]][0], newdata[line[1]][0]], [newdata[line[0]][1], newdata[line[1]][1]], 'k-')

        show()

__all__ = ['MatplotlibPhaseDiagramVisualizer']        
