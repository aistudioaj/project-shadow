#!/usr/bin/env python3
"""
Project Shadow - Morning Intelligence Brief
Runs daily at 7:00 AM Abu Dhabi time (03:00 UTC)
Fetches: Markets, News, Weather, Tasks, Trips, Memory
Generates: AI-powered personalized brief
Sends: Beautiful HTML email
"""

import os
import json
import requests
from datetime import datetime, timezone, timedelta
import smtplib
from email.mime.multipart import MIMEMultipart
from email.mime.text import MIMEText

# ── CONFIG FROM ENVIRONMENT ──
ANTHROPIC_KEY = os.environ['ANTHROPIC_KEY']
SUPABASE_URL  = os.environ['SUPABASE_URL']
SUPABASE_KEY  = os.environ['SUPABASE_KEY']
FINNHUB_KEY   = os.environ['FINNHUB_KEY']
EMAIL_FROM    = os.environ['EMAIL_FROM']    # Gmail address
EMAIL_PASS    = os.environ['EMAIL_PASS']    # Gmail app password
EMAIL_TO      = os.environ['EMAIL_TO']      # Recipient email
USER_ID       = os.environ.get('USER_ID', 'abdulrahman')
USER_NAME     = os.environ.get('USER_NAME', 'AJ')

# Abu Dhabi timezone (GMT+4)
ABU_DHABI_TZ = timezone(timedelta(hours=4))
NOW = datetime.now(ABU_DHABI_TZ)
TODAY_STR = NOW.strftime('%A, %B %d, %Y')
TIME_STR = NOW.strftime('%I:%M %p')

print(f"🌅 Shadow Morning Brief starting: {TODAY_STR} {TIME_STR}")

# ──────────────────────────────────────────────
# 1. FETCH PORTFOLIO & MARKET DATA
# ──────────────────────────────────────────────
def fetch_quote(symbol):
    try:
        url = f"https://finnhub.io/api/v1/quote?symbol={symbol}&token={FINNHUB_KEY}"
        r = requests.get(url, timeout=10)
        data = r.json()
        if data.get('c', 0) > 0:
            return data
    except Exception as e:
        print(f"  ⚠️ Quote error for {symbol}: {e}")
    return None

def fetch_portfolio():
    try:
        url = f"{SUPABASE_URL}/rest/v1/shadow_portfolio?user_id=eq.{USER_ID}&select=*"
        headers = {
            'apikey': SUPABASE_KEY,
            'Authorization': f'Bearer {SUPABASE_KEY}'
        }
        r = requests.get(url, headers=headers, timeout=10)
        return r.json()
    except Exception as e:
        print(f"  ⚠️ Portfolio fetch error: {e}")
        return []

def fetch_tasks():
    try:
        url = f"{SUPABASE_URL}/rest/v1/shadow_tasks?user_id=eq.{USER_ID}&status=neq.done&select=*&order=created_at.desc"
        headers = {
            'apikey': SUPABASE_KEY,
            'Authorization': f'Bearer {SUPABASE_KEY}'
        }
        r = requests.get(url, headers=headers, timeout=10)
        return r.json()
    except Exception as e:
        print(f"  ⚠️ Tasks fetch error: {e}")
        return []

def fetch_memories():
    try:
        url = f"{SUPABASE_URL}/rest/v1/shadow_memory?user_id=eq.{USER_ID}&select=*&order=importance.desc&limit=30"
        headers = {
            'apikey': SUPABASE_KEY,
            'Authorization': f'Bearer {SUPABASE_KEY}'
        }
        r = requests.get(url, headers=headers, timeout=10)
        return r.json()
    except Exception as e:
        print(f"  ⚠️ Memory fetch error: {e}")
        return []

print("📈 Fetching market data...")
WATCHLIST = ['AAPL', 'MSFT', 'NVDA', 'AMZN', 'GOOGL', 'META', 'TSLA', 'JPM']
market_data = {}
for sym in WATCHLIST:
    q = fetch_quote(sym)
    if q:
        market_data[sym] = q
        print(f"  ✅ {sym}: ${q['c']:.2f} ({q['dp']:+.2f}%)")

print("💼 Fetching portfolio...")
portfolio = fetch_portfolio()
print(f"  ✅ {len(portfolio)} holdings")

print("✅ Fetching tasks...")
tasks = fetch_tasks()
print(f"  ✅ {len(tasks)} pending tasks")

print("🧠 Fetching memories...")
memories = fetch_memories()
print(f"  ✅ {len(memories)} memories")

# ──────────────────────────────────────────────
# 2. FETCH WEATHER (Abu Dhabi)
# ──────────────────────────────────────────────
print("🌤️ Fetching weather...")
weather_info = "Weather data unavailable"
try:
    url = "https://api.open-meteo.com/v1/forecast"
    params = {
        'latitude': 24.4539,
        'longitude': 54.3773,
        'daily': 'temperature_2m_max,temperature_2m_min,weathercode,precipitation_sum',
        'current_weather': True,
        'timezone': 'Asia/Dubai',
        'forecast_days': 3
    }
    r = requests.get(url, params=params, timeout=10)
    w = r.json()
    current = w.get('current_weather', {})
    daily = w.get('daily', {})

    wcode_map = {
        0: 'Clear sky', 1: 'Mainly clear', 2: 'Partly cloudy', 3: 'Overcast',
        45: 'Foggy', 48: 'Icy fog', 51: 'Light drizzle', 53: 'Moderate drizzle',
        61: 'Slight rain', 63: 'Moderate rain', 65: 'Heavy rain',
        71: 'Slight snow', 80: 'Rain showers', 95: 'Thunderstorm'
    }
    wcode = current.get('weathercode', 0)
    condition = wcode_map.get(wcode, 'Clear')
    temp = current.get('temperature', 0)

    forecast_days = []
    if daily.get('time'):
        for i in range(min(3, len(daily['time']))):
            day_name = datetime.strptime(daily['time'][i], '%Y-%m-%d').strftime('%A')
            tmax = daily['temperature_2m_max'][i]
            tmin = daily['temperature_2m_min'][i]
            wc = daily['weathercode'][i]
            cond = wcode_map.get(wc, 'Clear')
            forecast_days.append(f"{day_name}: {cond}, {tmax:.0f}°C / {tmin:.0f}°C")

    weather_info = f"Current: {condition}, {temp:.0f}°C | " + " · ".join(forecast_days)
    print(f"  ✅ {weather_info[:80]}...")
except Exception as e:
    print(f"  ⚠️ Weather error: {e}")

# ──────────────────────────────────────────────
# 3. BUILD CONTEXT FOR CLAUDE
# ──────────────────────────────────────────────
def build_market_context():
    if not market_data:
        return "Market data unavailable - markets may be closed."
    lines = []
    for sym, q in market_data.items():
        direction = "▲" if q['dp'] >= 0 else "▼"
        lines.append(f"{sym}: ${q['c']:.2f} {direction} {q['dp']:+.2f}% (change: ${q['d']:+.2f})")
    return "\n".join(lines)

def build_portfolio_context():
    if not portfolio:
        return "No holdings tracked."
    lines = []
    total_value = 0
    total_cost = 0
    for h in portfolio:
        ticker = h.get('ticker', '')
        shares = h.get('shares', 0)
        avg_price = h.get('avg_buy_price', 0)
        q = market_data.get(ticker)
        if q and shares and avg_price:
            current_val = q['c'] * shares
            cost_basis = avg_price * shares
            gain = current_val - cost_basis
            gain_pct = (gain / cost_basis * 100) if cost_basis > 0 else 0
            total_value += current_val
            total_cost += cost_basis
            direction = "▲" if gain >= 0 else "▼"
            lines.append(f"{ticker}: {shares} shares @ ${avg_price:.2f} avg | Now ${q['c']:.2f} | Value ${current_val:,.2f} | P&L {direction} ${gain:+,.2f} ({gain_pct:+.2f}%)")
    if total_value > 0:
        total_pnl = total_value - total_cost
        total_pnl_pct = (total_pnl / total_cost * 100) if total_cost > 0 else 0
        lines.append(f"\nTOTAL PORTFOLIO: ${total_value:,.2f} | P&L: ${total_pnl:+,.2f} ({total_pnl_pct:+.2f}%)")
    return "\n".join(lines) if lines else "Holdings exist but market data unavailable."

def build_tasks_context():
    if not tasks:
        return "No pending tasks."
    today = NOW.date()
    lines = []
    overdue = [t for t in tasks if t.get('due_date') and datetime.fromisoformat(t['due_date'].replace('Z','+00:00')).date() < today]
    due_today = [t for t in tasks if t.get('due_date') and datetime.fromisoformat(t['due_date'].replace('Z','+00:00')).date() == today]
    upcoming = [t for t in tasks if not t.get('due_date')]
    if overdue:
        lines.append(f"OVERDUE ({len(overdue)}): " + ", ".join([t['title'] for t in overdue[:3]]))
    if due_today:
        lines.append(f"DUE TODAY ({len(due_today)}): " + ", ".join([t['title'] for t in due_today[:3]]))
    lines.append(f"PENDING: {len(upcoming)} tasks without due date")
    return "\n".join(lines)

def build_memory_context():
    if not memories:
        return "No memories stored."
    key_mems = [m for m in memories if m.get('importance', 1) >= 2]
    trip_mems = [m for m in memories if 'trip' in m.get('key','').lower() or 'travel' in m.get('category','').lower()]
    exam_mems = [m for m in memories if 'exam' in m.get('key','').lower() or 'assessment' in m.get('value','').lower()]
    lines = []
    if trip_mems:
        lines.append("UPCOMING TRIPS: " + "; ".join([f"{m['value']}" for m in trip_mems[:3]]))
    if exam_mems:
        lines.append("EXAMS/ASSESSMENTS: " + "; ".join([f"{m['value']}" for m in exam_mems[:2]]))
    if key_mems:
        lines.append("KEY FACTS: " + "; ".join([f"{m['key']}: {m['value']}" for m in key_mems[:5]]))
    return "\n".join(lines) if lines else "General memories stored."

# ──────────────────────────────────────────────
# 4. CALL CLAUDE FOR INTELLIGENCE
# ──────────────────────────────────────────────
print("🤖 Calling Claude for intelligence brief...")

system_prompt = f"""You are Shadow, a personal AI operating system generating a morning intelligence brief for {USER_NAME} in Abu Dhabi, UAE.

Today is {TODAY_STR} at {TIME_STR} (Abu Dhabi, GMT+4).

Your brief must be professional, insightful and genuinely useful. Be specific, not generic.
Do NOT say "I don't have real-time access" - use the data provided below.
Format with clear HTML-friendly sections using these exact markers:
[MARKET_ANALYSIS] [/MARKET_ANALYSIS]
[AI_NEWS] [/AI_NEWS]
[GEOPOLITICAL] [/GEOPOLITICAL]
[WEATHER] [/WEATHER]
[PORTFOLIO_ADVICE] [/PORTFOLIO_ADVICE]
[TASKS_PRIORITIES] [/TASKS_PRIORITIES]
[TRAVEL_UPDATES] [/TRAVEL_UPDATES]
[SHADOW_VERDICT] [/SHADOW_VERDICT]

DATA PROVIDED:
=== LIVE MARKET DATA ===
{build_market_context()}

=== PORTFOLIO ===
{build_portfolio_context()}

=== WEATHER (Abu Dhabi) ===
{weather_info}

=== PENDING TASKS ===
{build_tasks_context()}

=== MEMORY & UPCOMING EVENTS ===
{build_memory_context()}"""

user_message = f"""Generate my complete morning intelligence brief for {TODAY_STR}.

For each section:
- MARKET_ANALYSIS: Analyze the live market data above. Which stocks are leading/lagging? What does the overall market sentiment look like? Any notable moves?
- AI_NEWS: What are the most important AI and technology developments happening right now? Focus on breakthroughs, major releases, regulatory changes. (Use your knowledge up to your cutoff, flag if uncertain about recency)
- GEOPOLITICAL: Key geopolitical developments affecting markets and daily life. UAE region priority. Oil, trade, regional stability.
- WEATHER: Analyze the Abu Dhabi weather data. Any changes to plan for? Trip weather if applicable.
- PORTFOLIO_ADVICE: Based on my actual holdings and today's market moves, what should I pay attention to? Be specific and honest - not generic advice.
- TASKS_PRIORITIES: Given my tasks and today's date, what should I focus on first?
- TRAVEL_UPDATES: Any trips coming up? What should I know/prepare?
- SHADOW_VERDICT: One powerful paragraph - your overall assessment of what today means for me and what I should focus on.

Be direct, specific and genuinely useful. No fluff."""

try:
    response = requests.post(
        "https://api.anthropic.com/v1/messages",
        headers={
            "Content-Type": "application/json",
            "x-api-key": ANTHROPIC_KEY,
            "anthropic-version": "2023-06-01"
        },
        json={
            "model": "claude-sonnet-4-5",
            "max_tokens": 4000,
            "system": system_prompt,
            "messages": [{"role": "user", "content": user_message}]
        },
        timeout=60
    )
    brief_raw = response.json()['content'][0]['text']
    print("  ✅ Claude responded successfully")
except Exception as e:
    print(f"  ⚠️ Claude error: {e}")
    brief_raw = f"[SHADOW_VERDICT]Good morning {USER_NAME}. Shadow encountered an error generating today's brief. Please check the system.[/SHADOW_VERDICT]"

# ──────────────────────────────────────────────
# 5. PARSE CLAUDE RESPONSE
# ──────────────────────────────────────────────
def extract_section(text, tag):
    start = text.find(f'[{tag}]')
    end = text.find(f'[/{tag}]')
    if start != -1 and end != -1:
        return text[start+len(tag)+2:end].strip()
    return ""

sections = {
    'market': extract_section(brief_raw, 'MARKET_ANALYSIS'),
    'ai_news': extract_section(brief_raw, 'AI_NEWS'),
    'geopolitical': extract_section(brief_raw, 'GEOPOLITICAL'),
    'weather': extract_section(brief_raw, 'WEATHER'),
    'portfolio': extract_section(brief_raw, 'PORTFOLIO_ADVICE'),
    'tasks': extract_section(brief_raw, 'TASKS_PRIORITIES'),
    'travel': extract_section(brief_raw, 'TRAVEL_UPDATES'),
    'verdict': extract_section(brief_raw, 'SHADOW_VERDICT'),
}

# ──────────────────────────────────────────────
# 6. BUILD PORTFOLIO TABLE
# ──────────────────────────────────────────────
def build_portfolio_table():
    if not portfolio or not market_data:
        return "<p style='color:#6b7280;font-size:13px;'>No holdings or market data available.</p>"

    rows = []
    total_value = 0
    total_cost = 0

    for h in portfolio:
        ticker = h.get('ticker', '')
        shares = h.get('shares', 0)
        avg_price = h.get('avg_buy_price', 0)
        q = market_data.get(ticker)
        if not q or not shares:
            continue
        current_val = q['c'] * shares
        cost_basis = avg_price * shares
        gain = current_val - cost_basis
        gain_pct = (gain / cost_basis * 100) if cost_basis > 0 else 0
        day_change = q['d'] * shares
        total_value += current_val
        total_cost += cost_basis

        gain_color = '#10d9a0' if gain >= 0 else '#f43f5e'
        day_color = '#10d9a0' if q['dp'] >= 0 else '#f43f5e'
        gain_arrow = '▲' if gain >= 0 else '▼'

        rows.append(f"""
        <tr>
          <td style="padding:12px 16px;border-bottom:1px solid #1e2840;">
            <span style="font-family:monospace;font-weight:700;color:#e2e8f8;">{ticker}</span>
            <div style="font-size:11px;color:#6b7280;margin-top:2px;">{shares} shares</div>
          </td>
          <td style="padding:12px 16px;border-bottom:1px solid #1e2840;font-family:monospace;color:#e2e8f8;">${q['c']:.2f}</td>
          <td style="padding:12px 16px;border-bottom:1px solid #1e2840;font-family:monospace;color:{day_color};">{'+' if q['dp']>=0 else ''}{q['dp']:.2f}%</td>
          <td style="padding:12px 16px;border-bottom:1px solid #1e2840;font-family:monospace;color:#e2e8f8;">${current_val:,.2f}</td>
          <td style="padding:12px 16px;border-bottom:1px solid #1e2840;font-family:monospace;color:{gain_color};">{gain_arrow} ${abs(gain):,.2f} ({'+' if gain_pct>=0 else ''}{gain_pct:.2f}%)</td>
        </tr>""")

    if not rows:
        return "<p style='color:#6b7280;'>Holdings data unavailable today.</p>"

    total_pnl = total_value - total_cost
    total_pnl_pct = (total_pnl / total_cost * 100) if total_cost > 0 else 0
    total_color = '#10d9a0' if total_pnl >= 0 else '#f43f5e'
    total_arrow = '▲' if total_pnl >= 0 else '▼'

    return f"""
    <table style="width:100%;border-collapse:collapse;">
      <thead>
        <tr style="background:#0e1220;">
          <th style="padding:10px 16px;text-align:left;font-family:monospace;font-size:10px;color:#6b7280;letter-spacing:2px;text-transform:uppercase;">TICKER</th>
          <th style="padding:10px 16px;text-align:left;font-family:monospace;font-size:10px;color:#6b7280;letter-spacing:2px;text-transform:uppercase;">PRICE</th>
          <th style="padding:10px 16px;text-align:left;font-family:monospace;font-size:10px;color:#6b7280;letter-spacing:2px;text-transform:uppercase;">TODAY</th>
          <th style="padding:10px 16px;text-align:left;font-family:monospace;font-size:10px;color:#6b7280;letter-spacing:2px;text-transform:uppercase;">VALUE</th>
          <th style="padding:10px 16px;text-align:left;font-family:monospace;font-size:10px;color:#6b7280;letter-spacing:2px;text-transform:uppercase;">P&L</th>
        </tr>
      </thead>
      <tbody>
        {''.join(rows)}
        <tr style="background:#0e1220;">
          <td colspan="3" style="padding:14px 16px;font-family:monospace;font-weight:700;color:#e2e8f8;">TOTAL PORTFOLIO</td>
          <td style="padding:14px 16px;font-family:monospace;font-weight:700;color:#e2e8f8;">${total_value:,.2f}</td>
          <td style="padding:14px 16px;font-family:monospace;font-weight:700;color:{total_color};">{total_arrow} ${abs(total_pnl):,.2f} ({'+' if total_pnl_pct>=0 else ''}{total_pnl_pct:.2f}%)</td>
        </tr>
      </tbody>
    </table>"""

# ──────────────────────────────────────────────
# 7. BUILD MARKET TICKER ROW
# ──────────────────────────────────────────────
def build_market_ticker():
    items = []
    for sym, q in market_data.items():
        color = '#10d9a0' if q['dp'] >= 0 else '#f43f5e'
        arrow = '▲' if q['dp'] >= 0 else '▼'
        items.append(f"""
        <td style="padding:10px 20px;border-right:1px solid #1e2840;text-align:center;white-space:nowrap;">
          <div style="font-family:monospace;font-size:11px;font-weight:700;color:#8892a8;margin-bottom:4px;">{sym}</div>
          <div style="font-family:monospace;font-size:15px;font-weight:700;color:#e2e8f8;">${q['c']:.2f}</div>
          <div style="font-family:monospace;font-size:11px;color:{color};">{arrow} {q['dp']:+.2f}%</div>
        </td>""")
    return '<table style="width:100%;border-collapse:collapse;"><tr>' + ''.join(items) + '</tr></table>'

# ──────────────────────────────────────────────
# 8. BUILD HTML EMAIL
# ──────────────────────────────────────────────
def section_html(icon, title, content, accent='#4f8ef7'):
    if not content:
        return ""
    formatted = content.replace('\n', '<br>').replace('**', '<strong>').replace('**', '</strong>')
    return f"""
    <div style="margin-bottom:24px;background:#0e1220;border:1px solid #1e2840;border-radius:12px;overflow:hidden;">
      <div style="padding:14px 20px;background:#141928;border-bottom:1px solid #1e2840;display:flex;align-items:center;gap:10px;">
        <span style="font-size:18px;">{icon}</span>
        <span style="font-family:monospace;font-size:11px;letter-spacing:2px;color:{accent};text-transform:uppercase;font-weight:700;">{title}</span>
      </div>
      <div style="padding:20px;font-size:14px;color:#8892a8;line-height:1.7;">
        {formatted}
      </div>
    </div>"""

h = NOW.hour
greeting_word = "Good morning" if h < 12 else "Good afternoon" if h < 17 else "Good evening"

html_email = f"""<!DOCTYPE html>
<html>
<head>
<meta charset="UTF-8">
<meta name="viewport" content="width=device-width, initial-scale=1.0">
<title>Shadow Brief · {TODAY_STR}</title>
</head>
<body style="margin:0;padding:0;background:#060810;font-family:'Inter',sans-serif;">
<table width="100%" cellpadding="0" cellspacing="0" style="background:#060810;min-height:100vh;">
<tr><td align="center" style="padding:20px;">
<table width="680" cellpadding="0" cellspacing="0" style="max-width:680px;width:100%;">

  <!-- HEADER -->
  <tr><td style="background:linear-gradient(135deg,#0e1220 0%,#141928 100%);border:1px solid #1e2840;border-radius:16px;padding:32px;margin-bottom:24px;text-align:center;">
    <div style="font-family:monospace;font-size:42px;font-weight:900;letter-spacing:8px;color:#4f8ef7;text-shadow:0 0 40px rgba(79,142,247,0.4);margin-bottom:8px;">SHADOW</div>
    <div style="font-family:monospace;font-size:11px;letter-spacing:3px;color:#454d60;text-transform:uppercase;margin-bottom:24px;">MORNING INTELLIGENCE BRIEF</div>
    <div style="font-family:monospace;font-size:13px;color:#7889a8;">{TODAY_STR} · {TIME_STR} · Abu Dhabi, GMT+4</div>
  </td></tr>

  <tr><td style="height:16px;"></td></tr>

  <!-- GREETING -->
  <tr><td style="background:#0e1220;border:1px solid #1e2840;border-radius:12px;padding:24px;margin-bottom:16px;">
    <div style="font-size:22px;font-weight:700;color:#e2e8f8;margin-bottom:8px;">{greeting_word}, {USER_NAME}. 👋</div>
    <div style="font-size:14px;color:#6b7280;line-height:1.6;">Here is your daily intelligence brief. Shadow has analyzed your portfolio, monitored global developments, and prepared everything you need to start the day sharp.</div>
  </td></tr>

  <tr><td style="height:16px;"></td></tr>

  <!-- MARKET TICKER -->
  <tr><td style="background:#0e1220;border:1px solid #1e2840;border-radius:12px;overflow:hidden;margin-bottom:16px;">
    <div style="padding:12px 20px;background:#141928;border-bottom:1px solid #1e2840;">
      <span style="font-family:monospace;font-size:10px;letter-spacing:2px;color:#4f8ef7;text-transform:uppercase;font-weight:700;">📊 Live Market Snapshot</span>
    </div>
    <div style="overflow-x:auto;">
      {build_market_ticker()}
    </div>
  </td></tr>

  <tr><td style="height:16px;"></td></tr>

  <!-- SHADOW VERDICT (top) -->
  {"" if not sections['verdict'] else f"""
  <tr><td style="background:linear-gradient(135deg,#1d4ed8,#2563eb);border-radius:12px;padding:24px;margin-bottom:16px;">
    <div style="font-family:monospace;font-size:10px;letter-spacing:2px;color:rgba(255,255,255,0.6);text-transform:uppercase;margin-bottom:12px;">⚡ Shadow's Verdict</div>
    <div style="font-size:15px;color:#ffffff;line-height:1.7;font-weight:500;">{sections['verdict'].replace(chr(10),'<br>')}</div>
  </td></tr>
  <tr><td style="height:16px;"></td></tr>"""}

  <!-- PORTFOLIO TABLE -->
  <tr><td style="background:#0e1220;border:1px solid #1e2840;border-radius:12px;overflow:hidden;margin-bottom:16px;">
    <div style="padding:14px 20px;background:#141928;border-bottom:1px solid #1e2840;">
      <span style="font-family:monospace;font-size:11px;letter-spacing:2px;color:#4f8ef7;text-transform:uppercase;font-weight:700;">💼 Your Portfolio</span>
    </div>
    <div style="overflow-x:auto;">
      {build_portfolio_table()}
    </div>
  </td></tr>

  <tr><td style="height:16px;"></td></tr>

  <!-- SECTIONS -->
  <tr><td>
    {section_html('📈', 'Market Analysis', sections['market'], '#4f8ef7')}
    {section_html('🤖', 'AI & Technology News', sections['ai_news'], '#a855f7')}
    {section_html('🌍', 'Geopolitical Intelligence', sections['geopolitical'], '#f59e0b')}
    {section_html('☀️', 'Weather & Conditions', sections['weather'], '#10d9a0')}
    {section_html('💼', 'Portfolio Intelligence', sections['portfolio'], '#4f8ef7')}
    {section_html('✅', 'Tasks & Priorities', sections['tasks'], '#10d9a0')}
    {section_html('✈️', 'Travel Updates', sections['travel'], '#f59e0b')}
  </td></tr>

  <!-- CTA -->
  <tr><td style="text-align:center;padding:24px 0;">
    <a href="https://aistudioaj.github.io/project-shadow/" style="display:inline-block;background:linear-gradient(135deg,#2563eb,#4f8ef7);color:#ffffff;text-decoration:none;padding:14px 32px;border-radius:10px;font-family:monospace;font-size:12px;font-weight:700;letter-spacing:2px;text-transform:uppercase;">
      ⚡ OPEN SHADOW
    </a>
  </td></tr>

  <!-- FOOTER -->
  <tr><td style="padding:20px;text-align:center;border-top:1px solid #1e2840;">
    <div style="font-family:monospace;font-size:10px;color:#3d4d6a;letter-spacing:1px;">
      PROJECT SHADOW · PERSONAL AI OPERATING SYSTEM<br>
      Generated {TODAY_STR} at {TIME_STR} Abu Dhabi<br>
      <span style="color:#4f8ef7;">shadow.aistudio.aj</span>
    </div>
  </td></tr>

</table>
</td></tr>
</table>
</body>
</html>"""

# ──────────────────────────────────────────────
# 9. SEND EMAIL
# ──────────────────────────────────────────────
print("📧 Sending email...")

msg = MIMEMultipart('alternative')
msg['Subject'] = f"⚡ Shadow Brief · {NOW.strftime('%a %b %d')} · {len(portfolio)} Holdings · {len(tasks)} Tasks"
msg['From'] = f"Shadow AI <{EMAIL_FROM}>"
msg['To'] = EMAIL_TO

# Plain text fallback
plain_text = f"""Shadow Morning Brief - {TODAY_STR}

MARKET ANALYSIS:
{sections.get('market', 'N/A')}

AI NEWS:
{sections.get('ai_news', 'N/A')}

GEOPOLITICAL:
{sections.get('geopolitical', 'N/A')}

PORTFOLIO:
{sections.get('portfolio', 'N/A')}

TASKS:
{sections.get('tasks', 'N/A')}

SHADOW VERDICT:
{sections.get('verdict', 'N/A')}

Open Shadow: https://aistudioaj.github.io/project-shadow/
"""

msg.attach(MIMEText(plain_text, 'plain'))
msg.attach(MIMEText(html_email, 'html'))

try:
    server = smtplib.SMTP_SSL('smtp.gmail.com', 465)
    server.login(EMAIL_FROM, EMAIL_PASS)
    server.sendmail(EMAIL_FROM, EMAIL_TO, msg.as_string())
    server.quit()
    print(f"  ✅ Email sent to {EMAIL_TO}")
except Exception as e:
    print(f"  ❌ Email error: {e}")
    raise

print(f"\n✅ Shadow Morning Brief complete! {TODAY_STR}")
print(f"   Sections generated: {sum(1 for v in sections.values() if v)}/8")
print(f"   Portfolio: {len(portfolio)} holdings")
print(f"   Tasks: {len(tasks)} pending")
print(f"   Memories: {len(memories)} stored")
