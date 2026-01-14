# 情感輪盤配置 (8x3 陣列)
# 基於圖片中的情感輪盤定義

EMOTION_WHEEL = [
    # row 0 - 喜悅系：鮮黃色
    [
        {"name": "平靜", "color": "#FFFF00"},      # 亮黃色
        {"name": "喜悅", "color": "#FFFF00"},
        {"name": "狂喜", "color": "#FFFF00"},
    ],
    # row 1 - 信任系：綠色
    [
        {"name": "接納", "color": "#00FF00"},      # 亮綠色
        {"name": "信任", "color": "#00FF00"},
        {"name": "敬佩", "color": "#00FF00"},
    ],
    # row 2 - 恐懼系：青色
    [
        {"name": "憂慮", "color": "#00FFFF"},      # 亮青色
        {"name": "害怕", "color": "#00FFFF"},
        {"name": "恐懼", "color": "#00FFFF"},
    ],
    # row 3 - 驚喜系：藍色
    [
        {"name": "分心", "color": "#0000FF"},      # 亮藍色
        {"name": "驚喜", "color": "#0000FF"},
        {"name": "驚奇", "color": "#0000FF"},
    ],
    # row 4 - 悲傷系：深藍色
    [
        {"name": "沉思", "color": "#000080"},      # 海軍藍
        {"name": "難過", "color": "#000080"},
        {"name": "悲傷", "color": "#000080"},
    ],
    # row 5 - 厭惡系：紫色
    [
        {"name": "無聊", "color": "#FF00FF"},      # 亮紫色（洋紅）
        {"name": "噁心", "color": "#FF00FF"},
        {"name": "厭惡", "color": "#FF00FF"},
    ],
    # row 6 - 憤怒系：紅色
    [
        {"name": "煩躁", "color": "#FF0000"},      # 亮紅色
        {"name": "憤怒", "color": "#FF0000"},
        {"name": "盛怒", "color": "#FF0000"},
    ],
    # row 7 - 期待系：橙色
    [
        {"name": "有興趣", "color": "#FF8000"},    # 亮橙色
        {"name": "期待", "color": "#FF8000"},
        {"name": "警戒", "color": "#FF8000"},
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
    計算從當前位置移動到目標位置（一次只能走一格，支援斜向）
    返回新的 (row, col)
    """
    # 計算差距
    row_diff = target_row - current_row
    col_diff = target_col - current_col

    # 一次只能移動一格
    new_row = current_row
    new_col = current_col

    # 支援斜向移動：同時移動 row 和 col
    if row_diff != 0:
        if row_diff > 0:
            new_row = min(current_row + 1, 7)
        else:
            new_row = max(current_row - 1, 0)

    if col_diff != 0:
        if col_diff > 0:
            new_col = min(current_col + 1, 2)
        else:
            new_col = max(current_col - 1, 0)

    return new_row, new_col


def get_adjacent_positions(row: int, col: int) -> list:
    """取得相鄰的所有可能位置（包含斜向，最多8個方向）"""
    positions = []

    # 8 個方向：上、下、左、右、左上、右上、左下、右下
    directions = [
        (-1, 0),   # 上
        (1, 0),    # 下
        (0, -1),   # 左
        (0, 1),    # 右
        (-1, -1),  # 左上
        (-1, 1),   # 右上
        (1, -1),   # 左下
        (1, 1),    # 右下
    ]

    for dr, dc in directions:
        new_row = row + dr
        new_col = col + dc
        # 檢查是否在有效範圍內
        if 0 <= new_row < 8 and 0 <= new_col < 3:
            positions.append((new_row, new_col))

    return positions
