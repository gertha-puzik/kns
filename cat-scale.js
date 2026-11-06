// KNS cat-scale — единый масштаб кота на всех экранах редактора (карточка размеров).
//
// Механизм (канон принят витриной /archive, T=320): per-frame масштаб
//     s = T / catH  (catH — высота силуэта кадра, bbox по альфе>64)
// с якорем «низ-центр»: НОГИ на нижний край канвы, силуэт по центру.
// Никаких ×2-ассетов ради размера: размер кота задаётся ТОЛЬКО параметром T
// в TARGETS ниже (один параметр на экран), данные силуэтов — в cat_h.js
// (генерирует tools/measure_cat_h.py; после регенерации арта перегнать скрипт).
//
// Правки lx/bg: если силуэт не доходит до нижней кромки кадра (bg>0, бывает
// 1-2 px АА) или смещён влево/вправо (lx), якорь ставится по НОГАМ и по центру
// СИЛУЭТА — пиксельное дрожание опоры между кадрами (bg 0..2) убирается.
//
// Подключение: <script src="cat_h.js"></script><script src="cat-scale.js"></script>
// до tint.js/использования. Хелперы возвращают null, если данных нет
// (ассет неизвестен или помечен bad) — вызывающий делает свой фолбэк.
'use strict';
(function (global) {
  // ЦЕЛЕВЫЕ РАЗМЕРЫ ЭКРАНОВ — единственное место, где задаётся видимый размер кота.
  // editorPair: панель пары index.html (канва 176×150, сит в натуральную величину);
  // tintDemo: демо тонировки tint.html (канва 240×280);
  // framesStudio: анимация-просмотр frames-studio.html (канва CVH=240, ширина динамическая).
  const TARGETS = {
    editorPair:   { T: 106 },
    tintDemo:     { T: 144 },
    framesStudio: { T: 176 }
  };

  function dataOf(ref) {
    const d = (typeof KNS_CAT_H !== 'undefined') ? KNS_CAT_H[ref] : null;
    return (d && !d.bad) ? d : null;
  }

  // масштаб кадра: кот будет высотой T px (null — данных нет / кадр помечен bad)
  function fitScale(ref, T) {
    const d = dataOf(ref);
    return d ? T / d.h : null;
  }

  // геометрия отрисовки: кадр src (img/canvas), кот = T px, ноги на низ канвы,
  // силуэт по центру; mirror — отразить в месте (W = зеркало E).
  // Возвращает {s, dx, dy, dw, dh} или null.
  function fitRect(canvasW, canvasH, src, ref, T, mirror) {
    const d = dataOf(ref);
    if (!d) return null;
    const s = T / d.h;
    const iw = src.naturalWidth || src.width, ih = src.naturalHeight || src.height;
    const dw = iw * s, dh = ih * s;
    const catCx = d.lx + d.w / 2;                 // центр силуэта в исходнике
    const cxInDraw = mirror ? (iw - catCx) : catCx; // после flip-в-месте центр зеркален
    const dx = canvasW / 2 - cxInDraw * s;
    const dy = canvasH - (ih - d.bg) * s;         // ноги: низ силуэта == низ канвы
    return { s: s, dx: dx, dy: dy, dw: dw, dh: dh, mirror: !!mirror, T: T };
  }

  // вписать и нарисовать на уже очищенный ctx; imageSmoothing ставить вызывающему (NEAREST)
  function drawFitted(ctx, canvas, src, ref, T, mirror) {
    const f = fitRect(canvas.width, canvas.height, src, ref, T, mirror);
    if (!f) return null;
    if (f.mirror) {
      ctx.save();
      ctx.translate(f.dx + f.dw, 0);
      ctx.scale(-1, 1);
      ctx.drawImage(src, 0, f.dy, f.dw, f.dh);
      ctx.restore();
    } else {
      ctx.drawImage(src, f.dx, f.dy, f.dw, f.dh);
    }
    return f;
  }

  global.KNS_CAT_SCALE = {
    TARGETS: TARGETS,
    dataOf: dataOf,
    fitScale: fitScale,
    fitRect: fitRect,
    drawFitted: drawFitted
  };
})(typeof window !== 'undefined' ? window : this);
