#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""Сборка данных для страницы mask-annotator.html (редактор разметки зон).

Что делает:
1. (однократно, при --bf-thin/--bf-chub) вычнымляет маски телосложений skinny/chubby
   из сырых файлов генераций и кладёт канонизированную копию в artpack/
   (только ключи 0-4 — те, что подтверждены кадрами репо; QC union==silhouette).
2. Читает маски нормала (artpack/m2_layer_masks.json) и телосложений из artpack/.
3. Строит явный каталог кадров (все телосложения/серии/N-S/E-W;.hw) с указанием
   канон-ключа масок (или null — кадр без масок, старт «всё тело»).
4. Попиксельно сверяет каждую пару (кадр, маски): union==silhouette, 0 дыр/0 вне/0 пересечений.
5. Пишет обёртку artpack/mask-annotator-data.js: const KNS_MASK_ANNOTATOR_DATA = {...};
   (JS-переменная, а не fetch — на file:// fetch(JSON) запрещён CORS'ом).

Запуск из корня репо:  python3 tools/build_mask_annotator_data.py
                        [--bf-thin <путь до bf-masks/thin_layer_masks.json>]
                        [--bf-chub <путь .../chubby_layer_masks.json>]
Повторный прогон без --bf-* работает целиком по файлам репо (ре-генерация после
движения канона масок — например, после правок разметки).
"""
import argparse
import datetime
import json
import os
import sys

try:
    from PIL import Image
except ImportError:
    sys.exit("нужен Pillow: pip install pillow (или через uv)")

HERE = os.path.dirname(os.path.abspath(__file__))
ROOT = os.path.dirname(HERE)

# 13 канонических зон; порядок = приоритет вычитания
# (глаза→уши→нос→хвост→лапы(4, по сторонам «на виде»)→голова→светлые→тело)
ZONES = [
    ("eyes", "Глаза (не тонировать)"),
    ("earL", "Ухо 1 (левое на виде)"),
    ("earR", "Ухо 2 (правое на виде)"),
    ("nose", "Нос + зона морды вокруг"),
    ("tail", "Хвост"),
    ("foreL", "Передняя лапа (левая на виде)"),
    ("foreR", "Передняя лапа (правая на виде)"),
    ("hindL", "Задняя лапа/бедро (левое на виде)"),
    ("hindR", "Задняя лапа/бедро (правое на виде)"),
    ("head", "Голова (без глаз/ушей/носа)"),
    ("chest", "Грудка (светлая зона спереди)"),
    ("belly", "Живот"),
    ("body", "Тело (остаток)"),
]
ZONE_IDS = [z[0] for z in ZONES]

BF_KEYS = [str(i) for i in range(5)]  # sit + native walk 0..3 — ключи, подтверждённые кадрами


def frame_sil(path):
    """Множество flat-индексов alpha>0 + размеры."""
    im = Image.open(path).convert("RGBA")
    w, h = im.size
    px = im.load()
    s = set()
    for y in range(h):
        base = y * w
        for x in range(w):
            if px[x, y][3] > 0:
                s.add(base + x)
    return s, w, h


def qc_masks(frame_path, layers):
    total = 0
    union = set()
    for v in layers.values():
        total += len(v)
        union.update(v)
    sil, w, h = frame_sil(frame_path)
    return {
        "w": w, "h": h,
        "union": len(union), "sil": len(sil), "total": total,
        "holes": len(sil - union), "outside": len(union - sil),
        "inter": total - len(union),
    }


def build_catalog(masks_norm, masks_thin, masks_chub):
    """Каталог кадров: build -> [{key, file, label, group}]."""
    cat = {"norm": [], "thin": [], "chub": []}
    # --- norm ---
    cat["norm"].append({"key": "0", "file": "model/sit_norm.png", "label": "Сидит (родной M2)", "group": "Сид"})
    for k in range(4):
        cat["norm"].append({"key": str(k + 1), "file": "model/walk_norm_up_k%d.png" % k,
                             "label": "Ходьба вбок, фаза %d (хвост вверх)" % k, "group": "Ходьба (натив, хвост вверх)"})
    for k in range(4):
        cat["norm"].append({"key": None, "file": "model/walk_norm_down_k%d.png" % k,
                            "label": "Ходьба вбок, фаза %d (хвост вниз)" % k, "group": "Ходьба (хвост вниз)"})
    for k in range(4):
        cat["norm"].append({"key": "E%d" % k, "file": "model/dirs/E%d.png" % k,
                            "label": "Вправо ×2, фаза %d" % k, "group": "Направления E/W/N/S"})
    for k in range(4):
        cat["norm"].append({"key": "W%d" % k, "file": "model/dirs/W%d.png" % k,
                            "label": "Влево ×2, фаза %d" % k, "group": "Направления E/W/N/S"})
    for k in range(4):
        cat["norm"].append({"key": "N%d" % k, "file": "model/dirs/N%d.png" % k,
                            "label": "N (уход от камеры), фаза %d" % k, "group": "Направления E/W/N/S"})
    for k in range(4):
        cat["norm"].append({"key": "S%d" % k, "file": "model/dirs/S%d.png" % k,
                            "label": "S (на камеру), фаза %d" % k, "group": "Направления E/W/N/S"})
    # --- thin ---
    cat["thin"].append({"key": "0", "file": "model/sit_thin.png", "label": "Сидит (худая)", "group": "Сид"})
    for k in range(4):
        cat["thin"].append({"key": str(k + 1), "file": "model/walk_thin_down_k%d.png" % k,
                             "label": "Ходьба, фаза %d (натив: хвост вниз)" % k, "group": "Ходьба (натив, хвост вниз)"})
    for k in range(4):
        cat["thin"].append({"key": None, "file": "model/walk_thin_up_k%d.png" % k,
                            "label": "Ходьба, фаза %d (хвост вверх)" % k, "group": "Ходьба (хвост вверх)"})
    # --- chub ---
    cat["chub"].append({"key": "0", "file": "model/sit_chub.png", "label": "Сидит (пухлая)", "group": "Сид"})
    for k in range(4):
        cat["chub"].append({"key": str(k + 1), "file": "model/walk_chub_up_k%d.png" % k,
                            "label": "Ходьба, фаза %d (натив: хвост вверх)" % k, "group": "Ходьба (натив, хвост вверх)"})
    for k in range(4):
        cat["chub"].append({"key": None, "file": "model/walk_chub_down_k%d.png" % k,
                            "label": "Ходьба, фаза %d (хвост вниз)" % k, "group": "Ходьба (хвост вниз)"})
    return cat


def main():
    ap = argparse.ArgumentParser()
    ap.add_argument("--bf-thin", help="сырой bf-masks/thin_layer_masks.json (первичная канонизация)")
    ap.add_argument("--bf-chub", help="сырой bf-masks/chubby_layer_masks.json (первичная канонизация)")
    ap.add_argument("--allow-mismatch", action="store_true", help="не падать при QC-расхождении (печать и выход 2)")
    args = ap.parse_args()

    artpack = os.path.join(ROOT, "artpack")

    # 1) канонизация bf-масок при первом прогоне
    for src, dst, label in [
        (args.bf_thin, os.path.join(artpack, "thin_layer_masks.json"), "худой"),
        (args.bf_chub, os.path.join(artpack, "chub_layer_masks.json"), "пухлый"),
    ]:
        if src and not os.path.exists(dst):
            raw = json.load(open(src))
            out = {}
            for k in BF_KEYS:
                if k not in raw:
                    sys.exit("в bf-масках %s нет ключа %s" % (label, k))
                out[k] = {z: list(raw[k].get(z, [])) for z, _ in ZONES}
            json.dump(out, open(dst, "w"), ensure_ascii=False)
            print("канонизирован %s -> artpack/%s (ключи 0-4)" % (label, os.path.basename(dst)))

    # 2) чтение масок
    masks = {
        "norm": json.load(open(os.path.join(artpack, "m2_layer_masks.json"))),
        "thin": json.load(open(os.path.join(artpack, "thin_layer_masks.json"))),
        "chub": json.load(open(os.path.join(artpack, "chub_layer_masks.json"))),
    }

    # 3) каталог + 4) QC
    cat = build_catalog(masks["norm"], masks["thin"], masks["chub"])
    bad = 0
    total_frames = 0
    masked_frames = 0
    for build, frames in cat.items():
        for fr in frames:
            total_frames += 1
            path = os.path.join(ROOT, fr["file"])
            if not os.path.exists(path):
                print("⛔ НЕТ КАДРА: %s %s" % (build, fr["file"]))
                bad += 1
                continue
            if fr["key"] is None:
                continue
            masked_frames += 1
            if fr["key"] not in masks[build]:
                print("⛔ НЕТ КЛЮЧА МАСОК: %s %s" % (build, fr["key"]))
                bad += 1
                continue
            q = qc_masks(path, masks[build][fr["key"]])
            okflag = q["holes"] == 0 and q["outside"] == 0 and q["inter"] == 0 and q["union"] == q["sil"]
            if not okflag:
                print("⛔ QC %s/%s %s: %s" % (build, fr["key"], fr["file"], q))
                bad += 1
    print("кадров в каталоге: %d, с масками: %d, QC-расхождений: %d" % (total_frames, masked_frames, bad))
    if bad:
        if args.allow_mismatch:
            sys.exit(2)
        sys.exit("QC не сошёлся — правь источники, а не флаг")

    # 5) обёртка
    data = {
        "format": 1,
        "generated": datetime.datetime.now().isoformat(timespec="seconds"),
        "zones": [{"id": z, "label": l} for z, l in ZONES],
        "zonePriority": ZONE_IDS,
        "buildLabels": {"norm": "Среднее", "thin": "Худая", "chub": "Пухлая"},
        "builds": cat,
        "masks": masks,
    }
    payload = json.dumps(data, ensure_ascii=False, separators=(",", ":"))
    out = os.path.join(artpack, "mask-annotator-data.js")
    with open(out, "w", encoding="utf-8") as f:
        f.write("// Сгенерировано tools/build_mask_annotator_data.py — НЕ править руками.\n")
        f.write("// Источники: artpack/m2_layer_masks.json (нормал) + artpack/{thin,chub}_layer_masks.json.\n")
        f.write("const KNS_MASK_ANNOTATOR_DATA = ")
        f.write(payload)
        f.write(";\n")
    print("OK: %s (%d байт)" % (out, os.path.getsize(out)))


if __name__ == "__main__":
    main()
