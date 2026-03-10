import requests
import json
import os
import snscrape.modules.twitter as sntwitter

USERNAME = "shizenboueigun"
WEBHOOK = os.getenv("DISCORD_WEBHOOK")
STATE_FILE = "following.json"


def get_following():
    users = []
    for i, user in enumerate(sntwitter.TwitterUserScraper(USERNAME).get_items()):
        if i > 200:
            break
        users.append(user.username)
    return users


def send_embed(user, first=False):

    title = "👀 最近フォロー" if first else "🆕 新しいフォロー"

    embed = {
        "title": title,
        "description": f"[@{user}](https://x.com/{user})",
        "color": 1942002,
        "thumbnail": {
            "url": f"https://unavatar.io/twitter/{user}"
        },
        "footer": {
            "text": "X Follow Monitor"
        }
    }

    data = {
        "embeds": [embed]
    }

    requests.post(WEBHOOK, json=data)


def main():
    following = get_following()

    try:
        with open(STATE_FILE) as f:
            old = json.load(f)
    except:
        old = None

    if old is None:
        for u in following[:10]:
            send_embed(u, True)
    else:
        new = [u for u in following if u not in old]
        for u in new:
            send_embed(u)

    with open(STATE_FILE, "w") as f:
        json.dump(following, f)


if __name__ == "__main__":
    main()
