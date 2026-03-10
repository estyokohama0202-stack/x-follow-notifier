import requests
import json
import os
import time
import snscrape.modules.twitter as sntwitter

TARGET = "shizenboueigun"
WEBHOOK = os.getenv("DISCORD_WEBHOOK")
STATE_FILE = "following.json"


def get_following():

    users = []

    try:

        scraper = sntwitter.TwitterUserScraper(TARGET)

        for i, user in enumerate(scraper.get_items()):

            if i >= 200:
                break

            users.append({
                "username": user.username,
                "name": user.displayname,
                "icon": user.profileImageUrl
            })

    except Exception as e:

        print("Fetch error:", e)

    return users


def send_embed(title, user, color):

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

    try:
        requests.post(WEBHOOK, json={"embeds": [embed]})
    except Exception as e:
        print("Discord error:", e)


def load_state():

    if os.path.exists(STATE_FILE):

        try:
            with open(STATE_FILE) as f:
                return json.load(f)
        except:
            return None

    return None


def save_state(data):

    try:
        with open(STATE_FILE,"w") as f:
            json.dump(data,f)
    except Exception as e:
        print("Save error:", e)


def main():

    print("Checking follows...")

    following = get_following()

    if not following:
        print("Failed to fetch data")
        return

    usernames = [u["username"] for u in following]

    old = load_state()

    if old is None:

        print("First run")

        for user in following[:10]:
            send_embed("👀 最近のフォロー", user, 3447003)

            time.sleep(1)

    else:

        new = [u for u in following if u["username"] not in old]
        removed = [u for u in old if u not in usernames]

        for user in new:

            send_embed("🆕 新しくフォローしました", user, 3066993)

            time.sleep(1)

        for user in removed:

            fake = {
                "username":user,
                "name":user,
                "icon":f"https://unavatar.io/twitter/{user}"
            }

            send_embed("❌ フォロー解除しました", fake, 15158332)

            time.sleep(1)

    save_state(usernames)

    print("Done")


if __name__ == "__main__":
    main()
