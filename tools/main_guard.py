#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""main_guard — дисциплинарная защита ветки main (GitHub Free: серверной блокировки приватного репо нет).

Команды:
  classify <sha>   — вердикт коммита: ok (<почему>) | offender (<почему>) | skip
  gate <sha>       — exit 1, если коммит — прямой пуш мимо PR; вызывается
                     из deploy.yml ДО rsync: прод не получает нарушителя.
  revert <sha>     — для offender: реверт-коммит поверх (дерево родителя),
                     fast-forward main без force + alarm-issue.

Легитимные коммиты (ok): merge-коммиты (>=2 родителя, мердж PR по регламенту);
реверты самого guard (REVERT(main-guard): / автор github-actions[bot]);
мерджи UI rebase/squash (committer web-flow/GitHub). Остальное с одним
родителем — прямой пуш в main, запрещён регламентом (досье §8.7).

Известные пределы (v1): нарушитель, переписавший ВСЮ историю, не
останавливается здесь — это дисциплинарный бот, не криптобарьер;
полная серверная блокировка — GitHub Pro (payload сохранён в scratch).
"""
import json
import os
import subprocess
import sys

REPO = os.environ.get("REPO", "gertha-puzik/kns")


def api(path, *args, method=None, die=True):
    cmd = ["gh", "api"]
    if method:
        cmd += ["--method", method]
    cmd += [f"repos/{REPO}/{path}"] + list(args)
    r = subprocess.run(cmd, capture_output=True, text=True)
    if r.returncode != 0:
        print(f"gh api {path}: {r.stderr.strip()[:300]}", file=sys.stderr)
        if die:
            sys.exit(3)
        return None
    return json.loads(r.stdout)


def classify(sha):
    if not sha or set(sha) == {"0"}:
        return "skip", "пустое/нулевое sha"
    c = api(f"commits/{sha}")
    parents = c.get("parents", [])
    commit = c.get("commit", {})
    msg = (commit.get("message") or "").strip()
    committer = (c.get("committer") or {}).get("login") or ""
    committer_name = (commit.get("committer") or {}).get("name") or ""
    if len(parents) >= 2:
        return "ok", f"merge-commit мерджа PR ({len(parents)} родителя)"
    if msg.startswith("REVERT(main-guard):"):
        return "ok", "реверт самого guard"
    if committer in ("web-flow", "github-actions[bot]") or committer_name == "GitHub":
        return "ok", f"серверный мердж PR (committer={committer or committer_name})"
    pulls = api(f"commits/{sha}/pulls", die=False) or []
    for pr in pulls:
        if pr.get("merged_at") and pr.get("merge_commit_sha") == sha:
            return "ok", f"серверный мердж PR #{pr.get('number', '?')} (squash/rebase, merge_commit_sha совпал)"
    author = (c.get("author") or {}).get("login") or (commit.get("author") or {}).get("name") or "?"
    actor = os.environ.get("GITHUB_ACTOR", "")
    return (
        "offender",
        f"прямой пуш мимо PR (1 родитель; коммиттер {committer_name or committer or '?'}, "
        f"автор {author}{', пушнул ' + actor if actor else ''})",
    )


def gate(sha):
    verdict, why = classify(sha)
    print(f"{verdict}: {why}")
    if verdict == "offender":
        print("::error::Прямой пуш в main обнаружен — деплой заблокирован (досье §8.7: только через PR).")
        sys.exit(1)


def revert(sha):
    verdict, why = classify(sha)
    print(f"{verdict}: {why}")
    if verdict != "offender":
        print("реверт не нужен")
        return
    c = api(f"commits/{sha}")
    parent = c["parents"][0]["sha"]
    parent_commit = api(f"git/commits/{parent}")
    tree = parent_commit["tree"]["sha"]
    actor = os.environ.get("GITHUB_ACTOR", "неизвестный")
    msg = (
        f"REVERT(main-guard): {sha[:12]} — прямой пуш в main от {actor} нарушает регламент досье §8.7; "
        f"контент откачен на дерево {parent[:12]}. Правильный путь — ветка + PR с зелёным QC."
    )
    r = subprocess.run(
        ["gh", "api", "--method", "POST", f"repos/{REPO}/git/commits",
         "-f", f"message={msg}", "-f", f"tree={tree}", "-f", f"parents[]={sha}"],
        capture_output=True, text=True,
    )
    if r.returncode != 0:
        print(f"создание реверт-коммита не удалось: {r.stderr[:300]}", file=sys.stderr)
        sys.exit(4)
    new_sha = json.loads(r.stdout)["sha"]
    r = subprocess.run(
        ["gh", "api", "--method", "PATCH", f"repos/{REPO}/git/refs/heads/main",
         "-f", f"sha={new_sha}"],
        capture_output=True, text=True,
    )
    if r.returncode != 0:
        print(f"update main не удался: {r.stderr[:300]}", file=sys.stderr)
        sys.exit(5)
    print(f"main восстановлен реверт-коммитом {new_sha[:12]} (fast-forward поверх {sha[:12]})")
    body = (
        f"## ⛔ Прямой пуш в main откачен ботом `main-guard`\n\n"
        f"- Нарушитель: `{sha[:12]}` (автор пуша: **{actor}**)\n"
        f"- Причина вердикта: {why}\n"
        f"- Дифф: {REPO}/compare/{parent[:12]}...{sha[:12]}\n"
        f"- Откачен ревертом: `{new_sha[:12]}` (дерево {parent[:12]})\n\n"
        f"Регламент (досье §8.7): изменения в main — только через ветку + PR "
        f"с зелёным чеком «KNS QC / qc». Деплой нарушителя был заблокирован "
        f"гейтом в deploy.yml — на прод ничего не попало."
    )
    r = subprocess.run(
        ["gh", "issue", "create", "--repo", REPO,
         "--title", f"⛔ Прямой пуш в main откачен (kns-main-guard): {sha[:8]}",
         "--body", body],
        capture_output=True, text=True,
    )
    print("alarm-issue: " + (r.stdout.strip() or r.stderr.strip()[:200]))


def main():
    if len(sys.argv) < 3 or sys.argv[1] not in ("classify", "gate", "revert"):
        print(__doc__)
        sys.exit(2)
    cmd, sha = sys.argv[1], sys.argv[2]
    if cmd == "classify":
        verdict, why = classify(sha)
        print(f"{verdict}: {why}")
    elif cmd == "gate":
        gate(sha)
    else:
        revert(sha)


if __name__ == "__main__":
    main()
