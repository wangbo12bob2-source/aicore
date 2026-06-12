from __future__ import annotations

from pathlib import Path


_PACKAGE_ROOT = Path(__file__).resolve().parent
_SRC_PACKAGE = _PACKAGE_ROOT.parent / "src" / "aicore"
__path__ = [str(_PACKAGE_ROOT), str(_SRC_PACKAGE)]

exec(
    compile(
        (_SRC_PACKAGE / "__init__.py").read_text(encoding="utf-8"),
        str(_SRC_PACKAGE / "__init__.py"),
        "exec",
    ),
    globals(),
)
