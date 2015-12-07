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
# Uses parts from 'Pedro M Duarte',
# http://stackoverflow.com/questions/8247973/how-do-i-specify-an-arrow-like-linestyle-in-matplotlib

import numpy as np
import matplotlib.pyplot as plt


def arrowplot(axes, x, y, narrs=10, dspace=0.5, aspace=0.1, direc='pos',
              hl=0.025, hw=2.5, c='black'):
    ''' narrs  :  Number of arrows that will be drawn along the curve

        dspace :  Shift the position of the arrows along the curve.
                  Should be between 0. and 1.

        direc  :  can be 'pos' or 'neg' to select direction of the arrows

        hl     :  length of the arrow head

        hw     :  width of the arrow head

        c      :  color of the edge and face of the arrow head
    '''

    x = np.array(x)[::-1]
    y = np.array(y)[::-1]

    # r is the distance spanned between pairs of points
    r = [0]
    for i in range(1, len(x)):
        dx = x[i]-x[i-1]
        dy = y[i]-y[i-1]
        r.append(np.sqrt(dx*dx+dy*dy))
    r = np.array(r)

    # rtot is a cumulative sum of r, it's used to save time
    rtot = []
    for i in range(len(r)):
        rtot.append(r[0:i].sum())
    rtot.append(r.sum())

    # based on narrs set the arrow spacing
    #aspace = r.sum() / narrs
    narrs = r.sum()/aspace

    if direc is 'neg':
        dspace = -1.*abs(dspace)
    else:
        dspace = abs(dspace)

    arrowData = []  # will hold tuples of x,y,theta for each arrow
    arrowPos = aspace*(dspace)  # current point on walk along data
                                 # could set arrowPos to 0 if you want
                                 # an arrow at the beginning of the curve

    ndrawn = 0
    rcount = 1
    while arrowPos < r.sum() and ndrawn < narrs:
        x1, x2 = x[rcount-1], x[rcount]
        y1, y2 = y[rcount-1], y[rcount]
        da = arrowPos-rtot[rcount]
        theta = np.arctan2((x2-x1), (y2-y1))
        ax = np.sin(theta)*da+x1
        ay = np.cos(theta)*da+y1
        arrowData.append((ax, ay, theta))
        ndrawn += 1
        arrowPos += aspace
        while arrowPos > rtot[rcount+1]:
            rcount += 1
            if arrowPos > rtot[-1]:
                break

    # could be done in above block if you want
    for ax, ay, theta in arrowData:
        # use aspace as a guide for size and length of things
        # scaling factors were chosen by experimenting a bit

        dx0 = np.sin(theta)*hl/2. + ax
        dy0 = np.cos(theta)*hl/2. + ay
        dx1 = -1.*np.sin(theta)*hl/2. + ax
        dy1 = -1.*np.cos(theta)*hl/2. + ay

        if direc is 'neg':
            ax0 = dx0
            ay0 = dy0
            ax1 = dx1
            ay1 = dy1
        else:
            ax0 = dx1
            ay0 = dy1
            ax1 = dx0
            ay1 = dy0

        axes.annotate('', xy=(ax0, ay0), xycoords='data',
                      xytext=(ax1, ay1), textcoords='data',
                      arrowprops=dict(headwidth=hw, frac=1., ec=c, fc=c))

    axes.plot(x, y, color=c)
    #axes.set_xlim(x.min()*.9,x.max()*1.1)
    #axes.set_ylim(y.min()*.9,y.max()*1.1)


if __name__ == '__main__':
    fig = plt.figure()
    axes = fig.add_subplot(111)

    # my random data
    scale = 10
    np.random.seed(101)
    #x = np.random.random(10)*scale
    #y = np.random.random(10)*scale
    x = [0, 1]
    y = [0, 1]
    arrowplot(axes, x, y)

    plt.show()
