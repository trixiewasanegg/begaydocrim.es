#/bin/bash
systemctl stop 
cd /home/trixie/begaydocri.mes/
git pull -q
cp PUBLIC_HTML/* /var/www/begaydocri.mes/html