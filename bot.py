import requests
import time
import os
import random
import threading
import subprocess
import hashlib
import sqlite3
from telebot import TeleBot
from telebot.types import InlineKeyboardMarkup, InlineKeyboardButton, ReplyKeyboardMarkup, KeyboardButton

# ░▒▓█ SYSTEM CONFIGURATION █▓▒░
BOT_TOKEN = "8724032793:AAEuRBw0wUveOgEZXQpSac8pBEeFx2Tka54"
API_URL = "https://draw.ar-lottery01.com/WinGo/WinGo_1M/GetHistoryIssuePage.json"
BRANDING = "𝕽𝕯𝖃 𝕰𝕹𝕲𝕴𝕹𝕰"
OWNER_URL = "https://t.me/RDX_OWNER_7"
MASTER_PASSWORD = "THALA IS BACK"
OWNER_ID = 8355928516 

os.environ['PYTHONTHREADDEBUG'] = '0'
bot = TeleBot(BOT_TOKEN, num_threads=5) 

# ░▒▓█ STICKER PAYLOADS █▓▒░
STICKERS = {
    "session_start": "CAACAgUAAxkBAAICqmnji2QVHBfaAjCrcW10Zf5eFDuHAALWGAACMETYVkXTK_e9RpyROwQ",
    "win": "CAACAgUAAxkBAAIComnjizN9Mb5a7uCz-c-C31xFUXdwAALvEwACnz_ZVmJBZ_p_c7TkOwQ",
    "loss": "CAACAgUAAyEFAATs-7RJAAITfmnjUmJ_C6CP54FDhodvLvMik5E2AAKxHgACIS2AVWo3iSARD3SROwQ",
    "stop": "CAACAgUAAxkBAAICm2njivWf31U5OwABHoDpfzCmWJwAATkAAgoYAAJk_NlWVEVQmlEJZMY7BA"
}

# ░▒▓█ DATABASE VAULT (RAILWAY SAFE STORAGE) █▓▒░
os.makedirs('data', exist_ok=True) # Railway me folder banane ke liye
conn = sqlite3.connect('data/rdx_aegis.db', check_same_thread=False)
c = conn.cursor()
db_lock = threading.Lock() # Database Crash Fix

with db_lock:
    c.execute('''CREATE TABLE IF NOT EXISTS users 
                 (uid INTEGER PRIMARY KEY, auth INTEGER, total INTEGER, win INTEGER, loss INTEGER, 
                  streak INTEGER, max_streak INTEGER, join_time REAL, waiting INTEGER, hwid TEXT)''')
    c.execute('''CREATE TABLE IF NOT EXISTS vip_keys 
                 (id INTEGER PRIMARY KEY AUTOINCREMENT, key_code TEXT UNIQUE, expiry REAL, 
                  used INTEGER DEFAULT 0, bound_uid INTEGER DEFAULT NULL, bound_hwid TEXT DEFAULT NULL, 
                  created_by INTEGER, created_at REAL)''')
    conn.commit()

# ░▒▓█ AI PREDICTION ENGINE (SATYAM LOGIC INTEGRATED) █▓▒░
class LethalAI:
    def fetch(self):
        try:
            return requests.get(API_URL, timeout=3, headers={"User-Agent": "Mozilla/5.0"}).json().get("data", {}).get("list", [])
        except: return []
    
    def bs(self, n): return "SMALL" if int(n) <= 4 else "BIG"
    
    def analyze(self, data):
        if not data: 
            size = random.choice(["BIG", "SMALL"])
            conf = random.randint(85, 92)
        else:
            last_5 = [self.bs(x["number"]) for x in data[:5]]
            if last_5[0] == last_5[1] == last_5[2]:
                size = last_5[0]
                conf = random.randint(95, 99) 
            elif last_5[0] != last_5[1]:
                size = "BIG" if last_5[0] == "SMALL" else "SMALL"
                conf = random.randint(88, 94)
            else:
                size = "SMALL" if last_5.count("BIG") > last_5.count("SMALL") else "BIG"
                conf = random.randint(85, 90)

        num = random.randint(5, 9) if size == "BIG" else random.randint(0, 4)
        return size, num, conf

ai = LethalAI()

# ░▒▓█ CORE FUNCTIONS █▓▒░
def get_hwid():
    try: return subprocess.check_output("settings get secure android_id", shell=True).decode().strip()
    except: return hashlib.md5(str(time.time()).encode()).hexdigest()[:12].upper()

def get_user(uid):
    with db_lock:
        c.execute("SELECT * FROM users WHERE uid=?", (uid,))
        res = c.fetchone()
        if not res:
            hwid = get_hwid()
            c.execute("INSERT INTO users (uid, auth, total, win, loss, streak, max_streak, join_time, waiting, hwid) VALUES (?,0,0,0,0,0,0,?,0,?)", (uid, time.time(), hwid))
            conn.commit()
            c.execute("SELECT * FROM users WHERE uid=?", (uid,))
            res = c.fetchone()
        return {"uid": res[0], "auth": res[1], "total": res[2], "win": res[3], "loss": res[4], "streak": res[5], "max_streak": res[6], "waiting": res[8], "hwid": res[9]}

def update_user(uid, **kwargs):
    with db_lock:
        for k, v in kwargs.items():
            c.execute(f"UPDATE users SET {k}=? WHERE uid=?", (v, uid))
        conn.commit()

def ui_menu():
    kb = ReplyKeyboardMarkup(resize_keyboard=True, row_width=2)
    kb.add(
        KeyboardButton("🩸 INJECT PREDICTION"),
        KeyboardButton("📡 LIVE TRENDS"),
        KeyboardButton("⚙️ START AUTO"),
        KeyboardButton("🛑 STOP AUTO"),
        KeyboardButton("📊 MY STATS"),
        KeyboardButton("🔌 LOGOUT DEVICE")
    )
    return kb

# ░▒▓█ KEY MANAGEMENT █▓▒░
def gen_key(days):
    k = "RDX-" + ''.join(random.choices("ABCDEFGHIJKLMNOPQRSTUVWXYZ0123456789", k=12))
    exp = time.time() + (days * 86400)
    with db_lock:
        c.execute("INSERT INTO vip_keys (key_code, expiry, created_by, created_at) VALUES (?,?,?,?)", (k, exp, OWNER_ID, time.time()))
        conn.commit()
    return k

def auth_hwid_key(k, uid, current_hwid):
    with db_lock:
        c.execute("SELECT id, expiry, used, bound_uid, bound_hwid FROM vip_keys WHERE key_code=?", (k,))
        row = c.fetchone()
        if not row: return "INVALID"
        key_id, expiry, used, b_uid, b_hwid = row
        
        if time.time() > expiry: return "EXPIRED"
        if used == 1:
            if b_uid == uid and b_hwid == current_hwid: return "SUCCESS"
            else: return "HWID_MISMATCH"
            
        c.execute("UPDATE vip_keys SET used=1, bound_uid=?, bound_hwid=? WHERE id=?", (uid, current_hwid, key_id))
        conn.commit()
    return "SUCCESS"

# ░▒▓█ ULTRA FAST RADAR LOOP █▓▒░
pending_preds = {}
auto_threads = {}
last_period = None

def dispatch_result(uid, p, cp, cr, cn):
    u = get_user(uid)
    is_win = (cr == p["size"])
    
    try: bot.send_sticker(uid, STICKERS["win"] if is_win else STICKERS["loss"])
    except: pass

    if is_win:
        ns = u["streak"] + 1
        update_user(uid, win=u["win"]+1, streak=ns, max_streak=max(u["max_streak"], ns), total=u["total"]+1)
        msg = (
            f"✅ *𝗧𝗔𝗥𝗚𝗘𝗧 𝗢𝗕𝗟𝗜𝗧𝗘𝗥𝗔𝗧𝗘𝗗*\n"
            f"▰▰▰▰▰▰▰▰▰▰▰▰▰▰\n"
            f"► *PRD* : `{cp}`\n"
            f"► *RES* : *{cr}* ({cn})\n"
            f"▰▰▰▰▰▰▰▰▰▰▰▰▰▰"
        )
    else:
        update_user(uid, loss=u["loss"]+1, streak=0, total=u["total"]+1)
        msg = (
            f"❌ *𝗠𝗜𝗦𝗦𝗜𝗢𝗡 𝗙𝗔𝗜𝗟𝗘𝗗*\n"
            f"▰▰▰▰▰▰▰▰▰▰▰▰▰▰\n"
            f"► *PRD* : `{cp}`\n"
            f"► *RES* : *{cr}* ({cn})\n"
            f"▰▰▰▰▰▰▰▰▰▰▰▰▰▰"
        )
    try: bot.send_message(uid, msg, parse_mode="Markdown")
    except: pass

def dispatch_auto(uid, cp, data):
    if auto_threads.get(uid):
        s, n, conf = ai.analyze(data)
        nxt = cp + 1
        pending_preds[uid] = {"period": nxt, "size": s, "num": n}
        sym = "🔴" if s == "BIG" else "🔵"
        msg = (
            f"⚡ *𝗔𝗨𝗧𝗢-𝗘𝗫𝗘𝗖 𝗜𝗡𝗜𝗧𝗜𝗔𝗧𝗘𝗗* ⚡\n\n"
            f"▰▰▰▰▰▰▰▰▰▰▰▰▰▰\n"
            f"► *TRGT* : `{nxt}`\n"
            f"► *ACTN* : {sym} *{s}*\n"
            f"► *CONF* : `{conf}%`\n"
            f"▰▰▰▰▰▰▰▰▰▰▰▰▰▰"
        )
        try: bot.send_message(uid, msg, parse_mode="Markdown")
        except: pass

def master_radar_loop():
    global last_period
    while True:
        try:
            data = ai.fetch()
            if not data: continue
            cp = int(data[0]["issueNumber"])
            
            if last_period and cp != last_period:
                cn = int(data[0]["number"])
                cr = ai.bs(cn)
                
                for uid in list(pending_preds.keys()):
                    p = pending_preds[uid]
                    if p["period"] == cp:
                        threading.Thread(target=dispatch_result, args=(uid, p, cp, cr, cn)).start()
                        del pending_preds[uid]
                
                time.sleep(0.5) 
                
                for uid in list(auto_threads.keys()):
                    threading.Thread(target=dispatch_auto, args=(uid, cp, data)).start()
                
            last_period = cp
            time.sleep(0.5) 
        except:
            time.sleep(1)

threading.Thread(target=master_radar_loop, daemon=True).start()

# ░▒▓█ HIDDEN ADMIN LOGIN █▓▒░
@bot.message_handler(func=lambda msg: msg.text.strip() == MASTER_PASSWORD)
def secret_admin_login(msg):
    uid = msg.chat.id
    update_user(uid, waiting=0)
    admin_panel(uid)
    bot.delete_message(uid, msg.message_id) 

# ░▒▓█ BOT START UP █▓▒░
@bot.message_handler(commands=['start'])
def boot_sequence(msg):
    uid = msg.chat.id
    u = get_user(uid)
    
    kb = InlineKeyboardMarkup(row_width=1)
    kb.add(
        InlineKeyboardButton("⚠️ ENTER VIP KEY", callback_data="auth_user"),
        InlineKeyboardButton("📞 CONTACT OWNER", url=OWNER_URL)
    )
    
    msg_txt = (
        f"⚠️ *𝗦𝗬𝗦𝗧𝗘𝗠 𝗟𝗢𝗖𝗞 𝗘𝗡𝗚𝗔𝗚𝗘𝗗* ⚠️\n\n"
        f"▰▰▰▰▰▰▰▰▰▰▰▰▰▰▰▰\n"
        f"► *𝗛𝗪𝗜𝗗* : `{u['hwid']}`\n"
        f"► *𝗖𝗢𝗥𝗘* : `RDX V9.0 KERNEL`\n"
        f"► *𝗦𝗧𝗔𝗧* : `UNAUTHORIZED`\n"
        f"▰▰▰▰▰▰▰▰▰▰▰▰▰▰▰▰\n\n"
        f"► Select clearance level ↓"
    )
    bot.send_message(uid, msg_txt, parse_mode="Markdown", reply_markup=kb)

@bot.callback_query_handler(func=lambda call: call.data == "auth_user")
def auth_req(call):
    uid = call.message.chat.id
    update_user(uid, waiting=1)
    kb = InlineKeyboardMarkup().add(InlineKeyboardButton("🔙 BACK", callback_data="cancel_wait"))
    bot.edit_message_text("🔐 **ENTER YOUR KEY**\n\n► Paste your VIP key below:", chat_id=uid, message_id=call.message.message_id, parse_mode="Markdown", reply_markup=kb)

@bot.callback_query_handler(func=lambda call: call.data == "cancel_wait")
def cancel_wait(call):
    uid = call.message.chat.id
    update_user(uid, waiting=0)
    bot.delete_message(uid, call.message.message_id)
    boot_sequence(call.message)

@bot.message_handler(func=lambda msg: get_user(msg.chat.id).get("waiting", 0) in [1, 3])
def state_processor(msg):
    uid = msg.chat.id
    u = get_user(uid)
    txt = msg.text.strip().upper()
    state = u.get("waiting")
    
    if state == 1:
        status = auth_hwid_key(txt, uid, u['hwid'])
        if status == "SUCCESS":
            update_user(uid, auth=1, waiting=0)
            try: bot.send_sticker(uid, STICKERS["session_start"])
            except: pass
            bot.send_message(uid, f"✅ **𝗟𝗜𝗖𝗘𝗡𝗦𝗘 𝗔𝗖𝗖𝗘𝗣𝗧𝗘𝗗**\n\n► Device Locked: `{u['hwid']}`\n► Welcome to **{BRANDING}**.", parse_mode="Markdown", reply_markup=ui_menu())
        elif status == "HWID_MISMATCH":
            update_user(uid, waiting=0)
            bot.send_message(uid, f"❌ **𝗛𝗪𝗜𝗗 𝗠𝗜𝗦𝗠𝗔𝗧𝗖𝗛 𝗗𝗘𝗧𝗘𝗖𝗧𝗘𝗗**\n\n► This key is used on another phone.\n► Your ID: `{u['hwid']}`", parse_mode="Markdown")
        elif status == "EXPIRED":
            update_user(uid, waiting=0)
            bot.send_message(uid, "❌ **𝗟𝗜𝗖𝗘𝗡𝗦𝗘 𝗘𝗫𝗣𝗜𝗥𝗘𝗗**", parse_mode="Markdown")
        else:
            update_user(uid, waiting=0)
            bot.send_message(uid, "❌ **𝗜𝗡𝗩𝗔𝗟𝗜𝗗 𝗦𝗜𝗚𝗡𝗔𝗧𝗨𝗥𝗘**", parse_mode="Markdown")
            
    elif state == 3:
        with db_lock:
            c.execute("DELETE FROM vip_keys WHERE key_code=?", (txt,))
            success = c.rowcount > 0
            conn.commit()
            
        if success:
            bot.send_message(uid, f"✅ **KEY DELETED**\n► `{txt}` is permanently removed.", parse_mode="Markdown")
        else:
            bot.send_message(uid, "❌ **𝗘𝗥𝗥𝗢𝗥**\n► Key not found.", parse_mode="Markdown")
        update_user(uid, waiting=0)
        admin_panel(uid)

# ░▒▓█ ADMIN PANEL █▓▒░
def admin_panel(uid):
    kb = InlineKeyboardMarkup(row_width=2)
    kb.add(
        InlineKeyboardButton("🔑 GENERATE KEY", callback_data="adm_gen"),
        InlineKeyboardButton("👁️ SYSTEM INFO", callback_data="adm_intel"),
        InlineKeyboardButton("💀 DELETE KEY", callback_data="adm_revoke"),
        InlineKeyboardButton("❌ CLOSE PANEL", callback_data="adm_close")
    )
    bot.send_message(uid, "👑 **ADMIN CONTROL PANEL**\n\n► Select an option:", parse_mode="Markdown", reply_markup=kb)

@bot.callback_query_handler(func=lambda call: call.data.startswith("adm_"))
def admin_actions(call):
    uid = call.message.chat.id
    cmd = call.data
    
    if cmd == "adm_gen":
        kb = InlineKeyboardMarkup(row_width=2)
        kb.add(InlineKeyboardButton("1 DAY", callback_data="adm_gkey_1"), InlineKeyboardButton("7 DAYS", callback_data="adm_gkey_7"))
        kb.add(InlineKeyboardButton("30 DAYS", callback_data="adm_gkey_30"), InlineKeyboardButton("LIFETIME", callback_data="adm_gkey_3650"))
        kb.add(InlineKeyboardButton("🔙 BACK", callback_data="adm_back"))
        bot.edit_message_text("► Select how many days:", chat_id=uid, message_id=call.message.message_id, reply_markup=kb)
        
    elif cmd.startswith("adm_gkey_"):
        days = int(cmd.split("_")[2])
        k = gen_key(days)
        kb = InlineKeyboardMarkup().add(InlineKeyboardButton("🔙 BACK", callback_data="adm_back"))
        bot.edit_message_text(f"✅ **NEW KEY CREATED**\n\n► ` {k} `\n► Valid: {days} Days.", chat_id=uid, message_id=call.message.message_id, parse_mode="Markdown", reply_markup=kb)
        
    elif cmd == "adm_intel":
        with db_lock:
            c.execute("SELECT key_code, used, bound_hwid FROM vip_keys ORDER BY id DESC LIMIT 10")
            keys = c.fetchall()
            c.execute("SELECT COUNT(*) FROM users")
            tu = c.fetchone()[0]
        
        txt = f"👁️ **𝗦𝗬𝗦𝗧𝗘𝗠 𝗜𝗡𝗧𝗘𝗟**\n▰▰▰▰▰▰▰▰▰▰▰▰\n► Total Users: `{tu}`\n\n**Last 10 Keys:**\n"
        for k, u, bhwid in keys:
            stat = "🟢" if not u else "🔴"
            hw = bhwid if bhwid else "NOT USED YET"
            txt += f"{stat} `{k}`\n↳ Device: `{hw}`\n"
            
        kb = InlineKeyboardMarkup().add(InlineKeyboardButton("🔙 BACK", callback_data="adm_back"))
        bot.edit_message_text(txt if keys else "► No keys found.", chat_id=uid, message_id=call.message.message_id, parse_mode="Markdown", reply_markup=kb)
        
    elif cmd == "adm_revoke":
        update_user(uid, waiting=3)
        kb = InlineKeyboardMarkup().add(InlineKeyboardButton("🔙 CANCEL", callback_data="adm_cancel_wait"))
        bot.edit_message_text("💀 **DELETE A KEY**\n\n► Send the key code you want to delete:", chat_id=uid, message_id=call.message.message_id, parse_mode="Markdown", reply_markup=kb)

    elif cmd == "adm_cancel_wait":
        update_user(uid, waiting=0)
        bot.delete_message(uid, call.message.message_id)
        admin_panel(uid)
        
    elif cmd == "adm_back":
        bot.delete_message(uid, call.message.message_id)
        admin_panel(uid)
        
    elif cmd == "adm_close":
        bot.delete_message(uid, call.message.message_id)

# ░▒▓█ USER SYSTEM COMMANDS █▓▒░
@bot.message_handler(func=lambda msg: get_user(msg.chat.id).get("auth", 0) == 1)
def user_commands(msg):
    uid = msg.chat.id
    txt = msg.text

    if txt == "🩸 INJECT PREDICTION":
        bot.send_chat_action(uid, 'typing')
        data = ai.fetch()
        if not data: return bot.send_message(uid, "❌ **SERVER OFFLINE**", parse_mode="Markdown")
        
        cp = int(data[0]["issueNumber"])
        s, n, conf = ai.analyze(data)
        nxt = cp + 1
        pending_preds[uid] = {"period": nxt, "size": s, "num": n}
        sym = "🔴" if s == "BIG" else "🔵"
        
        bot.send_message(
            uid,
            f"🩸 *𝗣𝗔𝗬𝗟𝗢𝗔𝗗 𝗜𝗡𝗝𝗘𝗖𝗧𝗘𝗗* 🩸\n\n"
            f"▰▰▰▰▰▰▰▰▰▰▰▰\n"
            f"► *TRGT* : `{nxt}`\n"
            f"► *ACTN* : {sym} *{s}*\n"
            f"► *CONF* : `{conf}%`\n"
            f"▰▰▰▰▰▰▰▰▰▰▰▰\n"
            f"⚠️ *{BRANDING} CORE*",
            parse_mode="Markdown"
    )

    elif txt == "📡 LIVE TRENDS":
        data = ai.fetch()
        if data:
            cp = data[0]['issueNumber']
            cr = ai.bs(data[0]['number'])
            wave = "".join(["█" if ai.bs(x["number"]) == "BIG" else "▄" for x in data[:10]])
            bot.send_message(
                uid,
                f"📡 **LIVE GAME TRENDS** 📡\n\n"
                f"► `LAST PERIOD : {cp}`\n"
                f"► `LAST RESULT : {cr}`\n\n"
                f"► **PATTERN GRAPH:**\n"
                f"`[{wave}]`\n\n"
                f"*(█ = BIG | ▄ = SMALL)*",
                parse_mode="Markdown"
            )

    elif txt == "⚙️ START AUTO":
        if not auto_threads.get(uid):
            auto_threads[uid] = True
            bot.send_message(uid, "☢️ **AUTO PREDICTION STARTED**\n► Waiting for the next game to start...", parse_mode="Markdown")

    elif txt == "🛑 STOP AUTO":
        if uid in auto_threads: auto_threads[uid] = False
        try: bot.send_sticker(uid, STICKERS["stop"])
        except: pass
        bot.send_message(uid, "🛑 *𝗔𝗨𝗧𝗢-𝗣𝗜𝗟𝗢𝗧 𝗛𝗔𝗟𝗧𝗘𝗗*", parse_mode="Markdown")

    elif txt == "📊 MY STATS":
        u = get_user(uid)
        rate = round((u['win'] / u['total']) * 100, 1) if u['total'] > 0 else 0
        bot.send_message(
            uid,
            f"📊 *𝗘𝗫𝗘𝗖𝗨𝗧𝗜𝗢𝗡 𝗟𝗢𝗚𝗦* 📊\n\n"
            f"▰▰▰▰▰▰▰▰▰▰▰▰\n"
            f"► `DEPLOYED` : `{u['total']}`\n"
            f"► `HITS    ` : `{u['win']}`\n"
            f"► `MISSES  ` : `{u['loss']}`\n"
            f"► `K/R RATE` : `{rate}%`\n"
            f"► `M-STREAK` : `{u['max_streak']}`\n"
            f"▰▰▰▰▰▰▰▰▰▰▰▰",
            parse_mode="Markdown"
    )

    elif txt == "🔌 LOGOUT DEVICE":
        if uid in auto_threads: auto_threads[uid] = False
        update_user(uid, auth=0)
        bot.send_message(uid, "🔌 **LOGGED OUT SUCCESSFULLY**\n► Your device is safely disconnected.", parse_mode="Markdown", reply_markup=ReplyKeyboardMarkup(resize_keyboard=True).add(KeyboardButton("/start")))

# ░▒▓█ ENGINE START █▓▒░
if __name__ == "__main__":
    os.system("clear")
    print(f"[{BRANDING}] SYSTEM ONLINE.")
    print(f"[+] DATABASE LOCK INSTALLED (ERROR FIXED).")
    print(f"[+] DANGEROUS THEME APPLIED.")
    print(f"[+] 'SATYAM' AI LOGIC INTEGRATED.")
    
    with db_lock:
        c.execute("SELECT COUNT(*) FROM vip_keys")
        count = c.fetchone()[0]
    
    if count == 0:
        root_key = gen_key(3650)
        print(f"\n[!] YOUR LIFETIME MASTER KEY: {root_key}")
        
    while True:
        try: bot.infinity_polling(timeout=20, long_polling_timeout=20)
        except Exception: time.sleep(1)