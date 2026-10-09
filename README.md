# AR9 — Blue Rabbit animated 3D & AR

AR8のキャラクターと3Dビューを参考にした独立したリポジトリです。AR8のファイルは変更していません。

3Dアニメーションと、対応端末で床・テーブルを認識して空間に配置するARに対応します。

- 帽子から4色のボールが飛び出し、共通の軌道を等間隔で周回する、10秒のループ。顔・耳の周囲を避け、球体の縦横比を維持しています。
- 両目の瞳がピンクのボールを追う動き。
- 回転、拡大縮小、一時停止、再生位置の調整。
- Android: ChromeのWebXRでアニメーションを再生します。ARCore対応端末とGoogle Play開発者サービス（AR）が必要です。
- iPhone・iPad: SafariからQuick Lookを起動します。GLBからの自動変換ではアニメーションが失われるため、10チャンネルの変形アニメーションを保存した専用USDZを使用します。

公開ページ: https://bizmalsjp.github.io/AR9/

`assets/blue-rabbit-animated.glb` は背景を持たず、glTF標準のアニメーションを含む3Dモデルです。元のAR8のメッシュを維持して、4個のボールと2個の瞳の位置・大きさをアニメーションしています。

`vendor/model-viewer.min.js` は公式Google model-viewer 4.3.1です。ライセンスは同ディレクトリのファイルを参照してください。

元モデルは `assets/blue-rabbit.glb`、再生成は `python3 tools/create-animation.py` です。生成時にボールと頭・顔・耳の各部分、および全6組のボール同士の距離をループ全体で検証します。GLBのキーフレーム間を線形補間した実際の位置を240fpsで検証し、表面同士の隙間と均等なスケールを確認します。

USDZの再生成は `python3 tools/create-usdz.py` です。公式OpenUSDの `usd-core` 26.8以降が必要です。元のメッシュ・材質・10秒のアニメーションを保存し、OpenUSDの検証器での形式適合性と全チャンネルの301キーフレームを確認します。実空間への配置とiOSでの再生は実機での確認が必要です。
