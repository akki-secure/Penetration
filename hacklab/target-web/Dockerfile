FROM python:3.11-slim

WORKDIR /app

# 必要パッケージをインストール
RUN apt-get update && apt-get install -y --no-install-recommends \
    iputils-ping \
    && rm -rf /var/lib/apt/lists/*

COPY requirements.txt .
RUN pip install --no-cache-dir -r requirements.txt

COPY . .

# uploads ディレクトリの権限を設定 (ファイルアップロード脆弱性のため書き込み許可)
RUN mkdir -p /app/uploads && chmod 777 /app/uploads

# DB 初期化してから Web サーバー起動
CMD ["sh", "-c", "python init_db.py && python app.py"]

EXPOSE 80
