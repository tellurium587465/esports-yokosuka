/* 公開先URLはここで設定します。空文字の項目は「準備中」として動作します。
 * URLは https:// から始まる公開URLを指定してください。
 * Google Driveの資料は共有範囲、Googleフォームは回答受付を確認してください。
 */
window.YESF_CONFIG = {
  partnershipDetails: "https://drive.google.com/file/d/148V-sV6rzOl4F3vDRsea2rPzmpaVTFLx/view?usp=sharing", // 協賛資料
  partnershipApplication: "https://docs.google.com/forms/d/e/1FAIpQLSfxDjLAyXOVvVYmDvdQjWVGl3IFfGS3LptYknEXNQRa4Dj9Zg/viewform?usp=header", // 協賛申し込み
  youtube: "",                  // 公式YouTube URL
  website: "",                  // 公式Webサイト URL
  // ロゴを assets/partners/ に保存し、以下の形式で追加すると自動表示されます。
  // { name: "協賛企業名", logo: "assets/partners/company.svg", url: "https://..." }
  // url は省略できます。掲載が確定した企業・団体のみ追加してください。
  partners: []
};
