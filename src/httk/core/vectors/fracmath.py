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

import sys, fractions
from functools import reduce

PY3 = sys.version_info[0] == 3

default_accuracy = fractions.Fraction(1, 10000000000)


def is_string(arg):
    if PY3:
        return isinstance(arg, str)
    else:
        return isinstance(arg, basestring) # noqa: F821


# Euler's algorithm, code from https://code.google.com/p/mpmath/issues/detail?id=55
def get_continued_fraction(p, q):
    while q:
        n = p // q
        yield n
        q, p = p - q*n, q


#https://en.wikipedia.org/wiki/Continued_fraction#Best_rational_within_an_interval
def best_rational_in_interval(low, high):
    low = fractions.Fraction(low)
    lowcf = get_continued_fraction(low.numerator, low.denominator)
    high = fractions.Fraction(high)
    highcf = get_continued_fraction(high.numerator, high.denominator)
    cf = []
    while True:
        try:
            nextlow = next(lowcf)
        except StopIteration:
            nextlow = None
        try:
            nexthigh = next(highcf)
        except StopIteration:
            nexthigh = None
        if nextlow is None or nexthigh is None or nextlow != nexthigh:
            break
        cf += [nextlow]
    if nexthigh is not None and nextlow is not None:
        cf += [min(nexthigh, nextlow)+1]
    return fraction_from_continued_fraction(cf)


#http://stackoverflow.com/questions/14493901/continued-fraction-to-fraction-malfunction
def fraction_from_continued_fraction(cf):
    return cf[0] + reduce(lambda d, n: 1 / (d + n), cf[:0:-1], fractions.Fraction(0))


def string_to_val_and_delta(arg, min_accuracy=fractions.Fraction(1, 10000)):
    arg = arg.upper()

    if arg.find('/') >= 0:
        return fractions.Fraction(arg), fractions.Fraction(0)

    sd_start = arg.find('(')
    if sd_start >= 0:
        infered_delta = False
        sd_end = arg.find(')')
        val = arg[:sd_start]
        m, _e, _exp = val.partition('E')
        sd = arg[sd_start+1:sd_end]
    elif min_accuracy is not None:
        infered_delta = True
        val = arg
        m, _e, _exp = val.partition('E')
        if arg.find('.') >= 0:
            m = m + "0"
        else:
            m = m + ".0"
        sd = "5"
    else:
        return fractions.Fraction(arg), fractions.Fraction(0)
    numdigits = reduce(lambda y, x: y+1 if x.isdigit() else y, m, 0)
    replacelist = list('0'*(numdigits-len(sd)) + sd)
    delta = fractions.Fraction(''.join(replacelist.pop(0) if c.isdigit() else c for c in m))
    if infered_delta and delta > min_accuracy:
        delta = min_accuracy
    val = fractions.Fraction(val)
    return val, delta


def any_to_fraction(arg, min_accuracy=fractions.Fraction(1, 10000)):
    """
    min_accuracy: we always assume the accuracy is at least this good. i.e., with min_accuracy=1/10000, we take
    0.33 to really mean 0.3300, because we assume people meaning 1/3 at least makes the effort to write 0.3333
    """
    if is_string(arg):
        val, delta = string_to_val_and_delta(arg, min_accuracy=min_accuracy)
        if delta == 0:
            return fractions.Fraction(val)
        else:
            return best_rational_in_interval(val-delta, val+delta)
    else:
        try:
            return fractions.Fraction(arg)
        except Exception:
            print("any_to_fraction tried to convert this argument and failed:", arg)
            raise


def integer_sqrt(n):
    x = n
    y = (x + 1) // 2
    while y < x:
        x = y
        y = (x + n // x) // 2
    return x


# sqrt from Python decimal
def frac_sqrt_old(x, prec=default_accuracy, limit=True):
    iterprec = int(100/prec)

    # Check if there is an exact solution, in that case, make sure to return it
    sqrtnom = integer_sqrt(x.numerator)
    sqrtdenom = integer_sqrt(x.denominator)
    s = fractions.Fraction(sqrtnom, sqrtdenom)
    if s*s == x:
        return s

    # This actually accelerates convergence for 'large' numbers
    if x > 2:
        s = fractions.Fraction(integer_sqrt(x))
    #This does not, if s is initialized to int_sqrt(num)/int_sqrt(denum)
    #else:
    #    s = (x+1)/2

    while True:
        lasts = s
        s = (s + x/s)/2
        if abs(s-lasts) <= prec:
            break
        s = s.limit_denominator(iterprec)
        #print(s)
    if limit:
        s = s.limit_denominator(1/prec)
    return s

def frac_sqrt(x, prec=default_accuracy, limit=True):
    # Check if there is an exact solution, in that case, make sure to return it
    sqrtnom = integer_sqrt(x.numerator)
    sqrtdenom = integer_sqrt(x.denominator)
    s = fractions.Fraction(sqrtnom, sqrtdenom)
    if s*s == x:
        return s

    # This actually accelerates convergence for 'large' numbers
    if x > 2:
        s = fractions.Fraction(integer_sqrt(x))
    #This does not, if s is initialized to int_sqrt(num)/int_sqrt(denum)
    #else:
    #    s = (x+1)/2

    denom = int(100/prec)
    sn = (s.numerator * denom) // s.denominator
    xn = (x.numerator * denom) // x.denominator

    while True:
        lastsn = sn
        sn = (sn*sn + xn*denom) // (2*sn)
        if abs(sn-lastsn) < prec*denom:
            break

    s = fractions.Fraction(sn,denom)

    if limit:
        s = s.limit_denominator(1/prec)
    return s



#pi, exp, cos, sin adapted from python documentation examples:
#https://docs.python.org/2/library/decimal.html
def frac_cos(x, prec=default_accuracy, limit=True, degrees=False):
    if degrees:
        x *= frac_pi(prec=prec, limit=True)/180
    if abs(x) > 4:
        twopi = 2*frac_pi(prec=prec, limit=True)
        fac = (x/twopi).__trunc__()
        x -= fac*twopi

    denom = int(100/prec)
    x2 = x**2
    x2n = (x2.numerator * denom) // x2.denominator
    i, sn, fact, numn, sign = 0, denom, 1, denom, 1
    while True:
        i += 2
        fact *= i * (i-1)
        numn = (numn * x2n) // denom
        sign *= -1
        deltan = numn * sign
        deltad = fact
        sn = (sn*deltad + deltan) // deltad

        if abs(deltan) < prec*denom*deltad:
            break

    s = fractions.Fraction(sn,denom)

    if limit:
        s = s.limit_denominator(1/prec)
    return s


def frac_sin(x, prec=default_accuracy, limit=True, degrees=False):
    if degrees:
        x *= frac_pi(prec=prec)/180
    if abs(x) > 4:
        twopi = 2*frac_pi(prec=prec)
        fac = (x/twopi).__trunc__()
        x -= fac*twopi

    denom = int(100/prec)
    denom2 = denom**2
    xn = (x.numerator * denom) // x.denominator
    xn2 = xn**2
    i, deltan, deltad, sn, fact, numn, sign = 1, denom, 1, xn, 1, xn, 1
    while abs(deltan) > prec*deltad*denom:
        i += 2
        fact *= i * (i-1)
        numn = (numn * xn2) // denom2
        sign *= -1
        deltan = numn * sign
        deltad = fact
        sn = (sn*deltad + deltan) // deltad

    s = fractions.Fraction(sn,denom)

    if limit:
        s = s.limit_denominator(1/prec)
    return s

def frac_sin_old(x, prec=default_accuracy, limit=True, degrees=False):
    if degrees:
        x *= frac_pi(prec=prec)/180
    if abs(x) > 4:
        twopi = 2*frac_pi(prec=prec)
        fac = (x/twopi).__trunc__()
        x -= fac*twopi
    i, lasts, s, fact, num, sign = 1, 0, x, 1, x, 1
    while abs(s-lasts) > prec:
        lasts = s
        i += 2
        fact *= i * (i-1)
        num *= x * x
        sign *= -1
        s += num / fact * sign
    if limit:
        s = s.limit_denominator(1/prec)
    return s


def frac_exp_old(x, prec=default_accuracy, limit=True):
    """Return e raised to the power of x.
    """
    i, lasts, s, fact, num = 0, 0, 1, 1, 1
    while abs(s-lasts) > prec:
        lasts = s
        i += 1
        fact *= i
        num *= x
        s += num / fact
    if limit:
        s = s.limit_denominator(1/prec)
    return s

def frac_exp(x, prec=default_accuracy, limit=True):
    """Return e raised to the power of x.
    """
    denom = int(100/prec)
    xn = (x.numerator * denom) // x.denominator

    deltan, deltad = denom, 1
    i, sn, fact, numn = 0, denom, 1, denom
    while abs(deltan) > prec*deltad*denom:
        i += 1
        fact *= i
        numn = (numn * xn) // denom
        deltan = numn
        deltad = fact
        sn = (sn*deltad + deltan) // deltad

    s = fractions.Fraction(sn,denom)

    if limit:
        s = s.limit_denominator(1/prec)
    return s



def frac_pi_old(prec=default_accuracy, limit=True):
    """Compute Pi to the precision prec.
    """
    if prec >= fractions.Fraction(1, 10000000000000):
        s = fractions.Fraction(1812775448643948950904740389629316518445900010127,577024346734625462205756697620397878260206571339)
    else:
        three = fractions.Fraction(3)      # substitute "three=3.0" for regular floats
        lasts, t, s, n, na, d, da = 0, three, 3, 1, 0, 0, 24
        while abs(s-lasts) > prec:
            lasts = s
            n, na = n+na, na+8
            d, da = d+da, da+32
            t = (t * n) / d
            s += t
    if limit:
        s = s.limit_denominator(1/prec)
    return s

def frac_pi(prec=default_accuracy, limit=True):
    """Compute Pi to the precision prec.
    """
    if prec >= fractions.Fraction(1, 10000000000000):
        return fractions.Fraction(1812775448643948950904740389629316518445900010127,577024346734625462205756697620397878260206571339)

    denom = int(100/prec)
    deltan, deltad, tn, sn, n, na, d, da = denom, 1, 3*denom, 3*denom, 1, 0, 0, 24

    while abs(deltan) > prec*deltad*denom:
        n, na = n+na, na+8
        d, da = d+da, da+32
        deltan = tn*n
        deltad = d
        tn = (tn * n) // d
        sn = (sn*deltad + deltan) // deltad

    s = fractions.Fraction(sn,denom)

    if limit:
        s = s.limit_denominator(1/prec)
    return s

#The below functions have been adapted from Brian Beck and Christopher Hesse's dmath v0.9.1
#All modifications done are copyright (c) Rickard Armiento and licensed
#under GNU Affero General Public License as part of the rest of httk.
#
#The original source is copyright and was licensed as below:
#
#Copyright (c) 2006 Brian Beck <exogen@gmail.com>,
#                   Christopher Hesse <christopher.hesse@gmail.com>
#
#Permission is hereby granted, free of charge, to any person obtaining a copy of
#this software and associated documentation files (the "Software"), to deal in
#the Software without restriction, including without limitation the rights to
#use, copy, modify, merge, publish, distribute, sublicense, and/or sell copies
#of the Software, and to permit persons to whom the Software is furnished to do
#so, subject to the following conditions:
#
#The above copyright notice and this permission notice shall be included in all
#copies or substantial portions of the Software.
#
#THE SOFTWARE IS PROVIDED "AS IS", WITHOUT WARRANTY OF ANY KIND, EXPRESS OR
#IMPLIED, INCLUDING BUT NOT LIMITED TO THE WARRANTIES OF MERCHANTABILITY,
#FITNESS FOR A PARTICULAR PURPOSE AND NONINFRINGEMENT. IN NO EVENT SHALL THE
#AUTHORS OR COPYRIGHT HOLDERS BE LIABLE FOR ANY CLAIM, DAMAGES OR OTHER
#LIABILITY, WHETHER IN AN ACTION OF CONTRACT, TORT OR OTHERWISE, ARISING FROM,
#OUT OF OR IN CONNECTION WITH THE SOFTWARE OR THE USE OR OTHER DEALINGS IN THE
#SOFTWARE.

import math


def frac_log_old(x, base=None, prec=default_accuracy, limit=True):
    """Return the logarithm of x to the given base.

    If the base not specified, return the natural logarithm (base e) of x.

    """
    if x < 0:
        raise ValueError("frac_log: logarithm of negative number.")
    elif base == 1:
        raise ValueError("frac_log: logarithm of base 1 not valid.")
    elif x == base:
        return fractions.Fraction(1)
    elif x == 0:
        raise ValueError("frac_log: logarithm of zero.")

    if base is None:
        log_base = 1
    else:
        log_base = frac_log(base, prec=prec, limit=limit)

    lasts, s = 0, fractions.Fraction(1)
    while abs(s-lasts) > prec:
        lasts = s
        s -= 1 - x / frac_exp(s)
    s /= log_base
    if limit:
        s = s.limit_denominator(1/prec)
    return s


def frac_log(x, base=None, prec=default_accuracy, limit=True):
    """Return the logarithm of x to the given base.

    If the base not specified, return the natural logarithm (base e) of x.

    TODO: Fix: this fails for moderately large arguments.
    """
    if x < 0:
        raise ValueError("frac_log: logarithm of negative number.")
    elif base == 1:
        raise ValueError("frac_log: logarithm of base 1 not valid.")
    elif x == base:
        return fractions.Fraction(1)
    elif x == 0:
        raise ValueError("frac_log: logarithm of zero.")

    if base is None:
        log_base = 1
    else:
        log_base = frac_log(base, prec=prec, limit=limit)

    if x > 1:
        inv = True
        x = 1/x
    else:
        inv = False

    # Tests give that we need more accuracy margin for this one
    prec = prec/1000
    denom = int(100/prec)
    xn = (x.numerator * denom) // x.denominator

    deltan, deltad = denom, 1
    sn = denom

    def frac_inner_exp(xn):
        deltan, deltad = denom, 1
        i, sn, fact, numn = 0, denom, 1, denom
        while abs(deltan) > prec*deltad*denom:
            i += 1
            fact *= i
            numn = (numn * xn) // denom
            deltan = numn
            deltad = fact
            sn = (sn*deltad + deltan) // deltad
        return sn

    while True:
        en = frac_inner_exp(sn)
        deltan = (en - xn)*denom
        deltad = en
        sn = (sn*deltad - deltan) // deltad
        if (abs(deltan) < abs(prec*deltad*denom)):
            break

    #print(float(fractions.Fraction(sn,denom)),math.log(x))
    #exit(0)

    if inv:
        s = fractions.Fraction(-sn,denom)
    else:
        s = fractions.Fraction(sn,denom)
    s /= log_base

    if limit:
        s = s.limit_denominator(1/prec)
    return s


def frac_log10(x, prec=default_accuracy, limit=True):
    """Return the base 10 logarithm of x."""
    return frac_log(x, base=10, prec=prec, limit=limit)


def frac_tan(x, degrees=False, prec=default_accuracy, limit=True):
    """Return the tangent of x."""
    s = frac_sin(x, prec=prec, limit=False) / frac_cos(x, prec=prec, limit=False)
    if limit:
        s = s.limit_denominator(1/prec)
    return s


def frac_asin(x, degrees=False, prec=default_accuracy, limit=True):
    """Return the arc sine (measured in radians) of Decimal x."""
    iteracc = 1/(prec*100)
    if abs(x) > 1:
        raise ValueError("Domain error: asin accepts -1 <= x <= 1")

    if degrees:
        if x == -1:
            return fractions.Fraction(180, -2)
        elif x == 0:
            return 0
        elif x == 1:
            return fractions.Fraction(180, 2)
    else:
        if x == -1:
            return frac_pi(prec=prec, limit=limit) / -2
        elif x == 0:
            return fractions.Fraction(0)
        elif x == 1:
            return frac_pi(prec=prec, limit=limit) / 2

    one_half = fractions.Fraction(1, 2)
    i, lasts, s, gamma, fact, num = fractions.Fraction(0), 0, x, 1, 1, x
    while abs(s-lasts) > prec:
        lasts = s
        i += 1
        fact *= i
        num *= x * x
        gamma *= i - one_half
        coeff = gamma / ((2 * i + 1) * fact)
        s += coeff * num
        # The sizes of these numbers need to be kept under control during iteration
        num = num.limit_denominator(iteracc)
        s = s.limit_denominator(iteracc)
    if degrees:
        s = s*180/frac_pi(prec=prec, limit=limit)
    if limit:
        s = s.limit_denominator(1/prec)
    return s


# Alternative implementation
# def frac_asin(x, degrees=False, prec=default_accuracy, limit=True):
#     """Return the arcsine of x in radians."""
#     if abs(x) > 1:
#         raise ValueError("frac_asin: Domain error: asin accepts -1 <= x <= 1")
#
#     if degrees:
#         if x == -1:
#             return fractions.Fraction(180, -2)
#         elif x == 0:
#             return 0
#         elif x == 1:
#             return fractions.Fraction(180, 2)
#      else:
#        if x == -1:
#            return frac_pi(prec=prec, limit=limit) / -2
#        elif x == 0:
#            return fractions.Fraction(0)
#        elif x == 1:
#            return frac_pi(prec=prec, limit=limit) / 2
#
#    return atan2(x, D.sqrt(1 - x ** 2), frac = frac, limit=limit)


def frac_acos_old(x, degrees=False, prec=default_accuracy, limit=True):
    """Return the arc cosine (measured in radians) of Decimal x."""
    iteracc = 1/(prec*100)
    if abs(x) > 1:
        raise ValueError("Domain error: acos accepts -1 <= x <= 1")

    if x == -1:
        return frac_pi(prec=prec, limit=limit)
    elif x == 0:
        return frac_pi(prec=prec, limit=limit) / 2
    elif x == 1:
        return fractions.Fraction(0)

    half = fractions.Fraction(1, 2)
    i, lasts, s, gamma, fact, num = fractions.Fraction(0), 0, frac_pi(prec=prec, limit=False) / 2 - x, 1, 1, x
    while abs(s-lasts) > prec:
        lasts = s
        i += 1
        fact *= i
        num *= x * x
        gamma *= i - half
        coeff = gamma / ((2 * i + 1) * fact)
        s -= coeff * num
        # The sizes of these numbers need to be kept under control during iteration
        num = num.limit_denominator(iteracc)
        s = s.limit_denominator(iteracc)
    if degrees:
        s = s*180/frac_pi(prec=prec, limit=limit)
    if limit:
        s = s.limit_denominator(1/prec)

    return s

def frac_acos_alt(x, degrees=False, prec=default_accuracy, limit=True):
    """Return the arc cosine (measured in radians) of Decimal x."""
    if abs(x) > 1:
        raise ValueError("Domain error: acos accepts -1 <= x <= 1")

    if x == -1:
        return frac_pi(prec=prec, limit=limit)
    elif x == 0:
        return frac_pi(prec=prec, limit=limit) / 2
    elif x == 1:
        return fractions.Fraction(0)

    denom = int(100/(prec))

    denom2 = denom*denom
    s = frac_pi(prec=prec, limit=False) / 2 - x
    sn = (s.numerator * denom) // s.denominator
    xn = (x.numerator * denom) // x.denominator
    xn2 = xn * xn

    i, gamman, fact, numn, deltan = 0, denom, 1, xn, denom

    while abs(deltan) > prec*denom:
        i += 1
        fact *= 2*i
        numn = (numn * xn2)//denom2
        gamman = 2*i*gamman - gamman
        deltan = (gamman*numn) // ((2 * i + 1) * (fact*denom))
        sn -= deltan

    s = fractions.Fraction(sn,denom)

    if degrees:
        s = s*180/frac_pi(prec=prec, limit=limit)
    if limit:
        s = s.limit_denominator(1/prec)

    return s



# Alternative implementation
def frac_acos(x, degrees=False, prec=default_accuracy, limit=True):
    """Return the arccosine of x in radians."""
    if abs(x) > 1:
        raise ValueError("Domain error: acos accepts -1 <= x <= 1")
    PI = frac_pi(prec=prec, limit=False)

    if x == 1:
        return fractions.Fraction(0)
    else:
        if x == -1:
            return PI
        elif x == 0:
            return PI / 2

    s = PI / 2 - frac_atan2(x, frac_sqrt(1 - x ** 2, prec=prec, limit=limit), prec=prec, limit=limit)

    if degrees:
        s = s*180/PI
    if limit:
        s = s.limit_denominator(1/prec)
    return s

def frac_atan_old(x, degrees=False, prec=default_accuracy, limit=True):
    """Return the arctangent of x in radians."""
    iteracc = 1/(prec*100)

    c = None
    if x == 0:
        return fractions.Fraction(0)
    elif abs(x) > 1:
        PI = frac_pi(prec=prec, limit=False)
        if x < 0:
            c = -PI / 2
        else:
            c = PI / 2
        x = 1 / x

    x_squared = x ** 2
    y = x_squared / (1 + x_squared)
    y_over_x = y / x
    i, lasts, s, coeff, num = fractions.Fraction(0), 0, y_over_x, 1, y_over_x
    while abs(s-lasts) > prec:
        lasts = s
        i += 2
        coeff *= i / (i + 1)
        num *= y
        s += coeff * num
        # The sizes of these numbers need to be kept under control during iteration
        num = num.limit_denominator(iteracc)
        s = s.limit_denominator(iteracc)
    if c:
        s = c - s
    if degrees:
        s = s*180/frac_pi(prec=prec, limit=limit)
    if limit:
        s = s.limit_denominator(1/prec)
    return s


def frac_atan(x, degrees=False, prec=default_accuracy, limit=True):
    """Return the arctangent of x in radians."""

    c = None
    if x == 0:
        return fractions.Fraction(0)
    elif abs(x) > 1:
        PI = frac_pi(prec=prec, limit=False)
        if x < 0:
            c = -PI / 2
        else:
            c = PI / 2
        x = 1 / x

    denom = int(100/prec)

    x_squared = x**2
    y = x_squared / (1 + x_squared)
    yn = (y.numerator * denom) // y.denominator
    s = y / x
    sn = (s.numerator * denom) // s.denominator

    i = 0
    lasts = 0
    coeffn = 1
    coeffd = 1
    numn = sn
    deltan = denom

    while abs(deltan) > prec*denom:
        i += 2
        coeffn = coeffn * i
        coeffd = coeffd*(i + 1)
        numn = (numn * yn) // denom
        deltan = (coeffn * numn)//coeffd
        sn = sn + deltan

    s = fractions.Fraction(sn,denom)

    if c:
        s = c - s
    if degrees:
        s = s*180/frac_pi(prec=prec, limit=limit)
    if limit:
        s = s.limit_denominator(1/prec)
    return s



def frac_atan2(y, x, degrees=False, prec=default_accuracy, limit=True):
    """Return the arctangent of y/x in radians.

    Unlike atan(y/x), the signs of both x and y are considered.

    """
# TODO check the sign function make sure this still works
# decimal zero has a sign
    if x != 0:
        a = y and frac_atan(y / x, prec=prec, limit=limit) or fractions.Fraction(0)
        if x < 0:
            if y > 0:
                a += frac_pi(prec=prec, limit=limit)
            else:
                a -= frac_pi(prec=prec, limit=limit)
        return a

    if y != 0:
        return frac_atan(fractions.Fraction(0), prec=prec, limit=limit)
    elif x < 0:
        return frac_pi(prec=prec, limit=limit)
    else:
        return fractions.Fraction(0)

#
# hyperbolic trigonometric functions
#


# def frac_sinh(x):
#     """Return the hyperbolic sine of x."""
#     if x == 0:
#         return D(0)
#
#     # Uses the taylor series expansion of sinh, see:
#     # http://en.wikipedia.org/wiki/Hyperbolic_function#Taylor_series_expressions
#     getcontext().prec += 2
#     i, lasts, s, fact, num = 1, 0, x, 1, x
#     while s != lasts:
#         lasts = s
#         i += 2
#         num *= x * x
#         fact *= i * (i - 1)
#         s += num / fact
#     getcontext().prec -= 2
#     return +s
#
# def frac_cosh(x):
#     """Return the hyperbolic cosine of x."""
#     if x == 0:
#         return D(1)
#
#     # Uses the taylor series expansion of cosh, see:
#     # http://en.wikipedia.org/wiki/Hyperbolic_function#Taylor_series_expressions
#     getcontext().prec += 2
#     i, lasts, s, fact, num = 0, 0, 1, 1, 1
#     while s != lasts:
#         lasts = s
#         i += 2
#         num *= x * x
#         fact *= i * (i - 1)
#         s += num / fact
#     getcontext().prec -= 2
#     return +s
#
# def tanh(x):
#     """Return the hyperbolic tangent of x."""
#     return +(sinh(x) / cosh(x))
#
# #
# # miscellaneous functions
# #
#
# def frac_sgn(x):
#     """Return -1 for negative numbers, 1 for positive numbers and 0 for zero."""
#     # the signum function, see:
#     # http://en.wikipedia.org/wiki/Sign_function
#     if x > 0:
#         return D(1)
#     elif x < 0:
#         return D(-1)
#     else:
#         return D(0)
#
# def frac_degrees(x):
#     """Return angle x converted from radians to degrees."""
#     return x * 180 / pi()
#
# def frac_radians(x):
#     """Return angle x converted from degrees to radians."""
#     return x * pi() / 180
#
# def frac_ceil(x):
#     """Return the smallest integral value >= x."""
#     return x.to_integral(rounding=decimal.ROUND_CEILING)
#
# def frac_floor(x):
#     """Return the largest integral value <= x."""
#     return x.to_integral(rounding=decimal.ROUND_FLOOR)
#
# def frac_hypot(x, y):
#     """Return the Euclidean distance, sqrt(x**2 + y**2)."""
#     return sqrt(x * x + y * y)
#
# def frac_modf(x):
#     """Return the fractional and integer parts of x."""
#     int_part = x.to_integral(rounding=decimal.ROUND_FLOOR)
#     frac_part = x-int_part
#     return frac_part,int_part
#
# def frac_ldexp(s, e):
#     """Return s*(10**e), the value of a decimal floating point number with
#     significand s and exponent e.
#
#     This function is the inverse of frexp.  Note that this is different from
#     math.ldexp, which uses 2**e instead of 10**e.
#
#     """
#     return s*(10**e)
#
# def frac_frexp(x):
#     """Return s and e where s*(10**e) == x.
#
#     s and e are the significand and exponent, respectively of x.
#     This function is the inverse of ldexp.  Note that this is different from
#     math.frexp, which uses 2**e instead of 10**e.
#
#     """
#     e = D(x.adjusted())
#     s = D(10)**(-x.adjusted())*x
#     return s, e
#
# def frac_pow(x, y, context=None):
#     """Returns x**y (x to the power of y).
#
#     x cannot be negative if y is fractional.
#
#     """
#     context, x, y = _initialize(context, x, y)
#     # if y is an integer, just call regular pow
#     if y._isinteger():
#         return x**y
#     # if x is negative, the result is complex
#     if x < 0:
#         return context._raise_error(decimal.InvalidOperation, 'x (negative) ** y (fractional)')
#     return exp(y * log(x))
#
# def frac_tetrate(x, y, context=None):
#     """Return x recursively raised to the power of x, y times. ;)
#
#     y must be a natural number.
#
#     """
#     context, x, y = _initialize(context, x, y)
#
#     if not y._isinteger():
#         return context._raise_error(decimal.InvalidOperation, 'x *** (non-integer)')
#
#     def _tetrate(x,y):
#         if y == -1:
#             return D(-1)
#         if y == 0:
#             return D(1)
#         if y == 1:
#             return x
#         return x**_tetrate(x,y-1)
#
#     return _tetrate(x,y)

def run_alot(func,name,mathfun,fsmall, fmid, flarge,interval_within_one=False, positive=False, skip_worst=False):
    import time, random

    start_time = time.time()
    for i in range(1, 1000):
        func(fsmall)
    end_time = time.time()
    print(name+" small: %s     (%s, %s) :: %s, %s" % (end_time - start_time, float(func(fsmall)), mathfun(float(fsmall)),(float(func(fsmall))-mathfun(float(fsmall)))/mathfun(float(fsmall)),float(default_accuracy)))

    start_time = time.time()
    for i in range(1, 1000):
        func(fmid)
    end_time = time.time()
    print(name+" mid:   %s     (%s, %s) :: %s, %s" % (end_time - start_time, float(func(fmid)), mathfun(float(fmid)),(float(func(fmid))-mathfun(float(fmid)))/mathfun(float(fmid)),float(default_accuracy)))

    start_time = time.time()
    for i in range(1, 1000):
        func(flarge)
    end_time = time.time()
    print(name+" large: %s     (%s, %s) :: %s, %s" % (end_time - start_time, float(func(flarge)), mathfun(float(flarge)),(float(func(flarge))-mathfun(float(flarge)))/mathfun(float(flarge)),float(default_accuracy)))

    if not skip_worst:
        worst = None
        worstevaldelta = None
        for i in range(1,1000):
            if interval_within_one:
                #frand = fractions.Fraction(random.randint(-100000000000, 100000000000), 10000000000000)
                frand = fractions.Fraction(i, 1000)
            elif positive:
                frand = fractions.Fraction(random.randint(0, 10000000000000), random.randint(1, 10000000000000))
            else:
                frand = fractions.Fraction(random.randint(-10000000000000, 10000000000000), random.randint(1, 10000000000000))
            is_time = time.time()
            func(frand)
            delta = time.time() - is_time
            if worst is None or delta > worst:
                worst = delta
                worstval = frand
            if worstevaldelta is None or abs(float(func(frand)) - mathfun(float(frand))) > worstevaldelta:
                worstevaldelta = abs(float(func(frand))- mathfun(float(frand)))
                worsteval = frand
        print(name+" worst time: %s     %s   (%s, %s)" % (worst, worstval, float(func(worstval)), mathfun(float(worstval))))
        print(name+" worst val:  %s     %s   (%s, %s)" % (worstevaldelta, worsteval, float(func(worstval)), mathfun(float(worstval))))
        print(worst)

def main():
    import math, time, decimal

    decimal.getcontext().prec = 1000

    pistr = "3.141592653589793238462643383279502884197169399375105820974944592307816406286"+\
    "208998628034825342117067982148086513282306647093844609550582231725359408128481"+\
    "117450284102701938521105559644622948954930381964428810975665933446128475648233"+\
    "786783165271201909145648566923460348610454326648213393607260249141273724587006"+\
    "606315588174881520920962829254091715364367892590360011330530548820466521384146"+\
    "951941511609433057270365759591953092186117381932611793105118548074462379962749"+\
    "567351885752724891227938183011949129833673362440656643086021394946395224737190"+\
    "702179860943702770539217176293176752384674818467669405132000568127145263560827"+\
    "785771342757789609173637178721468440901224953430146549585371050792279689258923"+\
    "542019956112129021960864034418159813629774771309960518707211349999998372978049"+\
    "951059731732816096318595024459455346908302642522308253344685035261931188171010"+\
    "003137838752886587533208381420617177669147303598253490428755468731159562863882"
    #print(any_to_fraction("0.3333"))

    pi = decimal.Decimal(pistr)

    #exit(0)
    #f = fractions.Fraction('99999999992')
    #print(float(frac_sqrt(f)), math.sqrt(99999999992))
    #print(float(frac_cos(f)), math.cos(f))
    fsmall = fractions.Fraction(2, 37)
    fmid = fractions.Fraction(17999999, 200000)
    flarge = fractions.Fraction(17999999, 3)

    #ftest = fractions.Fraction(-7065909030689,67554620683)
    #is_time = time.time()
    #print(float(frac_cos(ftest)), math.cos(float(ftest)))
    ##print(frac_pi())
    #delta = time.time() - is_time
    #print("DELTA", delta)
    #exit(0)

    start_time = time.time()
    for i in range(1, 1000):
        frac_pi()
    end_time = time.time()
    print("pi small: %s     (%s, %s) :: %s, %s" % (end_time - start_time, float(frac_pi()),math.pi,(float(frac_pi())-math.pi)/math.pi,default_accuracy))

    for iprec in range(10, 100):
        start_time = time.time()
        prec = fractions.Fraction(1,10**iprec)
        val = frac_pi(prec=prec)
        end_time = time.time()
        dec = val.numerator / decimal.Decimal(val.denominator)
        print(end_time-start_time, float((dec-pi)/pi), float(prec), dec)

    #frac_pi(prec=fractions.Fraction(1,10000))

    #run_alot(frac_exp_old,"exp_old", math.exp,fractions.Fraction(1,100),fractions.Fraction(1,2),fractions.Fraction(1000,1001),interval_within_one=True)
    #run_alot(frac_log_old,"log_old", math.log,fsmall,fmid,flarge,positive=True)
    #run_alot(frac_log_old,"log_old", math.log,fractions.Fraction(1,100),fractions.Fraction(1,2),fractions.Fraction(1000,1001),skip_worst=True)
    run_alot(frac_log,"log", math.log,fractions.Fraction(1,100),fractions.Fraction(1,2),fractions.Fraction(1000,1001),skip_worst=True)
    run_alot(frac_log,"log", math.log,fsmall,fmid,fmid,positive=True)
    run_alot(frac_exp,"exp", math.exp,fractions.Fraction(1,100),fractions.Fraction(1,2),fractions.Fraction(1000,1001),interval_within_one=True)
    run_alot(frac_sqrt,"sqrt", math.sqrt,fsmall,fmid,flarge,positive=True)
    run_alot(frac_cos,"cos", math.cos,fsmall,fmid,flarge)
    run_alot(frac_sin,"sin", math.sin,fsmall,fmid,flarge)
    run_alot(frac_acos,"acos", math.acos,fractions.Fraction(1,100),fractions.Fraction(1,2),fractions.Fraction(1000,1001),interval_within_one=True)
    #run_alot(frac_acos,"acos1", math.acos,fractions.Fraction(1,100),fractions.Fraction(1,2),fractions.Fraction(100,1001))
    #run_alot(frac_acos,"acos", math.acos,fractions.Fraction(1,100),fractions.Fraction(1,2),fractions.Fraction(100,101))
    #run_alot(frac_acos,"acos", math.acos,fractions.Fraction(1,100),fractions.Fraction(1,2),fractions.Fraction(100,150))

if __name__ == "__main__":
    main()
