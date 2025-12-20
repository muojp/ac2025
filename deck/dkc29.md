---
presentationID: 1cKZEB7jd6gAUqRxARUstdUDkqu0Hcykfz2M6XSuENQ8
title: au Starlink Directで衛星直接データ通信
---

<!-- { "layout": "title" } -->

# Androidで衛星データ通信🛰️ 圏外での通信速度とレイテンシー実測結果

## muo / DroidKaigi.collect { #29@Tokyo }

---

<!-- { "layout": "title-short-body-image" } -->

## 自己紹介

- [@muo_jp](https://x.com/muo_jp/)
- 休みにはよく山に登っています

---

<!-- { "layout": "title-and-body" } -->

# DTC（Direct to Cell）

スマホ類が人工衛星と直接通信する

- Appleの緊急通報、メッセージ
- Pixelの緊急通報
- au Starlink Direct
  - SpaceX社のStarlinkベース
  - 今回はこの話

---

<!-- { "layout": "title-short-body-image" } -->

# Starlink DTC衛星

- スマホから直接つながる衛星
- 現在651機
- Starlink衛星全体 約10,000機の中ではごく少数
- [https://d2c-map.muo.jp/](https://d2c-map.muo.jp/)

---

<!-- { "layout": "title-short-body-image" } -->

# Starlink DTCのしくみ

宇宙空間で中継。すごい

---

<!-- { "layout": "title-and-body" } -->

# AndroidのDTC対応状況 - Android 15

- SMS/RCSやり取り
- 「Message」アプリがメイン
- この状態をDroidKaigi 2025でお話しました
  - [衛星元年 スマホ圏外からLEO衛星 で安否情報を届けるAndroid DTC (Direct to Cell)完全攻略](https://www.youtube.com/watch?v=tzESzyfYG3E)

---

<!-- { "layout": "title-and-body" } -->

# AndroidのDTC対応状況 - Android 16

- 「制約のある衛星ネットワーク」へオプトインしたアプリでデータ通信可能に！ （New！） ←今回はこの話です

---

<!-- { "layout": "title-and-body" } -->

# AndroidアプリでDTC対応する

- [制約のある衛星ネットワーク向けに開発する](https://developer.android.com/develop/connectivity/satellite/constrained-networks?hl=ja)
- 衛星非対応のアプリ: 普通にTCP類のconnect→失敗
- Manifestを1行書けば「不安定な衛星ネットワーク」をオプトインできる
  - `<meta-data android:name="android.telephony.PROPERTY_SATELLITE_DATA_OPTIMIZED" android:value="PACKAGE_NAME" />`

---

<!-- { "layout": "title-short-body-image" } -->

# 衛星データ通信対応アプリ

- Androidの設定画面が拡張された
- さきのManifest記述をするとこの一覧へ表示される

---

<!-- { "layout": "title-short-body-image" } -->

# DTC Monitorつくりました

- 電波、そして小型人工衛星
- 見えないものを見ようとする
- レイテンシー計測・DL/UL速度計測

---

<!-- { "layout": "title-short-body-image" } -->

# WearOS版もつくりました

- パッと時計を見ると衛星にどれぐらいつながっていてレイテンシーどれぐらいなのかが分かる
- 日常生活、「いま衛星回線！？」と思ったときに便利

---

<!-- { "layout": "title-short-body-image" } -->

# 通信速度を知りたい

5回計測結果

通信失敗するときは失敗する。試した限りはやはりアップロードのほうが失敗しやすい

---

<!-- { "layout": "title-short-body-image" } -->

# レイテンシー

- 散布図
  - 縦軸: レイテンシー（対数表示）
  - 横軸: 近隣衛星の仰角
- 感想「なんだよこれ・・・まるでノイズ」

---

# レイテンシー

- 地上回線でこういう繰り返しテストをすると普通は「芯」が出る

---

# レイテンシー

- 衛星経由のレイテンシー（再）
- レイテンシーのブレ幅が大きい（ジッターが大きい）
- 頭上にあれば安定するというわけでもない

---

<!-- { "layout": "title-short-body-image" } -->

# スループット（スピード）

- 出るときは出る
- 出ないときは出ない

---

<!-- { "layout": "title-short-body-image" } -->

# 安定性（ジッター）

<!--
p50, p90, p95, p99
-->

---

<!-- { "layout": "title-short-body-image" } -->

# HTTP/3の可能性

- 単純なTCP接続より「遅くない」だけでもnice！
  - 経路セキュリティ確保できるメリット
- 0-RTT
  - セキュリティ上使えないケースも多いので注意

---

<!-- { "layout": "title-and-body" } -->

# 「au Starlink DirectでDTC」アドベントカレンダーやってます

[https://github.com/muojp/ac2025](https://github.com/muojp/ac2025)

- アドベントカレンダー、佳境ですね！
- まだ4日目ですが データ通信、実地テスト用のお役立ち情報もまとめ中です
  - 寄稿も歓迎しております

<!--
データサンプル数を従来の100万倍ぐらい流せるようになったのでいろいろデータ取りながら書いています。
なにかミスっていると再検証するのに圏外へ行かないといけないのでなかなか時間がかかります
-->
