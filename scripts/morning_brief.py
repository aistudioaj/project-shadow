# -*- coding: utf-8 -*-
#!/usr/bin/env python3
"""
Project Shadow - Morning Intelligence Brief v4
JPMorgan analyst quality + Garmin health data
Runs daily at 7:00 AM Abu Dhabi time (03:00 UTC)
"""

import os
import json
import requests
from datetime import datetime, timezone, timedelta

ANTHROPIC_KEY = os.environ['ANTHROPIC_KEY']
SUPABASE_URL  = os.environ['SUPABASE_URL']
SUPABASE_KEY  = os.environ['SUPABASE_KEY']
FINNHUB_KEY   = os.environ['FINNHUB_KEY']
EMAIL_FROM    = os.environ['EMAIL_FROM']
EMAIL_TO      = os.environ['EMAIL_TO']
RESEND_KEY    = os.environ['RESEND_KEY']
GARMIN_EMAIL  = os.environ.get('GARMIN_EMAIL','')
GARMIN_PASSWORD = os.environ.get('GARMIN_PASSWORD','')
USER_ID       = os.environ.get('USER_ID', 'abdulrahman')
USER_NAME     = os.environ.get('USER_NAME', 'AJ')

ABU_DHABI_TZ = timezone(timedelta(hours=4))
NOW = datetime.now(ABU_DHABI_TZ)
TODAY_STR = NOW.strftime('%A, %B %d, %Y')
TIME_STR = NOW.strftime('%I:%M %p')
DATE_SHORT = NOW.strftime('%a %b %d')

print("Shadow Morning Brief v4: " + TODAY_STR + " " + TIME_STR)

def fetch_quote(symbol):
    try:
        url = "https://finnhub.io/api/v1/quote?symbol=" + symbol + "&token=" + FINNHUB_KEY
        r = requests.get(url, timeout=10)
        d = r.json()
        if d.get('c', 0) > 0:
            return d
    except Exception as e:
        print("Quote error " + symbol + ": " + str(e))
    return None

def fetch_yahoo(symbol):
    import urllib.parse
    encoded = urllib.parse.quote(symbol)
    urls = [
        "https://query1.finance.yahoo.com/v8/finance/chart/" + encoded + "?interval=1d&range=1d",
        "https://query2.finance.yahoo.com/v8/finance/chart/" + encoded + "?interval=1d&range=1d",
    ]
    headers = {'User-Agent': 'Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36'}
    for url in urls:
        try:
            r = requests.get(url, headers=headers, timeout=12)
            if r.status_code != 200:
                continue
            d = r.json()
            if not d.get('chart',{}).get('result'):
                continue
            meta = d['chart']['result'][0]['meta']
            price = meta.get('regularMarketPrice', 0)
            prev = meta.get('previousClose', price)
            if price <= 0:
                continue
            change = price - prev
            pct = (change/prev*100) if prev > 0 else 0
            return {'c': price, 'd': change, 'dp': pct, 'prev': prev}
        except Exception as e:
            continue
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

# -- FETCH GARMIN DATA --
def fetch_garmin_data():
    if not GARMIN_EMAIL or not GARMIN_PASSWORD:
        print("  Garmin credentials not configured")
        return None
    try:
        from garminconnect import Garmin
        client = Garmin(GARMIN_EMAIL, GARMIN_PASSWORD)
        client.login()
        print("  Garmin login successful")
        today = NOW.strftime('%Y-%m-%d')
        yesterday = (NOW - timedelta(days=1)).strftime('%Y-%m-%d')
        data = {}

        try:
            sleep = client.get_sleep_data(yesterday)
            if sleep and sleep.get('dailySleepDTO'):
                dto = sleep['dailySleepDTO']
                data['sleep_duration'] = round(dto.get('sleepTimeSeconds',0)/3600, 1)
                data['sleep_score'] = dto.get('sleepScores',{}).get('overall',{}).get('value',0)
                data['deep_sleep'] = round(dto.get('deepSleepSeconds',0)/3600, 1)
                data['rem_sleep'] = round(dto.get('remSleepSeconds',0)/3600, 1)
                data['light_sleep'] = round(dto.get('lightSleepSeconds',0)/3600, 1)
                print("  Sleep: " + str(data['sleep_duration']) + "h | Score: " + str(data['sleep_score']))
        except Exception as e:
            print("  Sleep error: " + str(e))

        try:
            hrv = client.get_hrv_data(today)
            if hrv and hrv.get('hrvSummary'):
                s = hrv['hrvSummary']
                data['hrv_weekly_avg'] = s.get('weeklyAvg', 0)
                data['hrv_last_night'] = s.get('lastNight', 0)
                data['hrv_status'] = s.get('status', 'UNKNOWN')
                print("  HRV: " + str(data['hrv_weekly_avg']) + "ms | " + data['hrv_status'])
        except Exception as e:
            print("  HRV error: " + str(e))

        try:
            bb = client.get_body_battery(today)
            if bb and len(bb) > 0:
                data['body_battery'] = bb[-1].get('value', 0)
                print("  Body battery: " + str(data['body_battery']))
        except Exception as e:
            print("  Body battery error: " + str(e))

        try:
            steps = client.get_steps_data(today)
            if steps:
                data['steps'] = sum(s.get('steps',0) for s in steps if s.get('steps'))
                print("  Steps: " + str(data['steps']))
        except Exception as e:
            print("  Steps error: " + str(e))

        try:
            activities = client.get_activities(0, 1)
            if activities and len(activities) > 0:
                act = activities[0]
                data['last_activity_name'] = act.get('activityName','')
                data['last_activity_type'] = act.get('activityType',{}).get('typeKey','')
                data['last_activity_distance'] = round(act.get('distance',0)/1000, 2)
                data['last_activity_duration'] = round(act.get('duration',0)/60, 0)
                data['last_activity_hr'] = act.get('averageHR', 0)
                data['last_activity_calories'] = act.get('calories', 0)
                data['last_activity_date'] = act.get('startTimeLocal','')[:10]
                print("  Last activity: " + data['last_activity_name'])
        except Exception as e:
            print("  Activity error: " + str(e))

        try:
            training = client.get_training_status(today)
            if training and training.get('trainingStatusDTO'):
                dto = training['trainingStatusDTO']
                data['training_status'] = dto.get('trainingStatus','UNKNOWN')
                data['training_load'] = dto.get('trainingLoad7Day', 0)
                print("  Training: " + str(data['training_status']))
        except Exception as e:
            print("  Training error: " + str(e))

        return data

    except Exception as e:
        print("  Garmin connection error: " + str(e))
        return None

def build_garmin_context(garmin):
    if not garmin:
        return "Garmin health data unavailable today."
    lines = []
    sleep_score = garmin.get('sleep_score', 0)
    body_battery = garmin.get('body_battery', 0)
    hrv_status = garmin.get('hrv_status', 'UNKNOWN')
    if sleep_score and body_battery:
        if sleep_score >= 80 and body_battery >= 70:
            readiness = "HIGH - excellent recovery"
        elif sleep_score >= 60 and body_battery >= 50:
            readiness = "MODERATE - good recovery"
        else:
            readiness = "LOW - poor recovery, consider rest"
        lines.append("READINESS: " + readiness)
    if garmin.get('sleep_duration'):
        lines.append("SLEEP: " + str(garmin['sleep_duration']) + "h | Score: " + str(sleep_score) + "/100 | Deep: " + str(garmin.get('deep_sleep',0)) + "h | REM: " + str(garmin.get('rem_sleep',0)) + "h")
    if garmin.get('hrv_weekly_avg'):
        lines.append("HRV: " + str(garmin['hrv_weekly_avg']) + "ms avg | Last night: " + str(garmin.get('hrv_last_night',0)) + "ms | Status: " + hrv_status)
    if garmin.get('body_battery'):
        lines.append("BODY BATTERY: " + str(body_battery) + "/100")
    if garmin.get('steps'):
        lines.append("STEPS: " + str(garmin['steps']))
    if garmin.get('last_activity_name'):
        lines.append("LAST WORKOUT: " + garmin['last_activity_name'] + " | " + str(garmin.get('last_activity_duration',0)) + " min | " + str(garmin.get('last_activity_distance',0)) + " km | HR: " + str(garmin.get('last_activity_hr',0)) + "bpm | " + str(garmin.get('last_activity_calories',0)) + " cal | " + garmin.get('last_activity_date',''))
    if garmin.get('training_status'):
        lines.append("TRAINING STATUS: " + str(garmin['training_status']) + " | 7-day load: " + str(garmin.get('training_load',0)))
    return "\n".join(lines) if lines else "Garmin connected but no data available."

# -- FETCH ALL DATA --
print("Fetching market data...")
WATCHLIST = ['AAPL', 'MSFT', 'NVDA', 'AMZN', 'GOOGL', 'META', 'TSLA', 'JPM', 'SPUS', 'SPWO']
market_data = {}
for sym in WATCHLIST:
    q = fetch_quote(sym)
    if q:
        market_data[sym] = q
        arrow = "+" if q['dp'] >= 0 else ""
        print("  " + sym + ": $" + str(round(q['c'],2)) + " (" + arrow + str(round(q['dp'],2)) + "%)")

print("Fetching indices...")
INDICES = {'SPY': 'S&P 500', 'QQQ': 'Nasdaq', 'DIA': 'Dow Jones'}
indices = {}
for sym, name in INDICES.items():
    q = fetch_quote(sym)
    if q:
        indices[sym] = {**q, 'name': name}

print("Fetching macro (VIX, Oil, Gold)...")
macro = {}
YAHOO_MACRO = {'^VIX': 'VIX Fear Index', 'CL=F': 'Oil WTI (USD/bbl)', 'GC=F': 'Gold (USD/oz)'}
for sym, name in YAHOO_MACRO.items():
    q = fetch_yahoo(sym)
    if q and q['c'] > 0:
        macro[name] = q
        print("  " + name + ": " + str(round(q['c'],2)))

print("Fetching earnings calendar...")
earnings = []
try:
    today_fmt = NOW.strftime('%Y-%m-%d')
    week_end = (NOW + timedelta(days=7)).strftime('%Y-%m-%d')
    r = requests.get("https://finnhub.io/api/v1/calendar/earnings?from=" + today_fmt + "&to=" + week_end + "&token=" + FINNHUB_KEY, timeout=10)
    data = r.json()
    if data and data.get('earningsCalendar'):
        my_tickers = set(WATCHLIST)
        for item in data['earningsCalendar']:
            if item.get('symbol') in my_tickers:
                earnings.append({'symbol': item['symbol'], 'date': item['date'], 'hour': item.get('hour',''), 'eps': item.get('epsEstimate','N/A')})
    print("  " + str(len(earnings)) + " earnings this week")
except Exception as e:
    print("  Earnings error: " + str(e))

print("Fetching news...")
all_news = []
news_from = (NOW - timedelta(days=2)).strftime('%Y-%m-%d')
today_fmt = NOW.strftime('%Y-%m-%d')
for sym in ['AAPL', 'MSFT', 'NVDA', 'AMZN']:
    try:
        r = requests.get("https://finnhub.io/api/v1/company-news?symbol=" + sym + "&from=" + news_from + "&to=" + today_fmt + "&token=" + FINNHUB_KEY, timeout=8)
        news = r.json()
        if news and isinstance(news, list):
            for n in news[:1]:
                all_news.append({'symbol': sym, 'headline': n.get('headline',''), 'source': n.get('source',''), 'dt': n.get('datetime',0)})
    except:
        pass
all_news.sort(key=lambda x: x['dt'], reverse=True)
print("  " + str(len(all_news)) + " news items")

print("Fetching portfolio, tasks, memories...")
portfolio = fetch_supabase('shadow_portfolio')
tasks = fetch_supabase('shadow_tasks', '&status=neq.done')
memories = fetch_supabase('shadow_memory', '&order=importance.desc&limit=15')
print("  " + str(len(portfolio)) + " holdings, " + str(len(tasks)) + " tasks, " + str(len(memories)) + " memories")

print("Fetching weather...")
weather_info = "Abu Dhabi weather unavailable"
weather_forecast = []
try:
    params = {'latitude': 24.4539, 'longitude': 54.3773, 'daily': 'temperature_2m_max,temperature_2m_min,weathercode,precipitation_sum', 'current_weather': True, 'timezone': 'Asia/Dubai', 'forecast_days': 5}
    w = requests.get("https://api.open-meteo.com/v1/forecast", params=params, timeout=10).json()
    current = w.get('current_weather', {})
    daily = w.get('daily', {})
    wmap = {0:'Clear',1:'Mainly clear',2:'Partly cloudy',3:'Overcast',45:'Foggy',61:'Rain',63:'Moderate rain',80:'Showers',95:'Thunderstorm'}
    temp = current.get('temperature', 0)
    cond = wmap.get(current.get('weathercode',0),'Clear')
    weather_info = "Abu Dhabi: " + cond + " " + str(round(temp)) + "C"
    if daily.get('time'):
        for i in range(min(5, len(daily['time']))):
            day = datetime.strptime(daily['time'][i], '%Y-%m-%d').strftime('%a %b %d')
            weather_forecast.append({'day': day, 'condition': wmap.get(daily['weathercode'][i],'Clear'), 'max': round(daily['temperature_2m_max'][i]), 'min': round(daily['temperature_2m_min'][i]), 'rain': round(daily.get('precipitation_sum',[0]*10)[i],1)})
    print("  " + weather_info)
except Exception as e:
    print("  Weather error: " + str(e))

print("Fetching Garmin health data...")
garmin_data = fetch_garmin_data()
garmin_context = build_garmin_context(garmin_data)
print("  Garmin: " + garmin_context[:60])

# -- CONTEXT BUILDERS --
def mkt_ctx():
    lines = []
    for sym, q in market_data.items():
        lines.append(sym + ": $" + str(round(q['c'],2)) + " " + ("UP" if q['dp']>=0 else "DOWN") + " " + str(round(q['dp'],2)) + "%")
    if indices:
        lines.append("INDICES: " + " | ".join([d['name'] + " $" + str(round(d['c'],2)) + " " + str(round(d['dp'],2)) + "%" for d in indices.values()]))
    if macro:
        lines.append("MACRO:")
        for name, q in macro.items():
            lines.append("  " + name + ": " + str(round(q['c'],2)) + " " + ("UP" if q['dp']>=0 else "DOWN") + " " + str(round(q['dp'],2)) + "%")
    else:
        lines.append("MACRO: Data unavailable - do NOT estimate commodity prices")
    return "\n".join(lines)

def port_ctx():
    if not portfolio:
        return "No portfolio holdings tracked."
    lines = []
    total_val = 0
    total_cost = 0
    for h in portfolio:
        q = market_data.get(h.get('ticker',''))
        if q and h.get('shares') and h.get('avg_buy_price'):
            val = q['c'] * h['shares']
            cost = h['avg_buy_price'] * h['shares']
            gain = val - cost
            pct = (gain/cost*100) if cost > 0 else 0
            total_val += val
            total_cost += cost
            lines.append(h['ticker'] + ": $" + str(round(val,2)) + " PnL $" + str(round(gain,2)) + " (" + str(round(pct,2)) + "%) today $" + str(round(q['d']*h['shares'],2)))
    if total_val > 0:
        pnl = total_val - total_cost
        pct = (pnl/total_cost*100) if total_cost > 0 else 0
        lines.append("TOTAL: $" + str(round(total_val,2)) + " PnL $" + str(round(pnl,2)) + " (" + str(round(pct,2)) + "%)")
    return "\n".join(lines) if lines else "No holdings with market data."

def earn_ctx():
    if not earnings:
        return "No earnings from your holdings this week."
    return "EARNINGS: " + " | ".join([e['symbol'] + " on " + e['date'] + " EPS est $" + str(e['eps']) for e in earnings])

def news_ctx():
    if not all_news:
        return "No recent news."
    return "\n".join(["[" + n['symbol'] + "] " + n['headline'] for n in all_news[:6]])

def tasks_ctx():
    if not tasks:
        return "No pending tasks."
    high = [t for t in tasks if t.get('priority') == 'high']
    return str(len(tasks)) + " pending. HIGH: " + (", ".join([t['title'] for t in high[:3]]) if high else "none")

def mem_ctx():
    if not memories:
        return "No memories stored."
    trips = [m for m in memories if 'trip' in m.get('key','').lower()]
    exams = [m for m in memories if 'exam' in m.get('key','').lower() or 'assessment' in m.get('value','').lower()]
    key = [m for m in memories if m.get('importance',1) >= 2][:5]
    lines = []
    if trips:
        lines.append("TRIPS: " + "; ".join([m['value'] for m in trips[:2]]))
    if exams:
        lines.append("EXAMS: " + "; ".join([m['value'] for m in exams[:2]]))
    if key:
        lines.append("KEY: " + "; ".join([m['key'] + ": " + m['value'] for m in key]))
    return "\n".join(lines) if lines else "General memories stored."

def weather_ctx():
    lines = [weather_info]
    for d in weather_forecast:
        rain = " rain " + str(d['rain']) + "mm" if d['rain'] > 0 else ""
        lines.append(d['day'] + ": " + d['condition'] + " " + str(d['max']) + "/" + str(d['min']) + "C" + rain)
    return "\n".join(lines)

# -- CALL CLAUDE --
print("Calling Claude...")
system_prompt = "\n".join([
    "You are Shadow, personal AI intelligence system for " + USER_NAME + " in Abu Dhabi.",
    "Write like a senior JPMorgan analyst briefing a VP of Investments.",
    "Today: " + TODAY_STR + " at " + TIME_STR + " Abu Dhabi GMT+4.",
    "",
    "CRITICAL RULES:",
    "- Use ONLY the exact section markers below.",
    "- Be specific with numbers from the data provided.",
    "- NEVER estimate or fabricate financial data not in the provided data.",
    "- If oil/VIX data is unavailable, say Data unavailable.",
    "- Be actionable. Each section ends with a clear implication or action.",
    "- Tone: Senior JPMorgan analyst briefing a respected client. Direct and honest but never condescending, never insulting. Respect the reader's intelligence.",
    "- For health section: be specific about readiness and give ONE fitness recommendation.",
    "",
    "YOU MUST USE THESE EXACT MARKERS:",
    "[MARKET_OPEN]",
    "Your market analysis here",
    "[/MARKET_OPEN]",
    "",
    "[PORTFOLIO_PULSE]",
    "Your portfolio analysis here",
    "[/PORTFOLIO_PULSE]",
    "",
    "[EARNINGS_WATCH]",
    "Your earnings analysis here",
    "[/EARNINGS_WATCH]",
    "",
    "[STOCK_NEWS]",
    "Your stock news analysis here",
    "[/STOCK_NEWS]",
    "",
    "[AI_TECH]",
    "Your AI tech news here",
    "[/AI_TECH]",
    "",
    "[GEOPOLITICAL]",
    "Your geopolitical analysis here",
    "[/GEOPOLITICAL]",
    "",
    "[WEATHER]",
    "Your weather analysis here",
    "[/WEATHER]",
    "",
    "[HEALTH_PERFORMANCE]",
    "Your health and performance analysis here based on Garmin data",
    "[/HEALTH_PERFORMANCE]",
    "",
    "[TASKS]",
    "Your task priorities here",
    "[/TASKS]",
    "",
    "[TRAVEL]",
    "Your travel intelligence here",
    "[/TRAVEL]",
    "",
    "[SHADOW_VERDICT]",
    "Your verdict here",
    "[/SHADOW_VERDICT]",
    "",
    "DATA:",
    "",
    "MARKETS:",
    mkt_ctx(),
    "",
    "PORTFOLIO:",
    port_ctx(),
    "",
    "EARNINGS:",
    earn_ctx(),
    "",
    "NEWS:",
    news_ctx(),
    "",
    "WEATHER:",
    weather_ctx(),
    "",
    "GARMIN HEALTH DATA:",
    garmin_context,
    "",
    "TASKS:",
    tasks_ctx(),
    "",
    "MEMORY:",
    mem_ctx(),
])

user_msg = (
    "Generate my complete morning brief for " + TODAY_STR + ".\n\n"
    "MARKET_OPEN: Index levels, key movers, what it means today.\n"
    "PORTFOLIO_PULSE: Each holding performance, biggest mover, concentration risk.\n"
    "EARNINGS_WATCH: Holdings reporting this week.\n"
    "STOCK_NEWS: Most important news for my specific holdings.\n"
    "AI_TECH: Latest AI/tech news relevant to my positions.\n"
    "GEOPOLITICAL: UAE region, US-China, oil, key macro events.\n"
    "WEATHER: Abu Dhabi 5-day forecast.\n"
    "HEALTH_PERFORMANCE: Based on Garmin data - my readiness score, sleep analysis, HRV status, body battery, last workout. Give ONE specific fitness recommendation for today.\n"
    "TASKS: Prioritized list for today.\n"
    "TRAVEL: Upcoming trips from memory.\n"
    "SHADOW_VERDICT: One key insight. One action. One risk. Punchy and direct."
)

brief_raw = ""
try:
    resp = requests.post(
        "https://api.anthropic.com/v1/messages",
        headers={"Content-Type": "application/json", "x-api-key": ANTHROPIC_KEY, "anthropic-version": "2023-06-01"},
        json={"model": "claude-sonnet-4-5", "max_tokens": 3500, "system": system_prompt, "messages": [{"role": "user", "content": user_msg}]},
        timeout=180
    )
    d = resp.json()
    if d.get('content'):
        brief_raw = d['content'][0]['text']
        print("  Claude OK - " + str(len(brief_raw)) + " chars")
    else:
        print("  Claude error: " + str(d))
        brief_raw = "[SHADOW_VERDICT]Morning " + USER_NAME + ". Claude error today.[/SHADOW_VERDICT]"
except Exception as e:
    print("  Claude error: " + str(e))
    brief_raw = "[SHADOW_VERDICT]Morning " + USER_NAME + ". Connection error.[/SHADOW_VERDICT]"

def extract(text, tag):
    s = text.find('[' + tag + ']')
    e = text.find('[/' + tag + ']')
    if s != -1 and e != -1:
        return text[s+len(tag)+2:e].strip()
    return ""

S = {
    'market':    extract(brief_raw, 'MARKET_OPEN'),
    'portfolio': extract(brief_raw, 'PORTFOLIO_PULSE'),
    'earnings':  extract(brief_raw, 'EARNINGS_WATCH'),
    'news':      extract(brief_raw, 'STOCK_NEWS'),
    'ai_tech':   extract(brief_raw, 'AI_TECH'),
    'geo':       extract(brief_raw, 'GEOPOLITICAL'),
    'weather':   extract(brief_raw, 'WEATHER'),
    'health':    extract(brief_raw, 'HEALTH_PERFORMANCE'),
    'tasks':     extract(brief_raw, 'TASKS'),
    'travel':    extract(brief_raw, 'TRAVEL'),
    'verdict':   extract(brief_raw, 'SHADOW_VERDICT'),
}
filled = sum(1 for v in S.values() if v)
print("  Sections: " + str(filled) + "/11")

def fmt(t):
    import re
    t = t.replace('\n', '<br>')
    t = re.sub(r'[*][*](.*?)[*][*]', r'<strong>\1</strong>', t)
    t = t.replace('*', '')
    return t

def sec(title, content, color):
    if not content:
        return ""
    return ('<div style="margin-bottom:14px;background:#0e1220;border:1px solid #1e2840;border-radius:12px;overflow:hidden;">'
            '<div style="padding:11px 18px;background:#141928;border-bottom:1px solid #1e2840;">'
            '<span style="font-family:monospace;font-size:11px;letter-spacing:2px;color:' + color + ';text-transform:uppercase;font-weight:700;">' + title + '</span>'
            '</div>'
            '<div style="padding:16px 18px;font-size:13px;color:#8892a8;line-height:1.75;">' + fmt(content) + '</div>'
            '</div>')

def ticker_row():
    items = ""
    for sym, q in market_data.items():
        col = '#10d9a0' if q['dp']>=0 else '#f43f5e'
        bg = 'rgba(16,217,160,0.05)' if q['dp']>=0 else 'rgba(244,63,94,0.05)'
        arrow = "+" if q['dp']>=0 else ""
        items += ('<td style="padding:11px 12px;border-right:1px solid #1e2840;text-align:center;background:' + bg + ';">'
                  '<div style="font-family:monospace;font-size:10px;color:#7889a8;margin-bottom:4px;font-weight:700;">' + sym + '</div>'
                  '<div style="font-family:monospace;font-size:15px;font-weight:700;color:#e2e8f8;margin-bottom:2px;">$' + str(round(q['c'],2)) + '</div>'
                  '<div style="font-family:monospace;font-size:10px;color:' + col + ';">' + arrow + str(round(q['dp'],2)) + '%</div>'
                  '</td>')
    return '<table style="width:100%;border-collapse:collapse;"><tr>' + items + '</tr></table>'

def garmin_card():
    if not garmin_data:
        return ""
    bb = garmin_data.get('body_battery', 0)
    sleep = garmin_data.get('sleep_duration', 0)
    sleep_score = garmin_data.get('sleep_score', 0)
    hrv = garmin_data.get('hrv_weekly_avg', 0)
    hrv_status = garmin_data.get('hrv_status', '')
    
    bb_color = '#10d9a0' if bb >= 70 else '#f59e0b' if bb >= 40 else '#f43f5e'
    sleep_color = '#10d9a0' if sleep_score >= 80 else '#f59e0b' if sleep_score >= 60 else '#f43f5e'
    
    items = ""
    if bb:
        items += ('<td style="padding:12px;text-align:center;border-right:1px solid #1e2840;">'
                  '<div style="font-family:monospace;font-size:10px;color:#6b7280;margin-bottom:4px;">BODY BATTERY</div>'
                  '<div style="font-family:monospace;font-size:22px;font-weight:700;color:' + bb_color + ';">' + str(bb) + '</div>'
                  '<div style="font-family:monospace;font-size:10px;color:#6b7280;">/100</div>'
                  '</td>')
    if sleep:
        items += ('<td style="padding:12px;text-align:center;border-right:1px solid #1e2840;">'
                  '<div style="font-family:monospace;font-size:10px;color:#6b7280;margin-bottom:4px;">SLEEP</div>'
                  '<div style="font-family:monospace;font-size:22px;font-weight:700;color:' + sleep_color + ';">' + str(sleep) + 'h</div>'
                  '<div style="font-family:monospace;font-size:10px;color:#6b7280;">score ' + str(sleep_score) + '</div>'
                  '</td>')
    if hrv:
        hrv_color = '#10d9a0' if hrv_status == 'BALANCED' else '#f59e0b'
        items += ('<td style="padding:12px;text-align:center;">'
                  '<div style="font-family:monospace;font-size:10px;color:#6b7280;margin-bottom:4px;">HRV</div>'
                  '<div style="font-family:monospace;font-size:22px;font-weight:700;color:' + hrv_color + ';">' + str(hrv) + '</div>'
                  '<div style="font-family:monospace;font-size:10px;color:#6b7280;">ms avg</div>'
                  '</td>')
    if not items:
        return ""
    return ('<tr><td style="padding-bottom:14px;">'
            '<div style="background:#0e1220;border:1px solid #1e2840;border-radius:12px;overflow:hidden;">'
            '<div style="padding:11px 18px;background:#141928;border-bottom:1px solid #1e2840;">'
            '<span style="font-family:monospace;font-size:10px;letter-spacing:2px;color:#10d9a0;text-transform:uppercase;font-weight:700;">HEALTH & PERFORMANCE</span>'
            '</div>'
            '<table style="width:100%;border-collapse:collapse;"><tr>' + items + '</tr></table>'
            '</div></td></tr>')

h = NOW.hour
greeting = "Good morning" if h < 12 else "Good afternoon" if h < 17 else "Good evening"

verdict_block = ""
if S.get('verdict'):
    verdict_block = ('<tr><td style="padding-bottom:14px;">'
                     '<div style="background:linear-gradient(135deg,#1d4ed8,#2563eb);border-radius:12px;padding:22px;">'
                     '<div style="font-family:monospace;font-size:10px;letter-spacing:3px;color:rgba(255,255,255,0.5);text-transform:uppercase;margin-bottom:10px;">SHADOW VERDICT</div>'
                     '<div style="font-size:15px;color:#fff;line-height:1.75;font-weight:500;">' + fmt(S['verdict']) + '</div>'
                     '</div></td></tr>')

html = (
    '<!DOCTYPE html><html><head><meta charset="UTF-8"><meta name="viewport" content="width=device-width,initial-scale=1.0">'
    '<title>Shadow Brief ' + DATE_SHORT + '</title></head>'
    '<body style="margin:0;padding:0;background:#060810;font-family:Arial,sans-serif;">'
    '<table width="100%" cellpadding="0" cellspacing="0" style="background:#060810;">'
    '<tr><td align="center" style="padding:20px 12px;">'
    '<table width="700" cellpadding="0" cellspacing="0" style="max-width:700px;width:100%;">'
    '<tr><td style="padding-bottom:14px;">'
    '<div style="background:#0e1220;border:1px solid #1e2840;border-radius:16px;padding:28px;text-align:center;">'
    '<div style="font-family:monospace;font-size:40px;font-weight:900;letter-spacing:10px;color:#4f8ef7;margin-bottom:6px;">SHADOW</div>'
    '<div style="font-family:monospace;font-size:10px;letter-spacing:3px;color:#454d60;text-transform:uppercase;margin-bottom:18px;">MORNING INTELLIGENCE BRIEF</div>'
    '<div style="font-family:monospace;font-size:12px;color:#7889a8;">' + TODAY_STR + ' - ' + TIME_STR + ' - Abu Dhabi GMT+4</div>'
    '</div></td></tr>'
    '<tr><td style="padding-bottom:14px;">'
    '<div style="background:#0e1220;border:1px solid #1e2840;border-radius:12px;padding:18px 22px;">'
    '<div style="font-size:20px;font-weight:700;color:#e2e8f8;margin-bottom:5px;">' + greeting + ', ' + USER_NAME + '.</div>'
    '<div style="font-size:13px;color:#6b7280;line-height:1.6;">Your morning intelligence brief is ready. ' + str(len(portfolio)) + ' holdings - ' + str(len(all_news)) + ' news items - ' + str(filled) + '/11 sections</div>'
    '</div></td></tr>'
    + verdict_block
    + garmin_card()
    + '<tr><td style="padding-bottom:14px;">'
    '<div style="background:#0e1220;border:1px solid #1e2840;border-radius:12px;overflow:hidden;">'
    '<div style="padding:11px 18px;background:#141928;border-bottom:1px solid #1e2840;">'
    '<span style="font-family:monospace;font-size:10px;letter-spacing:2px;color:#4f8ef7;text-transform:uppercase;font-weight:700;">US EQUITIES</span>'
    '</div>' + ticker_row() + '</div></td></tr>'
    '<tr><td>'
    + sec('MARKET OPEN ANALYSIS', S.get('market',''), '#4f8ef7')
    + sec('PORTFOLIO INTELLIGENCE', S.get('portfolio',''), '#10d9a0')
    + sec('EARNINGS WATCH', S.get('earnings',''), '#f59e0b')
    + sec('STOCK NEWS', S.get('news',''), '#7889a8')
    + sec('AI AND TECHNOLOGY', S.get('ai_tech',''), '#a855f7')
    + sec('GEOPOLITICAL INTELLIGENCE', S.get('geo',''), '#f59e0b')
    + sec('ABU DHABI WEATHER', S.get('weather',''), '#10d9a0')
    + sec('HEALTH AND PERFORMANCE', S.get('health',''), '#10d9a0')
    + sec('TASKS AND PRIORITIES', S.get('tasks',''), '#4f8ef7')
    + sec('TRAVEL INTELLIGENCE', S.get('travel',''), '#f59e0b')
    + '</td></tr>'
    '<tr><td style="text-align:center;padding:20px 0;">'
    '<a href="https://aistudioaj.github.io/project-shadow/" style="display:inline-block;background:linear-gradient(135deg,#1d4ed8,#4f8ef7);color:#fff;text-decoration:none;padding:13px 32px;border-radius:10px;font-family:monospace;font-size:12px;font-weight:700;letter-spacing:2px;text-transform:uppercase;">OPEN SHADOW</a>'
    '</td></tr>'
    '<tr><td style="padding:16px;text-align:center;border-top:1px solid #1e2840;">'
    '<div style="font-family:monospace;font-size:10px;color:#3d4d6a;">PROJECT SHADOW - ' + TODAY_STR + ' - Abu Dhabi UAE</div>'
    '</td></tr>'
    '</table></td></tr></table></body></html>'
)

# -- SAVE TO SUPABASE --
print("Saving brief to Supabase...")
try:
    brief_data = {
        "user_id": USER_ID,
        "brief_date": NOW.strftime('%Y-%m-%d'),
        "verdict": S.get('verdict',''),
        "market": S.get('market',''),
        "portfolio": S.get('portfolio',''),
        "earnings": S.get('earnings',''),
        "news": S.get('news',''),
        "ai_tech": S.get('ai_tech',''),
        "geopolitical": S.get('geo',''),
        "weather": S.get('weather',''),
        "tasks": S.get('tasks',''),
        "travel": S.get('travel',''),
        "sections_count": filled
    }
    headers2 = {'apikey': SUPABASE_KEY, 'Authorization': 'Bearer ' + SUPABASE_KEY, 'Content-Type': 'application/json'}
    r2 = requests.post(SUPABASE_URL + "/rest/v1/shadow_briefs", headers=headers2, json=brief_data, timeout=10)
    print("  Brief saved: " + str(r2.status_code))
except Exception as e:
    print("  Brief save error: " + str(e))

# -- SEND EMAIL --
print("Sending via Resend...")
plain = "Shadow Morning Brief " + TODAY_STR + "\n\n"
for key, val in S.items():
    if val:
        plain += key.upper() + ":\n" + val + "\n\n"
plain += "Open Shadow: https://aistudioaj.github.io/project-shadow/"

try:
    r = requests.post(
        "https://api.resend.com/emails",
        headers={"Authorization": "Bearer " + RESEND_KEY, "Content-Type": "application/json"},
        json={"from": "Shadow AI <onboarding@resend.dev>", "to": [EMAIL_TO], "subject": "Shadow Brief " + DATE_SHORT + " | " + str(filled) + "/11 sections | " + str(len(portfolio)) + " Holdings", "text": plain, "html": html},
        timeout=30
    )
    if r.status_code in [200,201]:
        print("Email sent to " + EMAIL_TO)
    else:
        print("Resend error: " + str(r.status_code) + " " + r.text)
        raise Exception("Resend failed")
except Exception as e:
    print("Email error: " + str(e))
    raise

print("Shadow Morning Brief v4 complete! " + TODAY_STR + " | " + str(filled) + "/11 sections")
