# -*- coding: utf-8 -*-
#!/usr/bin/env python3
"""
Project Shadow - Morning Intelligence Brief
Runs daily at 7:00 AM Abu Dhabi time (03:00 UTC)
"""

import os
import json
import requests
from datetime import datetime, timezone, timedelta
import smtplib
from email.mime.multipart import MIMEMultipart
from email.mime.text import MIMEText

ANTHROPIC_KEY = os.environ['ANTHROPIC_KEY']
SUPABASE_URL  = os.environ['SUPABASE_URL']
SUPABASE_KEY  = os.environ['SUPABASE_KEY']
FINNHUB_KEY   = os.environ['FINNHUB_KEY']
EMAIL_FROM    = os.environ['EMAIL_FROM']
EMAIL_PASS    = os.environ['EMAIL_PASS']
EMAIL_TO      = os.environ['EMAIL_TO']
USER_ID       = os.environ.get('USER_ID', 'abdulrahman')
USER_NAME     = os.environ.get('USER_NAME', 'AJ')

ABU_DHABI_TZ = timezone(timedelta(hours=4))
NOW = datetime.now(ABU_DHABI_TZ)
TODAY_STR = NOW.strftime('%A, %B %d, %Y')
TIME_STR = NOW.strftime('%I:%M %p')

print("Shadow Morning Brief starting: " + TODAY_STR + " " + TIME_STR)

def fetch_quote(symbol):
    try:
        url = "https://finnhub.io/api/v1/quote?symbol=" + symbol + "&token=" + FINNHUB_KEY
        r = requests.get(url, timeout=10)
        data = r.json()
        if data.get('c', 0) > 0:
            return data
    except Exception as e:
        print("Quote error for " + symbol + ": " + str(e))
    return None

def fetch_supabase(table, filters=""):
    try:
        url = SUPABASE_URL + "/rest/v1/" + table + "?user_id=eq." + USER_ID + filters + "&select=*"
        headers = {'apikey': SUPABASE_KEY, 'Authorization': 'Bearer ' + SUPABASE_KEY}
        r = requests.get(url, headers=headers, timeout=10)
        return r.json()
    except Exception as e:
        print("Supabase error " + table + ": " + str(e))
        return []

print("Fetching market data...")
WATCHLIST = ['AAPL', 'MSFT', 'NVDA', 'AMZN', 'GOOGL', 'META', 'TSLA', 'JPM']
market_data = {}
for sym in WATCHLIST:
    q = fetch_quote(sym)
    if q:
        market_data[sym] = q
        print("  " + sym + ": $" + str(round(q['c'],2)) + " (" + str(round(q['dp'],2)) + "%)")

print("Fetching portfolio...")
portfolio = fetch_supabase('shadow_portfolio')
print("  " + str(len(portfolio)) + " holdings")

print("Fetching tasks...")
tasks = fetch_supabase('shadow_tasks', '&status=neq.done')
print("  " + str(len(tasks)) + " pending")

print("Fetching memories...")
memories = fetch_supabase('shadow_memory', '&order=importance.desc&limit=30')
print("  " + str(len(memories)) + " memories")

print("Fetching weather...")
weather_info = "Weather unavailable"
try:
    params = {
        'latitude': 24.4539, 'longitude': 54.3773,
        'daily': 'temperature_2m_max,temperature_2m_min,weathercode',
        'current_weather': True, 'timezone': 'Asia/Dubai', 'forecast_days': 3
    }
    r = requests.get("https://api.open-meteo.com/v1/forecast", params=params, timeout=10)
    w = r.json()
    current = w.get('current_weather', {})
    daily = w.get('daily', {})
    wcode_map = {0:'Clear',1:'Mainly clear',2:'Partly cloudy',3:'Overcast',45:'Foggy',
                 61:'Rain',63:'Moderate rain',80:'Showers',95:'Thunderstorm'}
    temp = current.get('temperature', 0)
    cond = wcode_map.get(current.get('weathercode', 0), 'Clear')
    forecast = []
    if daily.get('time'):
        for i in range(min(3, len(daily['time']))):
            day = datetime.strptime(daily['time'][i], '%Y-%m-%d').strftime('%a')
            tmax = daily['temperature_2m_max'][i]
            tmin = daily['temperature_2m_min'][i]
            dc = wcode_map.get(daily['weathercode'][i], 'Clear')
            forecast.append(day + ": " + dc + " " + str(round(tmax)) + "/" + str(round(tmin)) + "C")
    weather_info = "Now: " + cond + " " + str(round(temp)) + "C | " + " | ".join(forecast)
    print("  " + weather_info[:60])
except Exception as e:
    print("  Weather error: " + str(e))

def build_market_context():
    if not market_data:
        return "Market data unavailable."
    lines = []
    for sym, q in market_data.items():
        arrow = "up" if q['dp'] >= 0 else "down"
        lines.append(sym + ": $" + str(round(q['c'],2)) + " " + arrow + " " + str(round(q['dp'],2)) + "%")
    return "\n".join(lines)

def build_portfolio_context():
    if not portfolio:
        return "No holdings."
    lines = []
    total_value = 0
    total_cost = 0
    for h in portfolio:
        ticker = h.get('ticker','')
        shares = h.get('shares', 0)
        avg = h.get('avg_buy_price', 0)
        q = market_data.get(ticker)
        if q and shares and avg:
            val = q['c'] * shares
            cost = avg * shares
            gain = val - cost
            pct = (gain/cost*100) if cost > 0 else 0
            total_value += val
            total_cost += cost
            lines.append(ticker + ": " + str(shares) + " shares | $" + str(round(q['c'],2)) + " | Value $" + str(round(val,2)) + " | PnL " + str(round(gain,2)) + " (" + str(round(pct,2)) + "%)")
    if total_value > 0:
        total_pnl = total_value - total_cost
        total_pct = (total_pnl/total_cost*100) if total_cost > 0 else 0
        lines.append("TOTAL: $" + str(round(total_value,2)) + " | PnL $" + str(round(total_pnl,2)) + " (" + str(round(total_pct,2)) + "%)")
    return "\n".join(lines)

def build_tasks_context():
    if not tasks:
        return "No pending tasks."
    return str(len(tasks)) + " pending tasks: " + ", ".join([t.get('title','') for t in tasks[:5]])

def build_memory_context():
    if not memories:
        return "No memories."
    trip_mems = [m for m in memories if 'trip' in m.get('key','').lower()]
    exam_mems = [m for m in memories if 'exam' in m.get('key','').lower() or 'assessment' in m.get('value','').lower()]
    key_mems = [m for m in memories if m.get('importance',1) >= 2][:5]
    lines = []
    if trip_mems:
        lines.append("TRIPS: " + "; ".join([m['value'] for m in trip_mems[:2]]))
    if exam_mems:
        lines.append("EXAMS: " + "; ".join([m['value'] for m in exam_mems[:2]]))
    if key_mems:
        lines.append("KEY: " + "; ".join([m['key'] + ": " + m['value'] for m in key_mems]))
    return "\n".join(lines) if lines else "General memories stored."

print("Calling Claude...")
system_prompt = (
    "You are Shadow, personal AI OS for " + USER_NAME + " in Abu Dhabi, UAE.\n"
    "Today is " + TODAY_STR + " at " + TIME_STR + " (Abu Dhabi, GMT+4).\n"
    "Generate a morning intelligence brief. Use the data provided. Be specific and direct.\n"
    "Use these exact section markers:\n"
    "[MARKET_ANALYSIS] [/MARKET_ANALYSIS]\n"
    "[AI_NEWS] [/AI_NEWS]\n"
    "[GEOPOLITICAL] [/GEOPOLITICAL]\n"
    "[WEATHER] [/WEATHER]\n"
    "[PORTFOLIO_ADVICE] [/PORTFOLIO_ADVICE]\n"
    "[TASKS_PRIORITIES] [/TASKS_PRIORITIES]\n"
    "[TRAVEL_UPDATES] [/TRAVEL_UPDATES]\n"
    "[SHADOW_VERDICT] [/SHADOW_VERDICT]\n\n"
    "LIVE MARKET DATA:\n" + build_market_context() + "\n\n"
    "PORTFOLIO:\n" + build_portfolio_context() + "\n\n"
    "WEATHER:\n" + weather_info + "\n\n"
    "TASKS:\n" + build_tasks_context() + "\n\n"
    "MEMORY:\n" + build_memory_context()
)

user_message = (
    "Generate my complete morning brief for " + TODAY_STR + ". "
    "Cover: market analysis with specific stock insights, latest AI and tech news, "
    "key geopolitical developments especially UAE region, weather analysis, "
    "portfolio-specific advice based on my actual holdings, task priorities, "
    "any travel updates from memory, and your overall Shadow Verdict for the day."
)

brief_raw = ""
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
    print("  Claude responded OK")
except Exception as e:
    print("  Claude error: " + str(e))
    brief_raw = "[SHADOW_VERDICT]Good morning " + USER_NAME + ". Shadow encountered an error today.[/SHADOW_VERDICT]"

def extract(text, tag):
    start = text.find('[' + tag + ']')
    end = text.find('[/' + tag + ']')
    if start != -1 and end != -1:
        return text[start+len(tag)+2:end].strip()
    return ""

sections = {
    'market':    extract(brief_raw, 'MARKET_ANALYSIS'),
    'ai_news':   extract(brief_raw, 'AI_NEWS'),
    'geo':       extract(brief_raw, 'GEOPOLITICAL'),
    'weather':   extract(brief_raw, 'WEATHER'),
    'portfolio': extract(brief_raw, 'PORTFOLIO_ADVICE'),
    'tasks':     extract(brief_raw, 'TASKS_PRIORITIES'),
    'travel':    extract(brief_raw, 'TRAVEL_UPDATES'),
    'verdict':   extract(brief_raw, 'SHADOW_VERDICT'),
}

def fmt(text):
    return text.replace('\n', '<br>')

def make_section(title, content, color):
    if not content:
        return ""
    return (
        '<div style="margin-bottom:20px;background:#0e1220;border:1px solid #1e2840;border-radius:12px;overflow:hidden;">'
        '<div style="padding:12px 20px;background:#141928;border-bottom:1px solid #1e2840;">'
        '<span style="font-family:monospace;font-size:11px;letter-spacing:2px;color:' + color + ';text-transform:uppercase;font-weight:700;">' + title + '</span>'
        '</div>'
        '<div style="padding:20px;font-size:14px;color:#8892a8;line-height:1.7;">' + fmt(content) + '</div>'
        '</div>'
    )

def make_portfolio_table():
    if not portfolio or not market_data:
        return '<p style="color:#6b7280;">No holdings data.</p>'
    rows = ""
    total_value = 0
    total_cost = 0
    for h in portfolio:
        ticker = h.get('ticker','')
        shares = h.get('shares', 0)
        avg = h.get('avg_buy_price', 0)
        q = market_data.get(ticker)
        if not q or not shares:
            continue
        val = q['c'] * shares
        cost = avg * shares
        gain = val - cost
        pct = (gain/cost*100) if cost > 0 else 0
        total_value += val
        total_cost += cost
        gain_color = '#10d9a0' if gain >= 0 else '#f43f5e'
        day_color = '#10d9a0' if q['dp'] >= 0 else '#f43f5e'
        rows += (
            '<tr>'
            '<td style="padding:10px 16px;border-bottom:1px solid #1e2840;font-family:monospace;font-weight:700;color:#e2e8f8;">' + ticker + '<div style="font-size:11px;color:#6b7280;">' + str(shares) + ' shares</div></td>'
            '<td style="padding:10px 16px;border-bottom:1px solid #1e2840;font-family:monospace;color:#e2e8f8;">$' + str(round(q['c'],2)) + '</td>'
            '<td style="padding:10px 16px;border-bottom:1px solid #1e2840;font-family:monospace;color:' + day_color + ';">' + ('+' if q['dp']>=0 else '') + str(round(q['dp'],2)) + '%</td>'
            '<td style="padding:10px 16px;border-bottom:1px solid #1e2840;font-family:monospace;color:#e2e8f8;">$' + str(round(val,2)) + '</td>'
            '<td style="padding:10px 16px;border-bottom:1px solid #1e2840;font-family:monospace;color:' + gain_color + ';">' + ('+' if gain>=0 else '') + '$' + str(round(abs(gain),2)) + ' (' + ('+' if pct>=0 else '') + str(round(pct,2)) + '%)</td>'
            '</tr>'
        )
    if not rows:
        return '<p style="color:#6b7280;">Holdings unavailable today.</p>'
    total_pnl = total_value - total_cost
    total_pct = (total_pnl/total_cost*100) if total_cost > 0 else 0
    total_color = '#10d9a0' if total_pnl >= 0 else '#f43f5e'
    rows += (
        '<tr style="background:#141928;">'
        '<td colspan="3" style="padding:12px 16px;font-family:monospace;font-weight:700;color:#e2e8f8;">TOTAL</td>'
        '<td style="padding:12px 16px;font-family:monospace;font-weight:700;color:#e2e8f8;">$' + str(round(total_value,2)) + '</td>'
        '<td style="padding:12px 16px;font-family:monospace;font-weight:700;color:' + total_color + ';">' + ('+' if total_pnl>=0 else '') + '$' + str(round(abs(total_pnl),2)) + ' (' + ('+' if total_pct>=0 else '') + str(round(total_pct,2)) + '%)</td>'
        '</tr>'
    )
    return (
        '<table style="width:100%;border-collapse:collapse;">'
        '<thead><tr style="background:#141928;">'
        '<th style="padding:10px 16px;text-align:left;font-family:monospace;font-size:10px;color:#6b7280;letter-spacing:2px;">TICKER</th>'
        '<th style="padding:10px 16px;text-align:left;font-family:monospace;font-size:10px;color:#6b7280;letter-spacing:2px;">PRICE</th>'
        '<th style="padding:10px 16px;text-align:left;font-family:monospace;font-size:10px;color:#6b7280;letter-spacing:2px;">TODAY</th>'
        '<th style="padding:10px 16px;text-align:left;font-family:monospace;font-size:10px;color:#6b7280;letter-spacing:2px;">VALUE</th>'
        '<th style="padding:10px 16px;text-align:left;font-family:monospace;font-size:10px;color:#6b7280;letter-spacing:2px;">P&amp;L</th>'
        '</tr></thead>'
        '<tbody>' + rows + '</tbody>'
        '</table>'
    )

def make_ticker_row():
    items = ""
    for sym, q in market_data.items():
        color = '#10d9a0' if q['dp'] >= 0 else '#f43f5e'
        arrow = "+" if q['dp'] >= 0 else ""
        items += (
            '<td style="padding:10px 16px;border-right:1px solid #1e2840;text-align:center;">'
            '<div style="font-family:monospace;font-size:11px;color:#8892a8;margin-bottom:4px;">' + sym + '</div>'
            '<div style="font-family:monospace;font-size:15px;font-weight:700;color:#e2e8f8;">$' + str(round(q['c'],2)) + '</div>'
            '<div style="font-family:monospace;font-size:11px;color:' + color + ';">' + arrow + str(round(q['dp'],2)) + '%</div>'
            '</td>'
        )
    return '<table style="width:100%;border-collapse:collapse;"><tr>' + items + '</tr></table>'

h = NOW.hour
greeting = "Good morning" if h < 12 else "Good afternoon" if h < 17 else "Good evening"

verdict_block = ""
if sections.get('verdict'):
    verdict_block = (
        '<tr><td style="background:linear-gradient(135deg,#1d4ed8,#2563eb);border-radius:12px;padding:24px;">'
        '<div style="font-family:monospace;font-size:10px;letter-spacing:2px;color:rgba(255,255,255,0.6);text-transform:uppercase;margin-bottom:12px;">SHADOW VERDICT</div>'
        '<div style="font-size:15px;color:#ffffff;line-height:1.7;font-weight:500;">' + fmt(sections['verdict']) + '</div>'
        '</td></tr>'
        '<tr><td style="height:16px;"></td></tr>'
    )

html_email = (
    '<!DOCTYPE html><html><head><meta charset="UTF-8">'
    '<title>Shadow Brief</title></head>'
    '<body style="margin:0;padding:0;background:#060810;font-family:Arial,sans-serif;">'
    '<table width="100%" cellpadding="0" cellspacing="0" style="background:#060810;">'
    '<tr><td align="center" style="padding:20px;">'
    '<table width="680" cellpadding="0" cellspacing="0" style="max-width:680px;width:100%;">'
    '<tr><td style="background:#0e1220;border:1px solid #1e2840;border-radius:16px;padding:32px;text-align:center;">'
    '<div style="font-family:monospace;font-size:42px;font-weight:900;letter-spacing:8px;color:#4f8ef7;">SHADOW</div>'
    '<div style="font-family:monospace;font-size:11px;letter-spacing:3px;color:#454d60;text-transform:uppercase;margin:8px 0 24px;">MORNING INTELLIGENCE BRIEF</div>'
    '<div style="font-family:monospace;font-size:13px;color:#7889a8;">' + TODAY_STR + ' - ' + TIME_STR + ' - Abu Dhabi GMT+4</div>'
    '</td></tr>'
    '<tr><td style="height:16px;"></td></tr>'
    '<tr><td style="background:#0e1220;border:1px solid #1e2840;border-radius:12px;padding:24px;">'
    '<div style="font-size:22px;font-weight:700;color:#e2e8f8;margin-bottom:8px;">' + greeting + ', ' + USER_NAME + '.</div>'
    '<div style="font-size:14px;color:#6b7280;line-height:1.6;">Here is your daily Shadow intelligence brief.</div>'
    '</td></tr>'
    '<tr><td style="height:16px;"></td></tr>'
    '<tr><td style="background:#0e1220;border:1px solid #1e2840;border-radius:12px;overflow:hidden;">'
    '<div style="padding:12px 20px;background:#141928;border-bottom:1px solid #1e2840;">'
    '<span style="font-family:monospace;font-size:10px;letter-spacing:2px;color:#4f8ef7;text-transform:uppercase;font-weight:700;">LIVE MARKET SNAPSHOT</span>'
    '</div>' + make_ticker_row() + '</td></tr>'
    '<tr><td style="height:16px;"></td></tr>'
    + verdict_block +
    '<tr><td style="background:#0e1220;border:1px solid #1e2840;border-radius:12px;overflow:hidden;">'
    '<div style="padding:12px 20px;background:#141928;border-bottom:1px solid #1e2840;">'
    '<span style="font-family:monospace;font-size:11px;letter-spacing:2px;color:#4f8ef7;text-transform:uppercase;font-weight:700;">YOUR PORTFOLIO</span>'
    '</div>' + make_portfolio_table() + '</td></tr>'
    '<tr><td style="height:16px;"></td></tr>'
    '<tr><td>'
    + make_section('MARKET ANALYSIS', sections.get('market',''), '#4f8ef7')
    + make_section('AI AND TECHNOLOGY NEWS', sections.get('ai_news',''), '#a855f7')
    + make_section('GEOPOLITICAL INTELLIGENCE', sections.get('geo',''), '#f59e0b')
    + make_section('WEATHER AND CONDITIONS', sections.get('weather',''), '#10d9a0')
    + make_section('PORTFOLIO INTELLIGENCE', sections.get('portfolio',''), '#4f8ef7')
    + make_section('TASKS AND PRIORITIES', sections.get('tasks',''), '#10d9a0')
    + make_section('TRAVEL UPDATES', sections.get('travel',''), '#f59e0b')
    + '</td></tr>'
    '<tr><td style="text-align:center;padding:24px 0;">'
    '<a href="https://aistudioaj.github.io/project-shadow/" style="display:inline-block;background:linear-gradient(135deg,#2563eb,#4f8ef7);color:#ffffff;text-decoration:none;padding:14px 32px;border-radius:10px;font-family:monospace;font-size:12px;font-weight:700;letter-spacing:2px;text-transform:uppercase;">OPEN SHADOW</a>'
    '</td></tr>'
    '<tr><td style="padding:20px;text-align:center;border-top:1px solid #1e2840;">'
    '<div style="font-family:monospace;font-size:10px;color:#3d4d6a;">PROJECT SHADOW - ' + TODAY_STR + '</div>'
    '</td></tr>'
    '</table></td></tr></table></body></html>'
)

print("Sending email...")
msg = MIMEMultipart('alternative')
msg['Subject'] = "Shadow Brief - " + NOW.strftime('%a %b %d') + " - " + str(len(portfolio)) + " Holdings"
msg['From'] = "Shadow AI <" + EMAIL_FROM + ">"
msg['To'] = EMAIL_TO

plain = "Shadow Morning Brief - " + TODAY_STR + "\n\n"
for key, val in sections.items():
    if val:
        plain += key.upper() + ":\n" + val + "\n\n"
plain += "Open Shadow: https://aistudioaj.github.io/project-shadow/"

msg.attach(MIMEText(plain, 'plain'))
msg.attach(MIMEText(html_email, 'html'))

try:
    server = smtplib.SMTP_SSL('smtp.gmail.com', 465)
    server.login(EMAIL_FROM, EMAIL_PASS)
    server.sendmail(EMAIL_FROM, EMAIL_TO, msg.as_string())
    server.quit()
    print("Email sent to " + EMAIL_TO)
except Exception as e:
    print("Email error: " + str(e))
    raise

print("Shadow Morning Brief complete! " + TODAY_STR)
