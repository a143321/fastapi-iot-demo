from fastapi import FastAPI, HTTPException
from fastapi.staticfiles import StaticFiles
from fastapi.responses import FileResponse
from pydantic import BaseModel, Field, ConfigDict
from typing import List, Dict, Optional, Any
import datetime
import random
import os
import boto3
from botocore.exceptions import ClientError
from boto3.dynamodb.conditions import Key

# DynamoDBの初期化
AWS_REGION = os.getenv("AWS_REGION", "ap-northeast-1")
DYNAMODB_ENDPOINT_URL = os.getenv("DYNAMODB_ENDPOINT_URL")
DYNAMODB_TABLE_NAME = "IoTData"

if DYNAMODB_ENDPOINT_URL:
    # ローカル開発環境（DynamoDB Local）用
    dynamodb = boto3.resource('dynamodb', region_name=AWS_REGION, endpoint_url=DYNAMODB_ENDPOINT_URL)
    # ローカル環境の場合、テーブルが存在しなければ自動作成する
    try:
        dynamodb.meta.client.describe_table(TableName=DYNAMODB_TABLE_NAME)
    except dynamodb.meta.client.exceptions.ResourceNotFoundException:
        print(f"Creating local DynamoDB table: {DYNAMODB_TABLE_NAME}")
        dynamodb.create_table(
            TableName=DYNAMODB_TABLE_NAME,
            KeySchema=[
                {'AttributeName': 'device_id', 'KeyType': 'HASH'},
                {'AttributeName': 'timestamp', 'KeyType': 'RANGE'}
            ],
            AttributeDefinitions=[
                {'AttributeName': 'device_id', 'AttributeType': 'S'},
                {'AttributeName': 'timestamp', 'AttributeType': 'S'}
            ],
            BillingMode='PAY_PER_REQUEST'
        )
else:
    # 本番環境（AWS）用
    dynamodb = boto3.resource('dynamodb', region_name=AWS_REGION)

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
    except Exception as e:
        import traceback
        error_details = f"DynamoDB Error: {str(e)}\n{traceback.format_exc()}"
        print(f"=== ERROR LOG ===\n{error_details}\n=================") # ECS（CloudWatch）の詳細ログ用
        raise HTTPException(status_code=500, detail=f"DynamoDBへの保存に失敗しました: {str(e)}") # Swagger UI用

    return status

@app.get("/api/sensors/status", response_model=List[DeviceStatus])
async def get_all_sensor_status():
    """
    登録されているすべてのセンサーの最新状態を取得します。
    """
    return [DeviceStatus(**data) for data in sensor_db.values()]

class HistoryResponse(BaseModel):
    items: List[Dict[str, Any]]
    total_count: int
    next_key: Optional[str] = None

@app.get("/api/sensors/{device_id}/history", response_model=HistoryResponse)
async def get_sensor_history(device_id: str, limit: int = 10, next_key: Optional[str] = None):
    """
    DynamoDBから指定されたデバイスの履歴データを取得します。
    ページネーション（limit, next_key）および全体件数に対応しています。
    """
    try:
        table = dynamodb.Table(DYNAMODB_TABLE_NAME)
        
        # 1. 全体件数の取得
        count_response = table.query(
            KeyConditionExpression=Key('device_id').eq(device_id),
            Select='COUNT'
        )
        total_count = count_response.get('Count', 0)
        
        # 2. データの取得（ページネーション）
        query_kwargs = {
            'KeyConditionExpression': Key('device_id').eq(device_id),
            'ScanIndexForward': False,  # 降順（最新順）
            'Limit': limit
        }
        
        if next_key:
            query_kwargs['ExclusiveStartKey'] = {
                'device_id': device_id,
                'timestamp': next_key
            }
            
        response = table.query(**query_kwargs)
        items = response.get('Items', [])
        last_evaluated_key = response.get('LastEvaluatedKey')
        
        new_next_key = last_evaluated_key.get('timestamp') if last_evaluated_key else None
        
        return HistoryResponse(
            items=items,
            total_count=total_count,
            next_key=new_next_key
        )
    except Exception as e:
        raise HTTPException(status_code=500, detail=f"DynamoDBからの履歴取得に失敗しました: {str(e)}")

@app.delete("/api/sensors/{device_id}/history")
async def clear_sensor_history(device_id: str):
    """
    DynamoDBから指定されたデバイスの全履歴データを削除（クリア）します。
    """
    try:
        table = dynamodb.Table(DYNAMODB_TABLE_NAME)
        response = table.query(
            KeyConditionExpression=Key('device_id').eq(device_id)
        )
        items = response.get('Items', [])
        
        # BatchWriteで一括削除
        with table.batch_writer() as batch:
            for item in items:
                batch.delete_item(
                    Key={
                        'device_id': item['device_id'],
                        'timestamp': item['timestamp']
                    }
                )
        
        # インメモリのキャッシュもクリア
        if device_id in sensor_db:
            del sensor_db[device_id]
            
        return {"message": f"{len(items)} items cleared successfully"}
    except Exception as e:
        raise HTTPException(status_code=500, detail=f"DynamoDBのデータクリアに失敗しました: {str(e)}")

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
