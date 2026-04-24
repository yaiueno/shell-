#!/usr/bin/env python3
import argparse
import datetime
import os
import re
import shlex
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
    parser.add_argument(
        "-s", "--script",
        nargs="+",
        help="実行するシェルスクリプトパス（自動で実行権限を付与して実行）",
    )
    parser.add_argument(
        "--grant-only",
        action="store_true",
        help="シェルスクリプトへ実行権限を付与するだけで終了する",
    )
    parser.add_argument(
        "--grant-root",
        default=os.getcwd(),
        help="--grant-only 時に再帰走査するルートディレクトリ（既定: 現在の作業ディレクトリ）",
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


def ensure_executable(script_path: str) -> bool:
    if not os.path.exists(script_path):
        return False
    st_mode = os.stat(script_path).st_mode
    os.chmod(script_path, st_mode | 0o111)
    return True


def grant_shell_scripts_in_tree(root_dir: str) -> list[str]:
    updated: list[str] = []
    for dirpath, _, filenames in os.walk(root_dir):
        for filename in filenames:
            if not filename.endswith(".sh"):
                continue
            script_path = os.path.join(dirpath, filename)
            if ensure_executable(script_path):
                updated.append(script_path)
    return updated


def grant_shell_scripts_silently(root_dir: str) -> None:
    grant_shell_scripts_in_tree(root_dir)


def shell_basename(shell_command: str) -> str:
    return os.path.basename(shlex.split(shell_command)[0])


def create_tcsh_hook_file(work_dir: str) -> str:
    home_dir = os.path.expanduser("~")
    hook_file = os.path.join(work_dir, ".tcshrc")
    lines = [
        f"if ( -f {shlex.quote(os.path.join(home_dir, '.tcshrc'))} ) source {shlex.quote(os.path.join(home_dir, '.tcshrc'))}",
        f"else if ( -f {shlex.quote(os.path.join(home_dir, '.cshrc'))} ) source {shlex.quote(os.path.join(home_dir, '.cshrc'))}",
        "endif",
        f"alias postcmd 'if ( ! $?VTERM_GRANT_RUNNING ) then; setenv VTERM_GRANT_RUNNING 1; python3 {os.path.abspath(__file__)} --grant-only --grant-root \"$cwd\" >& /dev/null; unsetenv VTERM_GRANT_RUNNING; endif'",
    ]
    with open(hook_file, "w", encoding="utf-8") as f:
        f.write("\n".join(lines) + "\n")
    return hook_file


def create_bash_hook_file(work_dir: str) -> str:
    home_dir = os.path.expanduser("~")
    hook_file = os.path.join(work_dir, ".bashrc")
    lines = [
        f"if [ -f {shlex.quote(os.path.join(home_dir, '.bashrc'))} ]; then source {shlex.quote(os.path.join(home_dir, '.bashrc'))}; fi",
        "__vterm_grant() {",
        f"  python3 {shlex.quote(os.path.abspath(__file__))} --grant-only --grant-root \"$PWD\" > /dev/null 2>&1",
        "}",
        "trap '__vterm_grant' DEBUG",
    ]
    with open(hook_file, "w", encoding="utf-8") as f:
        f.write("\n".join(lines) + "\n")
    return hook_file


def prepare_interactive_shell(shell_command: str) -> tuple[list[str], dict[str, str], list[str]]:
    shell_argv = shlex.split(shell_command)
    if not shell_argv:
        shell_argv = ["/bin/bash"]

    shell_name = shell_basename(shell_command)
    env = os.environ.copy()
    cleanup_paths: list[str] = []

    if shell_name in {"tcsh", "csh"}:
        temp_home = tempfile.mkdtemp(prefix="vterm_logger_home_")
        create_tcsh_hook_file(temp_home)
        env["HOME"] = temp_home
        cleanup_paths.append(temp_home)
        return shell_argv, env, cleanup_paths

    if shell_name == "bash":
        temp_home = tempfile.mkdtemp(prefix="vterm_logger_home_")
        bashrc = create_bash_hook_file(temp_home)
        env["HOME"] = temp_home
        shell_argv = shell_argv + ["--rcfile", bashrc, "-i"]
        cleanup_paths.append(temp_home)
        return shell_argv, env, cleanup_paths

    return shell_argv, env, cleanup_paths


def build_script_command(script_paths: list[str]) -> str:
    absolute_paths = [os.path.abspath(path) for path in script_paths]
    return " && ".join(shlex.quote(path) for path in absolute_paths)


def run_logged_command(cmd: list[str], raw_path: str, final_log_path: str) -> int:
    code = subprocess.call(cmd)
    clean_script_log(raw_path, final_log_path)
    return code


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

    if args.grant_only:
        grant_shell_scripts_silently(args.grant_root)
        return 0

    os.makedirs(os.path.dirname(args.log) or ".", exist_ok=True)
    final_log_path = build_unique_log_path(args.log)

    if not shutil.which("script"):
        print("Error: 'script' command not found.", file=sys.stderr)
        return 1

    cleanup_paths: list[str] = []

    # スクリプト実行モード
    if args.script:
        fd, raw_path = tempfile.mkstemp(prefix="vterm_logger_", suffix=".raw", dir=os.path.dirname(os.path.abspath(final_log_path)) or ".")
        os.close(fd)
        
        try:
            print("\n" + "=" * 60)
            print("[vterm_logger] スクリプト実行モード")
            print("=" * 60)
            
            # 各スクリプトに実行権限を付与
            for script_path in args.script:
                if ensure_executable(script_path):
                    print(f"  ✓ 実行権限付与: {script_path}")
                else:
                    print(f"  ✗ ファイルが見つかりません: {script_path}", file=sys.stderr)
            
            print(f"  ログ保存先: {final_log_path}")
            print("=" * 60 + "\n")
            
            # スクリプトをシェルで実行（安全に quote したコマンド列を使用）
            script_cmd = build_script_command(args.script)
            session_cmd = f"{shlex.quote(args.shell)} -c {shlex.quote(script_cmd)}"
            cmd = ["script", "-q", "-f", raw_path, "-c", session_cmd]
            code = run_logged_command(cmd, raw_path, final_log_path)
            
            print("\n" + "=" * 60)
            print(f"[vterm_logger] スクリプト実行完了")
            print(f"  終了コード: {code}")
            print(f"  ログ保存先: {final_log_path}")
            print("=" * 60 + "\n")
            return code
        finally:
            try:
                os.remove(raw_path)
            except OSError:
                pass
    
    # 通常のインタラクティブモード
    fd, raw_path = tempfile.mkstemp(prefix="vterm_logger_", suffix=".raw", dir=os.path.dirname(os.path.abspath(final_log_path)) or ".")
    os.close(fd)

    try:
        shell_argv, shell_env, cleanup_paths = prepare_interactive_shell(args.shell)
        print("\n" + "=" * 60)
        print("[vterm_logger] インタラクティブシェル 起動中...")
        print("=" * 60)
        print(f"  シェル: {args.shell}")
        print(f"  ログ保存先: {final_log_path}")
        granted = grant_shell_scripts_in_tree(os.getcwd())
        if granted:
            print(f"  実行権限付与済みの .sh: {len(granted)} 件")
        print()
        print("  【終了方法】")
        print("    • コマンド: exit")
        print("    • キーボード: Ctrl + D")
        print("=" * 60 + "\n")
        
        cmd = ["script", "-q", "-f", raw_path, "-c", shlex.join(shell_argv)]
        code = subprocess.call(cmd, env=shell_env)
        clean_script_log(raw_path, final_log_path)
        
        print("\n" + "=" * 60)
        print("[vterm_logger] インタラクティブシェル 終了")
        print(f"  終了コード: {code}")
        print(f"  ログ保存先: {final_log_path}")
        print("=" * 60 + "\n")
        return code
    finally:
        try:
            os.remove(raw_path)
        except OSError:
            pass
        for cleanup_path in cleanup_paths:
            try:
                shutil.rmtree(cleanup_path)
            except OSError:
                pass


if __name__ == "__main__":
    raise SystemExit(main())