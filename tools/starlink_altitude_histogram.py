import requests
import os
import sys
import subprocess
import json
from datetime import datetime
from collections import defaultdict
from pathlib import Path
import matplotlib.pyplot as plt
import numpy as np

def get_git_root():
    """
    Get the git repository root directory
    """
    try:
        result = subprocess.run(
            ["git", "rev-parse", "--show-toplevel"],
            capture_output=True,
            text=True,
            check=True
        )
        return Path(result.stdout.strip())
    except subprocess.CalledProcessError as e:
        print(f"Error finding git root: {e}", file=sys.stderr)
        sys.exit(1)

def ensure_data_dir():
    """
    データディレクトリが存在することを確認する関数
    """
    data_dir = "data"
    if not os.path.exists(data_dir):
        os.makedirs(data_dir)
    return data_dir

def get_cache_file_path(satellite_group):
    """
    衛星グループのキャッシュファイルパスを取得する関数

    Args:
        satellite_group (str): 衛星グループ名

    Returns:
        str: キャッシュファイルのパス
    """
    data_dir = ensure_data_dir()
    return os.path.join(data_dir, f"{satellite_group}.json")

def is_cache_valid(cache_file_path, max_age_hours=24):
    """
    キャッシュが有効かどうかを判断する関数

    Args:
        cache_file_path (str): キャッシュファイルのパス
        max_age_hours (int): キャッシュの最大有効時間（時間単位）

    Returns:
        bool: キャッシュが有効かどうか
    """
    if not os.path.exists(cache_file_path):
        return False

    # ファイルの最終更新時間を取得
    file_mtime = os.path.getmtime(cache_file_path)
    file_datetime = datetime.fromtimestamp(file_mtime)

    # 現在時刻との差分を計算
    time_diff = datetime.now() - file_datetime

    return time_diff.total_seconds() < max_age_hours * 3600

def load_satellites_from_cache(cache_file_path):
    """
    キャッシュから衛星データを読み込む関数

    Args:
        cache_file_path (str): キャッシュファイルのパス

    Returns:
        list: 衛星データのリスト
    """
    try:
        with open(cache_file_path, 'r') as file:
            cache_data = json.load(file)
            return cache_data['satellites']
    except Exception as e:
        print(f"キャッシュの読み込み中にエラーが発生しました: {e}")
        return None

def save_satellites_to_cache(cache_file_path, satellites):
    """
    衛星データをキャッシュに保存する関数

    Args:
        cache_file_path (str): キャッシュファイルのパス
        satellites (list): 衛星データのリスト
    """
    try:
        cache_data = {
            'timestamp': datetime.now().isoformat(),
            'satellites': satellites
        }

        with open(cache_file_path, 'w') as file:
            json.dump(cache_data, file, indent=2)

        print(f"衛星データを{cache_file_path}にキャッシュしました。")
    except Exception as e:
        print(f"キャッシュの保存中にエラーが発生しました: {e}")

def download_tle(satellite_group):
    """
    CelesTrakからTLEデータをダウンロードする関数
    キャッシュ機能付き

    Args:
        satellite_group (str): 衛星グループ名 (例: 'starlink')

    Returns:
        list: TLE形式の衛星データリスト
    """
    cache_file_path = get_cache_file_path(satellite_group)

    # キャッシュが有効な場合はキャッシュから読み込む
    if is_cache_valid(cache_file_path):
        print(f"{satellite_group}のキャッシュデータを使用します（有効期限: 24時間）")
        cached_satellites = load_satellites_from_cache(cache_file_path)
        if cached_satellites:
            return cached_satellites

    # キャッシュが無効または読み込めない場合は新しくダウンロード
    print(f"{satellite_group}の最新データをダウンロードしています...")
    url = f"https://celestrak.org/NORAD/elements/gp.php?GROUP={satellite_group}&FORMAT=tle"

    try:
        response = requests.get(url)

        if response.status_code != 200:
            raise Exception(f"データのダウンロードに失敗しました: {response.status_code}")

        # TLEデータを3行ずつに分割
        tle_data = response.text.strip().split('\n')
        satellites = []

        for i in range(0, len(tle_data), 3):
            if i+2 < len(tle_data):
                satellite_name = tle_data[i].strip()
                satellites.append({
                    'name': satellite_name,
                    'line1': tle_data[i+1].strip(),
                    'line2': tle_data[i+2].strip()
                })

        # 全ての衛星データをキャッシュに保存
        save_satellites_to_cache(cache_file_path, satellites)

        return satellites

    except Exception as e:
        print(f"データのダウンロード中にエラーが発生しました: {e}")

        # エラーが発生した場合、既存のキャッシュがあればそれを使用
        if os.path.exists(cache_file_path):
            print("最新のダウンロードに失敗しました。既存のキャッシュデータを使用します。")
            cached_satellites = load_satellites_from_cache(cache_file_path)
            if cached_satellites:
                return cached_satellites

        return []

def extract_orbital_elements_from_tle(line1, line2):
    """
    TLEから軌道要素を抽出する関数

    Args:
        line1 (str): TLEの1行目
        line2 (str): TLEの2行目

    Returns:
        dict: 軌道要素の辞書
    """
    try:
        # TLE Line 2: 平均運動（revs/day）を抽出（52-63桁目）
        mean_motion = float(line2[52:63].strip())

        # TLE Line 2: 軌道傾斜角（度）を抽出（8-16桁目）
        inclination = float(line2[8:16].strip())

        # 地球半径（km）
        EARTH_RADIUS = 6378.137

        # 平均運動から軌道周期を計算（分単位）
        orbital_period_minutes = 1440.0 / mean_motion  # 1日 = 1440分

        # ケプラーの第3法則を使用して軌道半径を計算
        # T^2 = (4π^2 / μ) * a^3
        # μ = GM (地球の標準重力パラメータ) = 398600.4418 km^3/s^2
        MU = 398600.4418  # km^3/s^2
        orbital_period_seconds = orbital_period_minutes * 60

        # a^3 = (T^2 * μ) / (4π^2)
        a_cubed = (orbital_period_seconds ** 2 * MU) / (4 * 3.14159265359 ** 2)
        semi_major_axis = a_cubed ** (1/3)

        # 地上からの高さ = 軌道半径 - 地球半径
        altitude = semi_major_axis - EARTH_RADIUS

        return {
            'inclination': inclination,
            'mean_motion': mean_motion,
            'orbital_period_minutes': orbital_period_minutes,
            'semi_major_axis': semi_major_axis,
            'altitude': altitude
        }
    except Exception as e:
        print(f"軌道要素の抽出に失敗しました: {e}")
        return None

def round_inclination(inclination, tolerance=1.0):
    """
    軌道傾斜角を指定された許容範囲で丸める関数

    Args:
        inclination (float): 軌道傾斜角（度）
        tolerance (float): 許容範囲（度）

    Returns:
        float: 丸められた軌道傾斜角
    """
    # 既知の軌道傾斜角のリスト
    known_inclinations = [43, 53, 70, 97]

    # 最も近い既知の軌道傾斜角を探す
    for known_inc in known_inclinations:
        if abs(inclination - known_inc) <= tolerance:
            return known_inc

    # 既知の軌道傾斜角に該当しない場合は元の値を返す
    return round(inclination, 1)

def create_altitude_histogram():
    """
    Starlink衛星の高度ヒストグラムを作成する関数
    """
    print("=== Starlink衛星の高度分布分析 ===\n")

    # Starlink衛星のTLEデータをダウンロード
    satellites = download_tle("starlink")

    if not satellites:
        print("Starlink衛星データの取得に失敗しました。")
        return

    print(f"合計{len(satellites)}個のStarlink衛星データを取得しました。\n")

    # メイン衛星とDTC衛星を分類、さらにinclinationごとに分類
    main_satellites = []
    dtc_satellites = []
    main_altitudes = []
    dtc_altitudes = []

    # Inclination別のデータ
    main_by_inclination = {43: [], 53: [], 70: [], 97: []}

    for sat in satellites:
        orbital_elements = extract_orbital_elements_from_tle(sat['line1'], sat['line2'])

        if orbital_elements is None:
            continue

        altitude = orbital_elements['altitude']
        inclination = orbital_elements['inclination']
        rounded_inc = round_inclination(inclination)

        if '[DTC]' in sat['name']:
            dtc_satellites.append(sat)
            dtc_altitudes.append(altitude)
        else:
            main_satellites.append(sat)
            main_altitudes.append(altitude)

            # Inclination別に分類
            if rounded_inc in main_by_inclination:
                main_by_inclination[rounded_inc].append(altitude)

    print(f"メイン衛星: {len(main_satellites)}個")
    print(f"DTC衛星: {len(dtc_satellites)}個\n")

    # Inclination別の統計情報
    print("=== メイン衛星のInclination別統計 ===")
    for inc in sorted(main_by_inclination.keys()):
        altitudes = main_by_inclination[inc]
        if altitudes:
            print(f"\n{inc}° 軌道面 ({len(altitudes)}個):")
            print(f"  最低高度: {min(altitudes):.2f} km")
            print(f"  最高高度: {max(altitudes):.2f} km")
            print(f"  平均高度: {np.mean(altitudes):.2f} km")
            print(f"  中央値: {np.median(altitudes):.2f} km")
            print(f"  標準偏差: {np.std(altitudes):.2f} km")

    # 統計情報の表示
    print("\n=== 高度統計情報 ===")
    if main_altitudes:
        print(f"メイン衛星（全体）:")
        print(f"  最低高度: {min(main_altitudes):.2f} km")
        print(f"  最高高度: {max(main_altitudes):.2f} km")
        print(f"  平均高度: {np.mean(main_altitudes):.2f} km")
        print(f"  中央値: {np.median(main_altitudes):.2f} km")
        print(f"  標準偏差: {np.std(main_altitudes):.2f} km\n")

    if dtc_altitudes:
        print(f"DTC衛星:")
        print(f"  最低高度: {min(dtc_altitudes):.2f} km")
        print(f"  最高高度: {max(dtc_altitudes):.2f} km")
        print(f"  平均高度: {np.mean(dtc_altitudes):.2f} km")
        print(f"  中央値: {np.median(dtc_altitudes):.2f} km")
        print(f"  標準偏差: {np.std(dtc_altitudes):.2f} km\n")

    # ヒストグラムの作成
    fig = plt.figure(figsize=(18, 12))

    # 全体のヒストグラム
    plt.subplot(3, 3, 1)
    all_altitudes = main_altitudes + dtc_altitudes
    plt.hist(all_altitudes, bins=50, range=(200, 600), color='blue', alpha=0.7, edgecolor='black')
    plt.xlabel('Altitude (km)')
    plt.ylabel('Number of Satellites')
    plt.title(f'All Satellites (n={len(all_altitudes)})')
    plt.xlim(200, 600)
    plt.grid(True, alpha=0.3)

    # メイン衛星の全体ヒストグラム
    plt.subplot(3, 3, 2)
    plt.hist(main_altitudes, bins=50, range=(200, 600), color='green', alpha=0.7, edgecolor='black')
    plt.xlabel('Altitude (km)')
    plt.ylabel('Number of Satellites')
    plt.title(f'Main Satellites - All (n={len(main_altitudes)})')
    plt.xlim(200, 600)
    plt.grid(True, alpha=0.3)

    # DTC衛星のヒストグラム（横軸は自動）
    plt.subplot(3, 3, 3)
    if dtc_altitudes:
        plt.hist(dtc_altitudes, bins=30, color='orange', alpha=0.7, edgecolor='black')
    plt.xlabel('Altitude (km)')
    plt.ylabel('Number of Satellites')
    plt.title(f'DTC Satellites (n={len(dtc_altitudes)})')
    plt.grid(True, alpha=0.3)

    # Inclination別のヒストグラム（43°）
    plt.subplot(3, 3, 4)
    inc43_altitudes = main_by_inclination[43]
    if inc43_altitudes:
        plt.hist(inc43_altitudes, bins=40, range=(200, 600), color='red', alpha=0.7, edgecolor='black')
    plt.xlabel('Altitude (km)')
    plt.ylabel('Number of Satellites')
    plt.title(f'Main Satellites - 43° (n={len(inc43_altitudes)})')
    plt.xlim(200, 600)
    plt.grid(True, alpha=0.3)

    # Inclination別のヒストグラム（53°）
    plt.subplot(3, 3, 5)
    inc53_altitudes = main_by_inclination[53]
    if inc53_altitudes:
        plt.hist(inc53_altitudes, bins=40, range=(200, 600), color='purple', alpha=0.7, edgecolor='black')
    plt.xlabel('Altitude (km)')
    plt.ylabel('Number of Satellites')
    plt.title(f'Main Satellites - 53° (n={len(inc53_altitudes)})')
    plt.xlim(200, 600)
    plt.grid(True, alpha=0.3)

    # Inclination別のヒストグラム（70°）
    plt.subplot(3, 3, 6)
    inc70_altitudes = main_by_inclination[70]
    if inc70_altitudes:
        plt.hist(inc70_altitudes, bins=40, range=(200, 600), color='cyan', alpha=0.7, edgecolor='black')
    plt.xlabel('Altitude (km)')
    plt.ylabel('Number of Satellites')
    plt.title(f'Main Satellites - 70° (n={len(inc70_altitudes)})')
    plt.xlim(200, 600)
    plt.grid(True, alpha=0.3)

    # Inclination別のヒストグラム（97°）
    plt.subplot(3, 3, 7)
    inc97_altitudes = main_by_inclination[97]
    if inc97_altitudes:
        plt.hist(inc97_altitudes, bins=40, range=(200, 600), color='brown', alpha=0.7, edgecolor='black')
    plt.xlabel('Altitude (km)')
    plt.ylabel('Number of Satellites')
    plt.title(f'Main Satellites - 97° (n={len(inc97_altitudes)})')
    plt.xlim(200, 600)
    plt.grid(True, alpha=0.3)

    # Inclination別の比較ヒストグラム
    plt.subplot(3, 3, 8)
    colors = ['red', 'purple', 'cyan', 'brown']
    labels = ['43°', '53°', '70°', '97°']
    data_to_plot = [main_by_inclination[inc] for inc in [43, 53, 70, 97] if main_by_inclination[inc]]
    active_labels = [labels[i] for i, inc in enumerate([43, 53, 70, 97]) if main_by_inclination[inc]]
    active_colors = [colors[i] for i, inc in enumerate([43, 53, 70, 97]) if main_by_inclination[inc]]

    if data_to_plot:
        plt.hist(data_to_plot, bins=40, range=(200, 600), color=active_colors, alpha=0.6,
                 label=active_labels, edgecolor='black')
    plt.xlabel('Altitude (km)')
    plt.ylabel('Number of Satellites')
    plt.title('Main Satellites - By Inclination')
    plt.xlim(200, 600)
    plt.legend()
    plt.grid(True, alpha=0.3)

    # 全体比較（Main vs DTC）
    plt.subplot(3, 3, 9)
    plt.hist([main_altitudes, dtc_altitudes], bins=50, range=(200, 600),
             color=['green', 'orange'], alpha=0.6,
             label=['Main', 'DTC'], edgecolor='black')
    plt.xlabel('Altitude (km)')
    plt.ylabel('Number of Satellites')
    plt.title('Main vs DTC Comparison')
    plt.xlim(200, 600)
    plt.legend()
    plt.grid(True, alpha=0.3)

    plt.tight_layout()

    # グラフを保存
    output_path = 'starlink_altitude_histogram.png'
    plt.savefig(output_path, dpi=150, bbox_inches='tight')
    print(f"ヒストグラムを {output_path} に保存しました。")
    plt.close()

    # 高度範囲別の集計
    print("\n=== 高度範囲別集計 ===")
    altitude_ranges = [
        (0, 400),
        (400, 450),
        (450, 500),
        (500, 550),
        (550, 600),
        (600, 1000),
        (1000, 2000)
    ]

    for low, high in altitude_ranges:
        main_count = sum(1 for alt in main_altitudes if low <= alt < high)
        dtc_count = sum(1 for alt in dtc_altitudes if low <= alt < high)
        total_count = main_count + dtc_count

        if total_count > 0:
            print(f"\n{low}-{high} km:")
            print(f"  メイン衛星: {main_count}個")
            print(f"  DTC衛星: {dtc_count}個")
            print(f"  合計: {total_count}個")

if __name__ == "__main__":
    # Change to git repository root to ensure relative paths work
    git_root = get_git_root()
    os.chdir(git_root)

    create_altitude_histogram()
