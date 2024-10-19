#/bin/bash
systemctl stop discordbot.service
mkdir /tmp/begaydocrim.es/git
cd /tmp/begaydocrim.es/git
git clone -q https://github.com/trixiewasanegg/begaydocrim.es.git
cd begaydocrim.es/
cp PUBLIC_HTML/* /var/www/begaydocrim.es/html
cp DISCORD_BOT/* /var/www/begaydocrim.es/bot
cp DISCORD_BOT/discordbot.service /etc/systemd/system
systemctl daemon-reload
systemctl start discordbot.service
rm -rf /tmp/begaydocrim.es/git/*