# Wireshark でパケットを盗聴する — HackLab `/login` 編

HackLab の `target-web` は HTTP (平文) で通信しているため、
Wireshark でパケットをキャプチャすると、ログイン時の
ユーザー名・パスワードがそのまま読み取れてしまう。
この文書はその手順をまとめたもの。

---

## 前提

- `hacklab` の Docker コンテナが起動していること (`docker compose ps` で `Up` を確認)
- Wireshark がインストールされていること (Mac は `brew install --cask wireshark` など)
- ブラウザから `http://localhost:8081` にアクセスできること

---

## 手順

### 1. Wireshark を起動する

Wireshark.app を開く。

### 2. キャプチャするインターフェースを選ぶ

インターフェース一覧から **`Loopback: lo0`** を選択してキャプチャを開始する。

> **なぜ `lo0` なのか**
> `target-web` は Docker によって `localhost:8081` にポートフォワードされている。
> Mac上のブラウザから `http://localhost:8081` へアクセスする通信は、
> 外部ネットワークではなく **ループバックインターフェース (`lo0`)** を通る。

### 3. ブラウザでログインする

`http://localhost:8081/login` を開き、`admin` / `hackme123` でログインする。

### 4. フィルタをかける

Wireshark のフィルタ欄に以下を入力して Enter：

```
http.request.method == "POST"
```

`/login` へのリクエストだけが絞り込まれる。

> フィルタをかけても何も表示されない場合、Wireshark がポート 8081 を
> HTTP として自動認識していない可能性がある。その場合は該当パケットを右クリック →
> **Decode As → HTTP** を選択する。

### 5. パケットの中身を復元する

絞り込んだパケットを右クリック → **Follow → HTTP Stream** を選択する。

`username=admin&password=hackme123` のように、フォーム送信内容が
**暗号化されずにそのまま** 表示される。

---

## 見るべきポイント

| 確認項目 | 見る場所 |
|---------|---------|
| リクエストボディ (平文パスワード) | Follow → HTTP Stream 内の `POST /login` 本文 |
| `Authorization` ヘッダー (Basic 認証、`/admin` アクセス時) | パケット詳細ペインの HTTP ヘッダー |
| `Set-Cookie: session=...` | ログイン成功レスポンスのヘッダー |

`Authorization: Basic ...` は Base64 エンコードされているだけで暗号化ではないため、
`echo "<値>" | base64 -d` でそのままデコードできる。

---

## HTTPS だとどうなるか (参考)

同じ手順を `https://` の通信に対して行った場合、Wireshark はパケット自体は
キャプチャできるが、TLS で暗号化されているため Follow Stream をしても
中身は復号できないバイト列にしかならない。これが SSL/TLS 化が
盗聴対策になる理由。

---

## 関連ドキュメント

- [sql-injection-login.md](sql-injection-login.md) — `/login` の SQL インジェクションの仕組み
- [vulnerability-report-template.md](vulnerability-report-template.md) — 発見した脆弱性をまとめる報告書テンプレート
