import os
import json
import requests
import time

TARGET = "shizenboueigun"
WEBHOOK = os.getenv("DISCORD_WEBHOOK")

STATE_FILE = "following.json"


def load_cookies():

    cookies = {}

    with open("cookies.txt") as f:

        for line in f:

            if line.startswith("#"):
                continue

            parts = line.strip().split("\t")

            if len(parts) >= 7:

                cookies[parts[5]] = parts[6]

    return cookies


def get_following():

    cookies = load_cookies()

    headers = {
        "authorization": "Bearer AAAAAAAAAAAAAAAAAAAAANRILgAAAAAA"
    }

    url = f"https://api.twitter.com/1.1/friends/list.json?screen_name={TARGET}&count=200"

    r = requests.get(url, headers=headers, cookies=cookies)

    data = r.json()

    users = []

    for u in data["users"]:

        users.append({
            "name": u["name"],
            "username": u["screen_name"],
            "icon": u["profile_image_url_https"]
        })

    return users


def send_embed(user, title, color):

    embed = {
        "title": title,
        "description": f"[{user['name']} (@{user['username']})](https://x.com/{user['username']})",
        "color": color,
        "thumbnail": {"url": user["icon"]}
    }

    requests.post(WEBHOOK, json={"embeds":[embed]})

    time.sleep(1)


def load_state():

    if os.path.exists(STATE_FILE):

        with open(STATE_FILE) as f:

            return json.load(f)

    return []


def save_state(data):

    with open(STATE_FILE,"w") as f:

        json.dump(data,f)


def main():

    following = get_following()

    usernames = [u["username"] for u in following]

    old = load_state()

    for user in following[:10]:

        send_embed(user,"🆕 最近のフォロー",3447003)

    new = [u for u in following if u["username"] not in old]

    for user in new:

        send_embed(user,"🆕 新しくフォローしました",3066993)

    removed = [u for u in old if u not in usernames]

    for user in removed:

        fake = {
            "username": user,
            "name": user,
            "icon": f"https://unavatar.io/twitter/{user}"
        }

        send_embed(fake,"❌ フォロー解除しました",15158332)

    save_state(usernames)


if __name__ == "__main__":
    main()
