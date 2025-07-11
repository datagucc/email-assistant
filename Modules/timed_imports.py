# timed_imports.py

import time

def timed_import(module_name, alias=None):
    start = time.time()
    module = __import__(module_name)
    duration = time.time() - start
    name = alias or module_name
    print(f"✅ {name} importé en {duration:.3f} secondes")
    return module

def timed_from_import(module_name, *submodules):
    start = time.time()
    exec(f"from {module_name} import {', '.join(submodules)}", globals())
    duration = time.time() - start
    print(f"✅ from {module_name} import {', '.join(submodules)} — {duration:.3f} sec")


