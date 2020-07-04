#!/usr/bin/env python
# This is an example program using the High-Throughput toolkit (httk)
"""
This is a simple program that just shows some basic functionality using the httk FracVector and MutableFracVector objects
"""

from httk import *

a = FracVector.create([[2, 3, 5], [3, 5, 4], [4, 6, 7]])

b = MutableFracVector.create(a)

print(a)
print(b)

print("MAX in row [1]: "+str(max(a[1])))

print("MAX in all of a "+str(a.max()))

print(b.__class__)
b[2, 1:] = [4711, 23]

print(a)
print(b)

b[0, 0] = 0.254
print(b)
print(b.inv())

c = FracVector.create([[2.5, 3.5, 5.5], [3.5, 5.5, 4.5], [4.5, 6.5, 7.5]])
print(c)


