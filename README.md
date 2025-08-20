# Jump & Smile Adventure（pygame）

かわいい横スクロールアクション。全4ステージ、各ステージ最後にボス戦。低年齢でも遊べるやさしめ設計です。

## 特徴
- 4ステージ構成の横スクロール
- ジャンプ主体（コヨーテタイム＋二段ジャンプ対応）
- 各ステージでボス登場（踏みつけでダメージ）
- ボス戦は地面のみでダイナミックに動く
- 日本語表示対応・やさしい色味のUI
- BGMと効果音（ジャンプ／踏みつけ／被弾／ポーズ）
- 落下時はスマブラ風の浮遊→落下で復活（無敵時間あり）
- 動く足場に“乗っている間”は足場と一緒に移動（慣性）

## 操作（キーボード）
- 移動: ← →
- ジャンプ: Space（空中で2回まで）
- ポーズ: P
- リスタート: R（タイトル/ゲームオーバー/勝利画面では Space/Enter でも可）
- 終了: Esc

## 実行（Windows）
```powershell
# 初回のみ
py -m venv .venv
.\.venv\Scripts\Activate.ps1
python -m pip install --upgrade pip
pip install -r requirements.txt

# 起動
python main.py
```

## 配布（exe 単体配布）
PyInstaller の onefile ビルドで `dist/JumpSmile.exe` を配布すれば、相手は環境構築なしで遊べます。

```powershell
.\.venv\Scripts\Activate.ps1
pip install pyinstaller
pyinstaller --name "JumpSmile" --onefile --noconsole --clean main.py
# うまく動かない時は pygame の収集を追加
pyinstaller --name "JumpSmile" --onefile --noconsole --clean main.py ^
  --collect-submodules pygame --collect-data pygame
```
- 配布物: `dist/JumpSmile.exe`
- SmartScreen が表示される場合があります（未署名のため）。配布先で「詳細情報」→「実行」。
- 誤検知が気になる場合は `--onedir` でフォルダごと配布も可。

## 主な変更点（実装メモ）
- 日本語フォント自動検出（Noto/Meiryo/游ゴシック/IPA等）
- UIフォントサイズ調整（切れにくく）
- 二段ジャンプ＋コヨーテタイム追加
- 動く足場の慣性（着地直後＋接地中は足場移動量を反映）
- ボスAI改善（スタック回避、ダッシュ/大ジャンプ、弾発射の向き制御）
- ボス戦は地面のみ、踏みつけ時は安全に反発（貫通防止）
- プレイヤー被弾時の点滅、音量バランス調整
- BGM/SE追加（簡易トーン、外部アセット不要）
- 復活は高め＋浮遊フェーズ→落下開始（1.8s 無敵）
- ゲームオーバー/勝利で Space/Enter で再スタート可

## トラブルシュート
- 画面が出ない/真っ黒: GPUドライバや外部モニタ構成を確認、別ウィンドウの裏に回っていないか確認
- 日本語が出ない: Windowsのフォント環境依存。`Meiryo`/`Yu Gothic` などが利用可。表示乱れはフォントを小さく
- 効果音が大きい/小さい: `main.py` の `AudioManager` 内 `set_volume` を調整
- 難易度調整: `JUMP_POWER`、足場の `move_range` / `move_speed`、ボスHPなどを調整

## ライセンス
学習/個人利用想定のサンプル。配布時は自己責任でお願いします（コード署名推奨）。
