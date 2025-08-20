# Jump & Smile Adventure（pygame）

かわいい横スクロールアクション。全4ステージ、各ステージ最後にボス戦。低年齢でも遊べるやさしめ設計です。

## ダウンロード（Windows .zip）
- Python環境なしで遊べます。以下から `JumpSmile.zip` をダウンロードして解凍後、`JumpSmile.exe` を実行してください。
- SmartScreen が出た場合は「詳細情報 > 実行」を選択してください。

[Windows用ZIPをダウンロード（JumpSmile.zip）](https://github.com/takeru4718/cursortest/releases/latest/download/JumpSmile.zip)

- 上記はGitHub Releasesの最新アセットを指します。ファイル名を変更した場合はリンク名も合わせて更新してください。

## 特徴
- 4ステージ構成の横スクロール
- ジャンプ主体（コヨーテタイム＋二段ジャンプ対応）
- 各ステージでボス登場（踏みつけでダメージ）
- ボス戦は地面のみでダイナミックに動く
- 日本語表示対応・やさしい色味のUI
- BGMと効果音（ジャンプ／踏みつけ／被弾／ポーズ）
- 落下時はスマブラ風の浮遊→落下で復活（無敵時間あり）

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

## 配布（onedir 配布）
PyInstaller の onedir ビルドで `dist/JumpSmile/` をzip化して配布すると、誤検知が起きにくく安定します。

```powershell
.\.venv\Scripts\Activate.ps1
pip install pyinstaller
pyinstaller --name "JumpSmile" --onedir --noconsole --clean main.py `
  --collect-submodules pygame `
  --collect-data pygame
# dist\JumpSmile\ を zip 化して公開
```
- 配布物例: `JumpSmile.zip`（解凍して `JumpSmile.exe` を実行）
- onefile（単体exe）で検知が強い場合、onedir配布を推奨

## 主な変更点（実装メモ）
- 日本語フォント自動検出（Noto/Meiryo/游ゴシック/IPA等）
- UIフォントサイズ調整（切れにくく）
- 二段ジャンプ＋コヨーテタイム追加
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
