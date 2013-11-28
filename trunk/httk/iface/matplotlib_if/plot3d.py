# 
#    The high-throughput toolkit (httk)
#    Copyright (C) 2012-2013 Rickard Armiento
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

from numpy import *
from numpy.linalg import norm
from matsci.math import hull
import pylab

def show():
    pylab.show()

def plotatoms(plot,xs,zs,sites,polysites,basis):
    copyxs = {}

    for i in range(0,len(zs)):
        for a in [0,-1,1]:
            for b in [0,-1,1]:
                for c in [0,-1,1]:
                    translated = xs[i] + dot(array((a,b,c)),basis)
                    if copyxs.has_key(zs[i]):
                        copyxs[zs[i]] = vstack((copyxs[zs[i]],translated))
                    else:
                        copyxs[zs[i]] = translated
                    
    for z,coord in copyxs.iteritems():
        if z in polysites:                        
            plot.ax.scatter3D(coord[:,0],coord[:,1],coord[:,2], color='r')
        else:
            plot.ax.scatter3D(coord[:,0],coord[:,1],coord[:,2], color='k')
        
    pylab.draw()

def plothull_home(plot,hull,home,color):
   
    vectors = hull.vertices
    plot.ax.scatter3D([home[0]],[home[1]],[home[2]], color,s=100)

    for vector1 in vectors:
        plot.ax.plot([home[0],vector1[0]], [home[1],vector1[1]], [home[2],vector1[2]],color=color)
        for vector2 in vectors:
            plot.ax.plot([vector1[0],vector2[0]], [vector1[1],vector2[1]], [vector1[2],vector2[2]],color=color)

    pylab.draw()

def plotvertex(plot,hullx,index,color,eps=1e-6):   
    for i in range(len(hullx.vertices)):
        if i == index:
            continue
        # find midpoint between these two points
        midpoint = (hullx.vertices[index] + hullx.vertices[i])*0.5
        if not hull.inside(hullx,midpoint,open=True,eps=eps):
            plot.ax.plot([hullx.vertices[index][0],hullx.vertices[i][0]], [hullx.vertices[index][1],hullx.vertices[i][1]], [hullx.vertices[index][2],hullx.vertices[i][2]],color=color)

def plothull(plot,hull,color):   
    vectors = hull.vertices
    for vector1 in vectors:
        for vector2 in vectors:
            plot.ax.plot([vector1[0],vector2[0]], [vector1[1],vector2[1]], [vector1[2],vector2[2]],color=color)

    pylab.draw()

def plotvects(plot,vectors,color):
    for vector1 in vectors:
        for vector2 in vectors:
            plot.ax.plot([vector1[0],vector2[0]], [vector1[1],vector2[1]], [vector1[2],vector2[2]],color=color)
    pylab.draw()

def plotjustvects(plot,vectors,color):
    for i in range(len(vectors)-1):
            plot.ax.plot([vectors[i][0],vectors[i+1][0]], [vectors[i][1],vectors[i+1][1]], [vectors[i][2],vectors[i+1][2]],color=color)
    pylab.draw()

def plotatom(plot,home,color):   
    plot.ax.scatter3D([home[0]],[home[1]],[home[2]], color=color,s=100)
    pylab.draw()
    

