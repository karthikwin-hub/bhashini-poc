#!/usr/bin/env python3
"""agent_hooks.py - deterministic guardrails for coding agents ("gates, not promises").

One script serves GitHub Copilot (CLI and cloud agent, .github/hooks/*.json) and Claude Code
(.claude/settings.json). It reads the hook payload (JSON) from stdin.

    agent_hooks.py pre-tool       before every tool call: deny / ask / allow
    agent_hooks.py session-start  records the session baseline and injects the session protocol
    agent_hooks.py stop           verify-on-stop guard: if code changed since the last passing
                                  `verify.py`, send the agent back to verify (max 2 times)

Decisions
  deny  -> exit 2 + reason on stderr (both tools block the call and show the reason to the agent)
  ask   -> JSON permissionDecision "ask" (a human approves in interactive sessions; under Copilot
           cloud agent "ask" is treated as deny because nobody is there to approve)
  allow -> no output
Internal errors fail OPEN (exit 0) so a bug in this script never bricks the agent; CI is the backstop.
Policy can be extended in harness.toml [agent_policy] (protected_paths, secret_paths, extra_deny_patterns,
extra_ask_patterns, ask_on_dependency_add). Decisions are logged to .agent/hook-log.jsonl.
Tier: STANDARD (kit-managed).
"""
from __future__ import annotations

import json
import os
import re
import sys
from pathlib import Path

sys.path.insert(0, str(Path(__file__).resolve().parent))
from _common import (  # noqa: E402
    DEFAULT_ACCEPTANCE_GLOBS, DEFAULT_NON_CODE_GLOBS, git, glob_match, is_placeholder, load_config, now_iso,
    read_json, rel, repo_root, state_dir, tree_fingerprint, working_tree_changes, write_json, detect_feature_dir,
)

SHELL_TOOLS = {"bash", "powershell", "shell", "execute", "run_in_terminal", "runinterminal", "terminal",
               "exec_command", "local_shell", "pwsh"}
EDIT_TOOLS = {"edit", "create", "write", "multiedit", "str_replace_editor", "str_replace_based_edit_tool",
              "apply_patch", "notebookedit", "insert_edit_into_file", "replace_string_in_file", "create_file",
              "edit_file", "editfiles", "write_file"}
READ_TOOLS = {"view", "read", "read_file", "readfile", "notebookread", "open_file", "grep", "search"}

PROTECTED_PATHS = [
    "AGENTS.md", "CLAUDE.md", ".github/copilot-instructions.md", ".github/hooks/**", ".github/workflows/**",
    ".github/agents/**", ".github/skills/**", ".github/instructions/**", ".github/CODEOWNERS", "CODEOWNERS",
    ".claude/settings.json", ".claude/agents/**", ".claude/skills/**", "scripts/harness/**", "harness.toml",
    ".specify/memory/constitution.md", "docs/standards/**",
]
SECRET_PATHS = ["**/.env", "**/.env.*", "**/*.pem", "**/*.key", "**/*.pfx", "**/*.p12", "**/id_rsa*",
                "**/id_ed25519*", "**/.aws/credentials", "**/.ssh/**", "**/.git-credentials", "**/.npmrc",
                "**/.pypirc", "**/.netrc", "**/secrets/**", "**/*.kdbx"]
SECRET_ALLOW = ["**/.env.example", "**/.env.sample", "**/.env.template", "**/.env.dist"]

# (decision, regex, reason) - evaluated case-insensitively against the full shell command.
SHELL_RULES = [
    ("deny", r"\bgit\s+push\b[^;&|\n]*(\s--force\b|\s--force-with-lease\b|\s-f\b|\s\+\S)",
     "Force-pushing rewrites shared history - a human gate."),
    ("deny", r"\bgit\s+push\b[^;&|\n]*\s(\S+:)?(refs/heads/)?(main|master|release(/\S*)?|prod|production)(\s|$)",
     "Pushing to main/master/release is a human gate. Push the feature branch and open a draft PR."),
    ("deny", r"\bgit\b[^;&|\n]*\s--no-verify\b", "Bypassing git hooks (--no-verify) defeats the harness."),
    ("deny", r"\bgit\s+(filter-branch|filter-repo)\b", "Rewriting history is a human gate."),
    ("ask", r"\bgit\s+reset\s+--hard\b", "git reset --hard discards work irreversibly."),
    ("ask", r"\bgit\s+clean\s+-\w*f", "git clean -f deletes untracked files irreversibly."),
    ("ask", r"\bgit\s+rebase\b", "Rebasing rewrites history; confirm it only touches your feature branch."),
    ("deny", r"\brm\s+(-\w+\s+)*-\w*[rR]\w*\s+(-\w+\s+)*(/|~|\$HOME|\*|\.\.?/?|\.git/?)(\s|$)",
     "Recursive delete of root, home, parent, everything or .git."),
    ("deny", r"\bRemove-Item\b[^;|\n]*-Recurse[^;|\n]*\s(/|\\|~|\$HOME|\$env:USERPROFILE|\*|\.\.|\.git)(\s|$)",
     "Recursive delete of root, home, parent, everything or .git."),
    ("deny", r"\b(curl|wget)\b[^\n]*\|\s*(sudo\s+)?(ba|z|da|k)?sh\b",
     "Piping a download into a shell runs unreviewed remote code."),
    ("deny", r"\b(iex|invoke-expression)\b[^\n]*\b(iwr|irm|invoke-webrequest|invoke-restmethod|downloadstring)\b",
     "Executing downloaded script content runs unreviewed remote code."),
    ("deny", r"\b(iwr|irm|invoke-webrequest|invoke-restmethod)\b[^\n]*\|\s*(iex|invoke-expression)\b",
     "Executing downloaded script content runs unreviewed remote code."),
    ("deny", r"\b(npm|pnpm|yarn)\s+publish\b|\btwine\s+upload\b|\bdotnet\s+nuget\s+push\b|\bmvnw?\b[^\n]*\bdeploy\b"
             r"|\bgradlew?\b[^\n]*\bpublish\b|\bdocker\s+push\b|\bgh\s+release\s+create\b",
     "Publishing artifacts is a human gate."),
    ("deny", r"\bterraform\s+(apply|destroy)\b|\bkubectl\s+(apply|delete|replace|scale|rollout|edit)\b"
             r"|\bhelm\s+(install|upgrade|uninstall|delete|rollback)\b|\bpulumi\s+(up|destroy)\b",
     "Deploying or changing infrastructure is a human gate."),
    ("deny", r"\bgh\s+pr\s+merge\b|\bgh\s+api\b[^\n]*/merge\b", "Merging is a human gate."),
    ("deny", r"\b(cat|type|more|less|head|tail|bat|nl|strings|get-content|gc|copy|cp)\b[^;&|\n]*"
             r"(\.env(?![\w.-]*(example|sample|template|dist))\b|id_rsa|id_ed25519|\.pem\b|\.pfx\b|\.p12\b"
             r"|\.aws[/\\]credentials|\.git-credentials|\.npmrc|\.pypirc|\.netrc)",
     "Reading secrets or credential files is not allowed for agents."),
    ("deny", r"(^|[;&|]\s*)(printenv|env)\s*($|[;&|])|\bprintenv\b|\b(get-childitem|gci|dir|ls)\s+env:",
     "Dumping environment variables can expose secrets."),
    ("deny", r"\bgh\s+auth\s+token\b|\baz\s+account\s+get-access-token\b|\baws\s+configure\s+get\b"
             r"|\bsecurity\s+find-(generic|internet)-password\b",
     "Extracting credentials is not allowed."),
    ("deny", r"\b(curl|wget)\b[^\n]*(\s-T\s|--upload-file|--data(-binary|-raw)?\s+@|\s-d\s+@|\s-F\s+\S+=@)",
     "Uploading local files to a remote host is an outward send - a human gate."),
    ("deny", r"\b(drop\s+(table|database|schema)|truncate\s+table)\b",
     "Destructive database statements are a human gate."),
]
DEPENDENCY_RULE = (
    "ask",
    r"\b(npm|pnpm|yarn)\s+(install|i|add)\b(\s+-\S+)*\s+[\w@]"
    r"|\bpip3?\s+install\b(?![^\n;&|]*\s-(r|e|c)\s)(\s+-\S+)*\s+[A-Za-z]"
    r"|\buv\s+add\b|\bpoetry\s+add\b|\bdotnet\s+add\b[^\n]*\bpackage\b|\bcargo\s+add\b|\bgo\s+get\b",
    "Adding a dependency needs a written justification in plan.md and human approval (smallest sufficient change).",
)
WRITE_CMD = re.compile(r"^\s*(sudo\s+)?(sed\s+(-\w+\s+)*-\w*i|perl\s+-\w*i|tee\b|rm\b|del\b|erase\b|rmdir\b|mv\b|move\b"
                       r"|cp\b|copy\b|truncate\b|chmod\b|set-content\b|add-content\b|out-file\b|remove-item\b"
                       r"|move-item\b|copy-item\b|rename-item\b|clear-content\b|git\s+(rm|mv|checkout\s+--|restore)\b)", re.I)
REDIRECT = re.compile(r"(?<![<>&\d])>{1,2}\s*([^\s;&|<>]+)")

# ---------------------------------------------------------------- payload helpers
def tool_name(p: dict) -> str:
    return str(p.get("toolName") or p.get("tool_name") or "").strip()


def tool_args(p: dict) -> dict:
    a = p.get("toolArgs", p.get("tool_input", {}))
    if isinstance(a, str):
        try:
            a = json.loads(a)
        except Exception:
            a = {"command": a}
    return a if isinstance(a, dict) else {}


def command_of(a: dict) -> str:
    for k in ("command", "cmd", "script", "commandLine", "input"):
        if isinstance(a.get(k), str):
            return a[k]
    return ""


def paths_of(a: dict) -> list:
    out = []
    for k in ("path", "file_path", "filePath", "filename", "notebook_path", "target_file", "file"):
        if isinstance(a.get(k), str):
            out.append(a[k])
    for k in ("paths", "files", "filePaths"):
        if isinstance(a.get(k), list):
            out += [x for x in a[k] if isinstance(x, str)]
    for k in ("patch", "input", "diff"):
        if isinstance(a.get(k), str):
            out += re.findall(r"^\*\*\* (?:Update|Add|Delete) File: (.+)$", a[k], flags=re.M)
    return out


def log(root: Path, event: str, **fields) -> None:
    try:
        entry = {"ts": now_iso(), "event": event, **fields}
        for k in ("cmd", "path"):
            if isinstance(entry.get(k), str):
                v = re.sub(r"(?i)((token|secret|password|passwd|apikey|api_key|key)\s*[=:]\s*)\S+", r"\1***", entry[k])
                entry[k] = v[:200]
        with (state_dir(root) / "hook-log.jsonl").open("a", encoding="utf-8") as fh:
            fh.write(json.dumps(entry, ensure_ascii=False) + "\n")
    except Exception:
        pass


def emit(decision: str, reason: str) -> int:
    if decision == "allow":
        return 0
    body = {"permissionDecision": decision, "permissionDecisionReason": reason,
            "hookSpecificOutput": {"hookEventName": "PreToolUse", "permissionDecision": decision,
                                   "permissionDecisionReason": reason}}
    print(json.dumps(body))
    if decision == "deny":
        sys.stderr.write(f"Blocked by harness guard: {reason}\n")
        return 2
    return 0


# ---------------------------------------------------------------- decisions
def evaluate_shell(cmd: str, policy: dict) -> tuple:
    rules = list(SHELL_RULES)
    if policy.get("ask_on_dependency_add", True):
        rules.append(DEPENDENCY_RULE)
    for rx in policy.get("extra_deny_patterns", []) or []:
        rules.append(("deny", rx, "Blocked by project policy (harness.toml extra_deny_patterns)."))
    for rx in policy.get("extra_ask_patterns", []) or []:
        rules.append(("ask", rx, "Needs approval by project policy (harness.toml extra_ask_patterns)."))
    verdict = ("allow", "")
    for decision, rx, reason in rules:
        try:
            if re.search(rx, cmd, flags=re.I):
                if decision == "deny":
                    return decision, reason
                verdict = (decision, reason)
        except re.error:
            continue
    protected = PROTECTED_PATHS + list(policy.get("protected_paths", []) or [])
    targets = [m.group(1) for m in REDIRECT.finditer(cmd)]
    for segment in re.split(r"&&|\|\||[;|\n]", cmd):
        if WRITE_CMD.search(segment):
            targets += re.split(r"[\s'\"=()]+", segment)[1:]
    for token in targets:
        t = token.strip().strip("'\"").replace("\\", "/")
        if t.startswith("./"):
            t = t[2:]
        if t and not t.startswith("-") and glob_match(t, protected):
            return "ask", f"This command may modify a protected harness file ({t}); a human must approve."
    return verdict


def evaluate_paths(root: Path, tool: str, paths: list, policy: dict, acceptance: list) -> tuple:
    protected = PROTECTED_PATHS + list(policy.get("protected_paths", []) or [])
    secrets = SECRET_PATHS + list(policy.get("secret_paths", []) or [])
    for raw in paths:
        rp = rel(root, raw)
        is_secret = glob_match(rp, secrets) and not glob_match(rp, SECRET_ALLOW)
        if tool in READ_TOOLS:
            if is_secret:
                return "deny", f"Reading secrets or credential files is not allowed for agents ({rp})."
            continue
        if is_secret:
            return "ask", f"Writing to a secrets/credentials file ({rp}) needs human approval."
        if Path(rp).is_absolute() or rp.startswith("../"):
            return "ask", f"Editing outside the repository ({rp}) needs human approval."
        if glob_match(rp, protected):
            return "ask", (f"{rp} is a protected harness file (AGENTS.md section 10). A human must approve this change; "
                           "if you were corrected, propose the rule in docs/agent-memory/lessons.md instead.")
        if glob_match(rp, acceptance) and (root / rp).exists():
            return "ask", (f"{rp} is an existing acceptance test (the spec owner's contract). Do not change it to get "
                           "green; record the problem in progress.md 'Open issues' and ask the human.")
    return "allow", ""


def pre_tool(root: Path, payload: dict, cfg: dict) -> int:
    policy = cfg.get("agent_policy", {}) or {}
    acceptance = (cfg.get("tests", {}) or {}).get("acceptance_globs") or DEFAULT_ACCEPTANCE_GLOBS
    name = tool_name(payload)
    lname = name.lower()
    args = tool_args(payload)
    decision, reason = "allow", ""
    cmd = ""
    if lname in SHELL_TOOLS:
        cmd = command_of(args)
        decision, reason = evaluate_shell(cmd, policy)
    elif lname in EDIT_TOOLS or lname in READ_TOOLS:
        decision, reason = evaluate_paths(root, lname, paths_of(args), policy, acceptance)
    if decision != "allow":
        log(root, "pre-tool", tool=name, decision=decision, reason=reason, cmd=cmd,
            path=",".join(paths_of(args))[:200])
    return emit(decision, reason)


def session_start(root: Path, payload: dict, cfg: dict) -> int:
    head = (git(["rev-parse", "HEAD"], root) or "").strip() or None
    write_json(state_dir(root) / "session.json", {"start_head": head, "started": now_iso(), "blocks": 0})
    feature = detect_feature_dir(root)
    lines = [
        "Agentic Delivery Standard is active. AGENTS.md (repo root) is your map; standards live in docs/standards/.",
        (f"Active feature: {feature.relative_to(root).as_posix()} - read spec.md, plan.md, tasks.md and progress.md before acting."
         if feature else "No active Spec Kit feature folder detected (chore/bug lane, or a new feature)."),
        "Before you finish a task that changed code, run `python scripts/harness/verify.py --fast` and read the result; "
        "a stop guard will send you back if you skip it.",
        "End every task with the AGENTS.md output contract (Needs from you, What changed, Evidence, Skipped, Blocked, Rollback, New rule).",
    ]
    text = "\n".join(lines)
    print(json.dumps({"additionalContext": text,
                      "hookSpecificOutput": {"hookEventName": "SessionStart", "additionalContext": text}}))
    log(root, "session-start", head=head)
    return 0


def on_stop(root: Path, payload: dict, cfg: dict) -> int:
    vcfg = cfg.get("verify", {}) or {}
    if vcfg.get("stop_guard", True) is False:
        return 0
    checks = cfg.get("check", []) or []
    if not checks or any(is_placeholder(c.get("run", "")) for c in checks if c.get("enabled", True) is not False):
        log(root, "stop", decision="allow", reason="harness not configured")
        return 0
    sd = state_dir(root)
    session = read_json(sd / "session.json") or {}
    start = session.get("start_head")
    head = (git(["rev-parse", "HEAD"], root) or "").strip()
    changed = set(working_tree_changes(root))
    if start and head and start != head:
        diff = git(["diff", "--name-only", f"{start}..{head}"], root) or ""
        changed.update(x.strip() for x in diff.splitlines() if x.strip())
    non_code = vcfg.get("non_code_globs", DEFAULT_NON_CODE_GLOBS)
    code_changed = sorted(p for p in changed if not glob_match(p, non_code))
    if not code_changed:
        return 0
    required = str(vcfg.get("stop_guard_stage", "fast"))
    rank = {"fast": 1, "full": 2}
    stamp = read_json(sd / "verify-stamp.json") or {}
    fingerprint = tree_fingerprint(root, non_code)
    if stamp.get("passed") and stamp.get("fingerprint") == fingerprint and \
            rank.get(stamp.get("stage"), 0) >= rank.get(required, 1):
        session["blocks"] = 0
        write_json(sd / "session.json", session)
        return 0
    blocks = int(session.get("blocks", 0) or 0)
    if payload.get("stop_hook_active") and blocks >= 2:
        session["blocks"] = 0
        write_json(sd / "session.json", session)
        log(root, "stop", decision="allow-unverified", files=len(code_changed))
        return 0
    session["blocks"] = blocks + 1
    write_json(sd / "session.json", session)
    cmd = "python scripts/harness/verify.py" + (" --fast" if required == "fast" else "")
    sample = ", ".join(code_changed[:3]) + (" ..." if len(code_changed) > 3 else "")
    reason = (f"Verification guard: {len(code_changed)} code file(s) changed since the last passing `{cmd}` ({sample}). "
              f"Run `{cmd}` now and fix any failures - never by weakening, skipping or deleting tests. "
              "If it cannot pass, stop and report BLOCKED with the failing output using the AGENTS.md output contract. "
              "If you are pausing for human input, still run it so the human sees the current state.")
    print(json.dumps({"decision": "block", "reason": reason}))
    log(root, "stop", decision="block", files=len(code_changed))
    return 0


def main() -> int:
    event = (sys.argv[1] if len(sys.argv) > 1 else "").strip()
    raw = ""
    try:
        if not sys.stdin.isatty():
            raw = sys.stdin.read()
    except Exception:
        raw = ""
    try:
        payload = json.loads(raw) if raw.strip() else {}
    except Exception:
        payload = {}
    if not isinstance(payload, dict):
        payload = {}
    try:
        root = repo_root(Path(payload.get("cwd") or os.environ.get("CLAUDE_PROJECT_DIR") or os.getcwd()))
        cfg = load_config(root)
        if event in ("pre-tool", "preToolUse", "PreToolUse"):
            return pre_tool(root, payload, cfg)
        if event in ("session-start", "sessionStart", "SessionStart"):
            return session_start(root, payload, cfg)
        if event in ("stop", "agentStop", "Stop"):
            return on_stop(root, payload, cfg)
        sys.stderr.write(f"[agent_hooks] unknown event '{event}' - ignored\n")
        return 0
    except Exception as exc:  # fail open: CI and review are the backstop
        sys.stderr.write(f"[agent_hooks] internal error ignored (fail-open): {exc}\n")
        return 0


if __name__ == "__main__":
    sys.exit(main())
