import asyncio
from playwright.async_api import async_playwright

async def main():

    async with async_playwright() as p:

        browser = await p.chromium.launch(headless=False)

        context = await browser.new_context()

        page = await context.new_page()

        await page.goto("https://x.com/login")

        print("Xにログインしてください")

        input("ログイン完了後 Enter")

        await context.storage_state(path="cookies.json")

        print("cookies.json 保存完了")

        await browser.close()

asyncio.run(main())
