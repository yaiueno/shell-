# shell-
# shell-
# shell-
# shell-

## Python 版: 仮想端末 + 入出力ログ

`vterm_logger.py` は Linux の `script` コマンドでセッションを記録し、終了後に ANSI などを軽く掃除して txt に保存します。

### 使い方

#### インタラクティブシェルモード

通常の対話型シェルを起動し、ログに記録します：

```bash
python3 vterm_logger.py
```

オプション:

```bash
python3 vterm_logger.py --shell /bin/bash --log logs/session.log
```

**起動状態の確認：**
- 起動時に `[vterm_logger] インタラクティブシェル 起動中...` と表示
- インタラクティブモードでは、各コマンド実行の直前に作業フォルダ配下の `.sh` へ自動で実行権限が付与される
- 終了方法が明記される（`exit` または `Ctrl+D`）

**終了方法：**
- コマンドで終了: `exit`
- キーボード: `Ctrl + D`

終了すると `[vterm_logger] インタラクティブシェル 終了` と表示され、ログが保存されます。

#### シェルスクリプト実行モード

シェルスクリプトを自動で `chmod +x` してから実行し、ログを記録します：

```bash
# 単一スクリプト実行
python3 vterm_logger.py -s script.sh --log logs/test.log

# 複数スクリプトを順序実行
python3 vterm_logger.py -s script1.sh script2.sh script3.sh --log logs/multi.log
```

このモードでは：
- `[vterm_logger] スクリプト実行モード` と表示される
- 各スクリプトに自動で実行権限（`chmod +x`）を付与します
- 複数指定した場合は全て実行します
- すべての出力をログファイルに記録します
- スクリプト実行完了後に自動で終了

補足:
- 実行権限の付与後は、Python からそのままスクリプトを起動します
- ログは `script` 経由で取得し、終了後に読みやすい txt に整形して保存します

### ログ形式

普通の txt として、セッション全体を記録します。

- `script` の生ログをそのまま残さず、終了後に見づらい制御文字を除去します。
- 実行ごとにセッションID付きファイル名で保存するため、既存ログは上書きしません。
- 保存はシェル終了時に行われます（終了後に「保存完了」を表示）。
