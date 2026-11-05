#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""Миграция канон-масок: fore -> foreL/foreR, hind -> hindL/hindR («на виде», как earL/earR).

Заказчица: передние и задние лапы размечаются отдельно по сторонам кадра.
Для каждого ключа каждого канона (artpack/m2_layer_masks.json — 21 ключ
0-4/E0..E3/W0..W3/N0..N3/S0..S3; artpack/thin_ и chub_layer_masks.json — по 5;
artpack/manual_layer_masks.json — если появится, та же миграция):
  - пиксели зоны fore разбиваются на связные компоненты (4-связность);
  - каждая компонента относится к foreL/foreR по X-центроиду своего bbox:
    cx < w/2 -> foreL, иначе foreR (w — фактическая ширина PNG кадра по каталогу
    build_mask_annotator_data.build_catalog; кадры 0-4/N/S 100, E/W 200);
  - hind -> hindL/hindR аналогично; ключи fore/hind из JSON удаляются.

Неделимая CC (лапы слились в профиле): вся компонента уходит по центроиду,
противоположная зона пуста — осознанная пустота; такой ключ попадает в
«needs-manual» (заказчица разделит руками в редакторе разметки).

Инвариант на каждый ключ (программно, до записи): foreL ∪ foreR == прежнее
fore, hindL ∪ hindR == прежнее hind — те же множества пикселей, пересечение
пусто; нарушение — аварийный выход без записи.

Повторный прогон идемпотентен: ключи без fore/hind пропускаются.
Стиль дампа каждого файла сохраняется (по сериализации исходника).

Запуск из корня репо: python3 tools/split_paw_zones.py [--dry-run]
"""
import json
import os
import sys

try:
    from PIL import Image
except ImportError:
    sys.exit("нужен Pillow: pip install pillow")

HERE = os.path.dirname(os.path.abspath(__file__))
ROOT = os.path.dirname(HERE)
sys.path.insert(0, HERE)
from build_mask_annotator_data import build_catalog  # noqa: E402  (каталог кадр->файл)

# (build, файл канона); manual-канон обрабатывается тем же кодом, если появится
CANONS = [
    ("norm", "artpack/m2_layer_masks.json"),
    ("thin", "artpack/thin_layer_masks.json"),
    ("chub", "artpack/chub_layer_masks.json"),
    ("manual", "artpack/manual_layer_masks.json"),
]
SPLIT = {"fore": ("foreL", "foreR"), "hind": ("hindL", "hindR")}


def dump_style(raw_closed, pristine):
    """Функция-дампер, воспроизводящая исходный стиль файла; иначе компакт.

    Стиль определяется по НЕизменённому объекту (до миграции): сравнивать
    сериализацию изменённого объекта с исходным текстом нельзя — они не равны
    по содержанию, и стиль всегда «не нашёлся бы».
    """
    d_compact = lambda obj: json.dumps(obj, ensure_ascii=False, separators=(",", ":"))
    if d_compact(pristine) == raw_closed:
        return d_compact
    d_full = lambda obj: json.dumps(obj, ensure_ascii=False)
    if d_full(pristine) == raw_closed:
        return d_full
    d_ind = lambda obj: json.dumps(obj, ensure_ascii=False, indent=1)
    if d_ind(pristine) == raw_closed:
        return d_ind
    return d_compact


def components(indexes, w):
    """CC-разбиение набора flat-индексов (y*w+x), 4-связность. Список списков."""
    pxset = set(indexes)
    seen = set()
    out = []
    for start in sorted(pxset):
        if start in seen:
            continue
        cc = []
        stack = [start]
        seen.add(start)
        while stack:
            i = stack.pop()
            cc.append(i)
            x = i % w
            for nbr in ((i - 1 if x > 0 else -1),
                        (i + 1 if x < w - 1 else -1),
                        i - w, i + w):
                if nbr in pxset and nbr not in seen:
                    seen.add(nbr)
                    stack.append(nbr)
        out.append(cc)
    return out


def frame_sizes(build, key, catalog):
    """(w, h) кадра по ключу: каталог конвейера либо PNG из manual-ключа 'build:file'."""
    if ":" in key:
        b, f = key.split(":", 1)
        with Image.open(os.path.join(ROOT, f)) as im:
            return im.size
    for e in catalog.get(build, []):
        if e.get("key") == key:
            with Image.open(os.path.join(ROOT, e["file"])) as im:
                return im.size
    sys.exit("нет кадра для ключа %s (%s)" % (key, build))


def split_zone(layers, zone, w, h, report):
    """Разброс зоны zone на {L,R} по CC/центроиду bbox; возвращает (left, right)."""
    idx = [p for p in layers[zone] if 0 <= p < w * h]
    left, right = [], []
    ncc = 0
    for cc in components(idx, w):
        ncc += 1
        xs = [i % w for i in cc]
        cx = (min(xs) + max(xs)) / 2.0  # X-центроид bbox компоненты
        (left if cx < w / 2.0 else right).extend(cc)
    old_set = set(idx)
    if old_set != (set(left) | set(right)) or (set(left) & set(right)):
        sys.exit("инвариант нарушен: split != исходному множеству (zone=%s)" % zone)
    report.append((zone, len(old_set), ncc, len(left), len(right)))
    return left, right


def main():
    dry = "--dry-run" in sys.argv
    catalogs = build_catalog({}, {}, {})  # пары ключ->{file} (для размеров PNG)
    needs_manual = []
    migrated = 0
    for build, rel in CANONS:
        path = os.path.join(ROOT, rel)
        if not os.path.exists(path):
            print("-- пропуск: %s (нет файла)" % rel)
            continue
        raw = open(path, encoding="utf-8").read()
        store = json.loads(raw)
        dumper = dump_style(raw.rstrip("\n"), store)
        changed = False
        print("== %s (%s)" % (build, rel))
        for key in store:
            layers = store[key]
            if not any(z in layers for z in ("fore", "hind")):
                print("  %-4s уже мигрирован (fore/hind нет) — пропуск" % key)
                continue
            w, h = frame_sizes(build, key, catalogs)
            rep = []
            new_layers = {}
            for z, vals in layers.items():
                if z in ("fore", "hind"):
                    lft, rgt = split_zone(layers, z, w, h, rep)
                    lname, rname = SPLIT[z]
                    new_layers[lname] = sorted(lft)
                    new_layers[rname] = sorted(rgt)
                    # неделимая CC: непустая группа легла на одну сторону — пустая
                    # противоположная осознанная, ключ на ручной заход в редакторе
                    if (len(lft) > 0) != (len(rgt) > 0):
                        needs_manual.append("%s:%s:%s" % (build, key, z))
                else:
                    new_layers[z] = vals
            store[key] = new_layers
            changed = True
            migrated += 1
            print("  %-4s (w=%d): %s" % (key, w, " | ".join(
                "%s %dpx -> %sL %d / %sR %d (CC %d)" % (z, old, z, l, z, r, ncc)
                for z, old, ncc, l, r in rep)))
        if not changed:
            continue
        out = dumper(store)
        if raw.endswith("\n"):
            out += "\n"
        if dry:
            print("  --dry-run: запись %s пропущена" % rel)
            continue
        tmp = path + ".tmp"
        with open(tmp, "w", encoding="utf-8") as f:
            f.write(out)
        os.replace(tmp, path)
        print("  записано: %s (%d байт)" % (rel, os.path.getsize(path)))
    print("")
    print("инвариант foreL∪foreR==fore, hindL∪hindR==hind: ок на всех %d ключах" % migrated)
    if needs_manual:
        print("needs-manual (неделимая CC, пустая противоположная): %s" % ", ".join(needs_manual))
    else:
        print("needs-manual: нет")


if __name__ == "__main__":
    main()
