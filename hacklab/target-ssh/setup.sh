#!/bin/sh
# SSH サーバー初期設定スクリプト
# 【脆弱性】弱いパスワード "dev2024!" を設定

# developer ユーザーを作成
adduser -D -s /bin/bash developer

# 【脆弱性】パスワードをハードコード: dev2024!
# FTP の notes.txt に ROT13 エンコードで記載されているヒントから解読可能
echo "developer:dev2024!" | chpasswd

# ホームディレクトリにフラグを配置
mkdir -p /home/developer
cat > /home/developer/flag.txt << 'EOF'
おめでとうございます！SSH への侵入に成功しました。

FLAG{ssh_foothold_established}

【次のステップ】
このサーバーで何ができるか探索してみましょう:
  - cat /etc/passwd     (ユーザー一覧)
  - ls /home            (他のユーザーのホームディレクトリ)
  - sudo -l             (sudo 権限の確認)
  - find / -perm -4000  (SUID ビットが立ったファイルの探索)
EOF

# /root にも隠しフラグ (権限昇格チャレンジ用)
cat > /root/root_flag.txt << 'EOF'
ここまで辿り着いたあなたは本物のハッカーです！

FLAG{privilege_escalation_bonus}

ヒント: このフラグを読めたなら、root 権限を取得できています。
       実際の侵入では権限昇格 (Privilege Escalation) が重要なフェーズです。
EOF

# ホームディレクトリの権限設定
chown -R developer:developer /home/developer
chmod 644 /home/developer/flag.txt

echo "[setup.sh] SSH サーバー初期設定完了"
