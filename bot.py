import requests
import json
import os
import re

TARGET = "shizenboueigun"
WEBHOOK = os.getenv("DISCORD_WEBHOOK")
STATE_FILE = "following.json"


def get_following():

    url = f"https://x.com/{TARGET}/following"

    headers = {
        "User-Agent": "Mozilla/5.0"
    }

    r = requests.get(url, headers=headers)

    users = re.findall(r'"/([A-Za-z0-9_]+)/followers"', r.text)

    users = list(set(users))

    result = []

    for u in users:

        result.append({
            "username": u,
            "name": u,
            "icon": f"https://unavatar.io/twitter/{u}"
        })

    return result


def send_embed(title, user, color):

    embed = {
        "title": title,
        "description": f"[{user['name']} (@{user['username']})](https://x.com/{user['username']})",
        "color": color,
        "thumbnail": {
            "url": user["icon"]
        }
    }

    requests.post(WEBHOOK, json={"embeds":[embed]})


def load_state():

    if os.path.exists(STATE_FILE):

        with open(STATE_FILE) as f:
            return json.load(f)

    return None


def save_state(data):

    with open(STATE_FILE,"w") as f:
        json.dump(data,f)


def main():

    following = get_following()

    usernames = [u["username"] for u in following]

    old = load_state()

    if old is None:

        for user in following[:10]:
            send_embed("👀 最近のフォロー",user,3447003)

    else:

        new = [u for u in following if u["username"] not in old]
        removed = [u for u in old if u not in usernames]

        for user in new:
            send_embed("🆕 新しくフォローしました",user,3066993)

        for user in removed:

            fake = {
                "username":user,
                "name":user,
                "icon":f"https://unavatar.io/twitter/{user}"
            }

            send_embed("❌ フォロー解除しました",fake,15158332)

    save_state(usernames)


if __name__ == "__main__":
    main()
