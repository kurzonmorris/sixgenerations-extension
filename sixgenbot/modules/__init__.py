"""Feature modules. One folder each, found by the loader, never named in core.

Three rules keep them from breaking each other:

  1. A module never imports another module.
  2. core never imports a module.
  3. They talk through the database and the event bus.

`tests/test_moduleIsolation.py` enforces rule 1 so it cannot rot quietly.
"""
