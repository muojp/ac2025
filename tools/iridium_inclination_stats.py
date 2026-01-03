import requests
import os
import sys
import subprocess
import json
from datetime import datetime
from collections import defaultdict
from pathlib import Path

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
        satellite_group (str): 衛星グループ名

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

def extract_inclination_from_tle(line2):
    """
    TLEの2行目から軌道傾斜角を抽出する関数

    Args:
        line2 (str): TLEの2行目

    Returns:
        float: 軌道傾斜角（度）
    """
    # TLE形式: 2行目の9-16桁目が軌道傾斜角（度）
    try:
        inclination_str = line2[8:16].strip()
        return float(inclination_str)
    except Exception as e:
        print(f"軌道傾斜角の抽出に失敗しました: {e}")
        return None

def extract_eccentricity_from_tle(line2):
    """
    TLEの2行目から離心率を抽出する関数

    Args:
        line2 (str): TLEの2行目

    Returns:
        float: 離心率
    """
    # TLE形式: 2行目の27-33桁目が離心率（先頭に0.が省略されている）
    try:
        eccentricity_str = line2[26:33].strip()
        return float("0." + eccentricity_str)
    except Exception as e:
        print(f"離心率の抽出に失敗しました: {e}")
        return None

def extract_mean_motion_from_tle(line2):
    """
    TLEの2行目から平均運動（1日あたりの周回数）を抽出する関数

    Args:
        line2 (str): TLEの2行目

    Returns:
        float: 平均運動（revs/day）
    """
    # TLE形式: 2行目の53-63桁目が平均運動
    try:
        mean_motion_str = line2[52:63].strip()
        return float(mean_motion_str)
    except Exception as e:
        print(f"平均運動の抽出に失敗しました: {e}")
        return None

def round_inclination(inclination, tolerance=0.5):
    """
    軌道傾斜角を指定された許容範囲で丸める関数

    Args:
        inclination (float): 軌道傾斜角（度）
        tolerance (float): 許容範囲（度）

    Returns:
        float: 丸められた軌道傾斜角
    """
    # 整数値に近い場合は整数値を返す
    rounded = round(inclination)
    if abs(inclination - rounded) <= tolerance:
        return rounded

    # そうでない場合は小数第1位まで丸める
    return round(inclination, 1)

def analyze_iridium_inclinations():
    """
    Iridium衛星の軌道傾斜角分布を分析する関数
    """
    print("=== Iridium衛星の軌道傾斜角分布分析 ===\n")

    # Iridium衛星のTLEデータをダウンロード
    satellites = download_tle("iridium-next")

    if not satellites:
        print("Iridium衛星データの取得に失敗しました。")
        return

    print(f"合計{len(satellites)}個のIridium衛星データを取得しました。\n")

    # DTC衛星とメイン衛星を分類
    main_satellites = []
    dtc_satellites = []

    for sat in satellites:
        if '[DTC]' in sat['name']:
            dtc_satellites.append(sat)
        else:
            main_satellites.append(sat)

    print(f"メイン衛星: {len(main_satellites)}個")
    print(f"DTC衛星: {len(dtc_satellites)}個\n")

    # メイン衛星の軌道傾斜角分布を集計
    print("=== メイン衛星の軌道傾斜角分布 ===")
    main_inclination_counts = defaultdict(int)
    main_inclinations = []

    for sat in main_satellites:
        inclination = extract_inclination_from_tle(sat['line2'])
        if inclination is not None:
            main_inclinations.append(inclination)
            rounded_inc = round_inclination(inclination)
            main_inclination_counts[rounded_inc] += 1

    # 軌道傾斜角でソートして表示
    for inc in sorted(main_inclination_counts.keys()):
        count = main_inclination_counts[inc]
        percentage = (count / len(main_satellites)) * 100
        print(f"{inc}°: {count}個 ({percentage:.1f}%)")

    print()

    # DTC衛星の軌道傾斜角分布を集計
    if dtc_satellites:
        print("=== DTC衛星の軌道傾斜角分布 ===")
        dtc_inclination_counts = defaultdict(int)
        dtc_inclinations = []

        for sat in dtc_satellites:
            inclination = extract_inclination_from_tle(sat['line2'])
            if inclination is not None:
                dtc_inclinations.append(inclination)
                rounded_inc = round_inclination(inclination)
                dtc_inclination_counts[rounded_inc] += 1

        # 軌道傾斜角でソートして表示
        for inc in sorted(dtc_inclination_counts.keys()):
            count = dtc_inclination_counts[inc]
            percentage = (count / len(dtc_satellites)) * 100
            print(f"{inc}°: {count}個 ({percentage:.1f}%)")

        print()

    # 統計情報
    print("=== 統計情報 ===")
    if main_inclinations:
        print(f"メイン衛星数: {len(main_satellites)}個")
        print(f"軌道傾斜角範囲: {min(main_inclinations):.2f}° - {max(main_inclinations):.2f}°")
        print(f"軌道傾斜角平均: {sum(main_inclinations) / len(main_inclinations):.2f}°")
        print(f"軌道傾斜角の種類: {len(main_inclination_counts)}種類")

    if dtc_satellites and dtc_inclinations:
        print(f"\nDTC衛星数: {len(dtc_satellites)}個")
        print(f"軌道傾斜角範囲: {min(dtc_inclinations):.2f}° - {max(dtc_inclinations):.2f}°")
        print(f"軌道傾斜角平均: {sum(dtc_inclinations) / len(dtc_inclinations):.2f}°")

    print()

    # 追加の軌道パラメータ分析
    print("=== 追加の軌道パラメータ分析 ===")
    eccentricities = []
    mean_motions = []

    for sat in main_satellites:
        ecc = extract_eccentricity_from_tle(sat['line2'])
        mm = extract_mean_motion_from_tle(sat['line2'])
        if ecc is not None:
            eccentricities.append(ecc)
        if mm is not None:
            mean_motions.append(mm)

    if eccentricities:
        print(f"離心率範囲: {min(eccentricities):.6f} - {max(eccentricities):.6f}")
        print(f"離心率平均: {sum(eccentricities) / len(eccentricities):.6f}")

    if mean_motions:
        print(f"平均運動範囲: {min(mean_motions):.4f} - {max(mean_motions):.4f} revs/day")
        print(f"平均運動平均: {sum(mean_motions) / len(mean_motions):.4f} revs/day")
        # 軌道周期を計算（分単位）
        avg_period = (24 * 60) / (sum(mean_motions) / len(mean_motions))
        print(f"平均軌道周期: {avg_period:.2f}分")

if __name__ == "__main__":
    # Change to git repository root to ensure relative paths work
    git_root = get_git_root()
    os.chdir(git_root)

    analyze_iridium_inclinations()
