from functools import partial
from parametrize_from_file import parametrize, Namespace
from voluptuous import Schema, Optional, Required, Invalid, Any
from textwrap import dedent
from unit_propagation import (
    UnitPropagatingQuantity, InvalidNumber, IncompatibleUnits
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
    strictly = dict(Quantity=StrictQuantity)
    try:
        if execute:
            locals = {}
            exec(execute, with_quantity, locals)
            assert eval(expect, strictly, locals)
        else:
            #assert eval(evaluate, with_quantity) == eval(expect, strictly)
            try:
                assert eval(expect, strictly) == eval(evaluate, with_quantity), name
            except SyntaxError:
                assert expect != eval(evaluate, with_quantity), name
    except (InvalidNumber, IncompatibleUnits) as e:
        assert str(e) == expect, name

