# Tools

このディレクトリには衛星データ分析ツールが含まれています。

## セットアップ

依存パッケージは自動的にインストールされます（uv使用）。

## 使い方

**このディレクトリに移動してから実行してください。**

```bash
cd tools/
```

### Starlink衛星の高度分布分析

```bash
uv run starlink_altitude_histogram.py
```

- CelesTrakからStarlink衛星のTLEデータをダウンロード
- 高度分布を分析し、傾斜角別（43°, 53°, 70°, 97°）の統計を表示
- 9分割のヒストグラム画像を生成: `../starlink_altitude_histogram.png`

### Iridium衛星の軌道傾斜角分析

```bash
uv run iridium_inclination_stats.py
```

- CelesTrakからIridium-NEXT衛星のTLEデータをダウンロード
- 軌道傾斜角の分布を分析
- 離心率、平均運動などの軌道パラメータを表示

### Table of Contents生成

```bash
uv run toc.py
```

- gitに登録されているNN.md形式のファイルからTOCを生成
- `../README.md`を更新

## キャッシュ

TLEデータは `../data/` にキャッシュされます（有効期限: 24時間）。
キャッシュが有効な場合は再ダウンロードせずにキャッシュを使用します。

## 出力

- `../starlink_altitude_histogram.png` - Starlink高度分布のヒストグラム
- `../data/starlink.json` - StarlinkのTLEキャッシュ
- `../data/iridium-next.json` - IridiumのTLEキャッシュ

## 依存パッケージ

- requests - TLEデータのダウンロード
- matplotlib - グラフ描画
- numpy - 数値計算

依存パッケージは `pyproject.toml` で管理されています。
