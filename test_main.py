import pytest
from fastapi.testclient import TestClient
from main import app

client = TestClient(app)

def test_read_root():
    """ルートURLのテスト: 正常にダッシュボードのHTMLが返ること"""
    response = client.get("/")
    assert response.status_code == 200
    assert "text/html" in response.headers["content-type"]

def test_post_sensor_data_success():
    """正常系のテスト: 正しい形式のセンサーデータが受け付けられるか"""
    payload = {
        "temperature": 25.5,
        "humidity": 45.0,
        "occupancy": True
    }
    response = client.post("/api/sensors/device-123/data", json=payload)
    
    assert response.status_code == 200
    data = response.json()
    assert data["device_id"] == "device-123"
    assert data["data"]["temperature"] == 25.5

def test_post_sensor_data_invalid_temperature():
    """異常系のテスト: 絶対零度未満の温度を送った場合 (422 Error)"""
    payload = {
        "temperature": -300.0, # 絶対零度(-273.15)未満
        "humidity": 45.0,
        "occupancy": True
    }
    response = client.post("/api/sensors/device-123/data", json=payload)
    
    assert response.status_code == 422
    error_detail = response.json()["detail"]
    assert any("greater than or equal to -273.15" in err["msg"] for err in error_detail)

def test_post_sensor_data_extra_forbidden_fields():
    """異常系のテスト: 未知のプロパティ(extra='forbid')を送った場合 (422 Error)"""
    payload = {
        "temperature": 25.0,
        "humidity": 45.0,
        "occupancy": True,
        "hacker_field": "unauthorized_access" # 未定義のフィールド
    }
    response = client.post("/api/sensors/device-123/data", json=payload)
    
    assert response.status_code == 422
    error_detail = response.json()["detail"]
    assert any("Extra inputs are not permitted" in err["msg"] for err in error_detail)

def test_ai_predict_anomaly():
    """AI推論モックのテスト: 温度が高い場合に異常検知されること"""
    # 事前にデータを投入
    payload = {"temperature": 29.0, "humidity": 50.0, "occupancy": True}
    client.post("/api/sensors/device-123/data", json=payload)
    
    # 予測APIを実行
    response = client.post("/api/ai/predict/device-123")
    
    assert response.status_code == 200
    data = response.json()
    assert data["anomaly_detected"] == True
    assert "冷房" in data["recommended_action"]
