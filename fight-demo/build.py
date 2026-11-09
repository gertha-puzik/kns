#!/usr/bin/env python3
"""Сборка index.html прототипа боёвки: инлайнит PNG-ассеты в шаблон (base64).
Источники ассетов — каноничные каталоги kns-clone (не копировать вручную):
  dirs-m2-x2/{E,W}{0..3}.png  — коты M2, смотрят вправо/влево (200x300, ~15 КБ)
  probe-field-bg/field_canvas_C.png — тайл травы поля (240x360)
Выход: index.html — самодостаточный файл (без сети и внешних путей).
"""
import base64
import pathlib
import sys

ROOT = pathlib.Path(__file__).resolve().parent
KGEN = pathlib.Path("~/Desktop/dev/catwar/research/kns-clone/kns-generations-2026-11-05").expanduser()

TEMPLATE = ROOT / "fight.template.html"
OUT = ROOT / "index.html"

def b64(p: pathlib.Path) -> str:
    return base64.b64encode(p.read_bytes()).decode("ascii")

def main() -> int:
    markers = {}
    for i in range(4):
        markers[f"__CAT_E{i}__"] = b64(KGEN / "dirs-m2-x2" / f"E{i}.png")
        markers[f"__CAT_W{i}__"] = b64(KGEN / "dirs-m2-x2" / f"W{i}.png")
    markers["__TILE__"] = b64(KGEN / "probe-field-bg" / "field_canvas_C.png")

    html = TEMPLATE.read_text(encoding="utf-8")
    missing_stub = []
    for m, payload in markers.items():
        if m not in html:
            print(f"WARN: маркер {m} не найден в шаблоне")
            continue
        html = html.replace(m, payload)

    # контроль: маркеров не осталось
    for m in markers:
        if m in html:
            missing_stub.append(m)
    if missing_stub:
        print(f"FAIL: незаменённые маркеры: {missing_stub}")
        return 1

    OUT.write_text(html, encoding="utf-8")
    sz = OUT.stat().st_size
    print(f"OK: {OUT} ({sz/1024:.0f} КБ), котов 8 + тайл, всё инлайн")
    return 0

if __name__ == "__main__":
    sys.exit(main())
