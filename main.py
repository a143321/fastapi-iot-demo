from fastapi import FastAPI, HTTPException
from fastapi.staticfiles import StaticFiles
from fastapi.responses import FileResponse
from pydantic import BaseModel, Field, ConfigDict
from typing import List, Dict
import datetime
import random
import os
import boto3
from botocore.exceptions import ClientError

# DynamoDBの初期化
AWS_REGION = os.getenv("AWS_REGION", "ap-northeast-1")
dynamodb = boto3.resource('dynamodb', region_name=AWS_REGION)
DYNAMODB_TABLE_NAME = "IoTData"

app = FastAPI(
    title="Smart Home IoT & AI Dashboard",
    description="FastAPI デモアプリケーション。IoTセンサーデータの収集とAIによる異常検知・最適化予測を行います。",
    version="1.0.0"
)

# Staticファイルの配信設定（フロントエンドUI用）
app.mount("/static", StaticFiles(directory="static"), name="static")

# インメモリ・データストア（モック用）
sensor_db: Dict[str, dict] = {}
alert_history: List[dict] = []

# --- データモデル (Pydantic) ---
class SensorData(BaseModel):
    model_config = ConfigDict(extra="forbid")
    
    temperature: float = Field(..., ge=-273.15, description="温度 (℃) ※絶対零度以上")
    humidity: float = Field(..., ge=0.0, le=100.0, description="湿度 (%) ※0〜100の範囲")
    occupancy: bool = Field(False, description="人感センサー (在室有無)")

class DeviceStatus(BaseModel):
    device_id: str
    last_update: str
    data: SensorData

class AIPredictionResponse(BaseModel):
    device_id: str
    anomaly_detected: bool
    recommended_action: str
    confidence: float

# --- エンドポイント ---

@app.get("/")
async def serve_dashboard():
    """フロントエンドのダッシュボードを返します。"""
    return FileResponse("static/index.html")

@app.post("/api/sensors/{device_id}/data", response_model=DeviceStatus)
async def receive_sensor_data(device_id: str, data: SensorData):
    """
    IoTデバイスからのセンサーデータを受信し、DynamoDBに永続化しつつインメモリにキャッシュします。
    """
    current_time = datetime.datetime.now().isoformat()
    status = DeviceStatus(device_id=device_id, last_update=current_time, data=data)
    
    # 1. ダッシュボードの高速表示用キャッシュ（インメモリ）
    sensor_db[device_id] = status.dict()
    
    # 2. DynamoDBへの永続化保存（データの蓄積）
    try:
        table = dynamodb.Table(DYNAMODB_TABLE_NAME)
        table.put_item(
            Item={
                'device_id': device_id,
                'timestamp': current_time,
                'temperature': str(data.temperature), # Decimal等への変換を避けるため文字列化
                'humidity': str(data.humidity),
                'occupancy': data.occupancy
            }
        )
    except ClientError as e:
        print(f"DynamoDB ClientError: {e}")
    except Exception as e:
        print(f"DynamoDB is not fully configured (local environment or missing permissions): {e}")

    return status

@app.get("/api/sensors/status", response_model=List[DeviceStatus])
async def get_all_sensor_status():
    """
    登録されているすべてのセンサーの最新状態を取得します。
    """
    return [DeviceStatus(**data) for data in sensor_db.values()]

@app.post("/api/ai/predict/{device_id}", response_model=AIPredictionResponse)
async def predict_optimization(device_id: str):
    """
    指定されたデバイスの最新データをもとに、AIが異常検知や推奨アクションを予測します（モック実装）。
    """
    if device_id not in sensor_db:
        raise HTTPException(status_code=404, detail="Device not found or no data available")
    
    current_data = sensor_db[device_id]["data"]
    temp = current_data["temperature"]
    hum = current_data["humidity"]
    occ = current_data["occupancy"]
    
    anomaly = False
    action = "現状維持"
    confidence = round(random.uniform(0.7, 0.99), 2)
    
    # 簡易的なAIルールのモック
    if temp > 28.0 and occ:
        anomaly = True
        action = "冷房をオンにしてください（設定温度: 26℃）"
    elif temp < 15.0 and occ:
        anomaly = True
        action = "暖房をオンにしてください（設定温度: 22℃）"
    elif not occ and (temp > 30.0 or temp < 10.0):
        action = "省エネモードを維持しています"
    
    if hum > 70.0:
        action += " / 除湿も推奨します"

    response = AIPredictionResponse(
        device_id=device_id,
        anomaly_detected=anomaly,
        recommended_action=action,
        confidence=confidence
    )
    
    if anomaly:
        alert_history.append({
            "time": datetime.datetime.now().isoformat(),
            "device_id": device_id,
            "action": action
        })

    return response

@app.get("/api/alerts", response_model=List[dict])
async def get_recent_alerts():
    """
    最近のAIアラート・推奨アクション履歴を取得します。
    """
    return list(reversed(alert_history))[:10]
