import os
os.system("playwright install chromium")

import asyncio
import json
import requests
from playwright.async_api import async_playwright

TARGET = "shizenboueigun"

WEBHOOK = os.getenv("DISCORD_WEBHOOK")
X_USER = os.getenv("X_USER")
X_PASS = os.getenv("X_PASS")

STATE_FILE = "following.json"
COOKIE_FILE = "cookies.json"


def send_embed(title,user,color):

    embed={
        "title":title,
        "description":f"[{user['name']} (@{user['username']})](https://x.com/{user['username']})",
        "color":color,
        "thumbnail":{"url":user["icon"]}
    }

    requests.post(WEBHOOK,json={"embeds":[embed]})


async def login(page):

    print("ログイン実行")

    await page.goto("https://x.com/i/flow/login")

    await page.fill('input[name="text"]',X_USER)
    await page.keyboard.press("Enter")

    await page.wait_for_timeout(2000)

    await page.fill('input[name="password"]',X_PASS)
    await page.keyboard.press("Enter")

    await page.wait_for_timeout(5000)


async def get_following():

    users=[]

    async with async_playwright() as p:

        browser=await p.chromium.launch(
            headless=True,
            args=["--no-sandbox","--disable-dev-shm-usage"]
        )

        context=await browser.new_context()
        page=await context.new_page()

        # cookie読み込み
        if os.path.exists(COOKIE_FILE):

            cookies=json.load(open(COOKIE_FILE))
            await context.add_cookies(cookies)

        await page.goto(f"https://x.com/{TARGET}/following")

        await page.wait_for_timeout(4000)

        # 未ログインチェック
        if "login" in page.url:

            print("cookie期限切れ → 再ログイン")

            await login(page)

            cookies=await context.cookies()
            json.dump(cookies,open(COOKIE_FILE,"w"))

            await page.goto(f"https://x.com/{TARGET}/following")
            await page.wait_for_timeout(4000)

        # スクロール
        for _ in range(80):

            await page.mouse.wheel(0,4000)
            await page.wait_for_timeout(800)

        cells=await page.query_selector_all('[data-testid="UserCell"]')

        for cell in cells:

            try:

                link=await cell.query_selector("a[href^='/']")
                href=await link.get_attribute("href")
                username=href.replace("/","")

                name_el=await cell.query_selector("div[dir='ltr'] span")
                name=await name_el.inner_text()

                icon_el=await cell.query_selector("img")
                icon=await icon_el.get_attribute("src")

                users.append({
                    "username":username,
                    "name":name,
                    "icon":icon
                })

            except:
                pass

        await browser.close()

    # 重複削除
    seen=set()
    result=[]

    for u in users:

        if u["username"] not in seen:

            seen.add(u["username"])
            result.append(u)

    return result


def load_state():

    if os.path.exists(STATE_FILE):
        return json.load(open(STATE_FILE))

    return []


def save_state(data):

    json.dump(data,open(STATE_FILE,"w"))


async def main():

    following=await get_following()

    print("取得フォロー数:",len(following))

    if len(following)==0:
        print("フォロー取得失敗")
        return

    usernames=[u["username"] for u in following]

    old=load_state()

    # 🔹最新10フォロー通知
    for user in following[:10]:
        send_embed("👀 最近のフォロー",user,3447003)

    # 🔹新フォロー
    new=[u for u in following if u["username"] not in old]

    for user in new:
        send_embed("🆕 新しくフォローしました",user,3066993)

    # 🔹フォロー解除
    removed=[u for u in old if u not in usernames]

    for user in removed:

        fake={
            "username":user,
            "name":user,
            "icon":f"https://unavatar.io/twitter/{user}"
        }

        send_embed("❌ フォロー解除しました",fake,15158332)

    save_state(usernames)


asyncio.run(main())
