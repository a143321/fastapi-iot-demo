# FastAPI IoT & AI Demo

IoTデバイス（スマートホーム等）から送信されるセンサーデータを収集し、簡単なモックAIによって異常検知・最適化予測を行うFastAPIデモアプリケーションです。

## 特徴
- **FastAPI**: 高速でモダンな非同期バックエンド
- **Python 3.13 対応**: パフォーマンスが向上した最新のPython環境を想定
- **Swagger UI 自動生成**: API仕様書とテストUIがWebブラウザで直感的に操作可能
- **Glassmorphism UI**: 付属のフロントエンドでデータとAI推論の様子を視覚化

---

## 🚀 環境構築手順 (Environment Setup)

### 1. リポジトリの配置
本ディレクトリ (`fastapi-iot-demo`) に移動します。
```bash
cd ~/projects/fastapi-iot-demo
```

### 2. 仮想環境の作成 (Python 3.13)
システム環境を汚さないために、Python 3.13を用いた仮想環境(`venv`)を作成します。

```bash
# 仮想環境を作成（pipなしで作成し、後から最新のpipを導入する安全な手順です）
python3.13 -m venv venv --without-pip

# 仮想環境を有効化
source venv/bin/activate

# 仮想環境内にpipをインストール
curl -sS https://bootstrap.pypa.io/get-pip.py | python
```

### 3. パッケージのインストール
`requirements.txt` を用いて、FastAPIとUvicorn等のパッケージをインストールします。

```bash
pip install -r requirements.txt
```

---

## 🏃 実行方法 (How to Run)

仮想環境に入った状態で、以下のコマンドを実行しサーバーを起動します。

```bash
uvicorn main:app --reload --host 0.0.0.0 --port 8000
```

起動後、以下のURLにアクセスして動作を確認してください。

1. **ダッシュボード画面 (UI)**
   👉 [http://localhost:8000/](http://localhost:8000/)
2. **自動生成APIドキュメント (Swagger UI)**
   👉 [http://localhost:8000/docs](http://localhost:8000/docs)

---

## 📂 フォルダ構成
- `main.py`: アプリケーション本体（APIエンドポイント、ビジネスロジック）
- `requirements.txt`: 依存パッケージリスト
- `static/`: 静的ファイル（HTML, CSS, JS）
  - `index.html`: ダッシュボード画面
