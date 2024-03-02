Simple-Minded Unit Propagation for QuantiPhy
============================================

| Author: Ken Kundert
| Version: 0.1
| Released: 2024-03-01
|

This is a package used to experiment with adding unit propagation to QuantiPhy_.  
It currently employs simple-minded simplification rules that are relatively easy 
to fool.  Also, there is a strong emphasis on simple electrical unit scenarios.  
Even so, it shows promise for use in well controlled settings.

Here is simple example::

    from unit_propagation import (
        UnitPropagatingQuantity as Quantity, QuantiPhyError
    )
    try:
        v = Quantity("2.5V")
        i = Quantity("100nA")
        print(v/i)
    except QuantiPhyError as e:
        print(f"error: {e!s}")

Included in the package is a simple RPN calculator that allows you to explore 
the capabilities and limitation of the *unit propagation*.

.. _QuantiPhy: https://quantiphy.readthedocs.io
