#!/usr/bin/env python3
"""KNS sprite pipeline: сырые листы gemini-flash-image → кадры 100×150 + QC + выбор фаз + превью.

Команды:
  process  — raw-листы (raw/<СЕРИЯ>_<pool>.png или *.png) → frames/, отчёт process_report.json
  preview  — frames/*_k{0..3}.png → автономный HTML с canvas-анимацией (PNG base64, 280 мс)
  palette  — фактическая палитра кадра (для промптов и style-скора django)

Правила, выстраданные 2026-11-04..05 (гонка M2, ракурсы N/S, bodyforms):
  * ПОЛ (чёрная полоса-«ground line») стирается на уровне ЛИСТА до сегментации,
    иначе слипшиеся коты не режутся; остатки — crop_floor по нижним строкам кадра.
  * ФИЛЬТРЫ ПЛОЩАДИ/МУСОРА — только ПОСЛЕ fit 100×150 (сырой сегмент всегда «слипшийся»).
  * стиль-скор — по палитре, измеренной из ФИНАЛЬНЫХ кадров (факт #F0B863/#F7E2C3,
    а НЕ из досье #E7BD8C — иначе скор занижается вдвое).
  * cc-сетка с шагом 2 обязана tolerant-делить размер (нечётные ширины).
"""
import argparse
import base64
import glob
import itertools
import json
import os
import sys
from collections import Counter

from PIL import Image

TW, TH = 100, 150
DEFAULT_PAL = [(240, 184, 99), (247, 226, 195), (94, 62, 40)]  # тело / крем / контур (факт M2)


def dist(p, q):
    return abs(p[0] - q[0]) + abs(p[1] - q[1]) + abs(p[2] - q[2])


# ---------- альфа ----------
def alpha_to_bg(im, d0=45, d1=110, floor=64):
    """Двухступенчатое «белое→прозрачное» по расстоянию от цвета фона (угол 4,4)."""
    im = im.convert("RGBA")
    W, H = im.size
    p = im.load()
    bg = im.getpixel((4, 4))[:3]
    out = Image.new("RGBA", (W, H))
    po = out.load()
    for y in range(H):
        for x in range(W):
            q = p[x, y]
            d = dist(q[:3], bg)
            a = 0 if d <= d0 else (255 if d >= d1 else int((d - d0) * 255 / (d1 - d0)))
            if a < floor:
                a = 0
            po[x, y] = (q[0], q[1], q[2], min(a, q[3]))
    return out


def erase_floor(im, dark_frac=0.5, min_dark=30):
    """Стирает полосы-пол на уровне ЛИСТА: строки, где ≥dark_frac непрозрачных (≠bg) пикселей — тёмные."""
    im = im.convert("RGBA")
    W, H = im.size
    p = im.load()
    bg = im.getpixel((4, 4))
    erased = []
    for y in range(H):
        dark = nonbg = 0
        for x in range(W):
            q = p[x, y]
            if dist(q[:3], bg[:3]) >= 30:
                nonbg += 1
                if q[0] < 120 and q[1] < 95 and q[2] < 95:
                    dark += 1
        if nonbg >= min_dark and dark / max(1, nonbg) >= dark_frac:
            erased.append(y)
    for y in erased:
        for x in range(W):
            p[x, y] = (bg[0], bg[1], bg[2], 255)
    return im, len(erased)


def crop_floor(im, max_rows=10, dark_frac=0.55):
    """Срезает нижние строки кадра, залитые тёмным «полом» (после erase_floor остаются хвосты)."""
    b = bbox(im)
    if not b:
        return im
    x0, y0, x1, y1 = b
    p = im.load()
    cut = 0
    for y in range(y1, max(y1 - max_rows, y0), -1):
        row = [p[x, y] for x in range(x0, x1 + 1) if p[x, y][3] > 8]
        if not row:
            break
        dark = sum(1 for q in row if q[0] < 120 and q[1] < 95 and q[2] < 95)
        if dark / len(row) >= dark_frac:
            cut += 1
        else:
            break
    if cut:
        im = im.crop((0, 0, im.size[0], y1 + 1 - cut))
    return im


# ---------- геометрия ----------
def bbox(im):
    W, H = im.size
    p = im.load()
    x0, y0, x1, y1 = W, H, -1, -1
    for y in range(H):
        for x in range(W):
            if p[x, y][3] > 8:
                if x < x0: x0 = x
                if x > x1: x1 = x
                if y < y0: y0 = y
                if y > y1: y1 = y
    return (x0, y0, x1, y1) if x1 >= 0 else None


def fit(im, tw=TW, th=TH):
    """Кроп по bbox → NEAREST-фит → опора у нижнего края, центр по X."""
    b = bbox(im)
    if not b:
        return None
    x0, y0, x1, y1 = b
    crop = im.crop((x0, y0, x1 + 1, y1 + 1))
    cw, ch = crop.size
    sc = min(tw / cw, th / ch)
    nw, nh = max(1, round(cw * sc)), max(1, round(ch * sc))
    small = crop.resize((nw, nh), Image.NEAREST)
    canvas = Image.new("RGBA", (tw, th), (0, 0, 0, 0))
    canvas.alpha_composite(small, ((tw - nw) // 2, th - nh))
    return canvas


def cc_boxes(im, thresh=30, min_area=3000):
    """Connected components (шаг 2) по отличию от фона → bbox блобов ≥ min_area px."""
    W, H = im.size
    p = im.load()
    bg = im.getpixel((8, 8))[:3]
    step = 2
    mw, mh = (W + step - 1) // step, (H + step - 1) // step  # фикс нечётных размеров
    mask = [[False] * mw for _ in range(mh)]
    for y in range(0, H, step):
        row = mask[y // step]
        for x in range(0, W, step):
            if dist(p[x, y][:3], bg) >= thresh:
                row[x // step] = True
    lab = [[0] * mw for _ in range(mh)]
    parent = [0]

    def find(a):
        while parent[a] != a:
            parent[a] = parent[parent[a]]
            a = parent[a]
        return a

    def union(a, b):
        ra, rb = find(a), find(b)
        if ra != rb:
            parent[max(ra, rb)] = min(ra, rb)

    nid = 1
    for y in range(mh):
        for x in range(mw):
            if not mask[y][x]:
                continue
            up = lab[y - 1][x] if y > 0 else 0
            lf = lab[y][x - 1] if x > 0 else 0
            if up and lf:
                lab[y][x] = up
                if up != lf:
                    union(up, lf)
            elif up or lf:
                lab[y][x] = up or lf
            else:
                parent.append(nid)
                lab[y][x] = nid
                nid += 1
    stats = {}
    for y in range(mh):
        for x in range(mw):
            if lab[y][x]:
                r = find(lab[y][x])
                s = stats.setdefault(r, [0, mw, 0, mh, 0])
                s[0] += 1
                if x < s[1]: s[1] = x
                if x > s[2]: s[2] = x
                if y < s[3]: s[3] = y
                if y > s[4]: s[4] = y
    out = []
    for r, (a, x0, x1, y0, y1) in stats.items():
        if a * step * step >= min_area:
            out.append((x0 * step, y0 * step, (x1 + 1) * step, (y1 + 1) * step))
    out.sort(key=lambda b: (b[1], b[0]))
    return out


def col_split(im, box, gap_px=4, min_len=150):
    """Широкий блоб-полоса → сегменты по пустым колонкам (профиль «котопикселей», порог 5)."""
    W, H = im.size
    p = im.load()
    bg = p[8, 8]
    x0, y0, x1, y1 = box
    prof = []
    for x in range(x0, min(x1, W)):
        n = 0
        for y in range(max(0, y0), min(H, y1), 3):
            if dist(p[x, y][:3], bg[:3]) >= 90:
                n += 1
        prof.append(n)
    segs = []
    on = False
    s = 0
    for i, v in enumerate(prof):
        if v >= 5 and not on:
            on = True
            s = i
        elif v < 5 and on:
            if i - s >= min_len:
                segs.append((x0 + s - gap_px, y0, x0 + i + gap_px, y1))
            on = False
    if on and len(prof) - s >= min_len:
        segs.append((x0 + s - gap_px, y0, x0 + len(prof) + gap_px, y1))
    return segs


def valleys(profile, n_parts, window=None):
    """Фокус-долины сплошного блоба: argmin сглаженного профиля в зоне k·(1/N)±0.18 — НЕ глобальный argmin."""
    if window is None:
        window = max(3, len(profile) // 30)
    sm = [sum(profile[max(0, i - window): i + window + 1]) / (2 * window + 1) for i in range(len(profile))]
    cuts = []
    Wp = len(sm)
    for k in range(1, n_parts):
        lo = max(1, int(Wp * (k / n_parts - 0.18)))
        hi = min(Wp - 1, int(Wp * (k / n_parts + 0.18)))
        cuts.append(min(range(lo, hi), key=lambda i: sm[i]))
    return cuts


def split_blob(im, box, n_parts):
    """Сплошной blob (без зазоров) → n_parts кусков фокус-долинами."""
    p = im.load()
    bg = p[8, 8][:3]
    x0, y0, x1, y1 = box
    prof = []
    for x in range(x0, min(x1, im.size[0])):
        n = 0
        for y in range(y0, min(y1, im.size[1]), 4):
            if dist(p[x, y][:3], bg) >= 60:
                n += 1
        prof.append(n)
    cuts = valleys(prof, n_parts)
    edges = [x0] + [x0 + c for c in cuts] + [x1]
    return [(edges[i], y0, edges[i + 1], y1) for i in range(len(edges) - 1)]


# ---------- QC ----------
def measure(im, pal):
    """Кадр 100×150 → (px, aspect, style, green, islands): после фита — все фильтры здесь."""
    b = bbox(im)
    if not b:
        return None
    w, h = b[2] - b[0] + 1, b[3] - b[1] + 1
    px = style = green = 0
    cc = 0
    seen = [[False] * TW for _ in range(TH)]
    p = im.load()
    for y in range(TH):
        for x in range(TW):
            q = p[x, y]
            if q[3] > 64:
                px += 1
                if min(dist(q[:3], c) for c in pal) <= 55:
                    style += 1
                if q[1] > q[0] + 25 and q[1] > q[2] + 25:
                    green += 1
                # заодно первый проход CC
                if not seen[y][x]:
                    stack = [(x, y)]
                    seen[y][x] = True
                    area = 0
                    while stack:
                        cx, cy = stack.pop()
                        area += 1
                        for dx, dy in ((1, 0), (-1, 0), (0, 1), (0, -1)):
                            nx, ny = cx + dx, cy + dy
                            if 0 <= nx < TW and 0 <= ny < TH and not seen[ny][nx] and p[nx, ny][3] > 40:
                                seen[ny][nx] = True
                                stack.append((nx, ny))
                        if area > 200000:
                            break
                    if area >= 50:
                        cc += 1
    if px < 100:
        return None
    return {"px": px, "aspect": round(w / h, 2), "style": round(style / px, 3),
            "green": round(green / px, 3), "islands": cc}


def frame_diff(i1, i2):
    """Доля пикселей |ΔRGB|>30 в объединённой маске alpha>64 — арбитр живости/дублей."""
    p1, p2 = i1.load(), i2.load()
    diff = mask = 0
    for y in range(TH):
        for x in range(TW):
            a1, a2 = p1[x, y][3], p2[x, y][3]
            if a1 > 64 or a2 > 64:
                mask += 1
                if a1 > 64 and a2 > 64 and dist(p1[x, y][:3], p2[x, y][:3]) > 30:
                    diff += 1
    return diff / max(1, mask)


def measure_palette(paths, top=6):
    """Фактическая палитра финальных кадров (частота, alpha>200). ПРАВИЛО: мерить из кадров, не из досье."""
    c = Counter()
    for path in paths:
        if not os.path.exists(path):
            continue
        im = Image.open(path).convert("RGBA")
        for q in im.getdata():
            if q[3] > 200:
                c[(q[0], q[1], q[2])] += 1
    return [(k, v, round(v / max(1, sum(c.values())), 4)) for k, v in c.most_common(top)]


# ---------- process ----------
def sheet_to_frames(path, expect_n, kind, pal, verbose=True):
    """raw-лист → кадры 100×150 (список [(имя, Image, метры)])."""
    name = os.path.basename(path).replace(".png", "")
    im, floor = erase_floor(Image.open(path))
    boxes = cc_boxes(im)
    segs = []
    for b in boxes:
        w, h = b[2] - b[0], b[3] - b[1]
        if w / h > 2.2 or (kind == "walk" and w > h and len(boxes) < expect_n):
            segs += col_split(im, b, min_len=max(60, int(w / 6)))
        else:
            segs.append(b)
    if kind == "walk" and len(segs) < expect_n and len(boxes) == 1:
        segs = split_blob(im, boxes[0], expect_n)
    if verbose:
        print(f"  {name}: {im.size[0]}x{im.size[1]}, пол-строк {floor}, блобы {len(boxes)} → сегментов {len(segs)}")
    out = []
    for i, b in enumerate(segs):
        fr = alpha_to_bg(im.crop(b))
        fr = crop_floor(fr)
        fitted = fit(fr)
        if fitted is None:
            continue
        m = measure(fitted, pal)
        if m is None:
            continue
        # ФИЛЬТРЫ ПОСЛЕ ФИТА (сырой сегмент всегда большой — не фильтровать до fit!)
        ok = True
        if kind == "walk":
            ok = 1500 <= m["px"] <= 12000 and 0.55 <= m["aspect"] <= 1.75
        else:
            ok = 2500 <= m["px"] <= 16000 and 0.35 <= m["aspect"] <= 1.60
        ok = ok and m["green"] < 0.05
        if verbose:
            why = "" if ok else " ← отбракован"
            print(f"      {name}_s{i}: px {m['px']}, aspect {m['aspect']}, стиль {m['style']}, "
                  f"зелень {m['green']}, островов {m['islands']}{why}")
        if ok:
            out.append((f"{name}_s{i}", fitted, m))
    return out


def pick_quartet(pool, pal, label, verbose=True):
    """Лучший цикл 4 фаз: сперва нативные первые-4 каждого листа, затем перестановки пула."""
    if len(pool) < 4:
        print(f"    {label}: кадров {len(pool)} < 4 — НЕ ХВАТАЕТ (догенерировать пул)")
        return None
    sheets = {}
    for key, f, m in pool:
        sheets.setdefault(key.rsplit("_s", 1)[0], []).append((key, f, m))
    cands = []
    for sheet, items in sheets.items():
        if len(items) >= 4:
            cands.append(items[:4])
    # перестановочный бонус-пул: лучшие 8 кадров по стилю
    extra = sorted(pool, key=lambda t: -t[2]["style"])[:8]
    if extra:
        cands.append(extra[:4])
    best = None
    for cand in cands:
        fs = [f for _, f, _ in cand]
        keys = [k for k, _, _ in cand]
        d = [frame_diff(fs[i], fs[(i + 1) % 4]) for i in range(4)]
        st = sum(m["style"] for _, _, m in cand) / 4
        hs = [bbox(f)[3] - bbox(f)[1] for f in fs]
        hspread = (max(hs) - min(hs)) / max(hs)
        ok = min(d[:3]) >= 0.16 and d[3] >= 0.12 and st >= 0.5 and hspread <= 0.25
        if verbose:
            print(f"    {label}/{keys[0].split('_s')[0]}: диффы {d[0]:.2f}/{d[1]:.2f}/{d[2]:.2f}, "
                  f"замык {d[3]:.2f}, стиль {st:.2f}, h-разброс {hspread:.2f} {'OK' if ok else 'мимо'}")
        if ok:
            val = (round(min(d[:3]), 3), st)
            if best is None or val > best[0]:
                best = (val, cand)
    if not best and len(pool) >= 4:
        # слабые пороги: если ничто не прошло — лучший по совокупности, но пометить слабость
        alt = None
        for cand in cands:
            fs = [f for _, f, _ in cand]
            d = [frame_diff(fs[i], fs[(i + 1) % 4]) for i in range(4)]
            st = sum(m["style"] for _, _, m in cand) / 4
            val = (round(min(d[:3]) + d[3], 3) + st, st)
            if alt is None or val > alt[0]:
                alt = (val, cand, d)
        if alt:
            keys = [k for k, _, _ in alt[1]]
            print(f"    {label}: СЛАБЫЙ кандидат (пороги не прошли) — {keys}, диффы "
                  f"{[round(x, 2) for x in alt[2]]} — на взгляд заказчицы")
    return best[1] if best else (alt[1] if alt else None)


def cmd_process(args):
    D = os.path.abspath(args.dir)
    raw_dir = os.path.join(D, "raw") if os.path.isdir(os.path.join(D, "raw")) else D
    out_dir = os.path.join(D, "frames")
    os.makedirs(out_dir, exist_ok=True)

    # палитра для скора: из эталонных кадров, переданных --ref-frames, иначе дефолт (факт M2)
    ref_paths = []
    for pat in (args.ref_frames or []):
        ref_paths += sorted(glob.glob(os.path.expanduser(pat)))
    pal = DEFAULT_PAL
    if ref_paths:
        pm = measure_palette(ref_paths)
        if pm:
            pal = [c for c, _, _ in pm] + [(94, 62, 40)]
            print(f"палитра из эталона: " + ", ".join("#%02X%02X%02X" % c for c, _, _ in pm))

    files = sorted(glob.glob(os.path.join(raw_dir, "*.png")))
    if args.filter:
        files = [f for f in files if args.filter in os.path.basename(f)]
    kind = args.kind
    pools = {}
    for f in files:
        stem = os.path.basename(f)[:-4]
        # суффикс пула (_a/_b/_c) — не часть имени серии; снимаем всем сериям единообразно
        core = stem.rsplit("_", 1)[0] if stem.rsplit("_", 1)[-1].isascii() and len(stem.rsplit("_", 1)[-1]) <= 2 else stem
        series = core
        pools.setdefault(series, []).extend(sheet_to_frames(f, args.frames, kind, pal))

    report = {}
    for series, items in sorted(pools.items()):
        print(f"== {series}: пул {len(items)}")
        if kind == "walk":
            quartet = pick_quartet(items, pal, series)
            if quartet:
                rec = {"keys": [k for k, _, _ in quartet],
                       "style": round(sum(m["style"] for _, _, m in quartet) / 4, 3)}
                for i, (_, f, _) in enumerate(quartet):
                    f.save(os.path.join(out_dir, f"{series}_k{i}.png"))
                d = [frame_diff(quartet[i][1], quartet[(i + 1) % 4][1]) for i in range(4)]
                rec["diffs"] = [round(x, 3) for x in d]
                report[series] = rec
                print(f"    ВЫБРАНО → {out_dir}/{series}_k0..3.png, диффы {[round(x, 2) for x in d]}")
            else:
                report[series] = None
        else:
            best = max(items, key=lambda t: t[2]["style"] - t[2]["green"] * 2) if items else None
            if best:
                best[1].save(os.path.join(out_dir, f"{series}_sit.png"))
                report[series] = {"key": best[0], "meters": best[2]}
                print(f"    ВЫБРАНО: {best[0]} {best[2]}")
            else:
                report[series] = None
    rp = os.path.join(D, "process_report.json")
    if os.path.exists(rp):  # прогон walk не должен затирать отчёт прогона sit (и наоборот) — merge
        try:
            old = json.load(open(rp))
            old.update(report)
            report = old
        except Exception:
            pass
    json.dump(report, open(rp, "w"), ensure_ascii=False, indent=1)
    print("отчёт →", rp)


# ---------- preview ----------
def cmd_preview(args):
    fr_dir = os.path.abspath(args.frames)
    series = {}
    for f in sorted(glob.glob(os.path.join(fr_dir, "*.png"))):
        stem = os.path.basename(f)[:-4]
        if "_k" in stem or "_sit" in stem:
            series.setdefault(stem.rsplit("_k", 1)[0].rsplit("_sit", 1)[0], []).append(f)
    if not series:
        print("кадры не найдены:", fr_dir)
        return
    tile = ""
    for cand in (os.path.join(fr_dir, "..", "field_tile.png"), os.path.join(fr_dir, "field_tile.png")):
        if os.path.exists(cand):
            tile = "data:image/png;base64," + base64.b64encode(open(cand, "rb").read()).decode()
            break
    out = ["<html><head><meta charset='utf-8'><title>KNS preview</title><style>",
           "body{font-family:system-ui;background:#24211c;color:#eee;margin:16px}",
           ".card{display:inline-block;margin:8px;padding:8px;background:#1e1b17;border-radius:8px;text-align:center}",
           "canvas{image-rendering:pixelated;background:#616517;border-radius:4px}",
           (".tile canvas{background:url('%s');background-size:64px}" % tile) if tile else "",
           "</style></head><body>"]
    sets = []
    for name, files in sorted(series.items()):
        frames64 = [base64.b64encode(open(f, "rb").read()).decode() for f in files]  # только PNG (JPEG жжёт альфу)
        sets.append((name, frames64))
    out.append("<script>const SETS=%s;</script>" % json.dumps(sets))
    out.append("""<script>
function mk(name, frames){
  const d=document.createElement('div');d.className='card';
  const c=document.createElement('canvas');c.width=100;c.height=150;[c.style].forEach(()=>0);
  const t=document.createElement('div');t.textContent=name;
  d.append(t,c);document.body.appendChild(d);
  const ctx=c.getContext('2d');
  const imgs=frames.map(b64=>{const i=new Image();i.src='data:image/png;base64,'+b64;return i;});
  let k=0;
  function tick(){
    if(!imgs.every(i=>i.complete)) return;
    ctx.clearRect(0,0,100,150);
    const im=imgs[k%imgs.length];
    const sc=Math.min(100/im.width,150/im.height);
    ctx.drawImage(im,(100-im.width*sc)/2,150-im.height*sc,im.width*sc,im.height*sc);
    k++;
  }
  setInterval(tick,280);
}
SETS.forEach(s=>mk(s[0],s[1]));
</script></body></html>""")
    dest = args.out or os.path.join(fr_dir, "preview.html")
    open(dest, "w").write("\n".join(out))
    print("preview →", dest)


# ---------- palette ----------
def cmd_palette(args):
    pm = measure_palette(args.framefiles)
    total = sum(v for _, _, v in pm)
    for c, n, share in pm:
        print("#%02X%02X%02X  %6d  %5.1f%%" % (c[0], c[1], c[2], n, 100 * share))


def main():
    ap = argparse.ArgumentParser(description=__doc__, formatter_class=argparse.RawDescriptionHelpFormatter)
    sub = ap.add_subparsers(dest="cmd", required=True)
    p = sub.add_parser("process")
    p.add_argument("--dir", required=True, help="папка волны (внутри raw/*.png или сразу *.png)")
    p.add_argument("--kind", choices=["walk", "sit"], default="walk")
    p.add_argument("--frames", type=int, default=4, help="ожидаемое число кадров walk-листа")
    p.add_argument("--filter", help="подстрока в имени файла (одна серия)")
    p.add_argument("--ref-frames", nargs="*", help="PNG-эталоны для палитры скора (glob), напр. mf/M2w_k*.png")
    p.set_defaults(fn=cmd_process)
    p = sub.add_parser("preview")
    p.add_argument("--frames", required=True, help="папка frames/ с *_k0..3.png / *_sit.png")
    p.add_argument("--out", help="куда писать HTML")
    p.set_defaults(fn=cmd_preview)
    p = sub.add_parser("palette")
    p.add_argument("framefiles", nargs="+", help="PNG кадры для замера")
    p.set_defaults(fn=cmd_palette)
    args = ap.parse_args()
    args.fn(args)


if __name__ == "__main__":
    main()
