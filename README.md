# Quick Start

* Go to https://www.reddit.com/prefs/apps/ and create a new **script** app.
* Enter all relevant information to `praw.py`
* Install dependencies (praw and requests), e.g. with [virtualenv](https://virtualenv.pypa.io/en/stable/) and test script with:
```
# Create virtual enviorment for python
virtualenv .venv

# Activate enviorment and install requirements (praw and requests)
source .venv/bin/activate
pip install -r requirements.txt

python undelete_bot.py
```

# Long term usage (with systemd)
1. Place all files in `/var/www/undelete`
1. Copy the service file with `cp /var/www/undelete/undelete.service /etc/systemd/system/undelete.service`
1. Start service with `sudo systemctl start undelete.service`

Show logs with `journalctl -u undelete.service`
