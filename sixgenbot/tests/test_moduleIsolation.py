"""Rule 1 of the module system, enforced so it cannot rot quietly.

A module never imports another module. Break it and changing the importer breaks
the dashboard — which is the exact thing modules are for avoiding.

Rule 2 is here too: core never imports a module.
"""

from __future__ import annotations

import ast
from pathlib import Path

ROOT = Path(__file__).resolve().parent.parent
MODULES = ROOT / "modules"
CORE = ROOT / "core"


def moduleNames() -> set[str]:
    return {p.name for p in MODULES.iterdir() if p.is_dir() and (p / "module.py").is_file()}


def importedNames(path: Path) -> set[str]:
    """Every dotted name this file imports, absolute and relative alike."""
    tree = ast.parse(path.read_text(encoding="utf-8"))
    found: set[str] = set()
    for node in ast.walk(tree):
        if isinstance(node, ast.Import):
            found.update(alias.name for alias in node.names)
        elif isinstance(node, ast.ImportFrom):
            base = node.module or ""
            found.add("." * node.level + base)
            found.update(f"{'.' * node.level}{base}.{alias.name}".strip(".") for alias in node.names)
    return found


def test_a_module_never_imports_another_module():
    names = moduleNames()
    for folder in sorted(names):
        others = names - {folder}
        for source in sorted((MODULES / folder).rglob("*.py")):
            for imported in importedNames(source):
                parts = imported.replace("sixgenbot.modules.", "").strip(".").split(".")
                hit = others.intersection(parts)
                assert not hit, (
                    f"{source.relative_to(ROOT)} imports {sorted(hit)}. "
                    "Modules must talk through the database or the event bus, never directly."
                )


def test_core_never_imports_a_module():
    names = moduleNames()
    for source in sorted(CORE.rglob("*.py")):
        for imported in importedNames(source):
            assert "modules" not in imported.split("."), (
                f"{source.relative_to(ROOT)} imports {imported}. "
                "core must not know which modules exist — the loader finds them."
            )


def test_every_module_declares_the_contract():
    for folder in sorted(moduleNames()):
        tree = ast.parse((MODULES / folder / "module.py").read_text(encoding="utf-8"))
        assigned = {
            target.id
            for node in tree.body
            if isinstance(node, ast.Assign)
            for target in node.targets
            if isinstance(target, ast.Name)
        }
        functions = {node.name for node in tree.body if isinstance(node, ast.FunctionDef)}
        assert {"NAME", "VERSION"} <= assigned, f"{folder}/module.py must declare NAME and VERSION"
        assert "register" in functions, f"{folder}/module.py must define register(bot)"
