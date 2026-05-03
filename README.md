# Security

ローカル完結型のセキュリティ学習・ペネトレーションテスト練習リポジトリです。

---

## 収録コンテンツ

### [HackLab](hacklab/README.md)

Docker で起動するペネトレーションテスト練習環境。
意図的に脆弱性を持つ Web・FTP・SSH サーバーを用意しており、
SQLi・コマンドインジェクション・ファイルアップロード RCE など
7 つのフラグを取得していくハンズオン形式の学習ができます。

```bash
cd hacklab
docker compose up --build
# → http://localhost:8081 を開く
```

詳細は [hacklab/README.md](hacklab/README.md) を参照してください。

---

> このリポジトリの内容は教育目的のみに使用してください。
> 実在するシステムへの攻撃には絶対に使用しないでください。
