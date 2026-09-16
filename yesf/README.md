# YeSF 2026 特設サイト

2026年11月3日（火・祝）開催のVALORANTオフライン大会特設ページです。
HTML / CSS / JavaScriptのみの静的サイトです。ビルドやAPIキーは不要です。

## ファイル

- `index.html` — 大会情報・X公式プロフィールタイムライン・協賛案内
- `styles.css` — 石膏の質感、タイポグラフィ、スマートフォン対応
- `site-config.js` — 協賛資料・申込・SNSリンク、将来の協賛ロゴの設定
- `script.js` — リンク設定、準備中案内、ロゴ追加、控えめなスクロール表示
- `assets/` — 同梱フォント、石膏背景、アイコン
- `.nojekyll` — GitHub Pagesで静的ファイルをそのまま配信するための指定

## URLの差し替え

`site-config.js` の次の項目を編集します。

| 項目 | 設定する内容 |
| --- | --- |
| `partnershipDetails` | Google Driveの協賛資料の公開共有URL |
| `partnershipApplication` | Googleフォームの協賛申込URL |
| `youtube` | 主催者の公式YouTube URL |
| `website` | 主催者の公式Webサイト URL |

URLは `https://` から始まる形で、引用符の中に入れてください。空欄のボタンは「準備中」の案内を表示します。資料・申込のURLを両方設定すると「近日公開予定」の文は自動で非表示になります。片方だけ設定した場合は未設定の項目だけ案内します。

協賛資料・申込先は、ご提供のGoogle Drive・GoogleフォームのURLを設定済みです。YouTube・Websiteは引き続き空欄です。Google Driveの共有範囲と、Googleフォームの回答受付設定は公開前に確認してください。

## 協賛ロゴの追加

1. `assets/partners/` フォルダを作成し、掲載許可のあるロゴ画像を置きます。
2. `site-config.js` の `partners` に下記の形式で追加します。

```js
partners: [
  {
    name: "協賛企業名",
    logo: "assets/partners/company.svg",
    url: "https://example.com"
  }
]
```

`url` は省略できます。`partners` が空の間、OUR PARTNERSは表示されません。画像はSVG、PNG、WebP、JPEGに対応します。ファイル名は英数字・ハイフン・アンダースコアを推奨します。

## GitHub Pagesでの公開

1. GitHubに公開用リポジトリを作成します。
2. このフォルダの**中身**をリポジトリのルートへ配置します。`index.html` と `assets/` の位置関係を維持してください。
3. リポジトリの **Settings → Pages** で **Deploy from a branch** を選択し、`main` ブランチの `/(root)` を指定して保存します。
4. デプロイ完了後、Pagesに表示されるHTTPSのURLで開きます。
5. 実際の公開URLで、Xの投稿表示と協賛リンクを確認してください。

相対パスのため、`https://ユーザー名.github.io/リポジトリ名/` の配下でも動作します。この納品にはGitHubへのアップロード・公開操作は含みません。

## X公式タイムライン

`@Yokosuka_eGen` の公式プロフィール埋め込みです。投稿をHTMLへ手作業で追加する必要はなく、APIキーも使用しません。高さ650px・lightテーマ・公式widgets.jsを使用しています。

- 読み込まれるのはXが提供するプロフィールタイムラインです。新規投稿の反映順・反映時刻・表示可否はX側の提供仕様に依存し、リアルタイム更新は保証できません。
- `file://` では表示されない場合があります。HTTPSでの公開後も、Xの配信状況、アカウントの公開状態、ブラウザの追跡防止設定などの影響を受けます。
- 読み込めない場合も公式Xへのリンクを表示します。手作業の投稿や架空の投稿への置き換えはありません。
- 動作確認では、Xスクリプトをブロックした場合の案内と、公式の描画完了イベントを受けた場合の表示切り替えを確認しています。公開先HTTPSでの実投稿表示は公開後に確認が必要です。

公式資料: [X ヘルプ・タイムラインの埋め込み](https://help.x.com/en/using-x/embed-x-feed)

## デザインと素材

元の `YeSF_2026_special_site_plaster_v5.html` の情報構成・大会コピー・X埋め込みを引き継ぎ、レイアウトとスタイルを改修しています。参考資料2枚はデザイン参照のみに使用し、サイトには含めていません。

元HTMLの背景画像に会場名が焼き込まれていたため、公開用アセットには含めていません。公開会場表記は「神奈川県内某所」です。

- 基本色: WHITE / LIGHT GRAY / BLACK
- 6色は参考画像2の指定に合わせた小さなラインのみで使用
- 大会ロゴ: ご提供の `assets/mainlogo.png` をヘッダー・Hero・フッター・ブラウザアイコンに使用。元画像は変更せず、ページ内では周囲の余白をCSSでトリミングし、乗算表示で白い背景になじませています。縦横比は維持しています。
- ロゴ以外の英字: Anton（SIL Open Font License、`assets/OFL-Anton.txt` を同梱）
- 日本語: 端末のゴシック体
- 背景: 内蔵imagegenで新規制作した文字なしの白い石膏レリーフ。WebPに軽量化
- ランタイムの外部スクリプト: X公式のみ。フォントと画像はローカル配信
- フェード表示は動きを減らす設定に対応し、JavaScript無効でも本文は読めます

### 背景生成プロンプト

Photorealistic material photograph for a luxury Japanese esports editorial website. Wide landscape 3:2. Pure white fine gypsum / plaster sculptural bas-relief, naturally troweled flowing diagonal ridges and thin chipped layers around the right third and outer edges, subtle circular arc relief at the far right. Broad smooth neutral-white negative space at left and center. Real microtexture, delicate hairline fissures, museum-gallery lighting from upper left, high-key exposure and soft grey shadows. Clean and sophisticated, no dirt, no concrete, no text, no letters, no numbers, no logos, no objects, no UI.

## 確認済み項目

- 画面幅320 / 375 / 390 / 760 / 768 / 1024 / 1440pxで横スクロールなし
- PC・スマートフォンの見た目、アンカー移動、準備中の案内
- フォント・背景のローカル読み込み
- X読み込み不可時の公式リンク表示
- 動きを減らす設定・JavaScript無効時の可読性

未設定URLの差し替えと、公開先HTTPSでのX実投稿表示の最終確認は別途必要です。
