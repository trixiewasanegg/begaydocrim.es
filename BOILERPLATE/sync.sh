#/bin/bash
systemctl stop discordbot.service
mkdir -p /tmp/begaydocrim.es/git
cd /tmp/begaydocrim.es/git
git clone -q https://github.com/trixiewasanegg/begaydocrim.es.git
cd begaydocrim.es/
cp -r PUBLIC_HTML/* /var/www/begaydocrim.es/html
cp -r DISCORD_BOT/* /var/www/begaydocrim.es/bot
sudo cp DISCORD_BOT/discordbot.service /etc/systemd/system
systemctl daemon-reload
systemctl start discordbot.service
rm -rf /tmp/begaydocrim.es/git/*