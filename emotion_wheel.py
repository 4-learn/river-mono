# 情感輪盤配置 (8x3 陣列)
# 基於圖片中的情感輪盤定義

EMOTION_WHEEL = [
    # row 0
    [
        {"name": "平靜", "color": "#FFFF99"},
        {"name": "喜悅", "color": "#FFFF99"},
        {"name": "狂喜", "color": "#FFFF99"},
    ],
    # row 1
    [
        {"name": "接納", "color": "#99FF99"},
        {"name": "信任", "color": "#99FF99"},
        {"name": "敬佩", "color": "#99FF99"},
    ],
    # row 2
    [
        {"name": "憂慮", "color": "#99FFFF"},
        {"name": "害怕", "color": "#99FFFF"},
        {"name": "恐懼", "color": "#99FFFF"},
    ],
    # row 3
    [
        {"name": "分心", "color": "#CC99FF"},
        {"name": "驚喜", "color": "#CC99FF"},
        {"name": "驚奇", "color": "#CC99FF"},
    ],
    # row 4
    [
        {"name": "沉思", "color": "#FF99FF"},
        {"name": "難過", "color": "#FF99FF"},
        {"name": "悲傷", "color": "#FF99FF"},
    ],
    # row 5
    [
        {"name": "無聊", "color": "#FF99CC"},
        {"name": "噁心", "color": "#FF99CC"},
        {"name": "厭惡", "color": "#FF99CC"},
    ],
    # row 6
    [
        {"name": "煩躁", "color": "#FF9999"},
        {"name": "憤怒", "color": "#FF9999"},
        {"name": "盛怒", "color": "#FF9999"},
    ],
    # row 7
    [
        {"name": "有興趣", "color": "#FFCC99"},
        {"name": "期待", "color": "#FFCC99"},
        {"name": "警戒", "color": "#FFCC99"},
    ],
]

# 情感強度對應 col
INTENSITY_LEVELS = {
    0: "低",    # 平靜、接納、憂慮等
    1: "中",    # 喜悅、信任、害怕等
    2: "高",    # 狂喜、敬佩、恐懼等
}

# 八大基本情感類別
EMOTION_CATEGORIES = {
    0: "joy",        # 喜悅系
    1: "trust",      # 信任系
    2: "fear",       # 恐懼系
    3: "surprise",   # 驚喜系
    4: "sadness",    # 悲傷系
    5: "disgust",    # 厭惡系
    6: "anger",      # 憤怒系
    7: "anticipation"  # 期待系
}


def get_emotion(row: int, col: int) -> dict:
    """取得指定位置的情感資訊"""
    if 0 <= row < 8 and 0 <= col < 3:
        emotion = EMOTION_WHEEL[row][col]
        return {
            "name": emotion["name"],
            "color": emotion["color"],
            "category": EMOTION_CATEGORIES[row],
            "intensity": INTENSITY_LEVELS[col]
        }
    return None


def calculate_move(current_row: int, current_col: int, target_row: int, target_col: int) -> tuple:
    """
    計算從當前位置移動到目標位置（一次只能走一格）
    返回新的 (row, col)
    """
    # 計算差距
    row_diff = target_row - current_row
    col_diff = target_col - current_col

    # 一次只能移動一格
    new_row = current_row
    new_col = current_col

    # 優先移動 row（情感類別）
    if row_diff != 0:
        if row_diff > 0:
            new_row = min(current_row + 1, 7)
        else:
            new_row = max(current_row - 1, 0)
    # 如果 row 已經相同，則移動 col（強度）
    elif col_diff != 0:
        if col_diff > 0:
            new_col = min(current_col + 1, 2)
        else:
            new_col = max(current_col - 1, 0)

    return new_row, new_col


def get_adjacent_positions(row: int, col: int) -> list:
    """取得相鄰的所有可能位置（上下左右，最多4個）"""
    positions = []
    # 上
    if row > 0:
        positions.append((row - 1, col))
    # 下
    if row < 7:
        positions.append((row + 1, col))
    # 左
    if col > 0:
        positions.append((row, col - 1))
    # 右
    if col < 2:
        positions.append((row, col + 1))
    return positions
