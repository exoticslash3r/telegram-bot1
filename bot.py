#!/usr/bin/env python3
import json
import os
import time
import uuid

from telegram import (
Update,
InlineKeyboardButton,
InlineKeyboardMarkup,
)
from telegram.ext import (
ApplicationBuilder,
CommandHandler,
CallbackQueryHandler,
MessageHandler,
ContextTypes,
filters,
)

# ================= CONFIG =================
TOKEN = "8513722194:AAG7PDl_Ql5rIWggp-4kUpomzeNrQxUcjgY"
ADMIN_ID = 8522370648

PUBLISH_CODE = "XDFGA741OE380"

QUESTIONS_ACCEPT_LINK = "https://t.me/+Coo8VtQI3gBhYmFk"

# Direct image links (logo/banner)
MAIN_BANNER = "https://i.ibb.co/fGt8zQmH/banner.jpg"
ROLE_BANNER = "https://i.ibb.co/Xf9x7R39/banner.jpg"

MISSIONS_FILE = "missions.json"
TARGETS_FILE = "targets.json"
# ==========================================


# ================= STORAGE =================
def load_file(path, default):
if os.path.exists(path):
with open(path, "r", encoding="utf-8") as f:
return json.load(f)
with open(path, "w", encoding="utf-8") as f:
json.dump(default, f, indent=2)
return default.copy()

def save_file(path, data):
with open(path, "w", encoding="utf-8") as f:
json.dump(data, f, indent=2)

MISSIONS = load_file(MISSIONS_FILE, {})
TARGETS = load_file(TARGETS_FILE, {})
# ==========================================


def user_label(u):
return f"@{u.username}" if u.username else u.first_name or str(u.id)

def token():
return uuid.uuid4().hex[:8]


# ================= START =================
async def start(update: Update, context: ContextTypes.DEFAULT_TYPE):
keyboard = [
[
InlineKeyboardButton("📝 Questions", callback_data="questions"),
InlineKeyboardButton("🔌 Missions", callback_data="missions"),
],
[
InlineKeyboardButton("❌ Targets", callback_data="targets"),
InlineKeyboardButton("❌ Publish Target", callback_data="publish_target"),
],
[
InlineKeyboardButton("🎭 Role Requestor", callback_data="roles"),
InlineKeyboardButton("📰 Publish Mission", callback_data="publish_mission"),
],
]

# Send main banner (logo) with caption and menu buttons
caption = "*741 faction*\n\nAbout 741 GROUP:https://741-forum.vercel.app/."
await update.message.reply_photo(
photo=MAIN_BANNER,
caption=caption,
parse_mode="Markdown",
reply_markup=InlineKeyboardMarkup(keyboard),
)


# ================= CALLBACKS =================
async def callback_handler(update: Update, context: ContextTypes.DEFAULT_TYPE):
q = update.callback_query
await q.answer()
d = q.data
u = q.from_user

# ---------- QUESTIONS ----------
if d == "questions":
context.user_data["q_step"] = 0
context.user_data["q_answers"] = []
await q.message.reply_text("1. are you sure about your actions?")

# ---------- MISSIONS ----------
elif d == "missions":
kb = [
[InlineKeyboardButton(m["title"], callback_data=f"open_mission:{mid}")]
for mid, m in MISSIONS.items()
]
await q.message.reply_text(
"🔌 *Missions*",
parse_mode="Markdown",
reply_markup=InlineKeyboardMarkup(kb),
)

elif d.startswith("open_mission:"):
mid = d.split(":")[1]
m = MISSIONS[mid]
kb = [[InlineKeyboardButton("✅ Do Mission", callback_data=f"do_mission:{mid}")]]
await q.message.reply_text(
f"*{m['title']}*\n\n{m['document']}",
parse_mode="Markdown",
reply_markup=InlineKeyboardMarkup(kb),
)

elif d.startswith("do_mission:"):
context.user_data["awaiting_proof"] = d.split(":")[1]
await q.message.reply_text(
"Send proof now (photo / video / file / text)."
)

# ---------- PUBLISH MISSION ----------
elif d == "publish_mission":
context.user_data["flow"] = "mission_code"
await q.message.reply_text("Enter publish code:")

# ---------- TARGETS ----------
elif d == "targets":
if not TARGETS:
await q.message.reply_text("No targets yet.")
return
kb = [[InlineKeyboardButton(title, callback_data="noop")] for title in TARGETS.values()]
await q.message.reply_text(
"❌ *Targets*",
parse_mode="Markdown",
reply_markup=InlineKeyboardMarkup(kb),
)

elif d == "publish_target":
context.user_data["flow"] = "target_code"
await q.message.reply_text("Enter publish code:")

# ---------- ROLES ----------
elif d == "roles":
# send role banner image then prompt
await q.message.reply_photo(
photo=ROLE_BANNER,
caption=(
".3: 741-.god = manage messages 2/3\n"
".2: 741-.supreme = manage stories 1/3\n"
".1: 741-.good = manage live streams\n\n"
"Send number (1–3)."
),
parse_mode="Markdown",
)
context.user_data["role_step"] = "choose"

# ---------- ADMIN: accept/decline for questions/role/proof ----------
elif d.startswith("q_accept:") or d.startswith("q_decline:") or d.startswith("admin:"):
# keep a simple admin gate here (some callbacks used by admin messages)
if q.from_user.id != ADMIN_ID:
await q.answer("Not authorized", show_alert=True)
return

# backwards-compatible: accept/decline q_ style
if d.startswith("q_accept:"):
uid = int(d.split(":", 1)[1])
await context.bot.send_message(uid, f"✅ Accepted. Join here:\n{QUESTIONS_ACCEPT_LINK}")
await q.message.edit_text("✅ Accepted")
return
if d.startswith("q_decline:"):
uid = int(d.split(":", 1)[1])
await context.bot.send_message(uid, "❌ You have been declined to join the 741 group.")
await q.message.edit_text("❌ Declined")
return

# admin:accept:form:uid:token or admin:decline:form:uid:token
parts = d.split(":")
# format: admin:action:kind:uid:extra
if len(parts) >= 5:
_, action, kind, uid_s, extra = parts[:5]
uid = int(uid_s)
if kind == "form":
if action == "accept":
await context.bot.send_message(uid, f"✅ Accepted. Join here:\n{QUESTIONS_ACCEPT_LINK}")
await q.message.edit_text(q.message.text + "\n\n✅ Accepted")
else:
await context.bot.send_message(uid, "❌ You have been declined to join the 741 group.")
await q.message.edit_text(q.message.text + "\n\n❌ Declined")
elif kind == "role":
role = extra
if action == "accept":
await context.bot.send_message(uid, f"✅ You have been accepted for the role *{role}*", parse_mode="Markdown")
else:
await context.bot.send_message(uid, f"❌ You have been refused for the role *{role}*", parse_mode="Markdown")
await q.message.edit_text(q.message.text + "\n\n✅ Reviewed")
elif kind == "proof":
mid = extra
mission_title = MISSIONS.get(mid, {}).get("title", mid)
if action == "accept":
await context.bot.send_message(uid, f"✅ Your proof for *{mission_title}* has been accepted.", parse_mode="Markdown")
else:
await context.bot.send_message(uid, f"❌ Your proof for *{mission_title}* has been declined.", parse_mode="Markdown")
await q.message.edit_text(q.message.text + "\n\n✅ Reviewed")
return

# unknown callback fallback
else:
await q.message.reply_text("Unknown action.")


# ================= MESSAGES =================
async def message_handler(update: Update, context: ContextTypes.DEFAULT_TYPE):
msg = update.message
u = msg.from_user
text = msg.text or ""

# ---------- QUESTIONS FLOW ----------
if "q_step" in context.user_data:
answers = context.user_data["q_answers"]
answers.append(text)
step = context.user_data["q_step"] + 1
context.user_data["q_step"] = step

QUESTIONS = [
"1. are you sure about your actions?",
"2. what is your nickname?",
"3. what is your country?",
]

if step < 3:
await msg.reply_text(QUESTIONS[step])
return

report = (
f"📥 *Questions Submission*\n\n"
f"👤 {user_label(u)}\n"
f"🆔 `{u.id}`\n\n"
f"1️⃣ {answers[0]}\n"
f"2️⃣ {answers[1]}\n"
f"3️⃣ {answers[2]}"
)

kb = InlineKeyboardMarkup([
[
InlineKeyboardButton("✅ Accept", callback_data=f"admin:accept:form:{u.id}:{token()}"),
InlineKeyboardButton("❌ Decline", callback_data=f"admin:decline:form:{u.id}:{token()}"),
]
])

await context.bot.send_message(
ADMIN_ID, report, parse_mode="Markdown", reply_markup=kb
)
await msg.reply_text(
"✅ your questions have been successfully submitted"
)
context.user_data.clear()
return

# ---------- MISSION PROOF ----------
if context.user_data.get("awaiting_proof"):
mid = context.user_data.pop("awaiting_proof")
m = MISSIONS.get(mid, {"title": mid, "document": ""})

caption = (
f"📥 *Mission Proof Submitted*\n\n"
f"⚙️ {m['title']}\n"
f"👤 {user_label(u)}\n"
f"🆔 `{u.id}`"
)

try:
await msg.copy(ADMIN_ID, caption=caption, parse_mode="Markdown")
except Exception:
await msg.forward(ADMIN_ID)
await context.bot.send_message(ADMIN_ID, caption, parse_mode="Markdown")

# admin buttons to accept/decline proof
kb = InlineKeyboardMarkup([
[
InlineKeyboardButton("✅ Accept Proof", callback_data=f"admin:accept:proof:{u.id}:{mid}"),
InlineKeyboardButton("❌ Decline Proof", callback_data=f"admin:decline:proof:{u.id}:{mid}"),
]
])
await context.bot.send_message(ADMIN_ID, "Review proof:", reply_markup=kb)
await msg.reply_text("✅ Proof submitted and sent to admin for review.")
return

# ---------- PUBLISH MISSION ----------
if context.user_data.get("flow") == "mission_code":
context.user_data.pop("flow")
if text == PUBLISH_CODE:
context.user_data["mission_title_step"] = True
await msg.reply_text("Send mission title.")
else:
await msg.reply_text("❌ Invalid code.")
return

if context.user_data.get("mission_title_step"):
context.user_data.pop("mission_title_step")
context.user_data["mission_title"] = text
context.user_data["mission_doc_step"] = True
await msg.reply_text("Send mission description.")
return

if context.user_data.get("mission_doc_step"):
title = context.user_data.pop("mission_title", f"Mission {int(time.time())}")
context.user_data.pop("mission_doc_step", None)
mid = f"m_{int(time.time())}"
MISSIONS[mid] = {"title": title, "document": text}
save_file(MISSIONS_FILE, MISSIONS)
await msg.reply_text(f"✅ Mission published: *{title}*", parse_mode="Markdown")
return

# ---------- PUBLISH TARGET (uses same code as missions) ----------
if context.user_data.get("flow") == "target_code":
context.user_data.pop("flow")
if text == PUBLISH_CODE:
context.user_data["target_title_step"] = True
await msg.reply_text("Send target title.")
else:
await msg.reply_text("❌ Invalid code.")
return

if context.user_data.get("target_title_step"):
context.user_data.pop("target_title_step")
tid = f"t_{int(time.time())}"
TARGETS[tid] = text
save_file(TARGETS_FILE, TARGETS)
await msg.reply_text(f"✅ Target published:\n🎯 {text}")
return

# ---------- ROLES: pick number then reason ----------
if context.user_data.get("role_step") == "choose":
if text not in ("1", "2", "3"):
await msg.reply_text("❌ Send 1, 2, or 3")
return
mapping = {"1": "741-.good", "2": "741-.supreme", "3": "741-.god"}
context.user_data["role_choice"] = mapping[text]
context.user_data["role_step"] = "reason"
await msg.reply_text("Why do you want this role?")
return

if context.user_data.get("role_step") == "reason":
role = context.user_data.pop("role_choice", "unknown")
reason = text
context.user_data.pop("role_step", None)

kb = InlineKeyboardMarkup([
[
InlineKeyboardButton("✅ Accept", callback_data=f"admin:accept:role:{u.id}:{role}"),
InlineKeyboardButton("❌ Decline", callback_data=f"admin:decline:role:{u.id}:{role}"),
]
])

await context.bot.send_message(
ADMIN_ID,
f"🎭 *Role Request*\n\n👤 {user_label(u)}\n🆔 `{u.id}`\n🎖 Role: *{role}*\n\n📝 Reason:\n{reason}",
parse_mode="Markdown",
reply_markup=kb,
)
await msg.reply_text("✅ Role request sent.")
return

# ---------- DEFAULT ----------
await msg.reply_text("Use /start")


# ================= MAIN =================
def main():
app = ApplicationBuilder().token(TOKEN).build()
# single callback handler handles menu and admin buttons
app.add_handler(CommandHandler("start", start))
app.add_handler(CallbackQueryHandler(callback_handler))
app.add_handler(MessageHandler(filters.ALL & ~filters.COMMAND, message_handler))
print("🤖 Bot running")
app.run_polling()


if __name__ == "__main__":
main()
