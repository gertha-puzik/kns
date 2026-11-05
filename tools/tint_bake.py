#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""tint_bake — серые маски M2-модели для рантайм-тонировки (карточка t_69e8c0f2).

Целевой формат досье: серые маски + тонирование на canvas в рантайме,
кеш по (код, поза, кадр), PNG-bake опционален.

Вход (вне репо, kns-generations-2026-11-05/):
  - слои-маски: m2_layer_masks.json, bf-masks/{thin,chubby}_layer_masks.json
    (21 ключ: '0' sit, '1'..'4' walk-E 100×150, E*=x2, W*=зеркало, N*/S*)
  - исходные кадры-источники (см. FRAME_MAP ниже)
Выход (в репо):
  - gray/{norm,thin,chub}/{key}_{layer}.png  — 9 мех-слоёв: RGB=нормированная
    люминанция (нейтральный серый), A=альфа исходника (мягкие края сохраняются)
  - gray/{build}/{key}_protect.png           — protect-зоны (глаза, нос,
    розовые раковины ушей): RGB/A исходника БАЙТ-В-БАЙТ
  - gray/tint_meta.json                      — карта ключей/слоёв для движка
Отчёт с smoke-цифрами — tint_report.json в scratch (в devlog уходит выжимка).

Слои и покраска по коду (cut_from-паритет kns.js L546-557: цвет родителя
по альфе маски; наш «родитель» = плоская заливка палитры дампа):
  tail -> слот 15 (TailBase), earL/earR fur -> слот 17 (EarBase),
  body/head/fore/hind/chest/belly -> слот 0 (Base, палитра 0 дампа = 24 цвета).
  eyes/nose/ушка-раковина — protect: НЕ тонировать (глаза/нос — гейты CatWar,
  раковина — палитра 5, файлы 404).
"""
import json
import os
import statistics
import sys

try:
    from PIL import Image
except ImportError:
    sys.exit('нужен Pillow: uv pip install pillow / pip install pillow')

ROOT = os.path.dirname(os.path.dirname(os.path.abspath(__file__)))
GENS_DEFAULT = os.path.expanduser('~/Desktop/dev/catwar/research/kns-clone/kns-generations-2026-11-05')
GENS = os.environ.get('KNS_GENERATIONS', sys.argv[sys.argv.index('--gens') + 1] if '--gens' in sys.argv else GENS_DEFAULT)
MEASURE = '--measure' in sys.argv
OUT_DIR = os.path.join(ROOT, 'gray')

FUR_LAYERS = ['tail', 'body', 'head', 'fore', 'hind', 'chest', 'belly', 'earL', 'earR']
FUR_COAT_LAYERS = ['tail', 'body', 'head', 'fore', 'hind']  # «мех» для калибровки K
PROTECT_STATIC = ['eyes', 'nose']
MEDIAN_LUM_TARGET = 235

W, H = 100, 150

# карты источник-кадров: ключ маски -> файл в kns-generations-2026-11-05/
FRAME_MAP = {
    'norm': {
        '0': 'mf/M2s_f.png',
        '1': 'mf/M2w_k0.png', '2': 'mf/M2w_k1.png', '3': 'mf/M2w_k2.png', '4': 'mf/M2w_k3.png',
        'N0': 'dirs-ns/final_N0.png', 'N1': 'dirs-ns/final_N1.png', 'N2': 'dirs-ns/final_N2.png', 'N3': 'dirs-ns/final_N3.png',
        'S0': 'dirs-ns/final_S0.png', 'S1': 'dirs-ns/final_S1.png', 'S2': 'dirs-ns/final_S2.png', 'S3': 'dirs-ns/final_S3.png',
    },
    'thin': {
        '0': 'bodyforms/frames/sit_thin_sit.png',
        '1': 'bodyforms/frames/walk_thin_down_k0.png', '2': 'bodyforms/frames/walk_thin_down_k1.png',
        '3': 'bodyforms/frames/walk_thin_down_k2.png', '4': 'bodyforms/frames/walk_thin_down_k3.png',
        'N0': 'bf-masks/frames/THIN_N_k0.png', 'N1': 'bf-masks/frames/THIN_N_k1.png',
        'N2': 'bf-masks/frames/THIN_N_k2.png', 'N3': 'bf-masks/frames/THIN_N_k3.png',
        'S0': 'bf-masks/frames/THIN_S_k0.png', 'S1': 'bf-masks/frames/THIN_S_k1.png',
        'S2': 'bf-masks/frames/THIN_S_k2.png', 'S3': 'bf-masks/frames/THIN_S_k3.png',
    },
    'chub': {
        '0': 'bodyforms/frames/sit_chubby_sit.png',
        '1': 'bodyforms/frames/walk_chub_up_k0.png', '2': 'bodyforms/frames/walk_chub_up_k1.png',
        '3': 'bodyforms/frames/walk_chub_up_k2.png', '4': 'bodyforms/frames/walk_chub_up_k3.png',
        'N0': 'bf-masks/frames/CHUB_N_k0.png', 'N1': 'bf-masks/frames/CHUB_N_k1.png',
        'N2': 'bf-masks/frames/CHUB_N_k2.png', 'N3': 'bf-masks/frames/CHUB_N_k3.png',
        'S0': 'bf-masks/frames/CHUB_S_k0.png', 'S1': 'bf-masks/frames/CHUB_S_k1.png',
        'S2': 'bf-masks/frames/CHUB_S_k2.png', 'S3': 'bf-masks/frames/CHUB_S_k3.png',
    },
}
MASKS_FILE = {
    'norm': 'm2_layer_masks.json',
    'thin': os.path.join('bf-masks', 'thin_layer_masks.json'),
    'chub': os.path.join('bf-masks', 'chubby_layer_masks.json'),
}
BUILD_LABEL = {'norm': 'Среднее', 'thin': 'Худой', 'chub': 'Пухлый'}
BUILD_TAIL = {'norm': 'up', 'thin': 'down', 'chub': 'up'}  # хвост walk-серии, на которой построены маски

# продукт-копии кадров (model/) — для инфо-сверки пиксельного совпадения
MODEL_FRAME = {
    'norm': {'0': 'model/sit_norm.png',
             '1': 'model/walk_norm_up_k0.png', '2': 'model/walk_norm_up_k1.png',
             '3': 'model/walk_norm_up_k2.png', '4': 'model/walk_norm_up_k3.png'},
    'thin': {'0': 'model/sit_thin.png',
             '1': 'model/walk_thin_down_k0.png', '2': 'model/walk_thin_down_k1.png',
             '3': 'model/walk_thin_down_k2.png', '4': 'model/walk_thin_down_k3.png'},
    'chub': {'0': 'model/sit_chub.png',
             '1': 'model/walk_chub_up_k0.png', '2': 'model/walk_chub_up_k1.png',
             '3': 'model/walk_chub_up_k2.png', '4': 'model/walk_chub_up_k3.png'},
}


def lum(px):
    r, g, b = px[0], px[1], px[2]
    return 0.299 * r + 0.587 * g + 0.114 * b


def load_img(relpath):
    im = Image.open(os.path.join(GENS, relpath)).convert('RGBA')
    assert im.size == (W, H), f'{relpath}: {im.size} != {(W, H)}'
    return im


def grid_key(key):
    """Ключи 100×150 ('0'..'4', N*, S*). E*/W* — производные, только валидация."""
    return not key.startswith('E') and not key.startswith('W')


def main():
    report = {'builds': {}, 'smoke': [], 'validation': []}

    for build in ('norm', 'thin', 'chub'):
        masks = json.load(open(os.path.join(GENS, MASKS_FILE[build])))
        keys100 = sorted([k for k in masks if grid_key(k)], key=lambda k: (k[0] == '0', len(k), k))
        assert len(keys100) == 13, f'{build}: ждём 13 ключей 100×150, есть {keys100}'

        # --- калибровка K: медиана люминанции меха по билду ---
        coat_lums = []
        for key in keys100:
            im = load_img(FRAME_MAP[build][key])
            pa = im.load()
            for L in FUR_COAT_LAYERS:
                for i in masks[key][L]:
                    x, y = i % W, i // W
                    coat_lums.append(lum(pa[x, y]))
        K = MEDIAN_LUM_TARGET / statistics.median(coat_lums)
        report['builds'][build] = {'K': round(K, 4), 'coat_px': len(coat_lums),
                                   'median_lum': round(statistics.median(coat_lums), 1)}
        print(f'== {build}: K = {K:.3f} (мех {len(coat_lums)} px, медиана lum '
              f'{statistics.median(coat_lums):.0f} -> {MEDIAN_LUM_TARGET})')

        if MEASURE:
            # замер цвета ушных зон — для настройки protect-правила раковины
            for key in ('0',):
                im = load_img(FRAME_MAP[build][key])
                pa = im.load()
                from collections import Counter
                cnt = Counter()
                for ear in ('earL', 'earR'):
                    for i in masks[key][ear]:
                        x, y = i % W, i // W
                        cnt[pa[x, y][:3]] += 1
                    top = cnt.most_common(14)
                    print(f'  {build} {key} {ear}: ' + ', '.join(f'{c}:{n}' for c, n in top))
                continue

        # --- бейк ключей 100×150 ---
        layers_meta = {}
        for key in keys100:
            im = load_img(FRAME_MAP[build][key])
            pa = im.load()
            px_of = {}
            koord = {}
            for L in list(masks[key].keys()):
                koord[L] = masks[key][L]
                for i in koord[L]:
                    px_of[i] = L

            # smoke-0: маски покрывают силуэт без дыр/пересечений (повтор родительского)
            sil = sum(1 for y in range(H) for x in range(W) if pa[x, y][3] > 0)
            assert len(px_of) == sil, f'{build}/{key}: маски {len(px_of)} px != силуэт {sil} px'

            # --- PNG-слои ---
            os.makedirs(os.path.join(OUT_DIR, build), exist_ok=True)
            protect = Image.new('RGBA', (W, H), (0, 0, 0, 0))
            ppa = protect.load()
            ear_pink = 0
            layer_px = {}
            for L in FUR_LAYERS:
                gray_im = Image.new('RGBA', (W, H), (0, 0, 0, 0))
                gpa = gray_im.load()
                n = 0
                for i in koord[L]:
                    x, y = i % W, i // W
                    src = pa[x, y]
                    if L in ('earL', 'earR') and is_ear_shell(src):
                        ppa[x, y] = src       # раковина уха — protect (розовое не тонировать)
                        ear_pink += 1
                        continue
                    g = int(round(lum(src) * K))
                    g = max(0, min(255, g))
                    gpa[x, y] = (g, g, g, src[3])
                    n += 1
                gray_im.save(os.path.join(OUT_DIR, build, f'{key}_{L}.png'), optimize=True)
                layer_px[L] = n
            for L in PROTECT_STATIC:
                for i in koord[L]:
                    x, y = i % W, i // W
                    ppa[x, y] = pa[x, y]
            protect.save(os.path.join(OUT_DIR, build, f'{key}_protect.png'), optimize=True)
            layer_px['protect'] = sum(1 for y in range(H) for x in range(W) if ppa[x, y][3] > 0)

            # smoke-1: весь силуэт покрыт ровно один раз (fur-gray ∪ protect == силуэт)
            covered = {}
            for L in FUR_LAYERS:
                for i in koord[L]:
                    covered[i] = covered.get(i, 0) + 1
            dup = sum(1 for v in covered.values() if v > 1)
            moved = sum(1 for i in koord['earL'] + koord['earR'] if is_ear_shell(pa[i % W, i // W]))
            assert dup == 0, f'{build}/{key}: дубли слоёв {dup}'
            fur_px = sum(layer_px[L] for L in FUR_LAYERS)
            assert fur_px + layer_px['protect'] == sil, \
                f'{build}/{key}: fur {fur_px} + protect {layer_px["protect"]} != силуэт {sil}'

            report['smoke'].append({
                'build': build, 'key': key, 'silhouette_px': sil,
                'fur_px': fur_px, 'protect_px': layer_px['protect'],
                'ear_shell_px': ear_pink,
                'layers': {L: layer_px[L] for L in FUR_LAYERS}
                if key == '0' else None,
            })
            print(f'  {build}/{key}: fur {fur_px}, protect {layer_px["protect"]} '
                  f'(уха-раковина {ear_pink}), силуэт {sil} — ок')

        # валидация производных ключей (E = x2, W = зеркало) по координатам
        for view in ('E', 'W'):
            for k in range(4):
                assert f'{view}{k}' in masks, f'{build}: нет ключа {view}{k}'
                src_key = str(k + 1)
                coords_src = set((i % W, i // W) for L in FUR_LAYERS for i in masks[src_key][L])
                coords_der = set()
                for L in FUR_LAYERS:
                    for i in masks[f'{view}{k}'][L]:
                        x, y = i % (W * 2), i // (W * 2)
                        xx = x // 2 if view == 'E' else (W * 2 - 1 - x) // 2
                        coords_der.add((xx, y // 2))
                assert coords_src == coords_der, f'{build}/{view}{k}: производная маска != исходной'
        report['validation'].append(f'{build}: E*/W* (16 ключей) == x2/зеркало слоёв 1..4 — ок')
        print(f'  {build}: E*/W* 16 производных ключей = x2/зеркало — ок')

        layers_meta = {
            'keys': keys100,
            'sources': {k: f'model-эквивалент {MODEL_FRAME[build][k]}' if k in MODEL_FRAME[build]
                        else f'N/S {FRAME_MAP[build][k]}' for k in keys100},
        }
        report['builds'][build]['keys'] = keys100

    # --- метаданные движка ---
    meta = {
        'canonicalSource': 'kns_def-live-2026-11-04 (килл palette[0]: 24 цвета, hex в манифесте catwar-manifest.js)',
        'format': 'gray: RGB=нейтральный серый (нормированная люминанция), A=альфа исходника; '
                  'protect: RGB/A исходника байт-в-байт (глаза, нос, ушные раковины — НЕ тонировать)',
        'ops': 'fill(paletteHex) -> multiply(gray) -> destination-in(gray) — cut_from-паритет kns.js L546-557',
        'medianLumTarget': MEDIAN_LUM_TARGET,
        'slotColour': {'tail': 15, 'earL': 17, 'earR': 17, 'body': 0, 'head': 0,
                       'fore': 0, 'hind': 0, 'chest': 0, 'belly': 0},
        'builds': {},
    }
    for build in ('norm', 'thin', 'chub'):
        meta['builds'][build] = {
            'label': BUILD_LABEL[build],
            'walkTail': BUILD_TAIL[build],
            'K': report['builds'][build]['K'],
            'keys': report['builds'][build]['keys'],
        }
    os.makedirs(OUT_DIR, exist_ok=True)
    json.dump(meta, open(os.path.join(OUT_DIR, 'tint_meta.json'), 'w'), ensure_ascii=False, indent=1)

    scratch = os.path.expanduser('~/.hermes/cache/scratch/kns-tint')
    os.makedirs(scratch, exist_ok=True)
    json.dump(report, open(os.path.join(scratch, 'tint_report.json'), 'w'), ensure_ascii=False, indent=1)
    total = len(FUR_LAYERS) * 13 * 3 + 13 * 3
    print(f'== готово: gray/ = {total} PNG + tint_meta.json; отчёт {scratch}/tint_report.json')


def is_ear_shell(px):
    """Ушная раковина M2 (розовая): тёплый насыщенный пиксель, мех таким не бывает.

    Мех M2 (#F0B863/#F7E2C3/контуры): r-b в диапазоне ~40..145, g близко к r.
    Раковина: яркий розовый — r > 180, g заметно ниже r (мясо), b ~ g (нейтраль с лёгким теплом).
    Порог откалиброван по замеру hist (см. --measure), уточнён по кадрам всех билдов.
    """
    r, g, b = px[0], px[1], px[2]
    return r > 175 and r - g >= 55 and abs(g - b) <= 45 and b > 60


if __name__ == '__main__':
    main()
