FROM alpine:3.19

# OpenSSH サーバーをインストール
RUN apk add --no-cache openssh bash

# SSH ホストキーを生成
RUN ssh-keygen -A

# setup.sh でユーザー作成・フラグ配置
COPY setup.sh /setup.sh
RUN chmod +x /setup.sh && /setup.sh

# SSH 設定: パスワード認証を許可 (【脆弱性】デフォルトでは無効だが有効化)
RUN sed -i 's/#PasswordAuthentication yes/PasswordAuthentication yes/' /etc/ssh/sshd_config && \
    sed -i 's/PasswordAuthentication no/PasswordAuthentication yes/' /etc/ssh/sshd_config && \
    echo "PasswordAuthentication yes" >> /etc/ssh/sshd_config && \
    echo "PermitRootLogin no" >> /etc/ssh/sshd_config

EXPOSE 22

# バナー設定: バージョン情報を含む (偵察で取得可能)
RUN echo "Banner /etc/ssh/hacklab_banner" >> /etc/ssh/sshd_config
COPY banner.txt /etc/ssh/hacklab_banner

CMD ["/usr/sbin/sshd", "-D"]
