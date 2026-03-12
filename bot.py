import os
import json
import asyncio
import time
import requests
from playwright.async_api import async_playwright

TARGET = "shizenboueigun"
WEBHOOK = os.getenv("DISCORD_WEBHOOK")

STATE_FILE = "following.json"

MAX_SCROLL = 50


async def get_following():

    users = {}
    
    async with async_playwright() as p:

        browser = await p.chromium.launch(
            headless=True,
            args=["--no-sandbox", "--disable-dev-shm-usage"]
        )

        page = await browser.new_page()

        url = f"https://x.com/{TARGET}/following"

        await page.goto(url, timeout=60000)
        await page.wait_for_timeout(5000)

        last_height = 0

        for _ in range(MAX_SCROLL):

            cards = await page.query_selector_all("div[data-testid='UserCell']")

            for card in cards:

                username_el = await card.query_selector("a[href^='/']")
                name_el = await card.query_selector("div[dir='ltr'] span")
                icon_el = await card.query_selector("img")

                if not username_el:
                    continue

                href = await username_el.get_attribute("href")
                username = href.replace("/", "")

                if username in users:
                    continue

                name = username
                if name_el:
                    name = await name_el.inner_text()

                icon = ""
                if icon_el:
                    icon = await icon_el.get_attribute("src")

                users[username] = {
                    "name": name,
                    "username": username,
                    "icon": icon
                }

            await page.mouse.wheel(0, 4000)
            await page.wait_for_timeout(2000)

            height = await page.evaluate("document.body.scrollHeight")

            if height == last_height:
                break

            last_height = height

        await browser.close()

    print("取得フォロー数:", len(users))

    return list(users.values())


def send_embed(user, title, color):

    embed = {
        "title": title,
        "description": f"[{user['name']} (@{user['username']})](https://x.com/{user['username']})",
        "color": color,
        "thumbnail": {"url": user["icon"]}
    }

    try:
        requests.post(WEBHOOK, json={"embeds": [embed]})
        time.sleep(1)
    except:
        pass


def load_state():

    if os.path.exists(STATE_FILE):
        with open(STATE_FILE) as f:
            return json.load(f)

    return []


def save_state(data):

    with open(STATE_FILE, "w") as f:
        json.dump(data, f)


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
