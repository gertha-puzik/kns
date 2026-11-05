# Шаблон ТЗ-брифа для claude-sonnet (проверен волной bodyforms 2026-11-05: 7/7 промптов пригодны с первого захода)

Заказывать у `router.py chat anthropic/claude-sonnet-5.5 "$(cat brief.txt)" --max-tokens 16000`.
Замени подсвеченные <>-поля, провал-лист не сокращай — он главный фактор качества.

---

Ты — постановщик ТЗ для image-модели google gemini-3.1-flash-image. Модель получает
РЕФЕРЕНС-картинку + промпт на английском и рисует пиксель-арт кота для 2D-игры.
Твоя задача — написать N промптов.

КОНТЕКСТ (обязателен к учёту в промптах):
- Базовый персонаж «M2» принят заказчиком: рыжий пиксель-арт кот, детальный пиксель-арт,
пропорции чуть реалистичнее чиби (НЕ жирный чиби), тёмно-коричневый самоцветный контур,
мягкие пиксельные ступени затенения.
- Точная палитра (замерить из финальных кадров pipeline.py palette — НЕ из досье):
шерсть <#F0B863>, светлые зоны <#F7E2C3>, тёмная терракота-коричневый для контуров и теней.
- Референс, который получит модель: для sit — <что на sit-эталоне>; для walk — готовая
полоса 1×4 с ходьбой вбок ВПРАВО, высота кота ~80 px в клетке кадра 100×150.
- Формулировка стиля «copy EXACTLY the art style of the attached reference strip» —
рабочая, используй её дословно.

ЗАДАЧА: <спись требуемых серий; на каждую — poza/ракурс/особенность>

ИЗВЕСТНЫЕ ПРОВАЛЫ ГЕНЕРАТОРА — обязательно контрить внутри каждого промпта:
1. «4 frames in ONE horizontal strip» рисуется сеткой 2×2 → single ONE horizontal row,
exactly 4 equal cells left-to-right, NEVER a 2x2 grid, never vertical stack.
2. Кадры-дубликаты → CRITICAL: 4 DIFFERENT stride phases (contact/passing/lift/swing),
silhouettes visibly differ, no duplicate poses.
3. Чёрная полоса-пол → NO ground line, NO floor, NO shadow, NO grass.
4. Текст/подписи/рамки → NO text, NO watermark, NO labels, NO cell borders, NO grid lines.
5. Палитру перекрашивает → явно указать обе hex-краски + «keep the exact palette of the reference».
6. Ракурс морды уезжает к зрителю → side view walking RIGHT, head stays in profile, no looking
at viewer; для ракурса от камеры — ANGLE OVERRIDE-блок: что ВИДИТ камера и чего НЕ видит
(«THE FACE IS NOT VISIBLE IN ANY FRAME»), для ракурса на камеру — «EYES MANDATORY».
7. Хвост меняет форму/длину/сторону между кадрами → tail geometry identical in all 4 frames.
8. У sit-промптов модель меняет позу → same sitting pose as the reference, ONLY <что> changes.
9. Фон → flat uniform light background #EDEAE3 everywhere (для последующего white→alpha).
10. Живость только за счёт лап/корпуса; масштаб кота одинаков во всех кадрах, кот по центру клетки.

ФОРМАТ ОТВЕТА — строго, без лишнего текста до/после, каждый промпт в отдельном fenced-блоке:
PROMPT_<ИМЯ>:
```text
<полный промпт на английском>
```
… и так все N. Промпты самодостаточны (модель видит только промпт и референс).
В промпте описывай кота как «the reference cat», не переизобретай дизайн.

---

## Парсинг ответа (проверено)
```python
import re
blocks = re.findall(r'PROMPT_([A-Z_]+):\s*```text\s*\n(.*?)\n```', text, re.S)
for name, body in blocks: open(f'PROMPT_{name}.txt', 'w').write(body.strip() + '\n')
# полнота: сверить набор имён с требуемым; каждый промпт содержит обе hex-краски и «tail» (для walk)
```
Пустой ответ claude (finish=refusal) — один ретрай без изменений параметров, далее дешёвой моделью; см. selectel-ai-router.
