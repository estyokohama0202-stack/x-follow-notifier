import os
os.system("playwright install chromium")

import asyncio
import json
import requests
from playwright.async_api import async_playwright

TARGET = "shizenboueigun"

DISCORD_WEBHOOK = os.getenv("DISCORD_WEBHOOK")
X_USER = os.getenv("X_USER")
X_PASS = os.getenv("X_PASS")

STATE_FILE = "following.json"
COOKIE_FILE = "cookies.json"


async def login(page):

    await page.goto("https://x.com/login")

    await page.fill('input[name="text"]', X_USER)
    await page.keyboard.press("Enter")

    await page.wait_for_timeout(2000)

    await page.fill('input[name="password"]', X_PASS)
    await page.keyboard.press("Enter")

    await page.wait_for_timeout(5000)


async def get_following():

    users = []

    async with async_playwright() as p:

        browser = await p.chromium.launch(
            headless=True,
            args=["--no-sandbox", "--disable-dev-shm-usage"]
        )

        context = await browser.new_context()
        page = await context.new_page()

        # cookie login
        if os.path.exists(COOKIE_FILE):

            cookies = json.load(open(COOKIE_FILE))
            await context.add_cookies(cookies)

        else:

            await login(page)
            cookies = await context.cookies()
            json.dump(cookies, open(COOKIE_FILE, "w"))

        await page.goto(f"https://x.com/{TARGET}/following")

        await page.wait_for_timeout(5000)

        # スクロールして読み込み
        for i in range(15):

            await page.mouse.wheel(0, 3000)
            await page.wait_for_timeout(1500)

        links = await page.query_selector_all("a[href^='/']")

        for link in links:

            href = await link.get_attribute("href")

            if not href:
                continue

            if href.count("/") != 1:
                continue

            username = href.replace("/", "")

            if username in ["home","explore","notifications","messages","login"]:
                continue

            if username == TARGET:
                continue

            users.append(username)

        await browser.close()

    return list(set(users))[:300]
    
def get_icon(username):

    return f"https://unavatar.io/twitter/{username}"


def send_embed(title, user, color):

    icon = f"https://unavatar.io/twitter/{user}"

    embed = {
        "title": title,
        "description": f"[@{user}](https://x.com/{user})",
        "color": color,
        "thumbnail": {
            "url": icon
        },
        "author": {
            "name": user,
            "url": f"https://x.com/{user}",
            "icon_url": icon
        },
        "footer": {
            "text": "X Follow Monitor"
        }
    }

    requests.post(DISCORD_WEBHOOK, json={"embeds":[embed]})


def load_state():

    if os.path.exists(STATE_FILE):

        return json.load(open(STATE_FILE))

    return None


def save_state(data):

    json.dump(data,open(STATE_FILE,"w"))


async def main():

    following = await get_following()

    old = load_state()

    if old is None:

        for user in following[:10]:

            send_embed("👀 最近のフォロー",user,3447003)

    else:

        new = [u for u in following if u not in old]
        removed = [u for u in old if u not in following]

        for user in new:

            send_embed("🆕 新しくフォローしました",user,3066993)

        for user in removed:

            send_embed("❌ フォロー解除しました",user,15158332)

    save_state(following)


asyncio.run(main())
