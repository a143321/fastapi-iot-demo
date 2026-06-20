# ベースイメージとして軽量なPython 3.13を採用
FROM python:3.13-slim

# コンテナ内の作業ディレクトリを設定
WORKDIR /app

# 依存パッケージのリストをコンテナにコピー
COPY requirements.txt .

# パッケージをインストール（--no-cache-dirでイメージサイズを軽量化）
RUN pip install --no-cache-dir -r requirements.txt

# アプリケーションのコード全体をコンテナにコピー
COPY . .

# FastAPIが通信に使用するポートを明示（App Runnerで指定するポートと同じ）
EXPOSE 8000

# uvicornを使ってFastAPIサーバーを起動
CMD ["uvicorn", "main:app", "--host", "0.0.0.0", "--port", "8000"]
