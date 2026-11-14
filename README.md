# KNS Paint — редактор окрасов для coop-field

Браузерный редактор: игрок красит кота кистью поверх скетча и выгружает PNG
для игры [coop-field / abnocw](https://abnocw.phainonsmilk.ru) (организация
[gertha-puzik](https://github.com/gertha-puzik)).

## Что здесь лежит

- `index.html` + `paint-data.js` — сам KNS Paint, он же главная сайта.
- `paint-demo/` — редирект на главную. Старые ссылки и диплинки
  (`?query`, `#hash`) продолжают работать.
- `tools/pr_qc.py` — проверка перед мержем, `tools/main_guard.py` — сторож `main`.

Всё остальное, что раньше жило в KNS (конструктор по коду окраса из игры-референса,
модель M2, тонировка, разметчик, fight-demo, weather-demo, генерация спрайтов),
по решению от 2026-11-14 перенесено в приватный архив `gertha-puzik/kns-archive`.

## Сайт

**https://paint.phainonsmilk.ru** — статика на VPS. Старые адреса
`kns.phainonsmilk.ru` и `kns.miew.ru` должны вести на него редиректом.

## Деплой

GitHub Actions, `.github/workflows/deploy.yml`: при пуше в `main` rsync-ит
репозиторий на VPS (`--delete`, без `.git`, `.github`, `tools`, досье и
агентских файлов). Секрет `VPS_SSH_KEY` — ключ юзера `deploy`.

Проверка без CI: `python3 -m http.server` в корне репо и открыть
http://127.0.0.1:8000/ (с `file://` canvas не работает).

## Для ИИ-агентов

`AGENTS.md` — карта входа, `KNS-CONTEXT.md` — досье и git-регламент
(ветка + PR, мерж = деплой).

## Правовая оговорка

Изображения игры-референса и её дамп палитр не коммитятся ни сюда, ни в coop-field.
Репозиторий публичный.
