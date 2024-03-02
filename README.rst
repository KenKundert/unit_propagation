Simple-Minded Unit Propagation for QuantiPhy
============================================

.. image:: https://pepy.tech/badge/unit_propagation/month
    :target: https://pepy.tech/project/unit_propagation

.. image:: https://github.com/KenKundert/unit_propagation/actions/workflows/build.yaml/badge.svg
    :target: https://github.com/KenKundert/unit_propagation/actions/workflows/build.yaml

.. image:: https://coveralls.io/repos/github/KenKundert/unit_propagation/badge.svg?branch=master
    :target: https://coveralls.io/github/KenKundert/unit_propagation?branch=master

.. image:: https://img.shields.io/pypi/v/unit_propagation.svg
    :target: https://pypi.python.org/pypi/unit_propagation

.. image:: https://img.shields.io/pypi/pyversions/unit_propagation.svg
    :target: https://pypi.python.org/pypi/unit_propagation/



| Author: Ken Kundert
| Version: 0.1
| Released: 2024-03-01
|

This is a package used to experiment with adding unit propagation to QuantiPhy_.  
It currently employs simple-minded simplification rules that are relatively easy 
to fool.  Also, there is a strong emphasis on simple electrical unit scenarios.  
Even so, it shows promise for use in well controlled settings.

Here is simple example::

    >>> from unit_propagation import UnitPropagatingQuantity as Quantity, QuantiPhyError

    >>> try:
    ...     v = Quantity("2.5V")
    ...     i = Quantity("100nA")
    ...     print(v/i)
    ... except QuantiPhyError as e:
    ...     print(f"error: {e!s}")
    25 MΩ

Operations can also involve integers, floats and strings::

    >>> Kvco = Quantity(500e6, "Hz") / "500mV"
    >>> print(Kvco)
    1 GHz/V

    >>> Vdd = Quantity("2.5V")
    >>> halfVdd = Vdd / 2
    >>> print(halfVdd)
    1.25 V

Included in the package is a simple RPN calculator that allows you to explore 
the capabilities and limitation of *unit propagation*.

.. _QuantiPhy: https://quantiphy.readthedocs.io
