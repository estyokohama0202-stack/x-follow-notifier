import os
import json
import asyncio
import requests
from playwright.async_api import async_playwright

TARGET = "shizenboueigun"
WEBHOOK = os.getenv("DISCORD_WEBHOOK")

STATE_FILE = "following.json"


async def get_following():

    users = []

    async with async_playwright() as p:

        browser = await p.chromium.launch(headless=True)
        page = await browser.new_page()

        url = f"https://x.com/{TARGET}/following"

        await page.goto(url)

        await page.wait_for_timeout(5000)

        cards = await page.query_selector_all("div[data-testid='UserCell']")

        for card in cards[:20]:

            name_el = await card.query_selector("div[dir='ltr'] span")
            username_el = await card.query_selector("a")

            if name_el and username_el:

                name = await name_el.inner_text()
                href = await username_el.get_attribute("href")

                username = href.replace("/", "")

                icon_el = await card.query_selector("img")

                icon = ""
                if icon_el:
                    icon = await icon_el.get_attribute("src")

                users.append({
                    "name": name,
                    "username": username,
                    "icon": icon
                })

        await browser.close()

    print("取得フォロー数:", len(users))

    return users


def send_embed(user, title, color):

    embed = {
        "title": title,
        "description": f"[{user['name']} (@{user['username']})](https://x.com/{user['username']})",
        "color": color,
        "thumbnail": {"url": user["icon"]}
    }

    requests.post(WEBHOOK, json={"embeds": [embed]})


def load_state():

    if os.path.exists(STATE_FILE):
        return json.load(open(STATE_FILE))

    return []


def save_state(data):

    json.dump(data, open(STATE_FILE, "w"))


async def main():

    following = await get_following()

    usernames = [u["username"] for u in following]

    old = load_state()

    print("最新フォロー送信")

    for user in following[:10]:

        send_embed(user, "🆕 最近のフォロー", 3447003)

    new = [u for u in following if u["username"] not in old]

    for user in new:

        send_embed(user, "🆕 新しくフォローしました", 3066993)

    removed = [u for u in old if u not in usernames]

    for user in removed:

        fake = {
            "username": user,
            "name": user,
            "icon": f"https://unavatar.io/twitter/{user}"
        }

        send_embed(fake, "❌ フォロー解除しました", 15158332)

    save_state(usernames)


asyncio.run(main())
