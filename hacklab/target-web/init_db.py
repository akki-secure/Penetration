"""
DB 初期化スクリプト
起動時に SQLite データベースとテーブルを作成し、初期データを投入する。
"""
import sqlite3
import hashlib
import os

DB_PATH = "/app/hacklab.db"


def md5(text: str) -> str:
    return hashlib.md5(text.encode()).hexdigest()


def init():
    conn = sqlite3.connect(DB_PATH)
    c = conn.cursor()

    # ユーザーテーブル: パスワードは MD5 ハッシュで保存 (意図的に弱い)
    # 【脆弱性】MD5 は衝突が容易で、レインボーテーブルで即座にクラック可能
    c.execute("""
        CREATE TABLE IF NOT EXISTS users (
            id INTEGER PRIMARY KEY AUTOINCREMENT,
            username TEXT NOT NULL,
            password TEXT NOT NULL,
            role TEXT NOT NULL,
            flag TEXT
        )
    """)

    # 【ヒント】admin のパスワードは "hackme123" を MD5 にしたもの
    c.execute("DELETE FROM users")
    c.execute("INSERT INTO users VALUES (1, 'admin', ?, 'admin', ?)",
              (md5("hackme123"), "FLAG{sql_injection_champion}"))
    c.execute("INSERT INTO users VALUES (2, 'alice', ?, 'user', NULL)",
              (md5("alice2024"),))
    c.execute("INSERT INTO users VALUES (3, 'bob', ?, 'user', NULL)",
              (md5("password123"),))

    # 秘密メモテーブル: コマンドインジェクション成功後に読めるフラグ
    c.execute("""
        CREATE TABLE IF NOT EXISTS secrets (
            id INTEGER PRIMARY KEY,
            content TEXT
        )
    """)
    c.execute("DELETE FROM secrets")
    c.execute("INSERT INTO secrets VALUES (1, 'FLAG{command_injection_rce}')")

    conn.commit()
    conn.close()
    print("[init_db] データベース初期化完了")


if __name__ == "__main__":
    init()
