from fastapi import FastAPI, Request
from fastapi.middleware.cors import CORSMiddleware
from pydantic import BaseModel
from dotenv import load_dotenv
import uvicorn
import json

from emotion_wheel import get_emotion
from llm_service import analyze_emotion_and_respond

load_dotenv()

app = FastAPI()

# CORS 設定（允許前端呼叫）
app.add_middleware(
    CORSMiddleware,
    allow_origins=["*"],
    allow_credentials=True,
    allow_methods=["*"],
    allow_headers=["*"],
)


# Request Model
class WheelRequest(BaseModel):
    text: str
    position: list[int]


# Response Models
class LEDPosition(BaseModel):
    row: int
    col: int


class WheelResponse(BaseModel):
    led_position: LEDPosition
    color: str
    sentiment: str
    text: str


@app.get("/health")
async def health_check():
    return {"status": "ok"}


@app.post("/wheel", response_model=WheelResponse)
async def wheel_endpoint(request: WheelRequest):
    # Debug: 印出收到的 request 值
    print("=" * 50)
    print("收到 /wheel 請求:")
    print(f"  text: {request.text}")
    print(f"  position: {request.position}")
    print(f"  current row: {request.position[0]}, col: {request.position[1]}")
    print("=" * 50)

    current_row = request.position[0]
    current_col = request.position[1]

    # 使用 LLM 分析情感並生成回應
    llm_result = analyze_emotion_and_respond(request.text, current_row, current_col)

    new_row = llm_result["target_row"]
    new_col = llm_result["target_col"]

    # 取得新位置的情感資訊
    emotion_info = get_emotion(new_row, new_col)

    print(f"  LLM 分析結果: {llm_result['detected_emotion']}")
    print(f"  新位置: ({new_row}, {new_col}) - {emotion_info['name']}")
    print(f"  顏色: {emotion_info['color']}")
    print("=" * 50)

    return {
        "led_position": {
            "row": new_row,
            "col": new_col
        },
        "color": emotion_info["color"],
        "sentiment": emotion_info["name"],
        "text": llm_result["response_text"]
    }


if __name__ == "__main__":
    uvicorn.run(app, host="0.0.0.0", port=9005)
