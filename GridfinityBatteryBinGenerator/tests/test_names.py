# Static check for names used but never bound, across the whole add-in.
# Run: python3 tests/test_names.py
#
# Most of entry.py cannot be executed outside Fusion, so the geometry
# functions have no test that runs their statements. That is exactly where a
# NameError hides: buildLabelTab referred to two locals that had been deleted
# along with the code that defined them, and nothing noticed until Fusion threw
# the traceback in a dialog. This walks every function instead of running it,
# and reports any name loaded that is not bound in that function, an enclosing
# function, the module, or builtins.

import ast
import builtins
import os
import sys

TESTS_DIR = os.path.dirname(os.path.abspath(__file__))
ADDIN_DIR = os.path.dirname(TESTS_DIR)

PASS = 0
FAIL = 0


def check(name, cond, detail=''):
    global PASS, FAIL
    if cond:
        PASS += 1
    else:
        FAIL += 1
        print('FAIL: {} {}'.format(name, detail))


def boundNames(node, includeNested=True):
    """Names this scope binds: assignments, imports, defs, args, except-as,
    comprehension and with targets."""
    names = set()
    for child in ast.walk(node):
        if child is not node and isinstance(child, (ast.FunctionDef, ast.AsyncFunctionDef,
                                                    ast.ClassDef)):
            names.add(child.name)
            if not includeNested:
                continue
        if isinstance(child, ast.Name) and isinstance(child.ctx, (ast.Store, ast.Del)):
            names.add(child.id)
        elif isinstance(child, ast.arg):
            names.add(child.arg)
        elif isinstance(child, ast.ExceptHandler) and child.name:
            names.add(child.name)
        elif isinstance(child, (ast.Import, ast.ImportFrom)):
            for alias in child.names:
                names.add((alias.asname or alias.name).split('.')[0])
        elif isinstance(child, ast.Global) or isinstance(child, ast.Nonlocal):
            names.update(child.names)
    return names


def checkModule(path):
    with open(path, 'r', encoding='utf-8') as handle:
        source = handle.read()
    try:
        tree = ast.parse(source)
    except SyntaxError as error:
        check('{} parses'.format(os.path.basename(path)), False, error)
        return
    check('{} parses'.format(os.path.basename(path)), True)

    moduleScope = boundNames(tree) | set(dir(builtins))
    problems = []

    def walk(node, enclosing):
        scope = enclosing | boundNames(node)
        for child in ast.walk(node):
            if child is node:
                continue
            if isinstance(child, (ast.FunctionDef, ast.AsyncFunctionDef)):
                walk(child, scope)
        # only report loads that belong to this function, not to a nested one
        nested = set()
        for child in ast.walk(node):
            if child is not node and isinstance(child, (ast.FunctionDef,
                                                        ast.AsyncFunctionDef,
                                                        ast.ClassDef)):
                nested.update(id(inner) for inner in ast.walk(child))
        for child in ast.walk(node):
            if id(child) in nested:
                continue
            if isinstance(child, ast.Name) and isinstance(child.ctx, ast.Load):
                if child.id not in scope:
                    problems.append((node.name, child.lineno, child.id))

    for node in tree.body:
        if isinstance(node, (ast.FunctionDef, ast.AsyncFunctionDef)):
            walk(node, moduleScope)
        elif isinstance(node, ast.ClassDef):
            for inner in node.body:
                if isinstance(inner, (ast.FunctionDef, ast.AsyncFunctionDef)):
                    walk(inner, moduleScope | boundNames(node, includeNested=False))

    for (func, line, name) in sorted(set(problems)):
        check('{}:{} {} is defined'.format(os.path.basename(path), line, name),
              False, 'in {}()'.format(func))
    if not problems:
        check('{} has no unbound names'.format(os.path.basename(path)), True)


# our own code only: the vendored gridfinity library is not ours to police
targets = []
for folder in ('commands', os.path.join('lib', 'batteryUtils')):
    for root, _dirs, files in os.walk(os.path.join(ADDIN_DIR, folder)):
        if '__pycache__' in root:
            continue
        targets.extend(os.path.join(root, f) for f in files if f.endswith('.py'))
targets.append(os.path.join(ADDIN_DIR, 'GridfinityBatteryBinGenerator.py'))

print('checking {} modules'.format(len(targets)))
for path in sorted(targets):
    checkModule(path)

print()
print('{} passed, {} failed'.format(PASS, FAIL))
sys.exit(1 if FAIL else 0)
