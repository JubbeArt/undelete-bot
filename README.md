# Quick Start

1. Go to https://www.reddit.com/prefs/apps/ and create a new **script** app.
1. Enter all relevant information to `secrets.py` (for undelete) or `longtail_secret.py` (for longtail).
1. Test the script with `python3 undelete_bot.py`, it will print removed posts if it finds any

# Long term usage (with systemd)
1. Place all files in `/var/www/undelete`
1. Copy the service file with `cp /var/www/undelete/undelete.service /etc/systemd/system/undelete.service`
1. Start service with `sudo systemctl start undelete.service`

Show logs with `journalctl -u undelete.service`
