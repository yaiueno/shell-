# 再現性メモ（2026-04-17）

## 1. 実行マシン情報
- 取得日時: 2026-04-17T15:34:37+09:00
- ユーザー: `t246270`
- ホスト名: `eib-pc064`
- OS: Ubuntu 24.04.3 LTS (Noble Numbat)
  - `PRETTY_NAME="Ubuntu 24.04.3 LTS"`
  - `VERSION_ID="24.04"`
- カーネル: `Linux 6.14.0-37-generic`
- アーキテクチャ: `x86_64`
- CPU: `Intel(R) Core(TM) i5-14500T`
- 論理CPU数: `20`
- タイムゾーン: `Asia/Tokyo`（`/etc/localtime -> /usr/share/zoneinfo/Asia/Tokyo`）
- ロケール: `LANG=ja_JP.UTF-8`

## 2. シェル・端末情報
- VS Code内ターミナル: `tcsh`
- `SHELL=/bin/tcsh`
- `TERM=xterm-256color`
- `TERM_PROGRAM=vscode`
- `TERM_PROGRAM_VERSION=1.109.5`
- シェル実体:
  - `tcsh`: `/usr/bin/tcsh`（`tcsh 6.24.10`）
  - `bash`: `/usr/bin/bash`（`GNU bash 5.2.21`）
  - POSIX `sh`: `/bin/sh -> dash`
  - `dash` パッケージ版: `0.5.12-6ubuntu5`

### 注意（再現で重要）
- 端末が `tcsh` のため、`bash` 向け構文（`set -e`, `2>/dev/null` など）がそのまま使えない。
- 課題スクリプトは `#!/bin/sh` のため、実行時は実質 `dash` で動作する。

## 3. VS Code 構成
- VS Code バージョン: `1.109.5`
- Commit: `072586267e68ece9a47aa43f8c108e0dcbf44622`
- Arch: `x64`
- `code` CLI: `/usr/bin/code`

### インストール済み拡張（`code --list-extensions --show-versions`）
- `github.codespaces@1.18.12`
- `github.copilot-chat@0.37.9`
- `mathematic.vscode-latex@1.3.0`
- `ms-ceintl.vscode-language-pack-ja@1.110.2026041514`
- `ms-python.debugpy@2025.18.0`
- `ms-python.python@2026.4.0`
- `ms-python.vscode-pylance@2026.2.1`
- `ms-python.vscode-python-envs@1.20.1`
- `ms-vscode.cmake-tools@1.23.51`
- `ms-vscode.cpp-devtools@0.4.6`
- `ms-vscode.cpptools@1.31.4`
- `ms-vscode.cpptools-extension-pack@1.5.1`
- `ms-vscode.cpptools-themes@2.0.0`
- `tomoki1207.pdf@1.2.2`
- `twxs.cmake@0.0.17`

## 4. ワークスペース情報
- ルート: `/home/s24/t246270/shell`
- 主なファイル:
  - `*.sh`: `4.sh, 8.sh, add.sh, calc.sh, cat.sh, div.sh, hello.sh, j4.sh, mul.sh, owner.sh, res.sh, sub.sh`
  - サブディレクトリ `2/`: `1.sh, 2.sh`
  - Python: `mymath.py, vterm_logger.py`
  - その他: `README.md, mondai.txt, terminal.txt`
  - ログ/生データ: `terminal_io.log, terminal_io_cleaned_preview.log, vterm_logger_*.raw`

### 権限
- `*.sh` と `2/*.sh` は全て `-rwxr-xr-x`（実行可能）

## 5. 実行PATH（tcsh）
`/home/s24/t246270/.config/Code/User/globalStorage/github.copilot-chat/debugCommand`
`/home/s24/t246270/.config/Code/User/globalStorage/github.copilot-chat/copilotCli`
`/home/s24/t246270/.local/bin`
`/usr/local/sbin`
`/usr/local/bin`
`/usr/sbin`
`/usr/bin`
`/sbin`
`/bin`
`/usr/games`
`/usr/local/games`
`/snap/bin`
`/home/s24/t246270/.vscode/extensions/ms-python.debugpy-2025.18.0-linux-x64/bundled/scripts/noConfigScripts`

## 6. 補足
- `git` コマンドは未インストール（この環境では `git: コマンドが見つかりません`）。
- `README.md` には `vterm_logger.py` の使い方（`python3 vterm_logger.py`）が記載されている。