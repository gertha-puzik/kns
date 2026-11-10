#!/usr/bin/env python3
"""Замер catH (высота силуэта кота, bbox по альфе>64) всех кадров, потребляемых редактором.

Правило единого масштаба (канон, витрина /archive T=320, досье §2 «Масштаб направлений»):
    per-frame s = T / catH, якорь «низ-центр» (ноги у нижнего края кадра).
Размер кота задаётся ПАРАМЕТРОМ T в коде (cat-scale.js TARGETS), а не ×2-ассетами.

Скрипт измеряет и ВЫДАЁТ:
  * cat_h.js          — данные для рантайма: KNS_CAT_H[ref] = {h, w} (ref = путь без .png)
  * cat_h_report.json — QC-числа: bbox, catH/catW, зазоры (pivot), якорные сверки,
                        допустимые T для каждого экрана (geometric feasibility)

Источники: model/*.png + model/dirs/*.png (все 43 кадра каталога),
gray/{build}/{key}_*.png (композит = объединение альфы слоёв — инвариант union==silhouette).
Запуск: python3 tools/measure_cat_h.py [repo_dir] — после регенерации любого арта.
Выход обновляет cat_h.js в корне репо (git diff покажет сдвиги).
"""
import json, os, re, struct, sys, datetime

REPO = os.path.abspath(sys.argv[1] if len(sys.argv) > 1 else
                       os.path.expanduser('~/Desktop/dev/catwar/research/kns-clone/kns-repo'))
OUT_JS = os.path.join(REPO, 'cat_h.js')

FUR = ['body', 'chest', 'belly', 'tail', 'hindL', 'hindR', 'foreL', 'foreR', 'head', 'earL', 'earR']

def png_size(p):
    with open(p, 'rb') as f:
        h = f.read(33)
    return struct.unpack('>II', h[16:24])

from PIL import Image, ImageChops

def measure(path):
    im = Image.open(path).convert('RGBA')
    a = im.split()[3].point(lambda v: 255 if v > 64 else 0)
    bbox = a.getbbox()
    if not bbox:
        return None
    return dict(w=im.width, h=im.height, bbox=bbox,
                catW=bbox[2] - bbox[0], catH=bbox[3] - bbox[1],
                topGap=bbox[1], bottomGap=im.height - bbox[3],
                leftGap=bbox[0], rightGap=im.width - bbox[2])

def measure_gray_composite(build, key):
    """Силуэт кадра = объединение альф 11 мех-слоёв + protect (инвариант union==silhouette)."""
    base = os.path.join(REPO, 'gray', build)
    acc = None
    for layer in FUR + ['protect']:
        p = os.path.join(base, f'{key}_{layer}.png')
        if not os.path.exists(p):
            return None
        a = Image.open(p).convert('RGBA').split()[3].point(lambda v: 255 if v > 64 else 0)
        acc = a if acc is None else Image.alpha_composite(Image.new('L', a.size, 0), a) if False else acc
        # объединение масок: max по точкам
        if acc is a:
            continue
        acc = Image.eval(Image.merge('L', (acc, a)) if False else acc, lambda v: v)  # placeholder
    # правильное объединение через chord — см. ниже: используем numpy-free через ImageChops.lighter
    return None

def measure_gray_lighter(build, key):
    from PIL import ImageChops
    base = os.path.join(REPO, 'gray', build)
    acc = None
    size = None
    for layer in FUR + ['protect']:
        p = os.path.join(base, f'{key}_{layer}.png')
        if not os.path.exists(p):
            continue
        a = Image.open(p).convert('RGBA').split()[3].point(lambda v: 255 if v > 64 else 0)
        size = a.size
        acc = a if acc is None else ImageChops.lighter(acc, a)
    if acc is None:
        raise SystemExit('нет слоёв gray/%s/%s' % (build, key))
    bbox = acc.getbbox()
    assert bbox, f'пустой композит gray/{build}/{key}'
    return dict(w=size[0], h=size[1], bbox=bbox,
                catW=bbox[2] - bbox[0], catH=bbox[3] - bbox[1],
                topGap=bbox[1], bottomGap=size[1] - bbox[3],
                leftGap=bbox[0], rightGap=size[0] - bbox[2])

def main():
    ts = datetime.datetime.now().strftime('%Y-%m-%dT%H:%M:%S')
    report = {'generated': ts, 'repo': REPO, 'frames': {}, 'anchors_check': {}, 'feasibility': {}}

    # 1) каталог frames-studio (43 кадра): model/*.png + model/dirs/*.png
    fs_src = open(os.path.join(REPO, 'artpack', 'frames-studio-data.js')).read()
    m = re.search(r'=\s*(\{.*\})\s*;?\s*$', fs_src, re.S)
    d = json.loads(m.group(1))
    fs_refs = {}
    for b in d['builds'].values():
        for fr in b['frames']:
            fs_refs[fr['name']] = fr['src']
    for name, src in sorted(fs_refs.items()):
        p = os.path.join(REPO, src)
        if not os.path.exists(p):
            print('!! нет файла каталога:', src); continue
        ref = src[:-4] if src.endswith('.png') else src
        report['frames'][ref] = measure(p)

    # model/*.png вне каталога (те же файлы — уже покрыты выше)^ каталог их включает

    # 2) gray-композиты по ключам tint_meta
    meta = json.load(open(os.path.join(REPO, 'gray', 'tint_meta.json')))
    for build, bm in meta['builds'].items():
        for key in bm['keys']:
            ref = f'gray/{build}/{key}'
            report['frames'][ref] = measure_gray_lighter(build, key)

    # 3) якорные сверки с принятыми ранее данными (комментарий 14:51 и досье §2)
    def gh(ref): return report['frames'][ref]['catH']
    anchors = {
        'E_x2 (dirs)': [gh('model/dirs/E%d' % i) for i in range(4)],
        'W_x2 (dirs)': [gh('model/dirs/W%d' % i) for i in range(4)],
        'N (dirs)':    [gh('model/dirs/N%d' % i) for i in range(4)],
        'S (dirs)':    [gh('model/dirs/S%d' % i) for i in range(4)],
        'ожидание': {'E/W_x2': [156, 166, 160, 160], 'N': [141, 149, 141, 149], 'S': [150, 149, 150, 149]},
    }
    report['anchors_check'] = anchors

    # стативная vs gray-тождественность (одна и та же модель = один catH)
    xchecks = {}
    for build, model_prefix, keys in [('norm', 'walk_norm_up_k', '1234'), ('thin', 'walk_thin_down_k', '1234'), ('chub', 'walk_chub_up_k', '1234')]:
        for k in range(4):
            a = gh(f'model/{model_prefix}{k}')
            g = gh(f'gray/{build}/{k + 1}')
            xchecks[f'{model_prefix}{k} vs gray/{build}/{k+1}'] = [a, g, a == g]
    for build in ['norm', 'thin', 'chub']:
        a = gh(f'model/sit_{build}')
        g = gh(f'gray/{build}/0')
        xchecks[f'sit_{build} vs gray/{build}/0'] = [a, g, a == g]
    report['state_vs_gray'] = xchecks

    # 4) pivot-инвариант: опора у нижнего края (bottomGap==0 — ноги на полу кадра)
    piv = {}
    for ref, f in report['frames'].items():
        piv[ref] = f['bottomGap']
    bad = {k: v for k, v in piv.items() if v != 0}
    report['pivot_bottom_gap'] = {'all_zero': not bad, 'violations': bad}

    # 5) feasibility: допустимый T для каждого экрана.
    # Механизм cat-fit: s = T/catH, ноги на пол, кот по центру. Гарантии геометрии:
    #   T <= canvasH (кот целиком по вертикали) и catW*s <= canvasW (кот целиком по ширине).
    # Пустые поля кадра (topGap/bg/lx) клипаются канвой — их вписывать НЕ нужно.
    # пара (index.html): статик-арт model/walk_* + model/sit_* (24+3), ИЛИ gray-композиты
    # native-tail билдов (кадры '0','1'..'4'); Н/С-каталог и E/W-×2 пара НЕ потребляет.
    pair_frames = [r for r in report['frames'] if r.startswith('model/walk_') or r.startswith('model/sit_')]
    # tint.html: все gray-ключи (13 на билд)
    tint_frames = [r for r in report['frames'] if r.startswith('gray/')]
    # frames-studio: весь каталог 43 кадра (анимация)
    fs_frames = [r for r in report['frames'] if r.startswith('model/')]

    def maxT(frames, canvasW, canvasH):
        """макс T: каждый кот влезает целиком (высота T, ширина catW*T/catH)."""
        lim = canvasH
        for r in frames:
            f = report['frames'][r]
            w_at_T = f['catW'] / f['catH']  # ширина кота при T=1
            if w_at_T > 0:
                lim = min(lim, canvasW / w_at_T)
        return int(lim)

    # ожидаемые окна catH по типу кадров (канон серии: sit ~нативные 104-107,
    # walk-E «приземистые» 62-93, N/S «стоячие» 124-150). Аномалия < 0.75 нижней
    # границы окна — битый источник, рантайм его НЕ масштабирует cat-fit'ом.
    EXPECT = {'sit': (100, 115), 'walkE': (55, 100), 'walkN': (110, 155), 'walkS': (130, 155)}

    def typ(ref):
        key = ref.rsplit('/', 1)[-1]
        if key == '0' or key.startswith('sit'): return 'sit'
        if key[0] in 'NESW' or key[0] in '1234': return 'walk' + (key[0] if key[0] in 'NS' else 'E')
        return 'walkE'

    for ref, f in report['frames'].items():
        lo, hi = EXPECT[typ(ref)]
        f['bad'] = bool(f['catH'] < int(lo * 0.75))
    report['bad_frames'] = {r: report['frames'][r]['catH'] for r in report['frames'] if report['frames'][r]['bad']}

    trio = {}
    for canvasW, canvasH, frames, name in [(176, 150, pair_frames, 'editorPair 176x150'),
                                            (100, 150, pair_frames, 'editorPair 100x150'),
                                            (240, 280, tint_frames, 'tintDemo 240x280'),
                                            (240, 360, tint_frames, 'tintDemo 240x360')]:
        good = [r for r in frames if not report['frames'][r]['bad']]
        trio[name] = dict(canvasW=canvasW, canvasH=canvasH, maxT=maxT(good, canvasW, canvasH))
    # frames-studio: ширина канвы ДИНАМИЧЕСКАЯ (под кота), высота фикс CVH=240
    good_fs = [r for r in fs_frames if not report['frames'][r]['bad']]
    trio['framesStudio dynW x240'] = dict(canvasW='dynamic', canvasH=240,
                                          maxT=maxT(good_fs, 10 ** 6, 240))
    report['feasibility'] = trio

    # 6) вписывания «до» (frame-fit, как сейчас) для сравнения в отчёте
    def frame_fit_vis_h(canvasH):
        out = {}
        for r in pair_frames + tint_frames:
            f = report['frames'][r]
            out[r] = round(canvasH * f['catH'] / f['h'])
        return out
    report['before_frame_fit_visible_catH'] = {'editorPair_css360': frame_fit_vis_h(360)}

    # 7) запись cat_h.js (данные рантайма) + отчёт
    # поля: h/catW — габариты силуэта; lx — левый отступ кота в кадре;
    # bg — зазор НОГ до нижней кромки кадра (якорь «низ» = ноги, а не пустая кромка)
    entries = {}
    for ref in sorted(report['frames']):
        f = report['frames'][ref]
        e = {'h': f['catH'], 'w': f['catW'], 'lx': f['leftGap'], 'bg': f['bottomGap']}
        if f['bad']:
            e['bad'] = 1
        entries[ref] = e
    js = ('// Сгенерировано tools/measure_cat_h.py — НЕ править руками. ' + ts + '\n'
          '// catH/catW = высота/ширина силуэта кадра (bbox по альфе>64); lx/bg — якоря силуэта в кадре.\n'
          '// Механизм единого масштаба: per-frame s = T/catH, якорь низ-центр (cat-scale.js, витрина /archive):\n'
          '// ноги на нижний край канвы, силуэт по центру — с поправками lx/bg, чтобы ноги стояли на полу,\n'
          '// даже если силуэт не доходит до кромки кадра на 1-2 px.\n'
          '// ref = путь ассета без расширения: "model/walk_norm_up_k0", "model/dirs/E0", "gray/norm/0", …\n'
          'var KNS_CAT_H = ' + json.dumps(entries, ensure_ascii=False, separators=(',', ':')) + ';\n'
          'if (typeof window !== "undefined") window.KNS_CAT_H = KNS_CAT_H;\n')
    open(OUT_JS, 'w').write(js)
    out_report = os.path.join(os.getcwd(), 'cat_h_report.json')
    json.dump(report, open(out_report, 'w'), indent=1, ensure_ascii=False)

    # 8) краткая сводка в stdout
    print('кадров измерено:', len(report['frames']))
    print('cat_h.js ->', OUT_JS)
    print('report   ->', out_report)
    print('pivot bottom-gap violations:', len(bad), bad if bad else '')
    for k in ['E_x2 (dirs)', 'W_x2 (dirs)', 'N (dirs)', 'S (dirs)']:
        print('anchors', k, anchors[k])
    print('state vs gray mismatches:', {k: v for k, v in xchecks.items() if v[2] is False} or 'нет')
    for name, t in trio.items():
        print('feasibility', name, 'maxT =', t['maxT'])

if __name__ == '__main__':
    main()
