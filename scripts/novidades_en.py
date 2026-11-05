#!/usr/bin/env python3
"""Gera NOVIDADES.en.md a partir de omni_help (mesmo formato do NOVIDADES.md)."""
import os
import sys

ROOT = os.path.dirname(os.path.dirname(os.path.abspath(__file__)))
sys.path.insert(0, os.path.join(ROOT, "port", "omni36os"))
import omni_help

out = ["# Omni36OS release notes", ""]
for version, date, items in omni_help.NOVIDADES:
    out += [f"## {version} ({date})", ""]
    out += [f"- {item}" for item in omni_help.NOVIDADES_EN[version]]
    out.append("")
with open(os.path.join(ROOT, "NOVIDADES.en.md"), "w", encoding="utf-8") as f:
    f.write("\n".join(out))
