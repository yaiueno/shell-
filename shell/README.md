# shell-
# shell-
# shell-
# shell-

## Python 版: 仮想端末 + 入出力ログ

`vterm_logger.py` は Linux の `script` コマンドでセッションを記録し、終了後に ANSI などを軽く掃除して txt に保存します。

### 使い方

```bash
python3 vterm_logger.py
```

オプション:

```bash
python3 vterm_logger.py --shell /bin/bash --log logs/session.log
```

### ログ形式

普通の txt として、セッション全体を記録します。

- `script` の生ログをそのまま残さず、終了後に見づらい制御文字を除去します。
- 実行ごとにセッションID付きファイル名で保存するため、既存ログは上書きしません。
- 保存はシェル終了時に行われます（終了後に「保存完了」を表示）。
