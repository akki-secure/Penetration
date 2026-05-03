"""
attacker-ui — HackLab 攻撃者コンソール
========================================
ブラウザから操作できるペネトレーションテスト練習ツール。
hacklab-net 内のターゲットに対して各種攻撃を実行する。
"""

import ftplib
import io
import json
import socket
import sqlite3
import threading
from pathlib import Path

import paramiko
import requests
from flask import Flask, jsonify, render_template, request, session

app = Flask(__name__)
app.secret_key = "attacker_ui_secret_2024"

# 獲得済みフラグを保存する簡易ファイル
FLAGS_FILE = Path("/app/captured_flags.json")

# ターゲット IP 定義
TARGETS = {
    "web": "172.20.0.10",
    "ftp": "172.20.0.20",
    "ssh": "172.20.0.30",
}

# 全フラグのマスターリスト (検証用)
VALID_FLAGS = {
    "FLAG{recon_network_master}":     "Stage 1 — ネットワーク偵察",
    "FLAG{web_recon_complete}":       "Stage 2 — Web 探索",
    "FLAG{ftp_anonymous_pwned}":      "Stage 3 — FTP 匿名ログイン",
    "FLAG{sql_injection_champion}":   "Stage 4 — SQL インジェクション",
    "FLAG{command_injection_rce}":    "Stage 5a — コマンドインジェクション",
    "FLAG{webshell_deployed}":        "Stage 5b — Web シェル",
    "FLAG{ssh_foothold_established}": "Stage 6 — SSH 侵入",
}


# -------------------------------------------------------
# フラグ永続化ヘルパー
# -------------------------------------------------------
def load_flags() -> dict:
    if FLAGS_FILE.exists():
        return json.loads(FLAGS_FILE.read_text())
    return {}


def save_flag(flag: str, stage: str):
    flags = load_flags()
    if flag not in flags:
        flags[flag] = stage
        FLAGS_FILE.write_text(json.dumps(flags, ensure_ascii=False, indent=2))


# -------------------------------------------------------
# ページルーティング
# -------------------------------------------------------
@app.route("/")
def index():
    flags = load_flags()
    score = len(flags)
    total = len(VALID_FLAGS)
    return render_template("index.html", flags=flags, score=score, total=total,
                           valid_flags=VALID_FLAGS, targets=TARGETS)


@app.route("/recon")
def recon():
    return render_template("recon.html", targets=TARGETS)


@app.route("/exploit")
def exploit():
    return render_template("exploit.html", targets=TARGETS)


@app.route("/flags")
def flags_page():
    flags = load_flags()
    return render_template("flags.html", flags=flags, valid_flags=VALID_FLAGS,
                           score=len(flags), total=len(VALID_FLAGS))


# -------------------------------------------------------
# API: ポートスキャン
# 指定した IP の TCP ポートに接続を試み、開いているか確認する
# -------------------------------------------------------
@app.route("/api/scan", methods=["POST"])
def api_scan():
    data = request.json or {}
    target = data.get("target", "")
    ports = data.get("ports", [21, 22, 80, 443, 3306, 8080])
    timeout = float(data.get("timeout", 1.0))

    if not target:
        return jsonify({"error": "target が必要です"}), 400

    results = []
    open_ports = []

    def check_port(port):
        """ポートに TCP 接続を試みてバナーを取得する"""
        try:
            with socket.create_connection((target, port), timeout=timeout) as sock:
                sock.settimeout(0.5)
                # バナーグラブ: 接続直後に送られてくるデータを受信
                try:
                    banner = sock.recv(1024).decode("utf-8", errors="replace").strip()
                except Exception:
                    banner = ""
                service = guess_service(port)
                results.append({"port": port, "state": "open", "service": service, "banner": banner})
                open_ports.append(port)
        except (ConnectionRefusedError, socket.timeout, OSError):
            results.append({"port": port, "state": "closed", "service": "", "banner": ""})

    threads = [threading.Thread(target=check_port, args=(p,)) for p in ports]
    for t in threads:
        t.start()
    for t in threads:
        t.join()

    results.sort(key=lambda x: x["port"])

    # 全ターゲットのオープンポートが見つかったら偵察フラグを付与
    flag = ""
    if len(open_ports) > 0 and target in TARGETS.values():
        flag = "FLAG{recon_network_master}"
        save_flag(flag, VALID_FLAGS[flag])

    return jsonify({"target": target, "results": results, "flag": flag})


def guess_service(port: int) -> str:
    mapping = {21: "FTP", 22: "SSH", 80: "HTTP", 443: "HTTPS",
               3306: "MySQL", 5432: "PostgreSQL", 8080: "HTTP-Alt"}
    return mapping.get(port, "Unknown")


# -------------------------------------------------------
# API: HTTP リクエスト送信
# ターゲット Web に対して任意の HTTP リクエストを送る
# -------------------------------------------------------
@app.route("/api/http", methods=["POST"])
def api_http():
    data = request.json or {}
    method = data.get("method", "GET").upper()
    url = data.get("url", "")
    params = data.get("params", {})
    body = data.get("body", {})
    headers = data.get("headers", {})

    if not url:
        return jsonify({"error": "url が必要です"}), 400

    # URL が hacklab-net 内のターゲットを指しているか確認
    allowed_prefixes = [f"http://172.20.0.{i}" for i in range(1, 255)]
    if not any(url.startswith(p) for p in allowed_prefixes):
        return jsonify({"error": "hacklab-net 内のターゲット (172.20.0.x) のみアクセス可能です"}), 403

    try:
        resp = requests.request(
            method, url,
            params=params if method == "GET" else None,
            data=body if method == "POST" else None,
            headers=headers,
            timeout=10,
            allow_redirects=True,
        )
        return jsonify({
            "status_code": resp.status_code,
            "headers": dict(resp.headers),
            "body": resp.text[:5000],  # 最大 5000 文字
        })
    except requests.exceptions.ConnectionError as e:
        return jsonify({"error": f"接続エラー: {e}"}), 502
    except Exception as e:
        return jsonify({"error": str(e)}), 500


# -------------------------------------------------------
# API: FTP 接続
# 匿名ログインでファイルを取得する
# -------------------------------------------------------
@app.route("/api/ftp", methods=["POST"])
def api_ftp():
    data = request.json or {}
    host = data.get("host", TARGETS["ftp"])
    user = data.get("user", "anonymous")
    password = data.get("password", "")
    action = data.get("action", "list")  # list / get
    path = data.get("path", "/")
    filename = data.get("filename", "")

    try:
        ftp = ftplib.FTP()
        ftp.connect(host, 21, timeout=10)
        ftp.login(user, password)

        if action == "list":
            items = []
            ftp.cwd(path)
            ftp.retrlines("LIST", items.append)
            ftp.quit()
            return jsonify({"status": "接続成功", "path": path, "listing": items})

        elif action == "get" and filename:
            buf = io.BytesIO()
            ftp.retrbinary(f"RETR {filename}", buf.write)
            ftp.quit()
            content = buf.getvalue().decode("utf-8", errors="replace")
            # FTP からフラグを含むファイルを取得したらフラグを付与
            flag = ""
            if "FLAG{ftp_anonymous_pwned}" in content:
                flag = "FLAG{ftp_anonymous_pwned}"
                save_flag(flag, VALID_FLAGS[flag])
            return jsonify({"status": "取得成功", "filename": filename,
                            "content": content, "flag": flag})

    except ftplib.error_perm as e:
        return jsonify({"error": f"FTP 認証エラー: {e}"}), 401
    except Exception as e:
        return jsonify({"error": str(e)}), 500


# -------------------------------------------------------
# API: SSH コマンド実行
# paramiko で SSH 接続し、コマンドを実行する
# -------------------------------------------------------
@app.route("/api/ssh", methods=["POST"])
def api_ssh():
    data = request.json or {}
    host = data.get("host", TARGETS["ssh"])
    port = int(data.get("port", 22))
    username = data.get("username", "")
    password = data.get("password", "")
    command = data.get("command", "whoami")

    if not username or not password:
        return jsonify({"error": "username と password が必要です"}), 400

    try:
        client = paramiko.SSHClient()
        # 【教育用】known_hosts チェックを無効化 (本番では絶対にやらないこと)
        client.set_missing_host_key_policy(paramiko.AutoAddPolicy())
        client.connect(host, port=port, username=username, password=password, timeout=10)

        stdin, stdout, stderr = client.exec_command(command)
        out = stdout.read().decode("utf-8", errors="replace")
        err = stderr.read().decode("utf-8", errors="replace")
        client.close()

        # SSH 侵入成功フラグ
        flag = ""
        if "FLAG{ssh_foothold_established}" in out:
            flag = "FLAG{ssh_foothold_established}"
            save_flag(flag, VALID_FLAGS[flag])

        return jsonify({"stdout": out, "stderr": err, "flag": flag})

    except paramiko.AuthenticationException:
        return jsonify({"error": "SSH 認証失敗: ユーザー名またはパスワードが間違っています"}), 401
    except Exception as e:
        return jsonify({"error": str(e)}), 500


# -------------------------------------------------------
# API: フラグ提出
# -------------------------------------------------------
@app.route("/api/flag", methods=["POST"])
def api_flag():
    data = request.json or {}
    flag = data.get("flag", "").strip()

    if flag in VALID_FLAGS:
        save_flag(flag, VALID_FLAGS[flag])
        flags = load_flags()
        return jsonify({
            "valid": True,
            "stage": VALID_FLAGS[flag],
            "score": len(flags),
            "total": len(VALID_FLAGS),
        })
    return jsonify({"valid": False, "message": "フラグが正しくありません"}), 400


# -------------------------------------------------------
# API: コマンドインジェクション・Web シェルのフラグ自動検出
# -------------------------------------------------------
@app.route("/api/check_flag", methods=["POST"])
def api_check_flag():
    data = request.json or {}
    text = data.get("text", "")
    found = []
    for flag, stage in VALID_FLAGS.items():
        if flag in text:
            save_flag(flag, stage)
            found.append({"flag": flag, "stage": stage})
    return jsonify({"found": found})


# -------------------------------------------------------
# API: Web シェルアップロード (exploit.html から使用)
# attacker-ui がターゲットの /upload に multipart でファイルを送る
# -------------------------------------------------------
@app.route("/api/shell_upload", methods=["POST"])
def api_shell_upload():
    data = request.json or {}
    code = data.get("code", "")
    filename = data.get("filename", "shell.py")

    if not code:
        return jsonify({"error": "code が必要です"}), 400

    try:
        import io as _io
        file_obj = _io.BytesIO(code.encode())
        file_obj.name = filename
        resp = requests.post(
            f"http://{TARGETS['web']}/upload",
            files={"file": (filename, file_obj, "text/plain")},
            timeout=10,
        )
        return jsonify({"status": "アップロード成功", "filename": filename,
                        "server_response": resp.text})
    except Exception as e:
        return jsonify({"error": str(e)}), 500


# -------------------------------------------------------
# API: ナビバー用スコア取得
# -------------------------------------------------------
@app.route("/api/nav_score")
def api_nav_score():
    flags = load_flags()
    return jsonify({"score": len(flags), "total": len(VALID_FLAGS)})


if __name__ == "__main__":
    FLAGS_FILE.parent.mkdir(parents=True, exist_ok=True)
    app.run(host="0.0.0.0", port=5000, debug=False)
