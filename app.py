# ================================================================
# ISL Connect — Final Fixed app.py
# ================================================================
# FIXES IN THIS VERSION:
#   1. OTP prints clearly in terminal (dev mode) when SMTP not set
#   2. send_otp_email() always takes 3 args: (email, otp, name)
#   3. Admin messages saved with key "ts" — matches messages.html
#   4. /messages route works correctly
#   5. /admin/send-message URL is correct
#   6. Route name is messages_page (avoids conflict with variable)
# ================================================================

from flask import (Flask, render_template, request,
                   redirect, url_for, session, jsonify, send_from_directory)
import json, os, random, smtplib, time
from email.mime.text import MIMEText
from email.mime.multipart import MIMEMultipart
from functools import wraps
from flask_socketio import SocketIO, emit, join_room, leave_room, rooms

app = Flask(__name__)
app.secret_key = "islconnect_final_2025"

socketio = SocketIO(app, cors_allowed_origins="*", async_mode='eventlet')

USERS_FILE    = "users.json"
MESSAGES_FILE = "messages.json"
otp_store     = {}

ADMIN_QUICK_MSGS = [
    "📞 I tried calling you. I'll call you back later.",
    "✅ Your account has been reviewed. Everything looks fine.",
    "⚠️ Please update your profile information when possible.",
    "🔒 Security notice: Please change your password soon.",
    "ℹ️ Scheduled maintenance: service may be briefly unavailable."
]

# ════════════════════════════════════════════
# DECORATORS
# ════════════════════════════════════════════
def user_required(f):
    @wraps(f)
    def d(*a, **kw):
        if "user_id" not in session:
            return redirect(url_for("login"))
        if session.get("role") == "admin":
            return redirect(url_for("admin_dashboard"))
        return f(*a, **kw)
    return d

def admin_required(f):
    @wraps(f)
    def d(*a, **kw):
        if "user_id" not in session:
            return redirect(url_for("login"))
        if session.get("role") != "admin":
            return redirect(url_for("home"))
        return f(*a, **kw)
    return d

# ════════════════════════════════════════════
# DATA HELPERS
# ════════════════════════════════════════════
def load_users():
    if os.path.exists(USERS_FILE):
        with open(USERS_FILE, "r") as f:
            return json.load(f)
    return {}

def save_users(u):
    with open(USERS_FILE, "w") as f:
        json.dump(u, f, indent=4)

def load_messages():
    if os.path.exists(MESSAGES_FILE):
        with open(MESSAGES_FILE, "r") as f:
            return json.load(f)
    return {}

def save_messages(m):
    with open(MESSAGES_FILE, "w") as f:
        json.dump(m, f, indent=4)

def get_unread_count(uid):
    msgs = load_messages()
    return sum(1 for m in msgs.get(uid, []) if not m.get("read"))

def get_smtp():
    u = load_users()
    a = u.get("admin", {})
    return a.get("smtp_email", ""), a.get("smtp_pass", "")

# ════════════════════════════════════════════
# EMAIL FUNCTIONS
# ════════════════════════════════════════════
def send_otp_email(to_email, otp, name="User"):
    """
    DEV MODE  : prints OTP in terminal when SMTP not configured.
    PROD MODE : sends real HTML email via Gmail SMTP.
    """
    smtp_email, smtp_pass = get_smtp()

    # ── DEV MODE ───────────────────────────────────────────────
    if not smtp_email or not smtp_pass:
        print("\n" + "=" * 52)
        print("  📧  ISL Connect — OTP (DEV MODE)")
        print("  " + "-" * 48)
        print(f"  👤  Name   : {name}")
        print(f"  📮  Email  : {to_email}")
        print(f"  🔑  OTP    : {otp}")
        print(f"  ⏰  Expires: 5 minutes")
        print("  " + "-" * 48)
        print("  ℹ️   To send real emails → Admin Panel → SMTP")
        print("=" * 52 + "\n")
        return True

    # ── PROD MODE ──────────────────────────────────────────────
    try:
        msg = MIMEMultipart("alternative")
        msg["Subject"] = "ISL Connect — Email Verification Code"
        msg["From"]    = f"ISL Connect <{smtp_email}>"
        msg["To"]      = to_email
        html = f"""<!DOCTYPE html>
<html><head><meta charset="UTF-8"></head>
<body style="margin:0;padding:0;background:#060d1a;font-family:Arial,sans-serif">
<table width="100%" cellpadding="0" cellspacing="0">
<tr><td align="center" style="padding:40px 20px">
<table width="480" cellpadding="0" cellspacing="0"
       style="background:#0f1e31;border-radius:16px;border:1px solid #1a2d44;overflow:hidden">
  <tr><td style="background:linear-gradient(135deg,#00c896,#3b82f6);padding:28px 36px">
    <h1 style="color:#fff;margin:0;font-size:22px">🤟 ISL Connect</h1>
    <p style="color:rgba(255,255,255,.7);margin:4px 0 0;font-size:13px">Email Verification</p>
  </td></tr>
  <tr><td style="padding:36px">
    <p style="color:#e2eaf4;font-size:15px;margin:0 0 8px">Hello <strong>{name}</strong>,</p>
    <p style="color:#7a9ab8;font-size:14px;margin:0 0 28px;line-height:1.6">
      Use the code below to verify your email. Expires in 5 minutes.
    </p>
    <div style="background:#111f33;border:1px solid rgba(0,200,150,.3);border-radius:12px;
                padding:24px;text-align:center;margin-bottom:28px">
      <div style="font-size:38px;font-weight:700;letter-spacing:14px;
                  color:#00c896;font-family:'Courier New',monospace">{otp}</div>
    </div>
    <p style="color:#5a7a9a;font-size:12px;margin:0;line-height:1.6">
      Never share this code with anyone.<br>
      If you didn't request this, ignore this email.
    </p>
  </td></tr>
  <tr><td style="padding:16px 36px;border-top:1px solid #1a2d44">
    <p style="color:#3a5a7a;font-size:11px;margin:0;text-align:center">
      2025 ISL Connect - Automated message, do not reply.
    </p>
  </td></tr>
</table></td></tr></table>
</body></html>"""
        msg.attach(MIMEText(html, "html"))
        with smtplib.SMTP_SSL("smtp.gmail.com", 465, timeout=10) as s:
            s.login(smtp_email, smtp_pass)
            s.sendmail(smtp_email, to_email, msg.as_string())
        print(f"✅ OTP email sent to {to_email}")
        return True
    except Exception as e:
        # SMTP failed — fall back to terminal so flow doesn't break
        print(f"\n⚠️  SMTP failed: {e}")
        print(f"  📧  Fallback OTP for {to_email}: {otp}\n")
        return True


def send_admin_notification(to_email, to_name, message_text):
    """Send admin message notification. DEV: prints to terminal."""
    smtp_email, smtp_pass = get_smtp()

    if not smtp_email or not smtp_pass:
        print(f"\n📨  [DEV] Admin message → {to_email}: {message_text}\n")
        return

    try:
        msg = MIMEMultipart("alternative")
        msg["Subject"] = "ISL Connect — Message from Admin"
        msg["From"]    = f"ISL Connect <{smtp_email}>"
        msg["To"]      = to_email
        html = f"""<!DOCTYPE html>
<html><body style="margin:0;padding:0;background:#060d1a;font-family:Arial,sans-serif">
<table width="100%" cellpadding="0" cellspacing="0">
<tr><td align="center" style="padding:40px 20px">
<table width="480" cellpadding="0" cellspacing="0"
       style="background:#0f1e31;border-radius:16px;border:1px solid #1a2d44">
  <tr><td style="background:linear-gradient(135deg,#6366f1,#8b5cf6);padding:24px 32px">
    <h2 style="color:#fff;margin:0;font-size:18px">Message from Admin</h2>
  </td></tr>
  <tr><td style="padding:32px">
    <p style="color:#e2eaf4;margin:0 0 6px">Hello <strong>{to_name}</strong>,</p>
    <div style="background:#111f33;border-left:3px solid #6366f1;border-radius:8px;
                padding:16px 20px;margin:18px 0">
      <p style="color:#e2eaf4;margin:0;font-size:15px;line-height:1.6">{message_text}</p>
    </div>
    <p style="color:#5a7a9a;font-size:12px;margin:0">
      Log in to ISL Connect to view your messages.
    </p>
  </td></tr>
</table></td></tr></table>
</body></html>"""
        msg.attach(MIMEText(html, "html"))
        with smtplib.SMTP_SSL("smtp.gmail.com", 465, timeout=10) as s:
            s.login(smtp_email, smtp_pass)
            s.sendmail(smtp_email, to_email, msg.as_string())
    except Exception as e:
        print(f"⚠️  Admin notification email failed: {e}")


# ════════════════════════════════════════════
# DATABASE INIT
# ════════════════════════════════════════════
def init_db():
    if not os.path.exists(USERS_FILE):
        save_users({
            "admin": {
                "password":   "admin123",
                "name":       "Administrator",
                "email":      "admin@islconnect.local",
                "role":       "admin",
                "approved":   True,
                "suspended":  False,
                "joined":     time.strftime("%Y-%m-%d"),
                "smtp_email": "",
                "smtp_pass":  ""
            }
        })
        print("✅ users.json created.")
    if not os.path.exists(MESSAGES_FILE):
        save_messages({})
        print("✅ messages.json created.")


# ════════════════════════════════════════════
# AUTH ROUTES
# ════════════════════════════════════════════
@app.route("/")
def index():
    if "user_id" not in session:
        return redirect(url_for("login"))
    if session.get("role") == "admin":
        return redirect(url_for("admin_dashboard"))
    return redirect(url_for("home"))

@app.route("/login", methods=["GET", "POST"])
def login():
    error = None
    if request.method == "POST":
        uid = request.form.get("user_id", "").strip()
        pwd = request.form.get("password", "").strip()
        u   = load_users()
        if uid not in u:
            error = "User ID not found. Please check or sign up."
        elif u[uid].get("suspended"):
            error = "Your account has been suspended. Contact admin."
        elif u[uid]["password"] != pwd:
            error = "Incorrect password. Please try again."
        elif not u[uid].get("approved"):
            error = "Your account is pending admin approval."
        else:
            session.clear()
            session["user_id"] = uid
            session["name"]    = u[uid]["name"]
            session["role"]    = u[uid].get("role", "user")
            if session["role"] == "admin":
                return redirect(url_for("admin_dashboard"))
            return redirect(url_for("home"))
    return render_template("login.html", error=error)

@app.route("/logout")
def logout():
    session.clear()
    return redirect(url_for("login"))

@app.route("/signup", methods=["GET", "POST"])
def signup():
    error = None
    if request.method == "POST":
        uid  = request.form.get("user_id", "").strip()
        name = request.form.get("name", "").strip()
        mail = request.form.get("email", "").strip().lower()
        pwd  = request.form.get("password", "").strip()
        cnf  = request.form.get("confirm", "").strip()
        u    = load_users()

        if not all([uid, name, mail, pwd, cnf]):
            error = "All fields are required."
        elif len(uid) < 3 or not uid.isalnum():
            error = "User ID: letters and numbers only, min 3 characters."
        elif uid in u:
            error = "This User ID is already taken. Choose another."
        elif "@" not in mail or "." not in mail.split("@")[-1]:
            error = "Enter a valid email address."
        elif any(v.get("email", "").lower() == mail for v in u.values()):
            error = "This email is already registered with another account."
        elif pwd != cnf:
            error = "Passwords do not match."
        elif len(pwd) < 6:
            error = "Password must be at least 6 characters."
        else:
            otp = str(random.randint(100000, 999999))
            otp_store[mail] = {
                "otp":      otp,
                "expires":  time.time() + 300,
                "uid":      uid,
                "name":     name,
                "email":    mail,
                "password": pwd
            }
            send_otp_email(mail, otp, name)   # always 3 args
            return redirect(url_for("verify_otp", email=mail))
    return render_template("signup.html", error=error)

@app.route("/verify-otp/<email>", methods=["GET", "POST"])
def verify_otp(email):
    email   = email.lower()
    error   = None
    success = None

    if request.method == "POST":
        entered = request.form.get("otp", "").strip()
        rec     = otp_store.get(email)

        if not rec:
            error = "OTP session expired. Please sign up again."
        elif time.time() > rec["expires"]:
            otp_store.pop(email, None)
            error = "OTP has expired. Please sign up again."
        elif rec["otp"] != entered:
            error = "Incorrect OTP. Please try again."
        else:
            u = load_users()
            u[rec["uid"]] = {
                "password":   rec["password"],
                "name":       rec["name"],
                "email":      email,
                "role":       "user",
                "approved":   False,
                "suspended":  False,
                "joined":     time.strftime("%Y-%m-%d"),
                "contacts":   [],
                "favourites": [],
                "emergency":  [],
                "theme":      "dark",
                "font_size":  "medium",
                "ringtone":   "default",
                "bio":        ""
            }
            save_users(u)
            otp_store.pop(email, None)
            success = "Email verified! Account pending admin approval. You can log in once approved."

    return render_template("verify_otp.html",
                           email=email, error=error, success=success)

@app.route("/resend-otp/<email>")
def resend_otp(email):
    email = email.lower()
    rec   = otp_store.get(email)
    if rec:
        new_otp = str(random.randint(100000, 999999))
        otp_store[email]["otp"]     = new_otp
        otp_store[email]["expires"] = time.time() + 300
        send_otp_email(email, new_otp, rec.get("name", "User"))
    return redirect(url_for("verify_otp", email=email))


# ════════════════════════════════════════════
# ADMIN ROUTES
# ════════════════════════════════════════════
def admin_render_data(u, pw_msg=None):
    pending   = {k: v for k, v in u.items() if not v.get("approved") and k != "admin"}
    approved  = {k: v for k, v in u.items() if v.get("approved") and not v.get("suspended") and k != "admin"}
    suspended = {k: v for k, v in u.items() if v.get("suspended") and k != "admin"}
    return dict(
        pending=pending, approved=approved, suspended=suspended,
        stats={"total": len(u)-1, "pending": len(pending),
               "approved": len(approved), "suspended": len(suspended)},
        admin_cfg=u.get("admin", {}),
        admin_name=session["name"],
        quick_msgs=ADMIN_QUICK_MSGS,
        all_users={k: v for k, v in u.items() if k != "admin"},
        pw_msg=pw_msg
    )

@app.route("/admin")
@admin_required
def admin_dashboard():
    return render_template("admin.html", **admin_render_data(load_users()))

@app.route("/admin/approve/<uid>")
@admin_required
def admin_approve(uid):
    u = load_users()
    if uid in u and uid != "admin":
        u[uid]["approved"] = True; u[uid]["suspended"] = False
        save_users(u)
    return redirect(url_for("admin_dashboard"))

@app.route("/admin/reject/<uid>")
@admin_required
def admin_reject(uid):
    u = load_users()
    if uid in u and uid != "admin":
        del u[uid]; save_users(u)
    return redirect(url_for("admin_dashboard"))

@app.route("/admin/suspend/<uid>")
@admin_required
def admin_suspend(uid):
    u = load_users()
    if uid in u and uid != "admin":
        u[uid]["suspended"] = True; u[uid]["approved"] = False
        save_users(u)
    return redirect(url_for("admin_dashboard"))

@app.route("/admin/unsuspend/<uid>")
@admin_required
def admin_unsuspend(uid):
    u = load_users()
    if uid in u and uid != "admin":
        u[uid]["suspended"] = False; u[uid]["approved"] = True
        save_users(u)
    return redirect(url_for("admin_dashboard"))

@app.route("/admin/smtp", methods=["POST"])
@admin_required
def admin_save_smtp():
    u = load_users()
    u["admin"]["smtp_email"] = request.form.get("smtp_email", "").strip()
    u["admin"]["smtp_pass"]  = request.form.get("smtp_pass", "").strip()
    save_users(u)
    return redirect(url_for("admin_dashboard"))

@app.route("/admin/change-password", methods=["POST"])
@admin_required
def admin_change_password():
    u   = load_users()
    old = request.form.get("old_password", "").strip()
    new = request.form.get("new_password", "").strip()
    cnf = request.form.get("confirm_password", "").strip()
    if u["admin"]["password"] != old:
        msg = ("error", "Current password is incorrect.")
    elif new != cnf:
        msg = ("error", "New passwords do not match.")
    elif len(new) < 6:
        msg = ("error", "Password must be at least 6 characters.")
    else:
        u["admin"]["password"] = new; save_users(u)
        msg = ("success", "Password updated successfully.")
    return render_template("admin.html", **admin_render_data(u, pw_msg=msg))

@app.route("/admin/send-message", methods=["POST"])
@admin_required
def admin_send_message():
    data     = request.get_json()
    target   = data.get("uid", "").strip()
    msg_text = data.get("message", "").strip()
    u        = load_users()

    if not target or not msg_text:
        return jsonify({"ok": False, "msg": "Missing user or message."})
    if target not in u or target == "admin":
        return jsonify({"ok": False, "msg": "User not found."})

    msgs = load_messages()
    msgs.setdefault(target, []).append({
        "from": "admin",
        "text": msg_text,
        "ts":   time.strftime("%d %b %Y, %I:%M %p"),  # key is "ts" — matches template
        "read": False
    })
    save_messages(msgs)
    send_admin_notification(u[target].get("email", ""), u[target].get("name", "User"), msg_text)
    return jsonify({"ok": True})


# ════════════════════════════════════════════
# USER ROUTES
# ════════════════════════════════════════════
@app.route("/home")
@user_required
def home():
    u   = load_users()
    uid = session["user_id"]
    me  = u.get(uid, {})
    favs = set(me.get("favourites", []))
    emer = set(me.get("emergency", []))

    contacts_detail = []
    for cid in me.get("contacts", []):
        cu = u.get(cid)
        if cu and cu.get("approved") and not cu.get("suspended"):
            contacts_detail.append({
                "uid": cid, "name": cu["name"],
                "email": cu.get("email", ""),
                "is_fav": cid in favs,
                "is_emergency": cid in emer
            })

    all_users = {k: v for k, v in u.items()
                 if v.get("approved") and not v.get("suspended")
                 and k != uid and k != "admin"}

    return render_template("home.html",
        uid=uid, name=session["name"], role="user",
        me=me, contacts=contacts_detail, all_users=all_users,
        favs=list(favs), emergency=list(emer),
        unread=get_unread_count(uid),
        theme=me.get("theme", "dark"))

@app.route("/messages")
@user_required
def messages_page():
    uid  = session["user_id"]
    msgs = load_messages()
    my   = msgs.get(uid, [])
    for m in my: m["read"] = True      # mark all read when inbox opened
    save_messages(msgs)
    u  = load_users()
    me = u.get(uid, {})
    return render_template("messages.html",
        uid=uid, name=session["name"], me=me,
        messages=list(reversed(my)),   # newest first
        theme=me.get("theme", "dark"))

@app.route("/settings", methods=["GET", "POST"])
@user_required
def settings():
    u   = load_users()
    uid = session["user_id"]
    me  = u[uid]
    msg = None

    if request.method == "POST":
        action = request.form.get("action", "")
        if action == "update_profile":
            n = request.form.get("name", "").strip()
            if not n: msg = ("error", "Name cannot be empty.")
            else:
                me["name"] = n; me["bio"] = request.form.get("bio", "").strip()
                session["name"] = n; msg = ("success", "Profile updated.")
        elif action == "change_password":
            old = request.form.get("old_password", "").strip()
            new = request.form.get("new_password", "").strip()
            cnf = request.form.get("confirm_password", "").strip()
            if me["password"] != old: msg = ("error", "Current password incorrect.")
            elif new != cnf: msg = ("error", "Passwords don't match.")
            elif len(new) < 6: msg = ("error", "Min 6 characters.")
            else: me["password"] = new; msg = ("success", "Password changed.")
        elif action == "update_appearance":
            me["theme"]     = request.form.get("theme", "dark")
            me["font_size"] = request.form.get("font_size", "medium")
            msg = ("success", "Appearance saved.")
        elif action == "update_ringtone":
            me["ringtone"] = request.form.get("ringtone", "default")
            msg = ("success", "Ringtone updated.")
        save_users(u)

    return render_template("settings.html",
        uid=uid, name=session["name"], me=me, msg=msg,
        theme=me.get("theme", "dark"))


@app.route("/dataset/<path:filename>")
def serve_dataset(filename):
    return send_from_directory("dataset", filename)


@app.route("/call/<target_id>")
@user_required
def call(target_id):
    u = load_users()
    t = u.get(target_id)
    if not t or not t.get("approved") or t.get("suspended"):
        return redirect(url_for("home"))
    me = u.get(session["user_id"], {})
    return render_template("call.html",
        caller_id=session["user_id"], caller_name=session["name"],
        target_id=target_id, target_name=t["name"],
        ringtone=me.get("ringtone", "default"),
        theme=me.get("theme", "dark"))



# ════════════════════════════════════════════
# USER API
# ════════════════════════════════════════════
@app.route("/api/search-user", methods=["POST"])
@user_required
def api_search_user():
    q     = request.get_json().get("uid", "").strip().lower()
    u     = load_users()
    me_id = session["user_id"]
    me    = u[me_id]
    results = [
        {"uid": k, "name": v["name"],
         "in_contacts": k in me.get("contacts", []),
         "is_fav": k in me.get("favourites", []),
         "is_emergency": k in me.get("emergency", [])}
        for k, v in u.items()
        if k != "admin" and k != me_id
        and v.get("approved") and not v.get("suspended")
        and (q in k.lower() or q in v["name"].lower())
    ]
    return jsonify({"ok": True, "results": results[:10]})

@app.route("/api/add-contact", methods=["POST"])
@user_required
def api_add_contact():
    target = request.get_json().get("uid", "").strip()
    u      = load_users(); me_id = session["user_id"]; me = u[me_id]
    if target == me_id: return jsonify({"ok": False, "msg": "Cannot add yourself."})
    if target not in u or not u[target].get("approved"): return jsonify({"ok": False, "msg": "User not found."})
    if target in me.get("contacts", []): return jsonify({"ok": False, "msg": "Already in contacts."})
    me.setdefault("contacts", []).append(target)
    save_users(u)
    return jsonify({"ok": True, "name": u[target]["name"]})

@app.route("/api/remove-contact", methods=["POST"])
@user_required
def api_remove_contact():
    target = request.get_json().get("uid", "").strip()
    u = load_users(); me = u[session["user_id"]]
    for lst in ("contacts", "favourites", "emergency"):
        ld = me.get(lst, [])
        if target in ld: ld.remove(target)
    save_users(u)
    return jsonify({"ok": True})

@app.route("/api/toggle-favourite", methods=["POST"])
@user_required
def api_toggle_favourite():
    target = request.get_json().get("uid", "").strip()
    u = load_users(); me = u[session["user_id"]]; favs = me.setdefault("favourites", [])
    if target in favs: favs.remove(target); state = False
    else:
        if target not in me.get("contacts", []): return jsonify({"ok": False, "msg": "Add to contacts first."})
        favs.append(target); state = True
    save_users(u)
    return jsonify({"ok": True, "fav": state})

@app.route("/api/toggle-emergency", methods=["POST"])
@user_required
def api_toggle_emergency():
    target = request.get_json().get("uid", "").strip()
    u = load_users(); me = u[session["user_id"]]; emer = me.setdefault("emergency", [])
    if target in emer: emer.remove(target); state = False
    else:
        if target not in me.get("contacts", []): return jsonify({"ok": False, "msg": "Add to contacts first."})
        emer.append(target); state = True
    save_users(u)
    return jsonify({"ok": True, "emergency": state})

@app.route("/api/mark-read", methods=["POST"])
@user_required
def api_mark_read():
    uid = session["user_id"]; msgs = load_messages()
    for m in msgs.get(uid, []): m["read"] = True
    save_messages(msgs)
    return jsonify({"ok": True})

@app.route("/api/call-history", methods=["GET", "POST"])
@user_required
def api_call_history():
    uid = session["user_id"]
    history_file = "call_history.json"
    if os.path.exists(history_file):
        with open(history_file, "r") as f:
            history = json.load(f)
    else:
        history = {}
    my_history = history.get(uid, [])
    if request.method == "POST":
        data = request.get_json()
        call = {
            "contact": data.get("contact", "unknown"),
            "duration": data.get("duration", 0),
            "status": data.get("status", "ended"),
            "timestamp": time.strftime("%Y-%m-%d %H:%M")
        }
        history.setdefault(uid, []).insert(0, call)
        if len(history[uid]) > 50:
            history[uid] = history[uid][-50:]
        with open(history_file, "w") as f:
            json.dump(history, f, indent=2)
        return jsonify({"ok": True})
    return jsonify({"calls": my_history})

# ════════════════════════════════════════════
# SOCKET.IO SIGNALING
# ════════════════════════════════════════════
@socketio.on('join')
def on_join(data):
    uid = data.get('uid')
    if uid:
        join_room(uid)
        print(f"📡 User {uid} joined signaling room")

@socketio.on('call-user')
def on_call_user(data):
    targetId = data.get('targetId')
    callerId = data.get('callerId')
    callerName = data.get('callerName')
    if targetId:
        emit('incoming-call', {'callerId': callerId, 'callerName': callerName}, room=targetId)

@socketio.on('call-response')
def on_call_response(data):
    callerId = data.get('callerId')
    accepted = data.get('accepted')
    targetId = data.get('targetId')
    if callerId:
        emit('call-response', {'accepted': accepted, 'targetId': targetId}, room=callerId)

@socketio.on('call-data')
def on_call_data(data):
    targetId = data.get('targetId')
    if targetId:
        emit('call-data', data, room=targetId)

# ════════════════════════════════════════════
# RUN
# ════════════════════════════════════════════
if __name__ == "__main__":
    init_db()
    print("\n" + "=" * 52)
    print("  ---  ISL Connect  ---")
    print("=" * 52)
    print("  🌐  http://127.0.0.1:5001")
    print("  🔑  Admin  :  admin / admin123")
    print("  📧  OTP    :  prints here in terminal (dev mode)")
    print("  💡  SMTP   :  Admin Panel → Settings → Email")
    print("=" * 52 + "\n")
    socketio.run(app, port=5001, debug=True)