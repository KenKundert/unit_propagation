# Unit Propagation — Simple Minded Unit Propagtaion for QuantiPhy
# encoding: utf8

# Description {{{1
"""
Adds unit propagation to *QuantiPhy*.
"""

# Issues
# The following examples represent challenges to unit propagation
#    2*pi*1.42GHz becomes rads/s
#        In this case pi needs a unit of rads, and then evaluator must recognize
#        that Hz is /s with the results becoming rads/s
#    T₀ + 25
#        T₀ is in Kelvin and 25 in in Celsius.  These appear to have different
#        units, but those units are compatible (where as Fahrenheit is not).
#        But in addition, you cannot convert Celsius to Kelvin before doing the
#        addition.

# MIT License {{{1
# Copyright (C) 2016-2024 Kenneth S. Kundert
#
# Permission is hereby granted, free of charge, to any person obtaining a copy
# of this software and associated documentation files (the "Software"), to deal
# in the Software without restriction, including without limitation the rights
# to use, copy, modify, merge, publish, distribute, sublicense, and/or sell
# copies of the Software, and to permit persons to whom the Software is
# furnished to do so, subject to the following conditions:
#
# The above copyright notice and this permission notice shall be included in all
# copies or substantial portions of the Software.
#
# THE SOFTWARE IS PROVIDED "AS IS", WITHOUT WARRANTY OF ANY KIND, EXPRESS OR
# IMPLIED, INCLUDING BUT NOT LIMITED TO THE WARRANTIES OF MERCHANTABILITY,
# FITNESS FOR A PARTICULAR PURPOSE AND NONINFRINGEMENT. IN NO EVENT SHALL THE
# AUTHORS OR COPYRIGHT HOLDERS BE LIABLE FOR ANY CLAIM, DAMAGES OR OTHER
# LIABILITY, WHETHER IN AN ACTION OF CONTRACT, TORT OR OTHERWISE, ARISING FROM,
# OUT OF OR IN CONNECTION WITH THE SOFTWARE OR THE USE OR OTHER DEALINGS IN THE
# SOFTWARE.

# Imports {{{1
from quantiphy import Quantity, IncompatibleUnits, QuantiPhyError, InvalidNumber
import numbers
import operator
import math


# Globals {{{1
# product_sep = self.narrow_non_breaking_space
# product_sep = '⋅'
product_sep = '-'
quotient_sep = '/'

__version__ = '0.1'
__released__ = '2024-03-01'

# Simplifications {{{2
SIMPLIFICATIONS = dict(
    multiply = {
        ('V', 'A'):      'W',        # power
        ('Ω', 'A'):      'V',        # voltage (from Ohm symbol)
        ('Ω', 'A'):      'V',        # voltage (from Greek Omega symbol)
        ('Ʊ', 'V'):      'A',        # amperes
        ('m', 'm'):      'm²',       # area
        ('rads', 'Hz'):  'rads/s',   # radial frequency
        ('(rads/s)', 's'):  'rads',  # radians
        ('(Hz/V)', 'V'): 'Hz',       # frequency
        ('(J/K)', 'K'):  'J',        # joules
    },
    divide = {
        ('V', 'A'): 'Ω' ,            # resistance (to Ohm symbol)
        ('V', 'Ω'): 'A' ,            # current (from Ohm symbol)
        ('V', 'Ω'): 'A' ,            # current (from Greek Omega symbol)
        ('A', 'V'): 'Ʊ' ,            # conductance
        ('',  's'): 'Hz',            # frequency
        ('', 'Hz'): 's' ,            # time
        ('J', 'C'): 'V' ,            # volts
        ('', 'Ω'): 'Ʊ',              # conductance (from Ohm symbol)
        ('', 'Ω'): 'Ʊ',              # conductance (from Ohm symbol)
        ('', 'Ʊ'): 'Ω',              # resistance (to Ohm symbol)
        ('(rads/s)', 'rads'): 'Hz',  # hertz
    },
)
# check for invalid units (a unit that contains an operator must be parenthesized)
for section, rules in SIMPLIFICATIONS.items():
    for units in rules.keys():
        for unit in units:
            if unit and not unit.isidentifier():
                assert unit[:1] == "(" and unit[-1:] == ")", f"{unit} must be parenthesized."


# def add_simplifications(multiply=None, divide=None):
#     if multiply:
#         SIMPLIFICATIONS['multiply'].update(multiply)
#     if divide:
#         SIMPLIFICATIONS['divide'].update(divide)
#   Not ready for prime time.  Need to recheck parentheses and resort
#   commutative operators after adding new simplifications


# sort the multiply units to make it insensitive to order, also group as needed
SIMPLIFICATIONS["multiply"] = {
    tuple(sorted(f)): t
    for f, t in SIMPLIFICATIONS["multiply"].items()
}


# Utilities {{{1
# group() {{{2
def group(units, aggressive=False):
    if '/' in units:
        return f"({units})"
    if aggressive and product_sep in units:
        return f"({units})"
    return units


# UnitPropagatingQuantity class {{{1
class UnitPropagatingQuantity(Quantity):
    check_units = True

    # operator overloads {{{2
    # pos {{{3
    def __pos__(self):
        return self

    # neg {{{3
    def __neg__(self):
        return self.__class__(-self.real, units=self.units)

    # abs {{{3
    def __abs__(self):
        return self.__class__(abs(self.real), units=self.units)

    # round {{{3
    def __round__(self, ndigits=None):
        return self.__class__(round(self.real, ndigits), units=self.units)

    # trunc {{{3
    def __trunc__(self):
        return self.__class__(math.trunc(self.real), units=self.units)

    # floor {{{3
    def __floor__(self):
        return self.__class__(math.floor(self.real), units=self.units)

    # ceil {{{3
    def __ceil__(self):
        return self.__class__(math.ceil(self.real), units=self.units)

    # generic binary operator {{{3
    # handles simple cases where units must match
    def _binary_operator(self, other, op):
        if isinstance(other, str):
            other = self.__class__(other)
        if not isinstance(other, numbers.Number):
            raise InvalidNumber(other)

        try:
            if self.check_units and self.units != other.units:
                raise IncompatibleUnits(self, other)
        except AttributeError:
            if self.check_units == 'strict':
                raise IncompatibleUnits(
                    getattr(self, 'units', None),
                    getattr(other, 'units', None)
                )

        new = self.__class__(op(self.real, other.real), units=self.units)
        new._inherit_attributes(self)
        return new

    # handles simple cases where units must match
    def _reflected_binary_operator(self, other, op):
        if isinstance(other, str):
            other = self.__class__(other)
        if not isinstance(other, numbers.Number):
            raise InvalidNumber(other)

        try:
            if self.check_units and self.units != other.units:
                raise IncompatibleUnits(self, other)
        except AttributeError:
            if self.check_units == 'strict':
                raise IncompatibleUnits(other, self)
        new = self.__class__(op(other.real, self.real), units=self.units)
        new._inherit_attributes(self)
        return new

    # add {{{3
    def __add__(self, addend):
        return self._binary_operator(addend, operator.add)

    def __radd__(self, addend):
        return self._reflected_binary_operator(addend, operator.add)

    __iadd__ = __add__

    # subtract {{{3
    def __sub__(self, subtrahend):
        return self._binary_operator(subtrahend, operator.sub)

    def __rsub__(self, minuend):
        return self._reflected_binary_operator(minuend, operator.sub)

    __isub__ = __sub__

    # multiply {{{3
    def __mul__(self, multiplicand):
        if isinstance(multiplicand, str):
            multiplicand = self.__class__(multiplicand)
        if not isinstance(multiplicand, numbers.Number):
            raise InvalidNumber(multiplicand)

        # units
        try:
            units = tuple(sorted([group(self.units), group(multiplicand.units)]))
        except AttributeError:
            units = (self.units,)
            if self.check_units == 'strict':
                raise IncompatibleUnits(self, multiplicand)
        simplifications = SIMPLIFICATIONS['multiply']
        if units in simplifications:
            units = simplifications[units]
        else:
            units = product_sep.join(u for u in units if u)

        # this is not quite right, perhaps when defining the simplifications I
        # could also define new classes for the product
        new = self.__class__(self.real * multiplicand.real, units=units)
        new._inherit_attributes(self)
        return new

    __rmul__ = __mul__
    __imul__ = __mul__

    # divide {{{3
    def __truediv__(self, divisor):
        if isinstance(divisor, str):
            divisor = self.__class__(divisor)
        if not isinstance(divisor, numbers.Number):
            raise InvalidNumber(divisor)

        # units
        try:
            units = (group(self.units), group(divisor.units, True))
        except AttributeError:
            units = (self.units, '')
            if self.check_units == 'strict':
                raise IncompatibleUnits(self, divisor)
        simplifications = SIMPLIFICATIONS['divide']
        if units in simplifications:
            units = simplifications[units]
        elif units[0]:
            units = quotient_sep.join(units) if units[1] else units[0]
        elif units[1]:
            units = units[1] + '⁻¹'
        else:
            units = ''

        # this is not quite right, perhaps when defining the simplifications I
        # could also define new classes for the product
        new = self.__class__(self.real / divisor.real, units=units)
        new._inherit_attributes(self)
        return new

    def __rtruediv__(self, dividend):
        if isinstance(dividend, str):
            dividend = self.__class__(dividend)
        if not isinstance(dividend, numbers.Number):
            raise InvalidNumber(dividend)

        # units
        try:
            units = (dividend.units, self.units)
        except AttributeError:
            units = ('', self.units)
            if self.check_units == 'strict':
                raise IncompatibleUnits(dividend, self)
        simplifications = SIMPLIFICATIONS['divide']
        if units in simplifications:
            units = simplifications[units]
        elif units[0]:
            units = quotient_sep.join(units) if units[1] else units[0]
        elif units[1]:
            units = units[1] + '⁻¹'
        else:
            units = ''

        # this is not quite right, perhaps when defining the simplifications I
        # could also define new classes for the product
        new = self.__class__(dividend.real / self.real, units=units)
        new._inherit_attributes(self)
        return new

    __itruediv__ = __truediv__

    # comparison operations {{{3
    def _compare(self, other, op):
        if isinstance(other, str):
            other = self.__class__(other)
        if not isinstance(other, numbers.Number):
            raise InvalidNumber(other)

        try:
            if self.check_units and self.units != other.units:
                raise IncompatibleUnits(self, other)
        except AttributeError:
            if self.check_units == 'strict':
                raise IncompatibleUnits(self, other)
        return op(self.real, other)

    # less than {{{3
    def __lt__(self, other):
        return self._compare(other, operator.lt)

    # less than or equal {{{3
    def __le__(self, other):
        return self._compare(other, operator.le)

    # greater than {{{3
    def __gt__(self, other):
        return self._compare(other, operator.gt)

    # greater than or equal {{{3
    def __ge__(self, other):
        return self._compare(other, operator.ge)

    # equality operations {{{3
    def _equality(self, other, op, on_failure):
        try:
            if isinstance(other, str):
                other = self.__class__(other)
            if not isinstance(other, numbers.Number):
                raise InvalidNumber(other)
        except InvalidNumber:
            return on_failure

        try:
            if self.check_units and self.units != other.units:
                return on_failure
        except AttributeError:
            if self.check_units == 'strict':
                return on_failure
        return op(self.real, other)

    # equal {{{3
    def __eq__(self, other):
        return self._equality(other, operator.eq, False)

    # equal {{{3
    def __ne__(self, other):
        return self._equality(other, operator.ne, True)
