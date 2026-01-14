import os
import logging
from openai import OpenAI
from emotion_wheel import EMOTION_CATEGORIES, get_emotion, get_adjacent_positions

logger = logging.getLogger("uvicorn")


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
    logger.info(f"[LLM] 當前位置: ({current_row},{current_col}) - {current_emotion['name']}")
    logger.info(f"[LLM] 使用者輸入: '{user_text}'")

    # 列出所有可能的情感位置（8x3 = 24 個）
    all_positions = []
    emotion_options = []
    for row in range(8):
        for col in range(3):
            emo = get_emotion(row, col)
            all_positions.append((row, col))
            emotion_options.append(f"({row},{col}): {emo['name']} - {emo['category']}")

    logger.info(f"[LLM] 全部可選位置數量: {len(all_positions)}")

    # 構建 prompt
    system_prompt = f"""你是一個敏銳的情感分析助手。請**純粹根據使用者當下的文字內容**判斷情感，不要被之前的情緒狀態影響。

當前情感位置: ({current_row}, {current_col}) - {current_emotion['name']} ({current_emotion['category']})

所有情感位置（可自由選擇）:
{chr(10).join(emotion_options)}

**重要規則**：
1. **獨立判斷**：每次都要重新分析使用者的文字，不要假設情緒會延續
2. **精確匹配**：選擇最符合當下文字情感的位置
3. **強度判斷**：col=0(低強度)、col=1(中強度)、col=2(高強度)

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

        logger.info(f"[LLM] 原始回應: {result}")

        # 驗證 target position 是否在相鄰位置中
        target_row = result.get("target_row", current_row)
        target_col = result.get("target_col", current_col)

        logger.info(f"[LLM] LLM 選擇位置: ({target_row},{target_col})")
        logger.info(f"[LLM] 偵測情緒: {result.get('detected_emotion', 'unknown')}")

        # 檢查位置是否有效
        if not (0 <= target_row < 8 and 0 <= target_col < 3):
            logger.warning(f"[LLM] 位置超出範圍！({target_row},{target_col})，保持原位置")
            target_row, target_col = current_row, current_col
        else:
            target_emotion = get_emotion(target_row, target_col)
            logger.info(f"[LLM] 最終位置: ({target_row},{target_col}) - {target_emotion['name']}")

        return {
            "target_row": target_row,
            "target_col": target_col,
            "response_text": result.get("response_text", "我理解你的感受。"),
            "detected_emotion": result.get("detected_emotion", "neutral")
        }

    except Exception as e:
        logger.error(f"[LLM] 錯誤: {e}", exc_info=True)
        # 發生錯誤時，保持當前位置
        return {
            "target_row": current_row,
            "target_col": current_col,
            "response_text": "抱歉，我現在無法回應。",
            "detected_emotion": "error"
        }
