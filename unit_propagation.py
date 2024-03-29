# Unit Propagation — Simple Minded Unit Propagtaion for QuantiPhy
# encoding: utf8

# Currently the code does not distinguish between unitless numbers (units == '')
# and numbers that cannot carry units, like floats.
# It might make sense to distinguish the two

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
from quantiphy import Quantity, QuantiPhyError, IncompatibleUnits, InvalidNumber
import math
import numbers
import operator


# Globals {{{1
__version__ = '0.1'
__released__ = '2024-03-01'
# product_sep = self.narrow_non_breaking_space
# product_sep = '⋅'
product_sep = '-'
quotient_sep = '/'

# Simplifications {{{2
SIMPLIFICATIONS = dict(
    additive = {
        ('°C', 'K'):          'K',        # Kelvin
        ('K', 'K'):           None,       # error
    },
    multiply = {
        ('V', 'A'):           'W',        # power
        ('Ω', 'A'):           'V',        # voltage (from Ohm symbol)
        ('Ω', 'A'):           'V',        # voltage (from Greek Omega symbol)
        ('Ʊ', 'V'):           'A',        # amperes
        ('rads', 'Hz'):       'rads/s',   # radial frequency
        ('rads/s', 's'):      'rads',    # radians
        ('Hz/V', 'V'):        'Hz',       # frequency
        ('m', 'm'):           'm²',       # area
        ('m²', 'm'):          'm³',       # volume
    },
    divide = {
        ('V', 'A'):           'Ω',        # resistance (to Ohm symbol)
        ('V', 'Ω'):           'A',        # current (from Ohm symbol)
        ('V', 'Ω'):           'A',        # current (from Greek Omega symbol)
        ('A', 'V'):           'Ʊ',        # conductance
        ('',  's'):           'Hz',       # frequency
        ('', 'Hz'):           's',        # time
        ('', 'Ω'):            'Ʊ',        # conductance (from Ohm symbol)
        ('', 'Ω'):            'Ʊ',        # conductance (from Ohm symbol)
        ('', 'Ʊ'):            'Ω',        # resistance (to Ohm symbol)
        ('rads/s', 'rads'):   'Hz',       # hertz
        ('m²', 'm'):          'm',        # length
        ('m', 'm'):           '',         # length ratio (unitless)
    },
)


# def add_simplifications(multiply=None, divide=None):
#     if multiply:
#         SIMPLIFICATIONS['multiply'].update(multiply)
#     if divide:
#         SIMPLIFICATIONS['divide'].update(divide)
#   Not ready for prime time.  Need to recheck parentheses and resort
#   commutative operators after adding new simplifications


# Utilities {{{1
# group() {{{2
def group(units, aggressive=False):
    if '/' in units:
        return f"({units})"
    if aggressive and product_sep in units:
        return f"({units})"
    return units


# communitive_group() {{{2
def normalize_units(unit0, unit1, type):
    if type in ['additive', 'multiply']:
        units = sorted([unit0, unit1])
        return group(units[0]), group(units[1])
    assert type == 'divide'
    return group(unit0), group(unit1, aggressive=True)


# normalize_simplifications {{{2
def normalize_simplifications(given):
    new = {}
    for section, rules in given.items():
        new[section] = {}
        for units, simplification in rules.items():
            units = normalize_units(*units, section)
            new[section][units] = simplification
    return new


SIMPLIFICATIONS = normalize_simplifications(SIMPLIFICATIONS)


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
    def _additive_operator(self, other, op):
        if isinstance(other, str):
            other = self.__class__(other)
        if not isinstance(other, numbers.Number):
            raise InvalidNumber(other)

        # extract the units
        try:
            self_units = self.units
        except AttributeError:
            self_units = ''
        try:
            other_units = other.units
        except AttributeError:
            other_units = ''

        # resolve the units
        units = tuple(sorted([group(self_units), group(other_units)]))
        units = normalize_units(self_units, other_units, 'additive')
        simplifications = SIMPLIFICATIONS['additive']
        if units in simplifications:
            units = simplifications[units]
            if units is None:
                raise IncompatibleUnits(self, other)
        else:
            if self.check_units and self_units != other_units:
                if self.check_units == 'strict':
                    raise IncompatibleUnits(self, other)
                if self_units and other_units:
                    raise IncompatibleUnits(self, other)
            units = self_units or other_units

        new = self.__class__(op(self.real, other.real), units=units)
        new._inherit_attributes(self)
        return new

    # handles simple cases where units must match
    def _reflected_additive_operator(self, other, op):
        if isinstance(other, str):
            other = self.__class__(other)
        if not isinstance(other, numbers.Number):
            raise InvalidNumber(other)

        # extract the units
        try:
            self_units = self.units
        except AttributeError:
            self_units = ''
        try:
            other_units = other.units
        except AttributeError:
            other_units = ''

        # resolve the units
        units = normalize_units(self_units, other_units, 'additive')
        simplifications = SIMPLIFICATIONS['additive']
        if units in simplifications:
            units = simplifications[units]
            if units is None:
                raise IncompatibleUnits(self, other)
        else:
            if self.check_units and self_units != other_units:
                if self.check_units == 'strict':
                    raise IncompatibleUnits(self, other)
                if self_units and other_units:
                    raise IncompatibleUnits(self, other)
            units = self_units or other_units

        new = self.__class__(op(other.real, self.real), units=units)
        new._inherit_attributes(self)
        return new

    # add {{{3
    def __add__(self, addend):
        return self._additive_operator(addend, operator.add)

    def __radd__(self, addend):
        return self._reflected_additive_operator(addend, operator.add)

    __iadd__ = __add__

    # subtract {{{3
    def __sub__(self, subtrahend):
        return self._additive_operator(subtrahend, operator.sub)

    def __rsub__(self, minuend):
        return self._reflected_additive_operator(minuend, operator.sub)

    __isub__ = __sub__

    # multiply {{{3
    def __mul__(self, multiplicand):
        if isinstance(multiplicand, str):
            multiplicand = self.__class__(multiplicand)
        if not isinstance(multiplicand, numbers.Number):
            raise InvalidNumber(multiplicand)

        # extract the units
        try:
            self_units = self.units
        except AttributeError:
            self_units = ''
        try:
            multiplicand_units = multiplicand.units
        except AttributeError:
            multiplicand_units = ''

        # resolve the units
        units = normalize_units(self_units, multiplicand_units, 'multiply')
        simplifications = SIMPLIFICATIONS['multiply']
        if units in simplifications:
            units = simplifications[units]
        else:
            units = product_sep.join(u for u in units if u)

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

        # extract the units
        try:
            self_units = self.units
        except AttributeError:
            self_units = ''
        try:
            divisor_units = divisor.units
        except AttributeError:
            divisor_units = ''

        # resolve the units
        units = normalize_units(self_units, divisor_units, 'divide')
        simplifications = SIMPLIFICATIONS['divide']
        if units in simplifications:
            units = simplifications[units]
        elif units[0]:
            if units[0] == units[1]:
                units = ''
            else:
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
