#!/usr/bin/env python3
import argparse
import datetime
import os
import re
import shutil
import subprocess
import sys
import tempfile


ANSI_RE = re.compile(r"\x1b\[[0-?]*[ -/]*[@-~]|\x1b[@-_]")


def parse_args() -> argparse.Namespace:
    parser = argparse.ArgumentParser(
        description="端末セッションをそのまま txt に記録する最小ラッパー",
    )
    parser.add_argument(
        "--shell",
        default=os.environ.get("SHELL", "/bin/bash"),
        help="起動するシェル（既定: 環境変数SHELL または /bin/bash）",
    )
    parser.add_argument(
        "--log",
        default="terminal_io.log",
        help="ログファイルパス（既定: terminal_io.log）",
    )
    return parser.parse_args()


def strip_ansi(text: str) -> str:
    return ANSI_RE.sub("", text)


def _parse_csi_sequence(text: str, index: int) -> tuple[int, str, list[int]]:
    i = index + 2
    while i < len(text) and not ("@" <= text[i] <= "~"):
        i += 1
    if i >= len(text):
        return len(text), "", []

    final = text[i]
    param_text = text[index + 2 : i]
    params: list[int] = []
    if param_text:
        for part in param_text.split(";"):
            if part.isdigit():
                params.append(int(part))
            else:
                params.append(0)
    return i + 1, final, params


def render_terminal_text(raw_text: str) -> list[str]:
    lines: list[str] = []
    current: list[str] = []
    cursor = 0

    def ensure_len(n: int) -> None:
        while len(current) < n:
            current.append(" ")

    def put_char(ch: str) -> None:
        nonlocal cursor
        if cursor == len(current):
            current.append(ch)
        else:
            current[cursor] = ch
        cursor += 1

    i = 0
    while i < len(raw_text):
        ch = raw_text[i]

        if ch == "\x1b":
            if i + 1 < len(raw_text) and raw_text[i + 1] == "[":
                i, final, params = _parse_csi_sequence(raw_text, i)
                n = params[0] if params else 1
                if final == "D":
                    cursor = max(0, cursor - max(1, n))
                elif final == "C":
                    cursor = min(max(0, n + cursor), max(len(current), cursor + n))
                    ensure_len(cursor)
                elif final == "G":
                    col = max(1, n)
                    cursor = col - 1
                    ensure_len(cursor)
                elif final == "K":
                    mode = params[0] if params else 0
                    if mode == 0:
                        del current[cursor:]
                    elif mode == 1:
                        for j in range(0, min(cursor, len(current))):
                            current[j] = " "
                    elif mode == 2:
                        current = []
                        cursor = 0
                continue
            i += 1
            continue

        if ch == "\r":
            cursor = 0
            i += 1
            continue

        if ch == "\n":
            lines.append("".join(current).rstrip())
            current = []
            cursor = 0
            i += 1
            continue

        if ch in ("\x08", "\x7f"):
            cursor = max(0, cursor - 1)
            i += 1
            continue

        if ch == "\x07":
            i += 1
            continue

        if ch == "\t":
            spaces = 4 - (cursor % 4)
            for _ in range(spaces):
                put_char(" ")
            i += 1
            continue

        if ord(ch) < 0x20:
            i += 1
            continue

        ensure_len(cursor)
        put_char(ch)
        i += 1

    if current:
        lines.append("".join(current).rstrip())

    return lines


def build_unique_log_path(base_log_path: str) -> str:
    base_dir = os.path.dirname(base_log_path) or "."
    base_name = os.path.basename(base_log_path)
    stem, ext = os.path.splitext(base_name)
    if not ext:
        ext = ".log"

    session_id = datetime.datetime.now().strftime("%Y%m%d_%H%M%S") + f"_{os.getpid()}"
    candidate = os.path.join(base_dir, f"{stem}_{session_id}{ext}")

    counter = 1
    while os.path.exists(candidate):
        candidate = os.path.join(base_dir, f"{stem}_{session_id}_{counter}{ext}")
        counter += 1

    return candidate


def clean_script_log(raw_path: str, final_path: str) -> None:
    with open(raw_path, "r", encoding="utf-8", errors="replace") as src:
        lines = render_terminal_text(src.read())

    cleaned: list[str] = []
    for line in lines:
        line = strip_ansi(line).rstrip()
        if not line:
            cleaned.append("")
            continue
        if line.startswith("スクリプトを ") and " に開始 " in line:
            continue
        if line.startswith("スクリプトは ") and " に終了しました" in line:
            continue
        if line.startswith("Script started on ") or line.startswith("Script done on "):
            continue
        cleaned.append(line)

    while cleaned and cleaned[0] == "":
        cleaned.pop(0)
    while cleaned and cleaned[-1] == "":
        cleaned.pop()

    os.makedirs(os.path.dirname(final_path) or ".", exist_ok=True)
    with open(final_path, "w", encoding="utf-8") as dst:
        dst.write("\n".join(cleaned))
        if cleaned:
            dst.write("\n")


def main() -> int:
    args = parse_args()
    os.makedirs(os.path.dirname(args.log) or ".", exist_ok=True)
    final_log_path = build_unique_log_path(args.log)

    if not shutil.which("script"):
        print("Error: 'script' command not found.", file=sys.stderr)
        return 1

    fd, raw_path = tempfile.mkstemp(prefix="vterm_logger_", suffix=".raw", dir=os.path.dirname(os.path.abspath(final_log_path)) or ".")
    os.close(fd)

    try:
        print(f"[vterm_logger] セッションID付きログ: {final_log_path}")
        cmd = ["script", "-q", "-f", raw_path, "-c", args.shell]
        code = subprocess.call(cmd)
        clean_script_log(raw_path, final_log_path)
        print(f"[vterm_logger] 保存完了: {final_log_path}")
        return code
    finally:
        try:
            os.remove(raw_path)
        except OSError:
            pass


if __name__ == "__main__":
    raise SystemExit(main())