# かわいい横スクロールアクション（Python + pygame）

## セットアップ（WSL / bash）
```bash
# 依存の準備（日本語フォント含む）
sudo apt update
sudo apt install -y python3-venv python3-pip fonts-noto-cjk

# 仮想環境の作成と有効化
python3 -m venv .venv
source .venv/bin/activate

# 依存インストールと実行
pip install -r requirements.txt
python3 main.py
```

- Windows 11 の WSLg ならそのままウィンドウが出ます。Windows 10 などで X サーバが必要な環境では、別途 X サーバ（VcXsrv 等）の起動と `DISPLAY` 設定が必要です。

## ゲームの遊び方
- 移動: 左右キー (← →)
- ジャンプ: スペース
- 休憩/ポーズ: P
- リスタート: R
- 終了: Esc または ウィンドウを閉じる

## ゲーム概要
- ステージは全部で4つ。横スクロールで、ジャンプ中心のアクション。
- 各ステージ終盤でボスが登場。ボスの上にジャンプで踏むとダメージ。
- 低年齢でも楽しめる、かわいい見た目・やさしめ難易度。

## 日本語が文字化けする場合
- 本リポジトリの `main.py` は、日本語に対応したフォント（Noto/Meiryo/游ゴシック/IPA など）を自動検出して使用します。
- それでも出ない場合は、次を確認してください。
  - `sudo apt install -y fonts-noto-cjk` を実行してフォントをインストール
  - 別の日本語フォントを入れている場合は、`get_japanese_font()` の候補に名前を追加
  - どうしても出ない場合は `README` の文言を英数字に一時的に置換

## トラブルシュート
- 画面が開かない: WSLg が有効かを確認（`wsl.exe --version`）。X サーバが必要な環境では X サーバの起動と `DISPLAY` の設定が必要です。
- 実行が重い: 別アプリを閉じてから試す、解像度を下げる（`main.py` の `WIDTH/HEIGHT` を調整）
