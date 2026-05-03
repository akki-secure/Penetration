# ⚡ HackLab — ローカル完結型ペネトレーションテスト練習環境

> **注意**: このアプリは教育目的の「やられアプリ」です。
> 実在するシステムへの攻撃には絶対に使用しないでください。
> 全ての通信はローカルの Docker ネットワーク内に完結します。

---

## 必要環境

| ツール | バージョン | 入手先 |
|--------|-----------|--------|
| Docker Desktop | 4.x 以上 | docker.com/products/docker-desktop |
| (Mac/Windows 両対応) | | |

ブラウザさえあれば OK。追加のツールは不要です。

---

## 起動方法

```bash
# このディレクトリに移動
cd hacklab

# ビルド & 起動 (初回は 5〜10 分かかります)
docker compose up --build

# ブラウザで開く
open http://localhost:8080    # Mac
start http://localhost:8080   # Windows
```

停止する場合:
```bash
docker compose down
```

---

## ネットワーク構成

```
あなたのブラウザ
    │
    ▼ localhost:8080
┌─────────────────────────────────────────────┐
│          hacklab-net (172.20.0.0/24)        │
│                                             │
│  attacker-ui   172.20.0.100  (攻撃コンソール) │
│  target-web    172.20.0.10   :80  HTTP      │
│  target-ftp    172.20.0.20   :21  FTP       │
│  target-ssh    172.20.0.30   :22  SSH       │
└─────────────────────────────────────────────┘
※ 外部インターネットへの通信は発生しません
```

---

## チャレンジ概要 (全 7 フラグ)

| Stage | タイトル | 技術 | フラグ |
|-------|---------|------|--------|
| 1 | ネットワーク偵察 | ポートスキャン | FLAG{recon_network_master} |
| 2 | Web 探索 | robots.txt / 情報漏洩 | FLAG{web_recon_complete} |
| 3 | FTP 匿名ログイン | FTP anonymous | FLAG{ftp_anonymous_pwned} |
| 4 | SQL インジェクション | SQLi | FLAG{sql_injection_champion} |
| 5a | コマンドインジェクション | OS Command Injection | FLAG{command_injection_rce} |
| 5b | Web シェル | File Upload RCE | FLAG{webshell_deployed} |
| 6 | SSH 侵入 | 弱い認証情報 | FLAG{ssh_foothold_established} |

---

## 攻略の流れ

```
偵察フェーズ                情報収集フェーズ            侵入フェーズ
─────────────────────────────────────────────────────────────────
[偵察] ページで              [侵入] ページで             [侵入] ページで
ポートスキャン          →    FTP 匿名ログイン        →   SQLi / RCE / SSH
    │                           │                          │
    ▼                           ▼                          ▼
3 ホスト発見              notes.txt 取得             フラグ取得 🚩
                        (ROT13 エンコード済み)
```

---

## よくある質問

**Q: 起動しても `localhost:8080` に接続できない**
A: `docker compose ps` でコンテナの状態を確認してください。
   `attacker-ui` の STATUS が `Up` になっているか確認します。

**Q: FTP ツールでエラーが出る**
A: target-ftp コンテナのパッシブモード設定が必要です。
   `docker compose logs target-ftp` でログを確認してください。

**Q: SSH 接続できない**
A: FTP の `notes.txt` を取得し、ROT13 をデコードしてください。
   画面内の ROT13 デコーダーが使えます。

**Q: 全フラグを取得後にリセットしたい**
A: `docker compose down -v && docker compose up --build` で完全リセットできます。

---

## 含まれる脆弱性 (学習リファレンス)

| 脆弱性 | OWASP カテゴリ | 場所 |
|--------|--------------|------|
| SQL インジェクション | A03:2021 Injection | target-web /login |
| OS コマンドインジェクション | A03:2021 Injection | target-web /ping |
| 任意ファイルアップロード | A04:2021 Insecure Design | target-web /upload |
| ディレクトリトラバーサル | A01:2021 Broken Access | target-web /file |
| 機密情報の漏洩 | A02:2021 Cryptographic | /backup/db.sql |
| デフォルト認証情報 | A07:2021 Auth Failures | SSH / FTP |
| 弱いハッシュ (MD5) | A02:2021 Cryptographic | users テーブル |

---

*HackLab は教育目的のみに使用してください。*
