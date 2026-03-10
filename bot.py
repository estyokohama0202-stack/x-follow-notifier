import requests
import json
import os
import snscrape.modules.twitter as sntwitter

TARGET = "shizenboueigun"
WEBHOOK = os.getenv("DISCORD_WEBHOOK")
STATE_FILE = "following.json"


def get_following():

    users = []

    scraper = sntwitter.TwitterUserScraper(TARGET)

    for i, user in enumerate(scraper.get_items()):

        if i > 300:
            break

        users.append({
            "username": user.username,
            "name": user.displayname,
            "icon": user.profileImageUrl
        })

    return users


def send_embed(user, mode):

    if mode == "follow":
        title = "🆕 新しくフォローしました"
        color = 3066993

    elif mode == "unfollow":
        title = "❌ フォロー解除しました"
        color = 15158332

    else:
        title = "👀 最近のフォロー"
        color = 3447003

    embed = {
        "title": title,
        "description": f"[{user['name']} (@{user['username']})](https://x.com/{user['username']})",
        "color": color,
        "thumbnail": {
            "url": user["icon"]
        },
        "footer": {
            "text": "X Follow Monitor"
        }
    }

    requests.post(WEBHOOK, json={"embeds": [embed]})


def main():

    following = get_following()

    usernames = [u["username"] for u in following]

    if os.path.exists(STATE_FILE):
        with open(STATE_FILE) as f:
            old = json.load(f)
    else:
        old = None

    if old is None:

        for user in following[:10]:
            send_embed(user, "first")

    else:

        new = [u for u in following if u["username"] not in old]
        removed = [u for u in old if u not in usernames]

        for user in new:
            send_embed(user, "follow")

        for user in removed:
            fake = {
                "username": user,
                "name": user,
                "icon": f"https://unavatar.io/twitter/{user}"
            }
            send_embed(fake, "unfollow")

    with open(STATE_FILE, "w") as f:
        json.dump(usernames, f)


if __name__ == "__main__":
    main()
