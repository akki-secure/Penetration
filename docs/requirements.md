# HackLab 要件定義書

**バージョン**: 1.0  
**作成日**: 2026-05-04  
**プロジェクト名**: HackLab — ローカル完結型ペネトレーションテスト練習環境

---

## 1. プロジェクト概要

### 1.1 目的

セキュリティ学習者がペネトレーションテストの基礎技術を、法的・倫理的リスクなしに習得できるローカル環境を提供する。実際の攻撃手法を体験することで、防御側の視点も養う。

### 1.2 対象ユーザー

| ユーザー層 | 前提知識 |
|-----------|---------|
| セキュリティ初学者 | Linux コマンド基礎、HTTP の基礎知識 |
| Web 開発者 | 自作アプリの脆弱性を理解したい方 |
| CTF 参加者 | 実機演習で手順を体に覚えさせたい方 |

### 1.3 スコープ

- **対象**: ローカル PC 上の Docker コンテナのみ
- **対象外**: 外部ネットワーク、インターネット上のホスト

---

## 2. システム構成要件

### 2.1 動作環境

| 項目 | 要件 |
|------|------|
| OS | macOS / Windows / Linux |
| Docker Desktop | 4.x 以上 |
| 空きポート | 8081 (ホスト側) |
| ディスク容量 | 2 GB 以上 (イメージビルド後) |

### 2.2 ネットワーク構成

```
ホスト OS
  │
  │  localhost:8081  → target-web (HTTP)
  │  172.20.0.20:21  → target-ftp (FTP) ※コンテナ内からアクセス
  │  172.20.0.30:22  → target-ssh (SSH) ※コンテナ内からアクセス
  │
┌──────────────────────────────────────┐
│     hacklab-net (172.20.0.0/24)      │
│  target-web  172.20.0.10  :80  HTTP  │
│  target-ftp  172.20.0.20  :21  FTP   │
│  target-ssh  172.20.0.30  :22  SSH   │
└──────────────────────────────────────┘
```

- Docker bridge ネットワーク (`hacklab-net`) で 3 サービスを接続する
- ホスト OS から外部インターネットへの通信は発生しない

### 2.3 サービス一覧

| コンテナ名 | イメージベース | 固定 IP | 公開ポート (ホスト) |
|-----------|-------------|--------|------------------|
| hacklab-web | Python (Flask) | 172.20.0.10 | 8081 → 80 |
| hacklab-ftp | vsftpd | 172.20.0.20 | なし |
| hacklab-ssh | OpenSSH | 172.20.0.30 | なし |

---

## 3. 機能要件

### 3.1 target-web (Flask アプリ)

| ID | 機能 | エンドポイント | 含まれる脆弱性 |
|----|------|--------------|--------------|
| F-W-01 | トップページ表示 | `GET /` | なし |
| F-W-02 | ログイン | `POST /login` | SQL インジェクション |
| F-W-03 | ダッシュボード | `GET /dashboard` | なし |
| F-W-04 | robots.txt 公開 | `GET /robots.txt` | 情報漏洩 (フラグ埋め込み) |
| F-W-05 | DB バックアップ公開 | `GET /backup/db.sql` | 機密情報漏洩 |
| F-W-06 | ping 診断 | `GET /ping?host=` | OS コマンドインジェクション |
| F-W-07 | ファイルアップロード | `POST /upload` | 任意ファイルアップロード |
| F-W-08 | スクリプト実行 (Webシェル) | `GET /run/<filename>` | 任意コード実行 (exec) |
| F-W-09 | ファイル読み込み | `GET /file?name=` | ディレクトリトラバーサル |
| F-W-10 | 管理画面 | `GET /admin` | デフォルト認証情報 |
| F-W-11 | レスポンスヘッダー | 全レスポンス | バージョン情報漏洩 |

### 3.2 target-ftp

| ID | 機能 | 詳細 |
|----|------|------|
| F-F-01 | 匿名ログイン | ユーザー名 `anonymous`、パスワード空で接続可 |
| F-F-02 | ファイル公開 | `notes.txt` (SSH 認証情報を ROT13 エンコードで格納) |

### 3.3 target-ssh

| ID | 機能 | 詳細 |
|----|------|------|
| F-S-01 | SSH ログイン | ユーザー `developer`、パスワード `dev2024!` で接続可 |
| F-S-02 | フラグ格納 | ログイン後に `FLAG{ssh_foothold_established}` を取得可能 |
| F-S-03 | 権限昇格チャレンジ | sudo / SUID 等で root 権限昇格が可能 |

### 3.4 チャレンジ設計 (全 7 フラグ + ボーナス)

| Stage | タイトル | 使用技術 | フラグ |
|-------|---------|---------|--------|
| 1 | ネットワーク偵察 | nmap | `FLAG{recon_network_master}` |
| 2 | Web 探索 | robots.txt / 情報漏洩 | `FLAG{web_recon_complete}` |
| 3 | FTP 匿名ログイン | FTP anonymous | `FLAG{ftp_anonymous_pwned}` |
| 4 | SQL インジェクション | SQLi | `FLAG{sql_injection_champion}` |
| 5a | コマンドインジェクション | OS Command Injection | `FLAG{command_injection_rce}` |
| 5b | Web シェル | File Upload RCE | `FLAG{webshell_deployed}` |
| 6 | SSH 侵入 | 弱い認証情報 | `FLAG{ssh_foothold_established}` |
| ボーナス | 権限昇格 | Privilege Escalation | `FLAG{privilege_escalation_bonus}` |

攻略フロー:
```
偵察 (nmap) → Web 探索 (robots.txt / db.sql) → FTP (notes.txt 取得) 
→ ROT13 デコード → SSH 認証情報入手 → SQLi / RCE → 権限昇格
```

---

## 4. 脆弱性要件

意図的に実装する脆弱性と対応する OWASP Top 10 カテゴリ:

| 脆弱性 | OWASP 2021 | 実装箇所 | 実装方法 |
|--------|-----------|---------|---------|
| SQL インジェクション | A03 Injection | `/login` | f-string で SQL 直接結合 |
| OS コマンドインジェクション | A03 Injection | `/ping` | `shell=True` + 入力直接結合 |
| 任意ファイルアップロード + 実行 | A04 Insecure Design | `/upload`, `/run` | 拡張子チェックなし + `exec()` |
| ディレクトリトラバーサル | A01 Broken Access Control | `/file` | `os.path.join` で `..` を許可 |
| 機密情報漏洩 | A02 Cryptographic Failures | `/backup/db.sql`, `/robots.txt` | DB スキーマ・パスをそのまま公開 |
| デフォルト認証情報 | A07 Auth Failures | `/admin`, SSH | ハードコードされた弱いパスワード |
| 弱いハッシュ (MD5) | A02 Cryptographic Failures | users テーブル | MD5 でパスワードを保存 |
| ハードコード SECRET_KEY | A02 Cryptographic Failures | Flask 設定 | 固定文字列をそのまま使用 |

---

## 5. 非機能要件

### 5.1 操作性

- `make up` 1 コマンドで全サービスが起動すること
- 初回ビルドの目安: 5〜10 分以内
- `make reset` で全データを初期状態に戻せること

### 5.2 独立性・安全性

- 全通信が `hacklab-net` (172.20.0.0/24) 内に閉じていること
- ホスト OS から外部インターネットへのトラフィックが発生しないこと
- FTP / SSH はホスト OS に直接ポートフォワードしない (コンテナ経由のみ)

### 5.3 再現性

- `docker compose down -v && docker compose up --build` で完全リセットが可能なこと
- フラグ文字列は固定値とし、リセット後も同じ値が取得できること

### 5.4 ドキュメント

- README に起動手順・ネットワーク構成・チャレンジ一覧を記載すること
- 各脆弱性に OWASP カテゴリと攻撃例を明記すること

---

## 6. 制約・倫理要件

| 項目 | 内容 |
|------|------|
| 利用目的 | 教育・学習目的のみ。実在するシステムへの攻撃への転用を禁止する |
| 外部攻撃防止 | 攻撃ツールは必ず `172.20.0.0/24` 内のホストのみを対象とすること |
| 警告表示 | アプリ起動時・README に「やられアプリ」である旨を明示すること |
| 配布制限 | 本環境をインターネット上の実サーバーとして公開しないこと |

---

## 7. 今後の拡張候補 (スコープ外)

以下は現バージョンのスコープ外だが、将来的な追加を検討できる項目:

- SSRF (Server-Side Request Forgery) チャレンジの追加
- XXE (XML External Entity) チャレンジの追加
- JWT 改ざんチャレンジの追加
- スコアボード機能 (フラグ提出・得点管理)
- `internal: true` による Docker ネットワーク完全遮断オプション
- Kali Linux コンテナを attacker サービスとして追加

---

*本ドキュメントは HackLab の教育目的に沿った設計・実装の基準を定めるものです。*
