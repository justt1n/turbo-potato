#!/usr/bin/env python3
from __future__ import annotations

import argparse
import re
import subprocess
import sys
from pathlib import Path

ALLOW_MARKER = "codex-allow-secret"

BLOCKED_PATHS = (
    re.compile(r"(^|/)secrets(/|$)"),
    re.compile(r"(^|/)\.env$"),
    re.compile(r"(^|/)config/local\.ya?ml$"),
)

BLOCKED_PATH_EXCEPTIONS = {
    ".env.example",
}

IGNORED_DIRS = {
    ".git",
    ".venv",
    "node_modules",
    "dist",
    "__pycache__",
    ".pytest_cache",
}

PATTERNS: list[tuple[str, re.Pattern[str]]] = [
    ("OpenAI key", re.compile(r"\bsk-[A-Za-z0-9_-]{20,}\b")),
    ("Google API key", re.compile(r"\bAIza[0-9A-Za-z\-_]{20,}\b")),
    ("AWS access key", re.compile(r"\bAKIA[0-9A-Z]{16}\b")),
    ("Private key block", re.compile(r"-----BEGIN (?:RSA |EC |OPENSSH |DSA |PGP )?PRIVATE KEY-----")),
    (
        "Generic credential assignment",
        re.compile(
            r"""(?ix)
            \b(api[_-]?key|secret|token|password|passwd|private[_-]?key)\b
            \s*[:=]\s*
            ["']
            (?=[A-Za-z0-9_\-\/+=:.]{20,}["'])
            (?=[^"'\n]*[A-Za-z])
            (?=[^"'\n]*\d)
            [A-Za-z0-9_\-\/+=:.]{20,}
            ["']
            """
        ),
    ),
]


def run(*args: str) -> str:
    result = subprocess.run(args, check=True, capture_output=True, text=True)
    return result.stdout


def staged_files() -> list[str]:
    output = run("git", "diff", "--cached", "--name-only", "--diff-filter=ACMR")
    return [line.strip() for line in output.splitlines() if line.strip()]


def staged_blob(path: str) -> bytes:
    result = subprocess.run(["git", "show", f":{path}"], check=True, capture_output=True)
    return result.stdout


def working_tree_files(root: Path) -> list[str]:
    return [
        str(path.relative_to(root))
        for path in root.rglob("*")
        if path.is_file() and not any(part in IGNORED_DIRS for part in path.parts)
    ]


def file_bytes(root: Path, path: str) -> bytes:
    return (root / path).read_bytes()


def looks_binary(data: bytes) -> bool:
    return b"\x00" in data


def path_blocked(path: str) -> str | None:
    if path in BLOCKED_PATH_EXCEPTIONS:
        return None
    for pattern in BLOCKED_PATHS:
        if pattern.search(path):
            return "blocked local-secret path"
    return None


def scan_text(path: str, text: str) -> list[str]:
    findings: list[str] = []
    for line_no, line in enumerate(text.splitlines(), start=1):
        if ALLOW_MARKER in line:
            continue
        for label, pattern in PATTERNS:
            if pattern.search(line):
                findings.append(f"{path}:{line_no}: {label}")
    return findings


def main() -> int:
    parser = argparse.ArgumentParser()
    parser.add_argument("--all-files", action="store_true", help="Scan working tree instead of staged files.")
    args = parser.parse_args()

    root = Path.cwd()
    paths = working_tree_files(root) if args.all_files else staged_files()

    findings: list[str] = []
    for path in paths:
        blocked = path_blocked(path)
        if blocked:
            findings.append(f"{path}: {blocked}")
            continue

        try:
            data = file_bytes(root, path) if args.all_files else staged_blob(path)
        except (FileNotFoundError, subprocess.CalledProcessError):
            continue

        if looks_binary(data):
            continue

        text = data.decode("utf-8", errors="ignore")
        findings.extend(scan_text(path, text))

    if not findings:
        print("secret check passed")
        return 0

    print("secret check failed:")
    for item in findings:
        print(f"  - {item}")
    print(f"Add '{ALLOW_MARKER}' on an intentional example line to bypass a false positive.")
    return 1


if __name__ == "__main__":
    sys.exit(main())
