# BeGay-DoCrim.Es

## v1.0 - Initial Release

Repo for development of my blog, [begay-docrim.es](https://begay-docrim.es)

Intended to replace my Wordpress blog [TrixiesManyThoughts.wordpress.com](https://TrixiesManyThoughts.wordpress.com) after the WP-Engine Fiasco.

## Stack Breakdown
### Front end
- Relatively raw HTML & CSS
- [md-block](https://github.com/leaverou/md-block) for markdown formatting
- JQuery to pull files together
- NGINX

### Back end
- CMS using a discord server
- Python Core
- Libwebp-dev
- [discord.py](https://github.com/Rapptz/discord.py) for interfacing with the discord server
- [pytz](https://pypi.org/project/pytz/) for datetime timezone shit
- [pillow](https://github.com/python-pillow/Pillow) for image compression

## Installation & Dependencies

### Daemon loading
1. Edit the discordbot.service file to be the appropriate user.
2. Copy discordbot.service to /etc/systemd/system then run the following commands
```
sudo systemctl daemon-reload && sudo systemctl enable discordbot.service && sudo systemctl start discordbot.service
```