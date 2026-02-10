import expense_core
import builtins

_orig = builtins.input
builtins.input = lambda prompt='': '12'
try:
    expense_core.main()
finally:
    builtins.input = _orig
