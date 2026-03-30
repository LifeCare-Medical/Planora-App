import streamlit as st
import random
import datetime
import json
from datetime import datetime as dt
from supabase import create_client, Client
from twilio.rest import Client as TwilioClient

# --- PAGE CONFIG (MUST BE FIRST) ---
st.set_page_config(page_title="Planora", page_icon="🚀", layout="wide")

# --- HIDE TOOLBAR ---
st.markdown("""
    <style>
    #MainMenu {visibility: hidden;}
    header {visibility: hidden;}
    footer {visibility: hidden;}
    .stApp { background-color: #f8fafc; }
    .block-container { padding-top: 2rem; padding-left: 3rem; padding-right: 3rem; }
    button { border-radius: 10px !important; font-weight: 600; }
    section[data-testid="stSidebar"] {
        background-color: #ffff;
        border-right: 1px solid #e5e7eb;
    }
    </style>
""", unsafe_allow_html=True)
# --- PWA SUPPORT ---
st.markdown("""
    <link rel="manifest" href="/manifest.json">
    <meta name="theme-color" content="#7c3aed">
    <meta name="mobile-web-app-capable" content="yes">
    <meta name="apple-mobile-web-app-capable" content="yes">
    <meta name="apple-mobile-web-app-status-bar-style" content="black-translucent">
    <meta name="apple-mobile-web-app-title" content="Planora">
    <script>
        if ('serviceWorker' in navigator) {
            window.addEventListener('load', function() {
                navigator.serviceWorker.register('/sw.js')
                .then(reg => console.log('Planora PWA Ready ✅', reg))
                .catch(err => console.log('SW Error:', err));
            });
        }
    </script>
""", unsafe_allow_html=True)
# --- WISDOM ENGINE QUOTES ---
QUOTES = [
    "The secret of getting ahead is getting started.",
    "Focus on being productive instead of busy.",
    "Your mind is for idea generation, Let planora handle scheduling.",
    "Infrastructure of confidence starts with a clear plan.",
    "Efficiency is doing things right; effectiveness is doing the right things.",
    "The best way to predict the future is to create it.",
    "Quality is not an act, it is a habit.",
    "Amateurs sit and wait for inspiration, the rest of us just get to work."
]
random_quote = random.choice(QUOTES)

# --- LEMON SQUEEZY CHECKOUT LINK ---
CHECKOUT_URL = "https://planora-personal-app.lemonsqueezy.com/checkout/buy/7561b79c-2f6d-4889-88c4-663bd9b2aa5a"

# --- CONNECTIONS ---
SUPABASE_URL = st.secrets["SUPABASE_URL"]
SUPABASE_KEY = st.secrets["SUPABASE_KEY"]
TWILIO_SID = st.secrets["TWILIO_SID"]
TWILIO_TOKEN = st.secrets["TWILIO_TOKEN"]
TWILIO_FROM = st.secrets["TWILIO_FROM"]

# Add this near your other initializations (like around line 50-100)
if "generate_insights" not in st.session_state:
    st.session_state["generate_insights"] = False


supabase: Client = create_client(SUPABASE_URL, SUPABASE_KEY)

# --- WHATSAPP FUNCTION ---
def send_whatsapp(message, to_number):
    try:
        client = TwilioClient(TWILIO_SID, TWILIO_TOKEN)
        from_number = TWILIO_FROM if TWILIO_FROM.startswith("whatsapp:") else f"whatsapp:{TWILIO_FROM}"
        to_number = to_number if to_number.startswith("whatsapp:") else f"whatsapp:{to_number}"
        client.messages.create(from_=from_number, body=message, to=to_number)
        st.success("WhatsApp Sent! 📱")
    except Exception as e:
        st.error(f"WhatsApp Error: {e}")

# --- LOGIN SCREEN ---
def login_screen():
    import os
    if os.path.exists("logo.png"):
        st.sidebar.image("logo.png", use_container_width=True)
    st.sidebar.markdown("""
    <div style='text-align: center; font-weight: 600; font-size: 18px; margin-top: -10px;'>
    Planora
    </div>
    """, unsafe_allow_html=True)
    st.sidebar.markdown("---")

    st.markdown(f"""
    <h1 style='font-size: 42px; font-weight: 700; margin-bottom: 0;'>
    🚀 Planora
    </h1>
    <p style='color: #6b7280; font-size: 18px; margin-top: 5px; font-style: italic;'>
    "{random_quote}"
    </p>
    """, unsafe_allow_html=True)

    tab1, tab2 = st.tabs(["Login", "Sign Up"])
    with tab1:
        email = st.text_input("Email")
        password = st.text_input("Password", type="password")
        if st.button("Login"):
            try:
                res = supabase.auth.sign_in_with_password({"email": email, "password": password})
                st.session_state.user = res.user
                st.rerun()
            except Exception as e:
                st.error(f"Login failed: {e}")
    with tab2:
        email = st.text_input("Email", key="signup_email")
        password = st.text_input("Password", type="password", key="signup_pass")
        if st.button("Create Account"):
            try:
                supabase.auth.sign_up({"email": email, "password": password})
                st.success("Account created. Please log in.")
            except Exception as e:
                st.error(f"Signup failed: {e}")

if "user" not in st.session_state:
    login_screen()
    st.stop()

user_id = st.session_state.user.id
user_email = st.session_state.user.email

# --- SMART CHECKOUT URL (pre-fills user email) ---
smart_checkout_url = f"{CHECKOUT_URL}?checkout[email]={user_email}"

# --- SIDEBAR (LOGGED IN) ---
import os
if os.path.exists("logo.png"):
    st.sidebar.image("logo.png", use_container_width=True)
st.sidebar.markdown("""
<div style='text-align: center; font-weight: 600; font-size: 18px; margin-top: -10px;'>
Planora
</div>
""", unsafe_allow_html=True)
st.sidebar.markdown("---")
st.sidebar.write(f"👤 {user_email}")
if st.sidebar.button("Logout"):
    supabase.auth.sign_out()
    del st.session_state.user
    st.rerun()

menu = st.sidebar.radio("Navigation", [
    "📋 Execution List",
    "🔥 Focus Mode",
    "📊 Performance",
    "🧠 Wisdom Engine",
    "⚙️ Settings"
])

# --- UPGRADE BUTTON IN SIDEBAR ---
st.sidebar.markdown("---")

# --- DATABASE FUNCTIONS ---
def get_tasks():
    return supabase.table("Tasks").select("*").eq("user_id", user_id).execute().data

def add_task(name, date, time, notes, reminder):
    supabase.table("Tasks").insert({
        "task_name": name,
        "task_date": str(date),
        "task_time": str(time),
        "notes": notes,
        "is_done": False,
        "user_id": user_id,
        "reminder_minutes": reminder
    }).execute()

def delete_task(task_id):
    supabase.table("Tasks").delete().eq("id", task_id).eq("user_id", user_id).execute()

def toggle_done(task_id, current):
    supabase.table("Tasks").update({"is_done": not current}).eq("id", task_id).eq("user_id", user_id).execute()

def get_profile():
    res = supabase.table("profiles").select("*").eq("id", user_id).execute()
    return res.data[0] if res.data else None

def save_profile(full_name, phone):
    existing = get_profile()
    if existing:
        supabase.table("profiles").update({
            "full_name": full_name,
            "phone": phone
        }).eq("id", user_id).execute()
    else:
        supabase.table("profiles").insert({
            "id": user_id,
            "full_name": full_name,
            "phone": phone
        }).execute()

def is_pro_user():
    profile = get_profile()
    if profile:
        return profile.get("is_pro", False)
    return False

# --- CHECK PRO STATUS ---
is_pro = is_pro_user()

# --- SIDEBAR PRO BADGE OR UPGRADE BUTTON ---
if is_pro:
    st.sidebar.success("✅ Planora Pro Active")
else:
    st.sidebar.markdown("### 🚀 Planora Pro")
    st.sidebar.write("Unlock the Wisdom Engine & advanced features.")
    st.sidebar.link_button("⚡ Upgrade to Pro — $10/mo", smart_checkout_url)

# --- MAIN HEADER ---
st.markdown(f"""
<h1 style='font-size: 36px; font-weight: 700; margin-bottom: 0;'>
🚀 Planora
</h1>
<p style='color: #6b7280; font-size: 16px; margin-top: 5px; font-style: italic;'>
"{random_quote}"
</p>
""", unsafe_allow_html=True)
st.markdown("---")

# ====
# 📋 EXECUTION LIST
# ====
if menu == "📋 Execution List":
    with st.expander("➕ Add Task"):
        with st.form("form", clear_on_submit=True):
            name = st.text_input("Task")
            d = st.date_input("Date")
            t = st.time_input("Time")
            notes = st.text_area("Notes")
            reminder = st.selectbox("Remind me (minutes before)", [5, 10, 15, 30, 60])
            if st.form_submit_button("Save Task"):
                if name:
                    add_task(name, d, t, notes, reminder)
                    st.success("Task saved ✅")
                    st.rerun()

    tasks = get_tasks()
    if not tasks:
        st.info("No tasks yet. Add one above!")
    for task in tasks:
        col1, col2, col3 = st.columns([1, 6, 2])
        done = col1.checkbox("", value=task["is_done"], key=task["id"])
        if done != task["is_done"]:
            toggle_done(task["id"], task["is_done"])
            st.rerun()
        style = "~~" if task["is_done"] else "**"
        col2.write(f"{style}{task['task_name']}{style}")
        col2.caption(f"📅 {task['task_date']} | ⏰ {task['task_time']}")
        if task.get("notes"):
            col2.caption(f"📝 {task['notes']}")
        if col3.button("🗑️ Delete", key=f"del{task['id']}"):
            delete_task(task["id"])
            st.rerun()

# ====
# 🔥 FOCUS MODE
# ====
elif menu == "🔥 Focus Mode":
    st.subheader("🔥 Today's Focus")
    tasks = get_tasks()
    today = str(datetime.date.today())
    now = dt.now()
    today_tasks = [t for t in tasks if t["task_date"] == today and not t["is_done"]]

    if not today_tasks:
        st.success("✅ You are all caught up for today!")
    else:
        voice_lines = []
        for t in today_tasks:
            task_dt = dt.strptime(f"{t['task_date']} {t['task_time']}", "%Y-%m-%d %H:%M:%S")
            reminder = int(t.get("reminder_minutes") or 10)
            reminder_time = task_dt - datetime.timedelta(minutes=reminder)

            if now > task_dt:
                st.error(f"⚠️ Overdue: **{t['task_name']}**")
                voice_lines.append(f"{t['task_name']} is overdue.")
            elif reminder_time <= now <= task_dt:
                st.warning(f"🔔 Due soon: **{t['task_name']}** in {reminder} mins")
                voice_lines.append(f"{t['task_name']} starts in {reminder} minutes.")
            else:
                st.info(f"📌 {t['task_name']} at {t['task_time']}")
                voice_lines.append(f"You have {t['task_name']} at {t['task_time']}.")

        if voice_lines:
            message = " ".join(voice_lines)
            profile = get_profile()
            phone = profile.get("phone") if profile else None

            c1, c2 = st.columns(2)
            if c1.button("🔊 Read Aloud"):
                st.components.v1.html(f"""
                <script>
                var msg = new SpeechSynthesisUtterance("{message}");
                msg.rate = 0.9;
                speechSynthesis.speak(msg);
                </script>
                """, height=0)

            if c2.button("📱 Send to WhatsApp"):
                if phone:
                    send_whatsapp(f"🚀 Planora Secretary:\n{message}", phone)
                else:
                    st.warning("⚠️ Please add your WhatsApp number in ⚙️ Settings first!")

# ====
# 📊 PERFORMANCE
# ====
elif menu == "📊 Performance":
    st.subheader("📊 Your Performance")
    tasks = get_tasks()
    total = len(tasks)
    done = len([t for t in tasks if t["is_done"]])
    pending = total - done

    if total > 0:
        percent = int((done / total) * 100)
        col1, col2, col3 = st.columns(3)
        col1.metric("Total Tasks", total)
        col2.metric("Completed", done)
        col3.metric("Pending", pending)
        st.progress(percent / 100)
        st.caption(f"Completion Rate: {percent}%")
        if percent == 100:
            st.balloons()
            st.success("🏆 Perfect execution today!")
        elif percent >= 70:
            st.success("💪 Great progress! Keep going!")
        elif percent >= 40:
            st.warning("⚡ You are halfway there. Push through!")
        else:
            st.error("🔥 Let's get moving. Your goals need you!")
    else:
        st.info("No tasks yet. Add some in the Execution List!")

# ====
# 🧠 WISDOM ENGINE (PRO) — PREMIUM REDESIGN
# ====
elif menu == "🧠 Wisdom Engine":
    if is_pro:
        # ─── WISDOM ENGINE PREMIUM CSS ───
        st.markdown("""
        <style>
        /* Override Streamlit background for Wisdom Engine */
        .wisdom-engine-wrapper {
            background: linear-gradient(135deg, #0a1628 0%, #0f2044 40%, #162a54 70%, #0a1628 100%);
            border-radius: 20px;
            padding: 40px 30px;
            margin: -20px -15px 20px -15px;
            position: relative;
            overflow: hidden;
        }
        .wisdom-engine-wrapper::before {
            content: '';
            position: absolute;
            top: -50%;
            left: -50%;
            width: 200%;
            height: 200%;
            background: radial-gradient(ellipse at 30% 20%, rgba(99, 102, 241, 0.08) 0%, transparent 50%),
                    radial-gradient(ellipse at 70% 80%, rgba(139, 92, 246, 0.06) 0%, transparent 50%);
            pointer-events: none;
        }

        /* Title */
        .we-title {
            text-align: center;
            font-size: 42px;
            font-weight: 800;
            letter-spacing: 6px;
            color: #e2e8f0;
            text-transform: uppercase;
            margin-bottom: 4px;
            text-shadow: 0 0 30px rgba(99, 102, 241, 0.5), 0 0 60px rgba(139, 92, 246, 0.3);
        }
        .we-subtitle {
            text-align: center;
            font-size: 15px;
            color: #94a3b8;
            letter-spacing: 3px;
            margin-bottom: 30px;
        }

        /* Glowing card */
        .we-card {
            background: linear-gradient(145deg, rgba(15, 23, 42, 0.9), rgba(30, 41, 59, 0.7));
            border: 1px solid rgba(99, 102, 241, 0.2);
            border-radius: 16px;
            padding: 28px;
            margin-bottom: 20px;
            backdrop-filter: blur(10px);
            box-shadow: 0 0 20px rgba(99, 102, 241, 0.08), inset 0 1px 0 rgba(255,255,255,0.05);
            transition: all 0.3s ease;
        }
        .we-card:hover {
            border-color: rgba(99, 102, 241, 0.4);
            box-shadow: 0 0 30px rgba(99, 102, 241, 0.15), inset 0 1px 0 rgba(255,255,255,0.08);
            transform: translateY(-2px);
        }

        .we-card-title {
            font-size: 18px;
            font-weight: 700;
            color: #c7d2fe;
            margin-bottom: 14px;
            display: flex;
            align-items: center;
            gap: 10px;
        }
        .we-card-title .icon {
            width: 32px;
            height: 32px;
            background: linear-gradient(135deg, #6366f1, #8b5cf6);
            border-radius: 8px;
            display: flex;
            align-items: center;
            justify-content: center;
            font-size: 16px;
            box-shadow: 0 0 12px rgba(99, 102, 241, 0.4);
        }

        .we-card-body {
            color: #cbd5e1;
            font-size: 15px;
            line-height: 1.7;
        }

        /* Quote card special */
        .we-quote-card {
            background: linear-gradient(145deg, rgba(99, 102, 241, 0.12), rgba(139, 92, 246, 0.08));
            border: 1px solid rgba(139, 92, 246, 0.25);
            border-radius: 16px;
            padding: 30px;
            margin-bottom: 20px;
            text-align: center;
        }
        .we-quote-text {
            font-size: 22px;
            font-weight: 600;
            color: #e2e8f0;
            font-style: italic;
            line-height: 1.6;
            text-shadow: 0 0 20px rgba(139, 92, 246, 0.3);
        }
        .we-quote-label {
            font-size: 13px;
            color: #8b5cf6;
            letter-spacing: 2px;
            text-transform: uppercase;
            margin-bottom: 12px;
            font-weight: 600;
        }

        /* Stats row */
        .we-stats-row {
            display: flex;
            gap: 16px;
            margin-bottom: 20px;
            flex-wrap: wrap;
        }
        .we-stat-box {
            flex: 1;
            min-width: 140px;
            background: linear-gradient(145deg, rgba(15, 23, 42, 0.9), rgba(30, 41, 59, 0.7));
            border: 1px solid rgba(99, 102, 241, 0.2);
            border-radius: 14px;
            padding: 22px 18px;
            text-align: center;
            transition: all 0.3s ease;
        }
        .we-stat-box:hover {
            border-color: rgba(99, 102, 241, 0.5);
            box-shadow: 0 0 20px rgba(99, 102, 241, 0.15);
        }
        .we-stat-value {
            font-size: 32px;
            font-weight: 800;
            color: #e2e8f0;
            text-shadow: 0 0 15px rgba(99, 102, 241, 0.4);
        }
        .we-stat-label {
            font-size: 12px;
            color: #94a3b8;
            letter-spacing: 1px;
            text-transform: uppercase;
            margin-top: 4px;
        }

        /* Progress ring */
        .we-progress-ring {
            width: 120px;
            height: 120px;
            margin: 0 auto 10px;
        }

        /* Recommendation list */
        .we-rec-item {
            display: flex;
            align-items: flex-start;
            gap: 12px;
            padding: 12px 0;
            border-bottom: 1px solid rgba(99, 102, 241, 0.1);
        }
        .we-rec-item:last-child { border-bottom: none; }
        .we-rec-bullet {
            width: 8px;
            height: 8px;
            background: linear-gradient(135deg, #6366f1, #8b5cf6);
            border-radius: 50%;
            margin-top: 7px;
            flex-shrink: 0;
            box-shadow: 0 0 8px rgba(99, 102, 241, 0.6);
        }
        .we-rec-text {
            color: #cbd5e1;
            font-size: 14px;
            line-height: 1.6;
        }

        /* Insight badge */
        .we-badge {
            display: inline-block;
            padding: 4px 12px;
            border-radius: 20px;
            font-size: 12px;
            font-weight: 600;
            letter-spacing: 0.5px;
        }
        .we-badge-green {
            background: rgba(34, 197, 94, 0.15);
            color: #4ade80;
            border: 1px solid rgba(34, 197, 94, 0.3);
        }
        .we-badge-yellow {
            background: rgba(250, 204, 21, 0.15);
            color: #fbbf24;
            border: 1px solid rgba(250, 204, 21, 0.3);
        }
        .we-badge-red {
            background: rgba(239, 68, 68, 0.15);
            color: #f87171;
            border: 1px solid rgba(239, 68, 68, 0.3);
        }
        .we-badge-blue {
            background: rgba(99, 102, 241, 0.15);
            color: #818cf8;
            border: 1px solid rgba(99, 102, 241, 0.3);
        }

        /* Glow divider */
        .we-divider {
            height: 1px;
            background: linear-gradient(90deg, transparent, rgba(99, 102, 241, 0.4), transparent);
            margin: 24px 0;
        }

        /* Welcome banner */
        .we-welcome {
            background: linear-gradient(135deg, rgba(34, 197, 94, 0.1), rgba(99, 102, 241, 0.1));
            border: 1px solid rgba(34, 197, 94, 0.2);
            border-radius: 12px;
            padding: 16px 24px;
            text-align: center;
            color: #4ade80;
            font-weight: 600;
            font-size: 15px;
            margin-bottom: 24px;
        }

        /* AI Loading animation */
        @keyframes we-pulse {
            0%, 100% { opacity: 0.6; }
            50% { opacity: 1; }
        }
        .we-loading {
            animation: we-pulse 1.5s infinite;
            color: #818cf8;
            text-align: center;
            font-size: 14px;
            padding: 20px;
        }

        /* Feature list in center panel */
        .we-feature-item {
            display: flex;
            align-items: center;
            gap: 12px;
            padding: 8px 0;
            color: #cbd5e1;
            font-size: 15px;
        }
        .we-feature-arrow {
            color: #8b5cf6;
            font-size: 18px;
            font-weight: bold;
        }
        </style>
        """, unsafe_allow_html=True)

        # ─── WISDOM ENGINE CONTENT ───
        tasks = get_tasks()
        total = len(tasks)
        done_tasks = [t for t in tasks if t["is_done"]]
        pending_tasks = [t for t in tasks if not t["is_done"]]
        done = len(done_tasks)
        pending = len(pending_tasks)
        percent = int((done / total) * 100) if total > 0 else 0

        today = str(datetime.date.today())
        today_tasks = [t for t in tasks if t["task_date"] == today]
        today_done = len([t for t in today_tasks if t["is_done"]])
        today_pending = len([t for t in today_tasks if not t["is_done"]])
        overdue_tasks = []
        now = dt.now()
        for t in pending_tasks:
            try:
                task_dt = dt.strptime(f"{t['task_date']} {t['task_time']}", "%Y-%m-%d %H:%M:%S")
                if now > task_dt:
                    overdue_tasks.append(t)
            except:
                pass

        # Determine performance badge
        if percent >= 80:
            perf_badge = '<span class="we-badge we-badge-green">🟢 Excellent</span>'
        elif percent >= 50:
            perf_badge = '<span class="we-badge we-badge-yellow">🟡 Good Progress</span>'
        elif total > 0:
            perf_badge = '<span class="we-badge we-badge-red">🔴 Needs Focus</span>'
        else:
            perf_badge = '<span class="we-badge we-badge-blue">🔵 Getting Started</span>'

        # Daily wisdom quote (changes daily based on day of year)
        day_index = datetime.date.today().timetuple().tm_yday % len(QUOTES)
        daily_quote = QUOTES[day_index]

        # ─── RENDER PREMIUM UI ───
        st.markdown('<div class="wisdom-engine-wrapper">', unsafe_allow_html=True)

        # Title
        st.markdown("""
        <div class="we-title">🧠 WISDOM ENGINE</div>
        <div class="we-subtitle">AI Insights & Recommendations</div>
        """, unsafe_allow_html=True)

        # Welcome banner
        profile = get_profile()
        user_name = profile.get("full_name", "Pro User") if profile else "Pro User"
        st.markdown(f'<div class="we-welcome">✅ Welcome back, {user_name} — Powered by Planora Pro</div>', unsafe_allow_html=True)

        # ─── DAILY WISDOM QUOTE ───
        st.markdown(f"""
        <div class="we-quote-card">
            <div class="we-quote-label">💡 Today's Wisdom</div>
            <div class="we-quote-text">"{daily_quote}"</div>
        </div>
        """, unsafe_allow_html=True)

        # ─── STATS ROW ───
        st.markdown(f"""
        <div class="we-stats-row">
            <div class="we-stat-box">
                <div class="we-stat-value">{total}</div>
                <div class="we-stat-label">Total Tasks</div>
            </div>
            <div class="we-stat-box">
                <div class="we-stat-value">{done}</div>
                <div class="we-stat-label">Completed</div>
            </div>
            <div class="we-stat-box">
                <div class="we-stat-value">{pending}</div>
                <div class="we-stat-label">Pending</div>
            </div>
            <div class="we-stat-box">
                <div class="we-stat-value">{percent}%</div>
                <div class="we-stat-label">Completion Rate</div>
            </div>
        </div>
        """, unsafe_allow_html=True)

        st.markdown('<div class="we-divider"></div>', unsafe_allow_html=True)

        # ─── TWO-COLUMN LAYOUT: Task Analysis + Performance ───
        col_left, col_right = st.columns(2)

        with col_left:
            # Task Analysis Card
            overdue_html = ""
            if overdue_tasks:
                overdue_items = "".join([
                    f'<div class="we-rec-item"><div class="we-rec-bullet"></div><div class="we-rec-text">⚠️ <strong>{t["task_name"]}</strong> — {t["task_date"]} {t["task_time"]}</div></div>'
                    for t in overdue_tasks[:5]
                ])
                overdue_html = f"""
                <div style="margin-top: 16px;">
                    <div style="color: #f87171; font-weight: 600; font-size: 14px; margin-bottom: 8px;">
                    ⚠️ Overdue Tasks ({len(overdue_tasks)})
                    </div>
                    {overdue_items}
                </div>
                """
            else:
                overdue_html = '<div style="color: #4ade80; font-size: 14px; margin-top: 12px;">✅ No overdue tasks — great job!</div>'

            today_summary = f"""
            <div style="margin-top: 12px;">
                <div style="color: #94a3b8; font-size: 13px; text-transform: uppercase; letter-spacing: 1px; margin-bottom: 8px;">Today's Summary</div>
                <div style="color: #cbd5e1; font-size: 14px;">
                    📋 {len(today_tasks)} task(s) today &nbsp;|&nbsp; ✅ {today_done} done &nbsp;|&nbsp; ⏳ {today_pending} remaining
                </div>
            </div>
            """

            # 1. Open the card
            st.markdown("""
            <div class="we-card">
                <div class="we-card-title">
                    <div class="icon">📊</div>
                    Task Analysis
                </div>
                <div class="we-card-body">
            """, unsafe_allow_html=True)

            # 2. Render each piece separately (this fixes the raw text issue!)
            st.markdown(perf_badge, unsafe_allow_html=True)
            st.markdown(today_summary, unsafe_allow_html=True)
            st.markdown(overdue_html, unsafe_allow_html=True)

            # 3. Close the card
            st.markdown("""
                </div>
            </div>
            """, unsafe_allow_html=True)

        with col_right:
            # Performance Insights Card
            # Calculate streaks and patterns
            if total > 0:
                focus_score = min(100, int(percent * 1.1 + (10 if not overdue_tasks else 0)))
                if percent >= 80:
                    trend = "📈 Upward trend — exceptional execution"
                    trend_color = "#4ade80"
                elif percent >= 50:
                    trend = "📊 Steady progress — room for improvement"
                    trend_color = "#fbbf24"
                else:
                    trend = "📉 Falling behind — time to refocus"
                    trend_color = "#f87171"
            else:
                focus_score = 0
                trend = "🆕 Add tasks to start tracking"
                trend_color = "#818cf8"

            st.markdown(f"""
            <div class="we-card">
                <div class="we-card-title">
                    <div class="icon">🎯</div>
                    Performance Insights
                </div>
                <div class="we-card-body">
                    <div style="display: flex; align-items: center; gap: 20px; margin-bottom: 16px;">
                    <div style="text-align: center;">
                    <div style="font-size: 48px; font-weight: 800; color: #e2e8f0; text-shadow: 0 0 20px rgba(99, 102, 241, 0.5);">{focus_score}</div>
                    <div style="font-size: 11px; color: #94a3b8; text-transform: uppercase; letter-spacing: 1px;">Focus Score</div>
                    </div>
                    <div style="flex: 1;">
                    <div style="color: {trend_color}; font-size: 14px; font-weight: 600; margin-bottom: 8px;">{trend}</div>
                    <div style="color: #94a3b8; font-size: 13px;">
                    Completed {done} of {total} tasks<br>
                    {len(overdue_tasks)} overdue items need attention
                    </div>
                    </div>
                    </div>
                    <div style="background: rgba(99, 102, 241, 0.1); border-radius: 8px; height: 8px; overflow: hidden;">
                    <div style="background: linear-gradient(90deg, #6366f1, #8b5cf6); width: {percent}%; height: 100%; border-radius: 8px; transition: width 0.5s ease;"></div>
                    </div>
                    <div style="color: #94a3b8; font-size: 12px; margin-top: 6px; text-align: right;">{percent}% Complete</div>
                </div>
            </div>
            """, unsafe_allow_html=True)

        st.markdown('<div class="we-divider"></div>', unsafe_allow_html=True)

        # ─── AI-POWERED RECOMMENDATIONS (Generate Insights) ───
        st.markdown("""
        <div class="we-card">
            <div class="we-card-title">
                <div class="icon">🤖</div>
                AI-Powered Recommendations
            </div>
        </div>
        """, unsafe_allow_html=True)

        # Generate Insights Button
        if st.button("⚡ GENERATE INSIGHTS", key="gen_btn", use_container_width=True):
            st.session_state["generate_insights"] = True
            st.rerun()

        if st.session_state.get("generate_insights", False):
            with st.spinner("🧠 Wisdom Engine is analyzing your productivity..."):
                try:
                    task_summary_parts = []
                    if tasks:
                        task_names = [t["task_name"] for t in tasks[:15]]
                        task_summary_parts.append(f"Tasks: {', '.join(task_names)}")
                        task_summary_parts.append(f"Total: {total}, Completed: {done}, Pending: {pending}")
                        task_summary_parts.append(f"Completion rate: {percent}%")
                        task_summary_parts.append(f"Overdue tasks: {len(overdue_tasks)}")
                        task_summary_parts.append(f"Today's tasks: {len(today_tasks)} ({today_done} done, {today_pending} pending)")
                        if overdue_tasks:
                            overdue_names = [t["task_name"] for t in overdue_tasks[:5]]
                            task_summary_parts.append(f"Overdue items: {', '.join(overdue_names)}")
                    else:
                        task_summary_parts.append("User has no tasks yet.")

                    task_context = "\n".join(task_summary_parts)
                    
                    # 1. BUILD THE PROMPT FIRST
                    task_context = "\n".join(task_summary_parts)
                    prompt = f"""You are the Wisdom Engine AI for Planora... {task_context} ..."""
                    
                    from openai import OpenAI
                    client = OpenAI(api_key=st.secrets["OPENAI_API_KEY"])
                    response = client.chat.completions.create(
                        model="gpt-4o-mini",
                        messages=[
                            {"role": "system", "content": "You are a productivity AI coach. Return only valid JSON."},
                            {"role": "user", "content": prompt}
                        ],
                        temperature=0.7
                    )
# 🛠️ CLEAN THE JSON (This fixes the error!)
                    response_text = response.choices[0].message.content
                    if "```json" in response_text:
                        response_text = response_text.split("```json")[1].split("```")[0]
                    elif "```" in response_text:
                        response_text = response_text.split("```")[1].split("```")[0]
                    response_text = response_text.strip()
                    insights = json.loads(response_text)


                    # Display AI Recommendations
                    recs = insights.get("smart_recommendations", [])
                    recs_html = ""
                    for rec in recs:
                        recs_html += f"""
                        <div class="we-rec-item">
                            <div class="we-rec-bullet"></div>
                            <div class="we-rec-text">{rec}</div>
                        </div>
                        """

                    focus_tip = insights.get("focus_tip", "Stay focused on your highest-priority task.")
                    pattern = insights.get("productivity_pattern", "Keep tracking tasks to reveal patterns.")
                    next_action = insights.get("next_action", "Review your task list and prioritize.")
                    motivation = insights.get("motivation", "You're making progress — keep going!")

                    # 1. Render the Card Header
                    st.markdown("""
                    <div class="we-card">
                        <div class="we-card-title">
                            <div class="icon">💡</div>
                            Smart Recommendations
                        </div>
                        <div class="we-card-body">
                    """, unsafe_allow_html=True)

                    # 2. Render the actual list (this fixes the raw text issue!)
                    st.markdown(recs_html, unsafe_allow_html=True)

                    # 3. Close the Card
                    st.markdown("""
                        </div>
                    </div>
                    """, unsafe_allow_html=True)

                    rec_col1, rec_col2 = st.columns(2)
                    with rec_col1:
                        st.markdown(f"""
                    <div class="we-card">
                    <div class="we-card-title">
                    <div class="icon">🔥</div>
                    Focus Tip
                    </div>
                    <div class="we-card-body">{focus_tip}</div>
                    </div>
                    """, unsafe_allow_html=True)

                    st.markdown(f"""
                    <div class="we-card">
                    <div class="we-card-title">
                    <div class="icon">🚀</div>
                    Next Best Action
                    </div>
                    <div class="we-card-body" style="color: #c7d2fe; font-weight: 600;">{next_action}</div>
                    </div>
                    """, unsafe_allow_html=True)

                    with rec_col2:
                        st.markdown(f"""
                    <div class="we-card">
                    <div class="we-card-title">
                    <div class="icon">📈</div>
                    Productivity Pattern
                    </div>
                    <div class="we-card-body">{pattern}</div>
                    </div>
                    """, unsafe_allow_html=True)

                    st.markdown(f"""
                    <div class="we-card">
                    <div class="we-card-title">
                    <div class="icon">💪</div>
                    Motivation
                    </div>
                    <div class="we-card-body" style="color: #a5b4fc; font-style: italic;">"{motivation}"</div>
                    </div>
                    """, unsafe_allow_html=True)

                except Exception as e:
                    st.error(f"AI Engine Error: {e}")
                    # Fallback to static insights
                    fallback_recs = []
                    if overdue_tasks:
                        fallback_recs.append(f"You have {len(overdue_tasks)} overdue task(s). Tackle these first to clear your backlog.")
                    if pending > 0:
                        fallback_recs.append(f"Break your {pending} pending task(s) into smaller, manageable steps.")
                    if percent >= 70:
                        fallback_recs.append("Strong momentum! Finish remaining tasks to hit 100%.")
                    else:
                        fallback_recs.append("Focus on completing one task at a time. Small wins build momentum.")
                    fallback_recs.append("Schedule your most important task during your peak energy hours.")

                    fallback_html = ""
                    for rec in fallback_recs:
                        fallback_html += f'<div class="we-rec-item"><div class="we-rec-bullet"></div><div class="we-rec-text">{rec}</div></div>'

                    st.markdown(f"""
                    <div class="we-card">
                    <div class="we-card-title">
                    <div class="icon">💡</div>
                    Productivity Tips
                    </div>
                    <div class="we-card-body">{fallback_html}</div>
                    </div>
                    """, unsafe_allow_html=True)

        # Feature list
        st.markdown("""
        <div class="we-divider"></div>
        <div style="text-align: center; margin-top: 10px;">
            <div class="we-feature-item" style="justify-content: center;">
                <span class="we-feature-arrow">›</span>
                <span style="color: #94a3b8; font-size: 13px;">Prioritize high-impact tasks</span>
                <span style="margin: 0 12px; color: #334155;">|</span>
                <span class="we-feature-arrow">›</span>
                <span style="color: #94a3b8; font-size: 13px;">Optimize your schedule</span>
                <span style="margin: 0 12px; color: #334155;">|</span>
                <span class="we-feature-arrow">›</span>
                <span style="color: #94a3b8; font-size: 13px;">Focus on key goals</span>
                <span style="margin: 0 12px; color: #334155;">|</span>
                <span class="we-feature-arrow">›</span>
                <span style="color: #94a3b8; font-size: 13px;">Enhance productivity</span>
            </div>
        </div>
        """, unsafe_allow_html=True)

        st.markdown('</div>', unsafe_allow_html=True)

    else:
        # ─── NON-PRO: UPGRADE PROMPT ───
        st.markdown("""
        <style>
        .upgrade-wrapper {
            background: linear-gradient(135deg, #0a1628 0%, #0f2044 40%, #162a54 70%, #0a1628 100%);
            border-radius: 20px;
            padding: 60px 40px;
            text-align: center;
            position: relative;
            overflow: hidden;
        }
        .upgrade-wrapper::before {
            content: '';
            position: absolute;
            top: -50%;
            left: -50%;
            width: 200%;
            height: 200%;
            background: radial-gradient(ellipse at 50% 50%, rgba(99, 102, 241, 0.1) 0%, transparent 60%);
            pointer-events: none;
        }
        .upgrade-title {
            font-size: 36px;
            font-weight: 800;
            color: #e2e8f0;
            letter-spacing: 4px;
            margin-bottom: 16px;
            text-shadow: 0 0 30px rgba(99, 102, 241, 0.5);
        }
        .upgrade-desc {
            color: #94a3b8;
            font-size: 16px;
            max-width: 500px;
            margin: 0 auto 30px;
            line-height: 1.7;
        }
        .upgrade-features {
            display: flex;
            justify-content: center;
            gap: 30px;
            flex-wrap: wrap;
            margin-bottom: 30px;
        }
        .upgrade-feature {
            background: rgba(99, 102, 241, 0.1);
            border: 1px solid rgba(99, 102, 241, 0.2);
            border-radius: 12px;
            padding: 16px 24px;
            color: #c7d2fe;
            font-size: 14px;
            font-weight: 600;
        }
        </style>

        <div class="upgrade-wrapper">
            <div style="font-size: 60px; margin-bottom: 20px;">🔒</div>
            <div class="upgrade-title">WISDOM ENGINE</div>
            <div class="upgrade-desc">
                Unlock AI-powered productivity insights, smart recommendations, task analysis, and advanced planning tools with Planora Pro.
            </div>
            <div class="upgrade-features">
                <div class="upgrade-feature">🤖 AI Recommendations</div>
                <div class="upgrade-feature">📊 Task Analysis</div>
                <div class="upgrade-feature">🎯 Focus Insights</div>
                <div class="upgrade-feature">💡 Daily Wisdom</div>
            </div>
        </div>
        """, unsafe_allow_html=True)

        st.markdown("")
        st.link_button("⚡ Upgrade to Planora Pro — $10/mo", smart_checkout_url, use_container_width=True)

# ====
# ⚙️ SETTINGS
# ====
elif menu == "⚙️ Settings":
    st.subheader("⚙️ Your Profile & Settings")
    profile = get_profile()
    with st.form("profile_form"):
        full_name = st.text_input(
            "Full Name",
            value=profile.get("full_name", "") if profile else ""
        )
        phone = st.text_input(
            "WhatsApp Number (include country code)",
            value=profile.get("phone", "") if profile else "",
            placeholder="+18683735271"
        )
        st.caption("⚠️ Include your country code. Example: +1 for USA/Caribbean, +234 for Nigeria, +254 for Kenya")
        if st.form_submit_button("💾 Save Settings"):
            if phone:
                save_profile(full_name, phone)
                st.success("✅ Settings saved!")
                st.balloons()
            else:
                st.error("Please enter your WhatsApp number.")