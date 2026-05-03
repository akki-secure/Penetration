"""
target-web — 意図的脆弱性を含む Web サーバー (教育目的)
==========================================================
このアプリは「やられアプリ」です。実際のサービスには絶対に使わないこと。
含まれる脆弱性:
  1. SQL インジェクション  (/login)
  2. コマンドインジェクション (/ping)
  3. 任意ファイルアップロード + 実行 (/upload, /run/<name>)
  4. ディレクトリトラバーサル (/file)
  5. 情報漏洩 (/backup/db.sql, /robots.txt)
  6. デフォルト認証情報 (admin / hackme123)
"""

import os
import sqlite3
import subprocess
from pathlib import Path
from flask import Flask, request, jsonify, send_from_directory, session, render_template, redirect, url_for

app = Flask(__name__)

# 【脆弱性】SECRET_KEY がハードコードされており変更されていない
app.secret_key = "super_secret_key_1234"

DB_PATH = "/app/hacklab.db"
UPLOAD_DIR = "/app/uploads"
FILES_DIR = "/app/files"


# -------------------------------------------------------
# トップページ
# -------------------------------------------------------
@app.route("/")
def index():
    return render_template("index.html")


# -------------------------------------------------------
# Stage 2: robots.txt — 隠しパスを列挙 (情報漏洩)
# 【脆弱性】管理画面やバックアップのパスを robots.txt に記載している
# -------------------------------------------------------
@app.route("/robots.txt")
def robots():
    content = (
        "User-agent: *\n"
        "Disallow: /admin\n"
        "Disallow: /backup\n"
        "Disallow: /upload\n"
        "# FLAG{web_recon_complete}\n"
    )
    return app.response_class(content, mimetype="text/plain")


# -------------------------------------------------------
# Stage 2: バックアップ SQL ファイル公開 (情報漏洩)
# 【脆弱性】DB スキーマと初期データが外部から丸見え
# -------------------------------------------------------
@app.route("/backup/db.sql")
def backup_sql():
    sql = """-- TechNova Solutions Database Backup
-- Generated: 2024-12-20 03:00:01
-- mysqldump 8.0.36

CREATE TABLE users (
    id INTEGER PRIMARY KEY AUTOINCREMENT,
    username TEXT NOT NULL,
    password TEXT NOT NULL,
    role TEXT NOT NULL,
    flag TEXT
);

INSERT INTO users VALUES (1, 'admin', '4d55ef6655de2b4a006ada41db320e6f', 'admin', 'FLAG{sql_injection_champion}');
INSERT INTO users VALUES (2, 'alice', 'f2a7e7f4b1c9e3d6a8b0c2d4e6f8a0b2', 'user', NULL);
INSERT INTO users VALUES (3, 'bob',   'e10adc3949ba59abbe56e057f20f883e', 'user', NULL);
"""
    return app.response_class(sql, mimetype="text/plain")


# -------------------------------------------------------
# Stage 4: ログイン — SQL インジェクション脆弱性
# 【脆弱性】ユーザー入力を直接 SQL に埋め込んでいる
# 攻撃例: username = "admin' --" でパスワードなしログイン可
#         username = "' UNION SELECT 1,username,password,'admin',flag FROM users --"
# -------------------------------------------------------
@app.route("/login", methods=["GET", "POST"])
def login():
    if request.method == "GET":
        return render_template("login.html")

    username = request.form.get("username", "")
    password = request.form.get("password", "")

    conn = sqlite3.connect(DB_PATH)
    c = conn.cursor()

    # 【脆弱性】SQL インジェクション: f-string で直接埋め込み (絶対に真似しないこと)
    query = f"SELECT * FROM users WHERE username='{username}' AND password='{password}'"
    try:
        c.execute(query)
        rows = c.fetchall()
    except Exception as e:
        conn.close()
        return jsonify({"error": str(e), "query": query}), 400

    conn.close()

    if rows:
        session["user"] = rows[0][1]
        session["role"] = rows[0][3]
        flag = rows[0][4] if rows[0][4] else ""
        # 複数行取得された場合も全フラグを結合して表示（UNION SELECT 対策なし）
        all_flags = " | ".join(r[4] for r in rows if r[4]) if len(rows) > 1 else flag
        return render_template(
            "dashboard.html",
            username=rows[0][1],
            role=rows[0][3],
            flag=all_flags or flag,
        )

    return render_template("login.html", error="ユーザー名またはパスワードが違います。")


# -------------------------------------------------------
# ダッシュボード (セッション確認)
# -------------------------------------------------------
@app.route("/dashboard")
def dashboard():
    if not session.get("user"):
        return redirect(url_for("login"))
    return render_template(
        "dashboard.html",
        username=session["user"],
        role=session.get("role", "user"),
        flag="",
    )


# -------------------------------------------------------
# ログアウト
# -------------------------------------------------------
@app.route("/logout")
def logout():
    session.clear()
    return redirect(url_for("index"))


# -------------------------------------------------------
# Stage 5: ping — コマンドインジェクション脆弱性
# 【脆弱性】shell=True + ユーザー入力の直接結合
# 攻撃例: host=127.0.0.1;cat /flag.txt
#         host=127.0.0.1 && cat /app/hacklab.db
# -------------------------------------------------------
@app.route("/ping")
def ping():
    host = request.args.get("host", "127.0.0.1")
    if not host:
        return jsonify({"error": "host パラメータが必要です"}), 400

    # 【脆弱性】シェルに直接渡している。セミコロンやパイプで任意コマンドが実行可能
    result = subprocess.run(
        f"ping -c 2 {host}",
        shell=True,
        capture_output=True,
        text=True,
        timeout=10,
    )
    output = result.stdout + result.stderr

    flag = ""
    if ";" in host or "&&" in host or "|" in host:
        try:
            conn = sqlite3.connect(DB_PATH)
            c = conn.cursor()
            c.execute("SELECT content FROM secrets WHERE id=1")
            row = c.fetchone()
            flag = row[0] if row else ""
            conn.close()
        except Exception:
            pass

    return jsonify({"host": host, "output": output, "flag": flag})


# -------------------------------------------------------
# ネットワーク診断ページ
# -------------------------------------------------------
@app.route("/tools")
def tools():
    return render_template("tools.html")


# -------------------------------------------------------
# Stage 5: ファイルアップロード — 拡張子チェックなし
# 【脆弱性】アップロードされたファイルの種類を検証していない
# -------------------------------------------------------
@app.route("/upload", methods=["GET", "POST"])
def upload():
    if request.method == "GET":
        return render_template("upload.html")

    f = request.files.get("file")
    if not f or f.filename == "":
        return jsonify({"error": "ファイルが選択されていません"}), 400

    # 【脆弱性】拡張子チェックなし・サニタイズなしで保存
    save_path = os.path.join(UPLOAD_DIR, f.filename)
    f.save(save_path)
    return jsonify({
        "status": "アップロード成功",
        "filename": f.filename,
    })


# -------------------------------------------------------
# Stage 5: アップロードされたスクリプトを実行 (Webシェル)
# 【脆弱性】アップロードファイルをそのまま exec() で実行
# -------------------------------------------------------
@app.route("/run/<filename>")
def run_script(filename):
    filepath = os.path.join(UPLOAD_DIR, filename)
    if not os.path.exists(filepath):
        return jsonify({"error": "ファイルが見つかりません"}), 404

    try:
        with open(filepath) as fh:
            code = fh.read()
        # 【脆弱性】exec() で任意コードを実行 — 絶対に実運用で使わないこと
        local_vars = {}
        exec(code, {}, local_vars)  # noqa: S102
        output = local_vars.get("output", "実行完了 (output 変数に結果を代入してください)")
        return jsonify({
            "status": "実行完了",
            "output": str(output),
            "flag": "FLAG{webshell_deployed}",
        })
    except Exception as e:
        return jsonify({"error": str(e)}), 500


# -------------------------------------------------------
# Stage 2: ディレクトリトラバーサル
# 【脆弱性】name パラメータをサニタイズせずにファイルパスへ結合
# 攻撃例: /file?name=../../etc/passwd
# -------------------------------------------------------
@app.route("/file")
def read_file():
    name = request.args.get("name", "")
    if not name:
        return jsonify({"error": "name パラメータが必要です"}), 400

    # 【脆弱性】パス結合のみで .. を許可 → トラバーサル可能
    path = os.path.join(FILES_DIR, name)
    try:
        with open(path) as fh:
            return jsonify({"name": name, "content": fh.read()})
    except FileNotFoundError:
        return jsonify({"error": "ファイルが見つかりません", "path": path}), 404
    except Exception as e:
        return jsonify({"error": str(e)}), 500


# -------------------------------------------------------
# 管理画面: デフォルト認証情報でアクセス可能
# 【脆弱性】admin/hackme123 という弱い認証情報がハードコード
# -------------------------------------------------------
@app.route("/admin")
def admin():
    auth = request.authorization
    if not auth or auth.username != "admin" or auth.password != "hackme123":
        return app.response_class(
            "認証が必要です", 401,
            {"WWW-Authenticate": 'Basic realm="TechNova Admin"'}
        )
    conn = sqlite3.connect(DB_PATH)
    c = conn.cursor()
    c.execute("SELECT id, username, password, role, flag FROM users")
    users = c.fetchall()
    conn.close()
    return render_template("admin.html", users=users)


# -------------------------------------------------------
# バナー: バージョン情報をヘッダーに露出 (情報漏洩)
# 【脆弱性】Server ヘッダーで内部バージョンを公開
# -------------------------------------------------------
@app.after_request
def add_headers(response):
    response.headers["Server"] = "FlaskApp/1.0 Python/3.11"
    response.headers["X-Powered-By"] = "HackLab-Target-Web"
    return response


if __name__ == "__main__":
    Path(FILES_DIR).mkdir(exist_ok=True)
    (Path(FILES_DIR) / "readme.txt").write_text(
        "TechNova Solutions — 社内ファイルサーバー\n"
        "このディレクトリには社内ドキュメントが格納されています。\n"
    )

    app.run(host="0.0.0.0", port=80, debug=False)
