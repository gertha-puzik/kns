#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""KNS QC — структурный гейт мерджа в main (Actions «KNS QC / qc»).

Ловит классы багов из питфолов скилла/досье ДО деплоя:
- битый JSON в манифестах;
- сломанный синтаксис JS, в т.ч. inline-<script> в HTML
  (жертвы fuzzy-патчей с потерянной парной скобкой — страница «ещё работает»);
- артефактные CJK-символы в текстовых файлах (мусор ИИ-патчей/склеек);
- шаблон 'act{act}' (баг actact1 — канва молча пустая);

Пиксельные A/B и браузерные зонды — вне гейта, их ведёт агент в рантайме.
Провал = красный чек 'KNS QC / qc' => мердж в main заблокирован.
"""
import json
import os
import pathlib
import re
import subprocess
import sys
import tempfile

ROOT = pathlib.Path(".").resolve()
SKIP_DIRS = {".git", ".github", ".husky", "node_modules"}
problems = []


def rel(p):
    try:
        return p.relative_to(ROOT).as_posix()
    except ValueError:
        return str(p)


def skip(p):
    return any(part in SKIP_DIRS for part in p.parts)


def ok(msg):
    print(f"  ✅ {msg}")


def bad(msg):
    print(f"  ⛔ {msg}")
    problems.append(msg)


def node_check(code, label):
    """Синтаксическая проверка JS через node --check. True = чисто."""
    fd, path = tempfile.mkstemp(suffix=".js")
    try:
        with os.fdopen(fd, "w", encoding="utf-8") as f:
            f.write(code)
        r = subprocess.run(
            ["node", "--check", path], capture_output=True, text=True
        )
    finally:
        try:
            os.unlink(path)
        except OSError:
            pass
    if r.returncode != 0:
        tail = (r.stderr or r.stdout or "").strip().splitlines()[:5]
        bad(f"синтаксис JS сломан: {label}\n    " + "\n    ".join(tail))
        return False
    return True


print("== 1/5 JSON-файлы ==")
jsons = [p for p in sorted(ROOT.rglob("*.json")) if not skip(p)]
if not jsons:
    print("  — json-файлов нет")
for p in jsons:
    try:
        json.loads(p.read_text(encoding="utf-8"))
        ok(rel(p))
    except Exception as e:
        bad(f"битый JSON {rel(p)}: {e}")

print("== 2/5 JS-файлы (node --check) ==")
jss = [p for p in sorted(ROOT.rglob("*.js")) if not skip(p)]
for p in jss:
    if node_check(p.read_text(encoding="utf-8"), rel(p)):
        ok(rel(p))

print("== 3/5 inline-JS в HTML ==")
script_re = re.compile(r"<script\b([^>]*)>(.*?)</script>", re.S | re.I)
htmls = [p for p in sorted(ROOT.rglob("*.html")) if not skip(p)]
for p in htmls:
    html = p.read_text(encoding="utf-8", errors="replace")
    checked = failed = 0
    idx = 0
    for m in script_re.finditer(html):
        attrs, body = m.group(1), m.group(2)
        idx += 1
        if re.search(r"\bsrc\s*=", attrs):
            continue
        tm = re.search(r"type\s*=\s*[\"']([^\"']+)", attrs, re.I)
        if tm and tm.group(1).lower() not in ("module", "text/javascript"):
            continue
        if not body.strip():
            continue
        if node_check(body, f"{rel(p)} <script #{idx}>"):
            checked += 1
        else:
            failed += 1
    if checked and not failed:
        ok(f"{rel(p)}: inline-JS ок ({checked} скриптов)")

print("== 4/5 CJK-мусор в текстах (артефакты ИИ-патчей) ==")
cjk_re = re.compile(
    "[\u3000-\u303f\u3190-\u319f\u4e00-\u9fff\uf900-\ufaff\uff00-\uff5f]"
)
text_files = []
for p in jsons + jss + htmls + [q for q in sorted(ROOT.rglob("*.md")) if not skip(q)]:
    if p not in text_files:
        text_files.append(p)
cjk_hits = 0
for p in text_files:
    try:
        lines = p.read_text(encoding="utf-8", errors="replace").splitlines()
    except Exception as e:
        bad(f"не читается {rel(p)}: {e}")
        continue
    for i, line in enumerate(lines, 1):
        m = cjk_re.search(line)
        if m:
            cjk_hits += 1
            bad(f"CJK {m.group(0)!r} в {rel(p)}:{i} — мусор ИИ-патча, почистить")
if not cjk_hits:
    ok(f"CJK-мусора нет ({len(text_files)} текстовых файлов)")

print("== 5/5 Прод-паттерны ==")
actbug = 0
for p in jss:
    if "act{act}" in p.read_text(encoding="utf-8", errors="replace"):
        actbug += 1
        bad(f"{rel(p)}: шаблон 'act{{act}}' (баг actact1 — канва молча пустая)")
if not actbug:
    ok("шаблоны путей без коллизии 'act{act}'")

print()
if problems:
    print(f"KNS QC: ⛔ ПРОВАЛ — {len(problems)} проблем(ы)")
    sys.exit(1)
print("KNS QC: ✅ все проверки пройдены")
