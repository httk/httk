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
#
# Uses parts from 'dave', http://stackoverflow.com/questions/701429/library-tool-for-drawing-ternary-triangle-plots

from pylab import *


class PolygonPlot(object):
    
    def __init__(self, start_angle=90, rotate_labels=False, labels=('one', 'two', 'three'), sides=3, 
                 label_offset=0.10, edge_args={'color': 'black', 'linewidth': 2}, fig_args = {'figsize': (8, 8), 'facecolor': 'white', 'edgecolor': 'white'},
                 text_args = {'fontsize': 24, 'color': 'black'}):
        """
        start_angle (90): Direction of first vertex.
        rotate_labels (False): Orient labels perpendicular to vertices.
        labels ('one','two','three'): Labels for vertices.
        sides (3): Number of dimensions to accommodate
        label_offset (0.10): Offset for label from vertex (percent of distance from origin).
        edge_args ({'color':'black','linewidth':2}): matplotlib keyword args for plots.
        fig_args ({'figsize':(8,8),'facecolor':'white','edgecolor':'white'}): matplotlib keyword args for figures.
        text_args: matplotlib keyword args for axis labels.

        """
        self.basis = array(
            [
                [
                    cos(2*_*pi/sides + start_angle*pi/180),
                    sin(2*_*pi/sides + start_angle*pi/180)
                ] 
                for _ in range(sides)
            ]
        )

        fig = figure(**fig_args)
        ax = fig.add_subplot(111)
    
        for i, l in enumerate(labels):
            if i >= sides:
                break
            x = self.basis[i, 0]
            y = self.basis[i, 1]
            if rotate_labels:
                angle = 180*arctan(y/x)/pi + 90
                if angle > 90 and angle <= 270:
                    angle = mod(angle + 180, 360)
            else:
                angle = 0
            ax.text(
                x*(1 + label_offset),
                y*(1 + label_offset),
                l,
                horizontalalignment='center',
                verticalalignment='center',
                rotation=angle,
                **text_args
            )
    
        # Clear normal matplotlib axes graphics.
        ax.set_xticks(())
        ax.set_yticks(())
        ax.set_frame_on(False)
    
        # Plot border
        ax.plot(
            [self.basis[_, 0] for _ in range(sides) + [0, ]],
            [self.basis[_, 1] for _ in range(sides) + [0, ]],
            **edge_args
        )
        self.ax = ax
        
    def translate_coords(self, data, scaling=True):
        if len(data) == 0:
            return data
        
        data = array(data)        
        
        # If data is Nxsides, newdata is Nx2.
        if scaling:
            # Scales data for you.
            newdata = dot((data.T / data.sum(-1)).T, self.basis)
        else:
            # Assumes data already sums to 1.
            newdata = dot(data, self.basis)
        return newdata

__all__ = ['PolygonPlot']

if __name__ == '__main__':
    k = 0.5
    s = 1000

    data = vstack((
        array([k, 0, 0]) + rand(s, 3), 
        array([0, k, 0]) + rand(s, 3), 
        array([0, 0, k]) + rand(s, 3)
    ))
    color = array([[1, 0, 0]]*s + [[0, 1, 0]]*s + [[0, 0, 1]]*s)

    pp = PolygonPlot()

    newdata = pp.translate_coords(data)

    pp.ax.scatter(
        newdata[:, 0],
        newdata[:, 1],
        s=2,
        alpha=0.5,
        color=color
    )
    show()
