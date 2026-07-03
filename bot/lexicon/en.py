"""
Centralized UI string dictionary (English language).

Rules:
- All keys are grouped by module: common_, diary_, hist_, info_, start_, stats_, kb_, sched_, analytics_.
- Dynamic data — via {placeholder}, substituted with .format() at call site.
- This file must NOT contain f-strings or any dynamic logic.
"""

LEXICON_EN: dict[str, str] = {

    # ── common.py ──────────────────────────────────────────────────────
    "common_no_user": "❌ You're not in the database, type /start",
    "common_digest_loading": "🔨 Building a test digest. Hold on, Gemini is thinking...",
    "common_digest_min_entries": "⚠️ Need at least 2 entries for a test. Found: {count}.",
    "common_digest_ai_empty": "❌ AI returned nothing or invalid JSON. Check the console logs.",
    "common_digest_error": "❌ Critical error during generation: {error}",
    "common_stray_text": (
        "👀 <b>I see your text, but I'm not in recording mode</b>\n\n"
        "To save a diary entry:\n"
        "• Tap the «📝 Write today» button.\n"
        "• Send or forward your text again."
    ),
    "common_stray_media": (
        "🔤 <b>I only understand text for now</b>\n\n"
        "Voice messages, photos and video notes won't work. Tap «📝 Write today» and tell me everything in words."
    ),

    # ── diary.py ───────────────────────────────────────────────────────
    "diary_already_wrote": (
        "🛡 <b>Today's entry is already saved</b>\n\n"
        "That's it for today. Rest up — we'll talk about the new day tomorrow!"
    ),
    "diary_start_reflection": (
        "✍️ <b>Time to reflect</b>\n\n"
        "How was your day? What did you get done, how are you feeling? Write it all as it is."
    ),
    "diary_text_only": (
        "🔤 <b>Text only, please</b>\n\n"
        "I can't process photos, stickers or voice messages yet. Write it out in words!"
    ),
    "diary_story_too_long": (
        "✂️ <b>Too many characters!</b>\n\n"
        "I can handle texts up to <code>1500</code> characters (yours is <code>{length}</code>).\n"
        "Shorten it and send again."
    ),
    "diary_answer_too_long": (
        "✂️ <b>Too many characters!</b>\n\n"
        "I can handle texts up to <code>800</code> characters (yours is <code>{length}</code>).\n"
        "Shorten your thought and send again."
    ),
    "diary_ai_processing": "⏳ <b>Hold on</b>\n\nI'm still processing your previous message.",
    "diary_analyzing_day": "🧠 <i>Analyzing your day...</i>",
    "diary_safety_block": (
        "🛡 <b>Your day has been saved.</b>\n\n"
        "Due to strict AI safety restrictions (platform censorship) "
        "I couldn't comment on this text, but everything has been safely recorded."
    ),
    "diary_ai_down": (
        "⚠️ <b>AI servers are taking a nap</b>\n\n"
        "Your text has been <b>saved</b> to the database, nothing is lost, "
        "but I can't respond to it right now."
    ),
    "diary_saved_bye": (
        "💾 <b>Entry saved</b>\n\n"
        "Have a great evening!"
    ),
    "diary_finalizing": "💾 <b>All written to the diary</b>\n\n<i>The AI is wrapping up your day summary, one moment...</i>",
    "diary_analyzing_answer": "🧠 <i>Analyzing your answer...</i>",
    "diary_finish_already_done": "Entry already finished",
    "diary_finish_no_text": "No text to save",

    # ── diary.py — "Write" button from reminder ────────────────────────
    "diary_start_from_reminder": (
        "✍️ <b>Great, let's write it down</b>\n\n"
        "How was your day? What did you get done, how are you feeling? Write it all as it is."
    ),

    # ── history.py ─────────────────────────────────────────────────────
    "hist_empty": (
        "📭 <b>Your diary is empty</b>\n\n"
        "Your entries will be stored here. Tap «📝 Write today» to make your first one."
    ),
    "hist_entry": "📅 <b>Entry from {date}</b>\n\n{text}",
    "hist_invalid_data": "Invalid data",
    "hist_no_more": "🛑 No more entries",

    # ── info.py ────────────────────────────────────────────────────────
    "info_donate_main": (
        "⭐️ <b>Support DayLog AI</b>\n\n"
        "Hey! I'm <a href='https://t.me/bimba_alpaca'>Bimba</a>, the creator of DayLog 🧠\n\n"
        "Right now this diary is my personal pet project, built purely on enthusiasm. "
        "I'm building it in my spare time, learning new technologies and really want to turn this idea into a full-fledged awesome product.\n\n"
        "But the reality is that development and stable operation of the bot require costs: server hosting, AI API fees, "
        "subscriptions for AI tools and dev instruments, and of course, energy drinks for late-night coding.\n\n"
        "If you want to support me and the development of DayLog, I'd be very grateful. "
        "Any donation is a contribution to DayLog's development and great motivation for me to make it even better.\n\n"
        "<i>Choose a convenient method below</i> 👇"
    ),
    "info_donate_crypto": (
        "🤝 <b>Thank you for your support!</b>\n\n"
        "Every transfer goes directly to server costs and bot development.\n\n"
        "Tap an address to copy:\n\n"
        "<b>EVM:</b>\n"
        "<code>0x4e6844271890e801F2666Ef73D1ba74c494FB1CC</code>\n\n"
        "<b>Solana:</b>\n"
        "<code>4u1ijqdx1Tt6ceo4FkNAR2Nh85zFSgAikSXkfAtEUuMi</code>\n\n"
        "<i>Please double-check wallet addresses before sending.</i>"
    ),
    "info_donate_stars": "⭐️ <b>Telegram Stars</b>\n\nPay in just a few taps right inside the messenger. Choose a comfortable amount below 👇",
    "info_help": (
        "🧠 <b>What is DayLog AI?</b>\n\n"
        "It's a personal diary that does all the work for you. No manual trackers or tedious ratings.\n\n"
        "<b>How we interact:</b>\n"
        "1. <b>Entry:</b> Just dump your thoughts in text — how the day went, what's bugging you or making you happy.\n"
        "2. <b>Dialogue:</b> I may ask a couple of follow-up questions to help you reflect. Answering is optional — you can always skip.\n"
        "3. <b>Analysis:</b> The bot quietly extracts your metrics: <i>mood, energy, stress and productivity</i>.\n"
        "4. <b>Digest:</b> Once a week I compile a smart summary. The AI will analyze all your entries, find hidden patterns, highlight energy drains and deliver insights.\n\n"
        "🕹 <b>Navigation:</b>\n"
        "• <b>Write today</b> — start a reflection (once per day)\n"
        "• <b>My diary</b> — your entry archive\n"
        "• <b>Statistics</b> — your well-being charts\n"
        "• <b>Settings</b> — timezone and digest schedule\n\n"
        "💡 <code>Pro tip: The more honest and detailed you are, the deeper and more accurate your weekly digest will be.</code>\n\n"
        "Found a bug or have a feature idea? Write to the developer 👇"
    ),
    "info_feedback_prefill": "Hey! Got some feedback on DayLog AI: ",
    "info_invalid_data": "Invalid data",
    "info_invalid_amount": "Invalid amount",
    "info_unknown_payment": "Unknown payment",
    "info_payment_success": (
        "🎉 <b>Payment successful!</b>\n\n"
        "Stars received. Huge thanks for supporting DayLog! 🫂"
    ),

    # ── start.py ───────────────────────────────────────────────────────
    "start_welcome": (
        "🧠 <b>Hey! I'm DayLog</b>\n\n"
        "Your smart personal diary. Forget boring trackers — just tell me how your day went and I'll do the rest:\n\n"
        "• Organize your thoughts\n"
        "• Extract metrics (mood, stress, energy, productivity)\n"
        "• Build beautiful statistics\n\n"
        "Ready to clear your head? Setup takes just 10 seconds!\n\n"
        "By tapping the button below, you accept the <a href='https://telegra.ph/POLITIKA-KONFIDENCIALNOSTI-I-OBRABOTKI-PERSONALNYH-DANNYH-06-08-2'>Privacy Policy</a>."
    ),
    "start_onboarding_tz": (
        "🌍 <b>Where are you located?</b>\n\n"
        "Choose your timezone below. This is needed so reminders arrive on time."
    ),
    "start_onboarding_tz_done": (
        "🌍 <b>Timezone: {tz_name}</b>\n\n"
        "What time would you like to wrap up your day?\n"
        "Send the time in <code>HH:MM</code> format (e.g., <code>21:00</code>)."
    ),
    "start_invalid_time": (
        "❌ <b>Invalid format</b>\n\n"
        "Type the time in <code>HH:MM</code> format (from <code>00:00</code> to <code>23:59</code>)."
    ),
    "start_onboarding_done": (
        "✅ <b>All set!</b>\n\n"
        "I'll check in for your report every day at <b>{time}</b>.\n\n"
        "<code>⚠️ Note: You can write one entry per day. Try to fit all your thoughts into one message.</code>\n\n"
        "Tap «📝 Write today» to make your first entry 👇"
    ),
    "start_text_only_time": (
        "🔤 <b>Text only, please</b>\n\n"
        "Send the time in <code>HH:MM</code> format (e.g., <code>21:00</code>)."
    ),
    "start_settings_title": "⚙️ <b>Settings</b>\n\nWhat would you like to change?",
    "start_tz_select": "🌍 <b>Timezone</b>\n\nWhere are you right now?",
    "start_tz_selected_toast": "Timezone set: {tz_name}",
    "start_tz_updated": "🌍 <b>Timezone updated!</b>\n\nI'm now working on <b>{tz_name}</b> time.",
    "start_time_prompt": (
        "🕒 <b>Reminder time</b>\n\n"
        "Send your preferred time in <code>HH:MM</code> format (e.g., <code>21:00</code>)."
    ),
    "start_time_saved": (
        "🕒 <b>Time saved!</b>\n\n"
        "I'll check in for your report every day at <b>{time}</b>."
    ),
    "start_cancelled": "🚫 <b>Action cancelled</b>",
    "start_digest_settings": "⚙️ Digest settings. What would you like to change?",
    "start_digest_day_select": "📅 Choose the day of the week for your digest:",
    "start_digest_time_select": "🕒 Choose the delivery time for your digest:",
    "start_invalid_data": "Invalid data",
    "start_invalid_day": "Invalid day",
    "start_invalid_time_value": "Invalid time",

    # ── stats.py ───────────────────────────────────────────────────────
    "stats_empty": (
        "📊 <b>No statistics yet</b>\n\n"
        "Write your first entry so the AI can start tracking your metrics."
    ),
    "stats_report": (
        "📊 <b>Your statistics</b>\n\n"
        "🏆 Total entries: <b>{total_count}</b>\n"
        "🔥 Current streak: <b>{streak} days</b>\n\n"
        "📈 <b>Weekly averages:</b>\n"
        "😌 Mood: <b>{mood}</b>\n"
        "⚡️ Energy: <b>{energy}</b>\n"
        "🧠 Productivity: <b>{productivity}</b>\n"
        "🌪 Stress: <b>{stress}</b>"
    ),

    # ── keyboards/main_kb.py ──────────────────────────────────────────
    "kb_write_day": "📝 Write today",
    "kb_my_diary": "📚 My diary",
    "kb_stats": "📊 Statistics",
    "kb_donate": "❤️ Support the project",
    "kb_settings": "⚙️ Settings",
    "kb_placeholder": "Choose an action...",
    "kb_onboarding_go": "Let's go 🚀",
    "kb_tz": "🌍 Timezone",
    "kb_reminder_time": "⏰ Reminder time",
    "kb_digest_settings": "📰 Digest settings",
    "kb_help": "❓ Help",
    "kb_cancel": "Cancel",
    "kb_finish_diary": "✅ Finish entry",
    "kb_history_prev": "⬅️ Earlier",
    "kb_history_next": "Later ➡️",
    "kb_donate_crypto": "🪙 Crypto (EVM, SOL)",
    "kb_donate_rub": "💳 Bank transfer",
    "kb_donate_stars": "⭐️ Telegram Stars",
    "kb_donate_back": "⬅️ Back to methods",
    "kb_donate_support": "⭐️ Support",
    "kb_donate_title": "Support DayLog AI",
    "kb_donate_description": "A contribution to the stable operation and development of the bot.",
    "kb_digest_day": "📅 Day of week",
    "kb_digest_time": "🕒 Delivery time",
    "kb_back": "⬅️ Back",
    "kb_write_developer": "💬 Write to developer",
    "kb_support_project": "⭐️ Support the project",

    # Days of the week for digest keyboard
    "kb_day_monday": "Monday",
    "kb_day_tuesday": "Tuesday",
    "kb_day_wednesday": "Wednesday",
    "kb_day_thursday": "Thursday",
    "kb_day_friday": "Friday",
    "kb_day_saturday": "Saturday",
    "kb_day_sunday": "Sunday",

    # Timezones (buttons)
    "kb_tz_kaliningrad": "Kaliningrad (MSK-1)",
    "kb_tz_moscow": "Moscow (MSK)",
    "kb_tz_samara": "Samara (MSK+1)",
    "kb_tz_yekaterinburg": "Yekaterinburg (MSK+2)",
    "kb_tz_omsk": "Omsk (MSK+3)",
    "kb_tz_krasnoyarsk": "Krasnoyarsk (MSK+4)",
    "kb_tz_irkutsk": "Irkutsk (MSK+5)",
    "kb_tz_yakutsk": "Yakutsk (MSK+6)",
    "kb_tz_vladivostok": "Vladivostok (MSK+7)",
    "kb_tz_magadan": "Magadan (MSK+8)",
    "kb_tz_kamchatka": "Kamchatka (MSK+9)",

    # ── scheduler.py ──────────────────────────────────────────────────
    "sched_nudge": (
        "👀 <b>I'm still waiting for your answer</b>\n\n"
        "We stopped at the most interesting part. Finish your thought or send \"done\" to wrap up the entry."
    ),
    "sched_daily_reminder": (
        "🌙 <b>Time to wrap up the day</b>\n\n"
        "How was your day? Tap the button below and let it all out."
    ),
    "sched_night_cleaner": (
        "💾 <b>Auto-save triggered</b>\n\n"
        "The dialogue stalled, so I carefully closed and saved your entry.\n\n"
        "<i>Already calculating AI metrics, results will appear in your statistics.</i>"
    ),

    # ── throttle.py ───────────────────────────────────────────────────
    "common_throttle": "⏳ <b>Too fast!</b>\n\nWait a couple of seconds and try again.",

    # ── analytics.py ──────────────────────────────────────────────────
    "analytics_day_summary": "📊 Day summary: {score} / 5\n\n📝 {summary}",

    # ── Language selection (onboarding) ───────────────────────────────
    "start_choose_language": "👋 Привет! Выбери язык / Hi! Choose your language:",
}
