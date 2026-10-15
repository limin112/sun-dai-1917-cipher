#!/usr/bin/env python3
"""Check Round 19 tests, frozen outputs and manifest without rewriting evidence."""
from __future__ import annotations

import hashlib
from pathlib import Path
import subprocess
import sys
import tempfile

HERE = Path(__file__).resolve().parent
ROOT = HERE.parents[1]


def run(*args: str) -> None:
    subprocess.run([sys.executable, "-B", *args], cwd=ROOT, check=True)


def main() -> int:
    run("-m", "unittest", "discover", "-s", str(HERE / "tests"), "-v")
    with tempfile.TemporaryDirectory(prefix="wenmi-round19-") as directory:
        for name in ("provenance_audit", "selection_controls"):
            generated = Path(directory) / f"{name}.json"
            run(str(HERE / f"{name}.py"), "--output", str(generated))
            expected = HERE / "results" / generated.name
            if generated.read_bytes() != expected.read_bytes():
                raise ValueError(f"Regenerated output differs: {expected}")
            print(f"Reproduced: {expected.relative_to(ROOT)}", flush=True)
    manifest = HERE / "MANIFEST.sha256"
    listed = set()
    for line in manifest.read_text(encoding="utf-8").splitlines():
        digest, relative = line.split("  ", 1)
        path = (HERE / relative).resolve()
        if not path.is_relative_to(HERE) or path == manifest or relative in listed:
            raise ValueError(f"Invalid manifest entry: {relative}")
        listed.add(relative)
        if hashlib.sha256(path.read_bytes()).hexdigest() != digest:
            raise ValueError(f"SHA-256 mismatch: {relative}")
    actual = {p.relative_to(HERE).as_posix() for p in HERE.rglob("*")
              if p.is_file() and p != manifest and "__pycache__" not in p.parts
              and p.suffix != ".pyc"}
    if listed != actual:
        raise ValueError(f"Manifest coverage mismatch: {sorted(listed ^ actual)}")
    print(f"Verified manifest: {len(listed)} files; frozen inputs match the stored audit outputs.")
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
