#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""Применение пакета правок из редактора разметки зон (mask-annotator.html).

Пакет (kns-mask-annotator-patch v1) — это JSON: перечисление отредактированных
кадров с послойными списками пикселей (flat-индексы y*w+x), QC от страницы
и PNG-визуализацией. Этот скрипт — приёмный пункт ИИ-конвейера:
- перепроверяет QC ПО ПИКСЕЛЯМ против кадра (union==silhouette, 0 дыр/0 вне/0
  пересечений) — цифровым арбитражем, а не доверием к числу из пакета;
- применяет правки в канон масок:
    norm -> artpack/m2_layer_masks.json
    thin -> artpack/thin_layer_masks.json
    chub -> artpack/chub_layer_masks.json
  кадры БЕЗ канон-ключа (новая разметка, напр. «хвост вниз») идут в
    artpack/manual_layer_masks.json  под ключом frameKey.
- --check: только проверка (для QC-гейта/ревью UNIX-код 1 при расхождении).

Порядок регенерации после применения: python3 tools/build_mask_annotator_data.py
(страница подхватит новый канон; тонировка — tools/tint_bake.py отдельно по этапу 9).
"""
import argparse
import json
import os
import sys
import tempfile

try:
    from PIL import Image
except ImportError:
    sys.exit("нужен Pillow")

HERE = os.path.dirname(os.path.abspath(__file__))
ROOT = os.path.dirname(HERE)

ZONES = ["eyes", "earL", "earR", "nose", "tail", "fore", "hind", "head", "chest", "belly", "body"]
TARGETS = {
    "norm": "artpack/m2_layer_masks.json",
    "thin": "artpack/thin_layer_masks.json",
    "chub": "artpack/chub_layer_masks.json",
}
MANUAL = "artpack/manual_layer_masks.json"


def frame_sil(path):
    im = Image.open(path).convert("RGBA")
    w, h = im.size
    px = im.load()
    sil = set()
    for y in range(h):
        base = y * w
        for x in range(w):
            if px[x, y][3] > 0:
                sil.add(base + x)
    return sil, w, h


def recompute_qc(layers, w, h, sil):
    listed = 0
    outside = 0
    seen_in = set()
    for z in ZONES:
        for px in layers.get(z, []):
            listed += 1
            if px < 0 or px >= w * h or px not in sil:
                outside += 1
                continue
            seen_in.add(px)
    holes = len(sil) - len(seen_in)
    inter = listed - outside - len(seen_in)
    return {"union": len(seen_in), "sil": len(sil), "holes": holes, "outside": outside,
            "inter": max(0, inter)}


def dump_like(source_path, obj):
    """Стиль дампа = стиль исходного файла (проба вариантов), иначе компакт."""
    if source_path and os.path.exists(source_path):
        raw = open(source_path, encoding="utf-8").read()
        cands = [
            json.dumps(obj, ensure_ascii=False, separators=(",", ":")),
            json.dumps(obj, ensure_ascii=False),
            json.dumps(obj, ensure_ascii=False, indent=1),
        ]
        for s in cands:
            if s == raw:
                return s
    return json.dumps(obj, ensure_ascii=False, separators=(",", ":"))


def main():
    ap = argparse.ArgumentParser()
    ap.add_argument("patch", help="файл пакета правок (kns_mask_patch_*.json)")
    ap.add_argument("--root", default=ROOT, help="корень репо (по умолчанию сам репо)")
    ap.add_argument("--check", action="store_true", help="только проверка QC, без записи")
    ap.add_argument("--dry-run", action="store_true", help="всё, кроме записи файлов")
    args = ap.parse_args()

    root = os.path.abspath(args.root)
    patch = json.load(open(args.patch, encoding="utf-8"))
    if patch.get("format") != "kns-mask-annotator-patch" or patch.get("version") != 1:
        sys.exit("не пакет правок редактора: format/version неверные")
    frames = patch.get("frames")
    if not isinstance(frames, list) or not frames:
        sys.exit("в пакете нет кадров (frames пуст)")

    problems = []
    touched = {}
    for fr in frames:
        if not isinstance(fr, dict) or not all(k in fr for k in ("w", "h", "file", "build", "zones")):
            problems.append("кадр без обязательных полей (w/h/file/build/zones): %s" % str(fr)[:80])
            continue
        w, h, fl = fr["w"], fr["h"], fr["file"]
        fpath = os.path.join(root, fl)
        if not os.path.exists(fpath):
            problems.append("нет кадра %s" % fl)
            continue
        img = Image.open(fpath)
        if (img.width, img.height) != (w, h):
            problems.append("%s: размеры пакета %sx%s != файла %sx%s" % (fl, w, h, img.width, img.height))
        sil, fw, fh = frame_sil(fpath)
        layers = {z: sorted(set(int(p) for p in fr["zones"].get(z, []))) for z in ZONES}
        q = recompute_qc(layers, w, h, sil)
        claimed = fr.get("qc", {})
        ok = (q["holes"] == 0 and q["outside"] == 0 and q["inter"] == 0 and q["union"] == q["sil"])
        print("%-42s build=%s key=%s  px=%-5d union=%d/%d holes=%d outside=%d inter=%d  %s" % (
            fl, fr.get("build"), fr.get("canonKey"), fr.get("editsPx"),
            q["union"], q["sil"], q["holes"], q["outside"], q["inter"],
            "OK" if ok else "QC-FAIL"))
        if claimed and (claimed.get("holes") != q["holes"] or claimed.get("outside") != q["outside"]
                        or claimed.get("inter") != q["inter"]):
            print("    ! расхождение с QC из пакета: заявлено %s, по факту %s" % (claimed, q))
        if not ok:
            problems.append("%s: QC не сошёлся %s" % (fl, q))
        else:
            g = (fr.get("build") or "manual") if fr.get("canonKey") not in (None, "") else "manual"
            touched.setdefault(g, []).append((fr, layers))

    if problems:
        print("\n⛔ пакеты не применены при QC-расхождении:", len(problems))
        for p in problems:
            print("   -", p)
        sys.exit(1)

    if args.check:
        print("\n--check: QC зелёный, запись не выполнялась. Кадров: %d" % len(frames))
        return

    changed_files = []
    for build, items in sorted(touched.items()):
        if build in TARGETS:
            rel = TARGETS[build]
        else:
            rel = MANUAL
        path = os.path.join(root, rel)
        store = {}
        if os.path.exists(path):
            store = json.load(open(path, encoding="utf-8"))
        for fr, layers in items:
            if build == "manual":
                k = fr.get("frameKey") or ("%s:%s" % (fr.get("build"), fr["file"]))
            else:
                k = fr.get("canonKey")
                if k in (None, ""):
                    problems.append("кадр без canonKey попал в канон-файл: %s" % fr["file"])
                    continue
            if k in store:
                before = {z: len(store[k].get(z, [])) for z in ZONES}
                print("    перезапись ключа %s (было px: %s)" % (k, before))
                for z in ZONES:
                    store[k][z] = layers[z]      # in-place: исходный порядок под-ключей сохраняется
            else:
                store[k] = {z: layers[z] for z in ZONES}
        if args.dry_run:
            print("--dry-run: запись %s пропущена (ключей: %d)" % (rel, len(items)))
            continue
        raw = open(path, encoding="utf-8").read() if os.path.exists(path) else ""
        out = dump_like(path if raw else None, store)
        tmp = path + ".tmp"
        with open(tmp, "w", encoding="utf-8") as f:
            f.write(out)
            if raw.endswith("\n") and not out.endswith("\n"):
                f.write("\n")
        os.replace(tmp, path)
        changed_files.append(rel)
        print("✔ записано: %s (ключей в файле: %d, применено: %d)" % (rel, len(store), len(items)))

    if changed_files:
        print("\nИзменённые файлы: " + ", ".join(changed_files))
        print("Дальше: python3 tools/build_mask_annotator_data.py  — перегенерация страницы-данных.")


if __name__ == "__main__":
    main()
