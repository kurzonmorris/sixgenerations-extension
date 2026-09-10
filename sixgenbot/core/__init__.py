"""Everything a module is allowed to depend on.

`core` never imports a module. Modules never import each other. They talk
through the database and the event bus. See docs/SIXGENBOT_PLAN.md section 3.
"""
