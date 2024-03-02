from functools import partial
from parametrize_from_file import parametrize, Namespace
from voluptuous import Schema, Optional, Required, Invalid, Any
from textwrap import dedent
from unit_propagation import (
    UnitPropagatingQuantity, InvalidNumber, IncompatibleUnits
)
import math


math_funcs = dict(
    ceil = math.ceil,
    floor = math.floor,
    trunc = math.trunc
)

def to_bool(s):
    if isinstance(s, str):
        s = s.lower()
        if s in ["no", "n", "false", "f", "off", "0"]:
            return False
        if s in ["yes", "y", "true", "t", "on", "1"]:
            return False
        if s == 'strict':
            return s
    return s

# Adapt parametrize_for_file to read dictionary rather than list
def name_from_dict_keys(tests):
    return [{**v, 'name': k} for k,v in tests.items()]

parametrize = partial(parametrize, preprocess=name_from_dict_keys)

schema = Schema({
    Required('name'): str,
    Optional('execute', default=''): str,
    Optional('evaluate', default=''): str,
    Required('expect'): str,
    Optional('check_units', default=True): to_bool,
})

class StrictQuantity(UnitPropagatingQuantity):
    check_units = 'strict'

@parametrize(schema=schema)
def test_unit_propagation(name, execute, evaluate, expect, check_units):

    UnitPropagatingQuantity.check_units = check_units
        # this is a hack
        # it is necessary as long as check_units is not a real preference
    with_quantity = dict(Quantity=UnitPropagatingQuantity)
    with_quantity.update(math_funcs)
    strictly = dict(Quantity=StrictQuantity)
    strictly.update(math_funcs)
    try:
        if execute:
            locals = {}
            exec(execute, with_quantity, locals)
            assert eval(expect, strictly, locals)
        else:
            try:
                result = eval(evaluate, with_quantity)
                expected = eval(expect, strictly)
                if type(expected) is bool:
                    assert expected == result, name
                else:
                    assert expected.is_close(result, check_units=True), name
            except SyntaxError:
                assert expect != eval(evaluate, with_quantity), name
    except (InvalidNumber, IncompatibleUnits) as e:
        assert str(e) == expect, name

