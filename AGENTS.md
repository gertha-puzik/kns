# AGENTS.md — KNS Paint (coat editor for coop-field)

KNS Paint is a browser coat-painting editor for the owner's game coop-field:
the player paints a cat over a sketch and exports a PNG for the game.
Live: https://paint.phainonsmilk.ru (pure static; the root is the editor).
This repo stays public; every push to `main` triggers CI (rsync) deploy — see
`.github/workflows/deploy.yml`.

**Read `KNS-CONTEXT.md` first** — it is the single-file canon (status, hard
limits, git protocol). This file is only an entry map; when the two disagree,
`KNS-CONTEXT.md` wins.

## Entry map

| Path | What |
|---|---|
| `index.html` + `paint-data.js` | KNS Paint itself (the site root) |
| `paint-demo/index.html` | Redirect to `/`, keeps `?query` and `#hash` so old links and deep links work |
| `KNS-CONTEXT.md` | Canon dossier. Excluded from deploy — never appears on the site |
| `tools/pr_qc.py` | Structural merge gate (JSON/JS/CJK checks) — must be green before merge |
| `tools/main_guard.py` | Helper for `main-guard` |
| `.github/workflows/` | `deploy.yml` (push main → rsync), `kns-qc.yml` (PR gate), `main-guard.yml` (direct pushes to main are auto-reverted) |
| `README.md` | Human overview (RU) |

## Scope

Owner decision 2026-11-14: KNS Paint is the only product here. Everything
else that used to live in this repo (the reference-game coat-code constructor, M2 model and
masks, tint, mask-annotator, frames studio, fight-demo, weather-demo,
`skills/kns-imagegen`, specs) is kept in the **private** repo
`gertha-puzik/kns-archive` (all branches as of 2026-11-14; Actions disabled,
never deploys). Do not add any of it back here. coop-field keeps its own copy
of the editor in `public/paint-demo/`; syncing it is a separate coop-field PR.

## Workflow (condensed; full protocol = KNS-CONTEXT §5.3)

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

- Do not touch the coop-field repo/runtime (reading it is fine). Never commit
  reference-game art or its palette dump into this repo or coop-field.
- No secrets in code/logs/chat; keys live in env variables / GitHub secrets.
- Never touch the VPS by hand; domain, nginx and certificates are the owner's.
- Commit identity: `user.name="polexka"`,
  `user.email="polexka@users.noreply.github.com"`.

## Context graph: graphify (optional local helper)

- Optional per-clone retrieval helper. Install: `uv tool install graphifyy`
  (double-y; other `graphify*` packages on PyPI are typosquats).
- Build: `graphify extract . --code-only --out graphify-out` — no LLM, nothing
  leaves the machine. The repo is tiny; the entry map usually beats the graph.
- `graphify-out/` is gitignored: never commit it, never build it in CI.
- Graph output is a hint: verify the cited `file:line` before editing.
