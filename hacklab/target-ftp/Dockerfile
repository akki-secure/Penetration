FROM alpine:3.19

# vsftpd: シンプルな FTP サーバー
RUN apk add --no-cache vsftpd

# 匿名ユーザー用ディレクトリ
RUN mkdir -p /var/ftp/pub && chmod 755 /var/ftp/pub

# vsftpd 設定ファイルをコピー
COPY vsftpd.conf /etc/vsftpd/vsftpd.conf

# 公開ファイルをコピー (認証情報ヒント入り)
COPY pub/ /var/ftp/pub/

# FTP ポート (パッシブモード用に範囲も開ける)
EXPOSE 21 30000-30009

CMD ["vsftpd", "/etc/vsftpd/vsftpd.conf"]
