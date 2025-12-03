import os
from openai import OpenAI
from emotion_wheel import EMOTION_CATEGORIES, get_emotion, get_adjacent_positions


def get_openai_client():
    """延遲初始化 OpenAI client，確保環境變數已載入"""
    api_key = os.getenv("OPENAI_API_KEY")
    if not api_key:
        raise ValueError("OPENAI_API_KEY not found in environment variables")
    return OpenAI(api_key=api_key)


def analyze_emotion_and_respond(user_text: str, current_row: int, current_col: int) -> dict:
    """
    使用 LLM 分析使用者文字的情感，並生成回應

    Args:
        user_text: 使用者輸入的文字
        current_row: 當前情感輪盤的 row 位置
        current_col: 當前情感輪盤的 col 位置

    Returns:
        {
            "target_row": int,
            "target_col": int,
            "response_text": str,
            "detected_emotion": str
        }
    """
    current_emotion = get_emotion(current_row, current_col)

    # 取得相鄰位置的情感選項
    adjacent_positions = get_adjacent_positions(current_row, current_col)
    emotion_options = []
    for row, col in adjacent_positions:
        emo = get_emotion(row, col)
        emotion_options.append(f"({row},{col}): {emo['name']} - {emo['category']}")

    # 構建 prompt
    system_prompt = f"""你是一個情感分析助手。根據使用者的文字，判斷情感並選擇最適合的情感位置。

當前情感位置: ({current_row}, {current_col}) - {current_emotion['name']} ({current_emotion['category']})

可移動的相鄰情感位置（一次只能移動一格）:
{chr(10).join(emotion_options)}

請分析使用者的文字情感，並：
1. 選擇最符合的情感位置 (row, col)
2. 生成一個同理且溫暖的回應（繁體中文，1-2句話）

請以 JSON 格式回應：
{{
    "target_row": <0-7的數字>,
    "target_col": <0-2的數字>,
    "response_text": "<你的回應>",
    "detected_emotion": "<偵測到的情感類別>"
}}
"""

    try:
        client = get_openai_client()
        response = client.chat.completions.create(
            model="gpt-4o-mini",
            messages=[
                {"role": "system", "content": system_prompt},
                {"role": "user", "content": user_text}
            ],
            response_format={"type": "json_object"},
            temperature=0.7
        )

        import json
        result = json.loads(response.choices[0].message.content)

        # 驗證 target position 是否在相鄰位置中
        target_row = result.get("target_row", current_row)
        target_col = result.get("target_col", current_col)

        # 確保移動合法（必須是相鄰位置）
        if (target_row, target_col) not in adjacent_positions and (target_row, target_col) != (current_row, current_col):
            # 如果 LLM 選擇了不合法的位置，保持當前位置
            target_row, target_col = current_row, current_col

        return {
            "target_row": target_row,
            "target_col": target_col,
            "response_text": result.get("response_text", "我理解你的感受。"),
            "detected_emotion": result.get("detected_emotion", "neutral")
        }

    except Exception as e:
        print(f"LLM 錯誤: {e}")
        # 發生錯誤時，保持當前位置
        return {
            "target_row": current_row,
            "target_col": current_col,
            "response_text": "抱歉，我現在無法回應。",
            "detected_emotion": "error"
        }
