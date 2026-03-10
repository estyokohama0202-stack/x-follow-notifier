import requests
import json
import os

TARGET = "shizenboueigun"
WEBHOOK = os.getenv("DISCORD_WEBHOOK")

STATE_FILE = "following.json"


def send_embed(user,title,color):

    embed={
        "title":title,
        "description":f"[{user['name']} (@{user['username']})](https://x.com/{user['username']})",
        "color":color,
        "thumbnail":{"url":user["icon"]}
    }

    requests.post(WEBHOOK,json={"embeds":[embed]})


def get_user_id():

    try:

        url=f"https://cdn.syndication.twimg.com/widgets/followbutton/info.json?screen_names={TARGET}"

        r=requests.get(url,timeout=10)

        data=r.json()

        return data[0]["id_str"]

    except:

        print("ユーザーID取得失敗")

        return None


def get_following():

    user_id=get_user_id()

    if not user_id:
        return []

    api=f"https://api.twitter.com/1.1/friends/list.json?user_id={user_id}&count=200"

    headers={
        "authorization":"Bearer AAAAAAAAAAAAAAAAAAAAANRILgAAAAAA",
        "user-agent":"Mozilla/5.0"
    }

    try:

        data=requests.get(api,headers=headers,timeout=10).json()

    except:

        print("フォロー取得失敗")
        return []

    users=[]

    for u in data.get("users",[]):

        users.append({
            "username":u["screen_name"],
            "name":u["name"],
            "icon":u["profile_image_url_https"].replace("_normal","")
        })

    print("取得フォロー数:",len(users))

    return users


def load_state():

    if os.path.exists(STATE_FILE):

        return json.load(open(STATE_FILE))

    return []


def save_state(data):

    json.dump(data,open(STATE_FILE,"w"))


def main():

    following=get_following()

    if not following:

        print("フォロー取得失敗")
        return

    usernames=[u["username"] for u in following]

    old=load_state()

    print("最新フォロー送信")

    for user in following[:10]:

        send_embed(user,"🆕 最近のフォロー",3447003)

    new=[u for u in following if u["username"] not in old]

    for user in new:

        send_embed(user,"🆕 新しくフォローしました",3066993)

    removed=[u for u in old if u not in usernames]

    for user in removed:

        fake={
            "username":user,
            "name":user,
            "icon":f"https://unavatar.io/twitter/{user}"
        }

        send_embed(fake,"❌ フォロー解除しました",15158332)

    save_state(usernames)


if __name__=="__main__":

    main()
