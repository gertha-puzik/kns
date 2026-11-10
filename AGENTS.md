# AGENTS.md — KNS (coat editor for coop-field)

KNS is a prototype coat-color editor for the owner's game coop-field.
Live: https://kns.miew.ru (pure static, served from `/opt/kns/www` on the VPS).
This repo stays public; every push to `main` triggers CI (rsync) deploy — see
`.github/workflows/deploy.yml`.

**Read `KNS-CONTEXT.md` first** — it is the single-file canon (project status,
hard limits, code grammar, paths, full git protocol). This file is only an entry
map; when the two disagree, `KNS-CONTEXT.md` wins.

## Entry map

| Path | What |
|---|---|
| `KNS-CONTEXT.md` | Canon dossier (§4 hard limits, §5 grammar, §6 paths, §8 conventions). Excluded from deploy — never appears on the site |
| `docs/kns-tz.md`, `docs/kns-art-list.md` | Product spec and art list |
| `skills/kns-imagegen/SKILL.md` | Canon sprite-generation pipeline (M2 style) |
| `tools/pr_qc.py` | Structural merge gate (JSON/JS/CJK/assetRoot checks) — must be green before merge |
| `.github/workflows/` | `deploy.yml` (push main → rsync), `kns-qc.yml` (PR gate), `main-guard.yml` (direct pushes to main are auto-reverted) |
| `README.md` | Human overview (RU) |

## Repo layout

`index.html` — one sentence: the reference pack is no longer shipped
(same notice on `tint.html`, `mask-annotator.html`, `frames-studio.html`).
`act0/`, `act1/`, `gray/`, `artpack/`, `model/`, `archive/`, `tint.js` and
`catwar-manifest.js` are removed from the tree and must not be added back;
git history is left as-is. `paint-demo/` stays. `weather-demo/` — weather
demo; `img/` — static extras. If `catwar-manifest.js` is ever restored,
`assetRoot` must stay `''`.

## Workflow (condensed; full protocol = KNS-CONTEXT §8.7)

- One task = one branch `<feat|fix|chore|agent>/<slug>` cut from fresh
  `origin/main`, in its own worktree (`git worktree add ../kns-wt/<slug> ...`).
  Never share a checkout between parallel agents.
- Direct pushes to `main` are forbidden — `main-guard` reverts them with an
  alarm issue.
- Before opening a PR: `git fetch origin && git rebase origin/main`, then run
  `python3 tools/pr_qc.py` locally. Red QC = do not merge.
- Merge = deploy to prod. Merge with a merge commit (never squash), and never
  merge your own PR without the owner's explicit go-ahead.
- After merge: remove the worktree, delete the branch, `git pull --ff-only`.

## Hard limits (condensed from KNS-CONTEXT §4)

- Do not touch the coop-field repo/runtime (reading it, e.g. `drawChar`, is
  fine). Never commit Cat War art or `kns_def.json` into coop-field.
- CatWar gate slots (whiskers 22, nose 23, ear tufts 10) always 404 on the
  source server — do not probe repeatedly and do not try to bypass.
- No secrets in code/logs/chat; keys live in env variables.
- Commit identity: `user.name="polexka"`,
  `user.email="polexka@users.noreply.github.com"`.

## Context graph: graphify (optional local helper)

- Optional per-clone retrieval helper. Install: `uv tool install graphifyy`
  (double-y; other `graphify*` packages on PyPI are typosquats).
- Build: `graphify extract . --code-only --out graphify-out` — deterministic
  tree-sitter AST parse, no LLM, nothing leaves the machine.
- This repo is small; the entry map above usually beats graph queries. The
  graph earns its keep for `path` / `affected` across `index.html` inline
  scripts, `catwar-manifest.js` and `tint.js`.
- `graphify-out/` is gitignored: a per-clone artifact — never commit it, never
  build it in CI, never let graph output weaken the QC gate.
- Graph output is a retrieval HINT: verify the cited `file:line` in the source
  before editing.
