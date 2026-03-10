import asyncio
import json
import os
import requests
from playwright.async_api import async_playwright

TARGET = "shizenboueigun"

WEBHOOK = os.getenv("DISCORD_WEBHOOK")
X_USER = os.getenv("X_USER")
X_PASS = os.getenv("X_PASS")

STATE_FILE = "following.json"
COOKIE_FILE = "cookies.json"


def send_embed(title, user, color):

    icon = f"https://unavatar.io/twitter/{user}"

    embed = {
        "title": title,
        "description": f"[@{user}](https://x.com/{user})",
        "color": color,
        "thumbnail": {"url": icon},
        "author": {
            "name": user,
            "icon_url": icon,
            "url": f"https://x.com/{user}"
        }
    }

    requests.post(WEBHOOK, json={"embeds":[embed]})


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
            args=["--no-sandbox","--disable-dev-shm-usage"]
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
            json.dump(cookies, open(COOKIE_FILE,"w"))

        await page.goto(f"https://x.com/{TARGET}/following")

        await page.wait_for_timeout(4000)

        # スクロール
        for i in range(15):

            await page.mouse.wheel(0,3000)
            await page.wait_for_timeout(1000)

        cells = await page.query_selector_all('[data-testid="UserCell"]')

        for cell in cells:

            link = await cell.query_selector("a[href^='/']")

            if not link:
                continue

            href = await link.get_attribute("href")
            username = href.replace("/","")

            if username != TARGET:

                users.append(username)

        await browser.close()

    return list(dict.fromkeys(users))


def load_state():

    if os.path.exists(STATE_FILE):

        return json.load(open(STATE_FILE))

    return None


def save_state(data):

    json.dump(data, open(STATE_FILE,"w"))


async def main():

    following = await get_following()

    # 接続時毎回最新10フォロー
    for user in following[:10]:
        send_embed("👀 最近のフォロー", user, 3447003)

    old = load_state()

    if old:

        new = [u for u in following if u not in old]
        removed = [u for u in old if u not in following]

        for user in new:
            send_embed("🆕 新しくフォローしました", user, 3066993)

        for user in removed:
            send_embed("❌ フォロー解除しました", user, 15158332)

    save_state(following)


asyncio.run(main())
