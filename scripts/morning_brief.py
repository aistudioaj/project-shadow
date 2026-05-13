# -*- coding: utf-8 -*-
#!/usr/bin/env python3
import os, requests, json
from datetime import datetime, timezone, timedelta

ANTHROPIC_KEY = os.environ['ANTHROPIC_KEY']
SUPABASE_URL  = os.environ['SUPABASE_URL']
SUPABASE_KEY  = os.environ['SUPABASE_KEY']
FINNHUB_KEY   = os.environ['FINNHUB_KEY']
EMAIL_FROM    = os.environ['EMAIL_FROM']
EMAIL_TO      = os.environ['EMAIL_TO']
RESEND_KEY    = os.environ['RESEND_KEY']
USER_ID       = os.environ.get('USER_ID', 'abdulrahman')
USER_NAME     = os.environ.get('USER_NAME', 'AJ')

ABU_DHABI_TZ = timezone(timedelta(hours=4))
NOW = datetime.now(ABU_DHABI_TZ)
TODAY_STR = NOW.strftime('%A, %B %d, %Y')
TIME_STR = NOW.strftime('%I:%M %p')
DATE_SHORT = NOW.strftime('%a %b %d')

print("Shadow Morning Brief v2: " + TODAY_STR)

def fetch_quote(sym):
    try:
        r = requests.get("https://finnhub.io/api/v1/quote?symbol=" + sym + "&token=" + FINNHUB_KEY, timeout=10)
        d = r.json()
        if d.get('c', 0) > 0:
            return d
    except:
        pass
    return None

def fetch_supabase(table, filters=""):
    try:
        url = SUPABASE_URL + "/rest/v1/" + table + "?user_id=eq." + USER_ID + filters + "&select=*"
        headers = {'apikey': SUPABASE_KEY, 'Authorization': 'Bearer ' + SUPABASE_KEY}
        return requests.get(url, headers=headers, timeout=10).json()
    except:
        return []

print("Fetching markets...")
WATCHLIST = ['AAPL', 'MSFT', 'NVDA', 'AMZN', 'GOOGL', 'META', 'TSLA', 'JPM', 'SPUS', 'SPWO']
market_data = {}
for sym in WATCHLIST:
    q = fetch_quote(sym)
    if q:
        market_data[sym] = q
        print("  " + sym + ": $" + str(round(q['c'],2)) + " (" + ("+" if q['dp']>=0 else "") + str(round(q['dp'],2)) + "%)")

print("Fetching indices...")
INDICES = {'SPY': 'S&P 500', 'QQQ': 'Nasdaq', 'DIA': 'Dow Jones'}
indices = {}
for sym, name in INDICES.items():
    q = fetch_quote(sym)
    if q:
        indices[sym] = {**q, 'name': name}
        print("  " + name + ": $" + str(round(q['c'],2)))

print("Fetching macro...")
MACRO = {'OANDA:XAU_USD': 'Gold', 'OANDA:USOIL': 'Oil WTI'}
macro = {}
for sym, name in MACRO.items():
    q = fetch_quote(sym)
    if q:
        macro[name] = q
        print("  " + name + ": " + str(round(q['c'],2)))

print("Fetching earnings calendar...")
earnings = []
try:
    today = NOW.strftime('%Y-%m-%d')
    week_end = (NOW + timedelta(days=7)).strftime('%Y-%m-%d')
    r = requests.get("https://finnhub.io/api/v1/calendar/earnings?from=" + today + "&to=" + week_end + "&token=" + FINNHUB_KEY, timeout=10)
    data = r.json()
    if data and data.get('earningsCalendar'):
        my_tickers = set(WATCHLIST)
        for item in data['earningsCalendar']:
            if item.get('symbol') in my_tickers:
                earnings.append({'symbol': item['symbol'], 'date': item['date'], 'hour': item.get('hour',''), 'eps': item.get('epsEstimate','N/A')})
    print("  " + str(len(earnings)) + " earnings this week in your portfolio")
except Exception as e:
    print("  Earnings error: " + str(e))

print("Fetching news...")
all_news = []
news_from = (NOW - timedelta(days=2)).strftime('%Y-%m-%d')
today = NOW.strftime('%Y-%m-%d')
for sym in ['AAPL', 'MSFT', 'NVDA', 'AMZN']:
    try:
        r = requests.get("https://finnhub.io/api/v1/company-news?symbol=" + sym + "&from=" + news_from + "&to=" + today + "&token=" + FINNHUB_KEY, timeout=8)
        news = r.json()
        if news and isinstance(news, list):
            for n in news[:2]:
                all_news.append({'symbol': sym, 'headline': n.get('headline',''), 'source': n.get('source',''), 'url': n.get('url',''), 'dt': n.get('datetime',0)})
    except:
        pass
all_news.sort(key=lambda x: x['dt'], reverse=True)
print("  " + str(len(all_news)) + " news items")

print("Fetching portfolio, tasks, memories...")
portfolio = fetch_supabase('shadow_portfolio')
tasks = fetch_supabase('shadow_tasks', '&status=neq.done')
memories = fetch_supabase('shadow_memory', '&order=importance.desc&limit=30')
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

def mkt_ctx():
    lines = []
    for sym, q in market_data.items():
        lines.append(sym + ": $" + str(round(q['c'],2)) + " " + ("UP" if q['dp']>=0 else "DOWN") + " " + str(round(q['dp'],2)) + "%")
    if indices:
        lines.append("INDICES: " + " | ".join([d['name'] + " $" + str(round(d['c'],2)) + " " + str(round(d['dp'],2)) + "%" for d in indices.values()]))
    if macro:
        lines.append("MACRO: " + " | ".join([n + " " + str(round(q['c'],2)) for n,q in macro.items()]))
    return "\n".join(lines)

def port_ctx():
    if not portfolio:
        return "No holdings."
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
        tech = sum(1 for h in portfolio if h.get('ticker') in ['AAPL','MSFT','NVDA','GOOGL','META'])
        if portfolio:
            lines.append("TECH CONCENTRATION: " + str(round(tech/len(portfolio)*100)) + "% - " + ("HIGH RISK" if tech/len(portfolio) > 0.6 else "MODERATE"))
    return "\n".join(lines)

def earn_ctx():
    if not earnings:
        return "No earnings from your holdings this week."
    return "EARNINGS THIS WEEK: " + " | ".join([e['symbol'] + " on " + e['date'] + " EPS est $" + str(e['eps']) for e in earnings])

def news_ctx():
    if not all_news:
        return "No recent news."
    return "\n".join(["[" + n['symbol'] + "] " + n['headline'] for n in all_news[:8]])

def tasks_ctx():
    if not tasks:
        return "No pending tasks."
    high = [t for t in tasks if t.get('priority') == 'high']
    return str(len(tasks)) + " pending. HIGH: " + (", ".join([t['title'] for t in high[:3]]) if high else "none")

def mem_ctx():
    if not memories:
        return "No memories."
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
    return "\n".join(lines) if lines else "General context stored."

def weather_ctx():
    lines = [weather_info]
    for d in weather_forecast:
        rain = " rain " + str(d['rain']) + "mm" if d['rain'] > 0 else ""
        lines.append(d['day'] + ": " + d['condition'] + " " + str(d['max']) + "/" + str(d['min']) + "C" + rain)
    return "\n".join(lines)

print("Calling Claude...")
system_prompt = (
    "You are Shadow, personal AI intelligence system for " + USER_NAME + " in Abu Dhabi.\n"
    "Write like a senior JPMorgan analyst briefing a VP of Investments.\n"
    "Today: " + TODAY_STR + " at " + TIME_STR + " Abu Dhabi GMT+4.\n\n"
    "RULES: Be specific with numbers. Be actionable. No hedging.\n"
    "Each section ends with a clear implication or action.\n\n"
    "Use these markers:\n"
    "[MARKET_OPEN] [/MARKET_OPEN]\n"
    "[PORTFOLIO_PULSE] [/PORTFOLIO_PULSE]\n"
    "[EARNINGS_WATCH] [/EARNINGS_WATCH]\n"
    "[STOCK_NEWS] [/STOCK_NEWS]\n"
    "[AI_TECH] [/AI_TECH]\n"
    "[GEOPOLITICAL] [/GEOPOLITICAL]\n"
    "[WEATHER] [/WEATHER]\n"
    "[TASKS] [/TASKS]\n"
    "[TRAVEL] [/TRAVEL]\n"
    "[SHADOW_VERDICT] [/SHADOW_VERDICT]\n\n"
    "DATA:\n"
    "MARKETS:\n" + mkt_ctx() + "\n\n"
    "PORTFOLIO:\n" + port_ctx() + "\n\n"
    "EARNINGS:\n" + earn_ctx() + "\n\n"
    "NEWS:\n" + news_ctx() + "\n\n"
    "WEATHER:\n" + weather_ctx() + "\n\n"
    "TASKS:\n" + tasks_ctx() + "\n\n"
    "MEMORY:\n" + mem_ctx()
)

user_msg = (
    "Generate my complete morning brief. Be specific and direct.\n"
    "MARKET_OPEN: Index levels, key movers, VIX, what it means for today.\n"
    "PORTFOLIO_PULSE: Each holding performance, biggest mover, concentration risk, alerts.\n"
    "EARNINGS_WATCH: Holdings reporting this week - what to expect.\n"
    "STOCK_NEWS: Most important news for my specific holdings.\n"
    "AI_TECH: Latest AI/tech news relevant to my NVDA, AAPL, MSFT, GOOGL positions.\n"
    "GEOPOLITICAL: UAE region, US-China (affects AAPL/NVDA), oil, key macro events today.\n"
    "WEATHER: Abu Dhabi 5-day forecast and any trip destinations from memory.\n"
    "TASKS: Prioritized list for today.\n"
    "TRAVEL: Upcoming trips - preparation needed.\n"
    "SHADOW_VERDICT: One key insight. One action. One risk. Make it punchy."
)

brief_raw = ""
try:
    resp = requests.post(
        "https://api.anthropic.com/v1/messages",
        headers={"Content-Type": "application/json", "x-api-key": ANTHROPIC_KEY, "anthropic-version": "2023-06-01"},
        json={"model": "claude-sonnet-4-5", "max_tokens": 3000, "system": system_prompt, "messages": [{"role": "user", "content": user_msg}]},
        timeout=180
    )
    d = resp.json()
    if d.get('content'):
        brief_raw = d['content'][0]['text']
        print("  Claude OK - " + str(len(brief_raw)) + " chars")
    else:
        print("  Claude error: " + str(d))
        brief_raw = "[SHADOW_VERDICT]Morning " + USER_NAME + ". Claude error today - check API key.[/SHADOW_VERDICT]"
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
    'market': extract(brief_raw, 'MARKET_OPEN'),
    'portfolio': extract(brief_raw, 'PORTFOLIO_PULSE'),
    'earnings': extract(brief_raw, 'EARNINGS_WATCH'),
    'news': extract(brief_raw, 'STOCK_NEWS'),
    'ai': extract(brief_raw, 'AI_TECH'),
    'geo': extract(brief_raw, 'GEOPOLITICAL'),
    'weather': extract(brief_raw, 'WEATHER'),
    'tasks': extract(brief_raw, 'TASKS'),
    'travel': extract(brief_raw, 'TRAVEL'),
    'verdict': extract(brief_raw, 'SHADOW_VERDICT'),
}
print("  Sections: " + str(sum(1 for v in S.values() if v)) + "/10")

def fmt(t):
    return t.replace('\n','<br>')

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
        items += ('<td style="padding:11px 12px;border-right:1px solid #1e2840;text-align:center;background:' + bg + ';">'
                  '<div style="font-family:monospace;font-size:10px;color:#7889a8;margin-bottom:4px;font-weight:700;">' + sym + '</div>'
                  '<div style="font-family:monospace;font-size:15px;font-weight:700;color:#e2e8f8;margin-bottom:2px;">$' + str(round(q['c'],2)) + '</div>'
                  '<div style="font-family:monospace;font-size:10px;color:' + col + ';">' + ("+" if q['dp']>=0 else "") + str(round(q['dp'],2)) + '%</div>'
                  '</td>')
    return '<table style="width:100%;border-collapse:collapse;"><tr>' + items + '</tr></table>'

def indices_row():
    if not indices:
        return ""
    items = ""
    for sym, d in indices.items():
        col = '#10d9a0' if d['dp']>=0 else '#f43f5e'
        items += ('<td style="padding:9px 12px;border-right:1px solid #1e2840;text-align:center;">'
                  '<div style="font-size:10px;color:#6b7280;margin-bottom:2px;">' + d['name'] + '</div>'
                  '<div style="font-family:monospace;font-size:13px;font-weight:700;color:#e2e8f8;">$' + str(round(d['c'],2)) + '</div>'
                  '<div style="font-family:monospace;font-size:10px;color:' + col + ';">' + ("+" if d['dp']>=0 else "") + str(round(d['dp'],2)) + '%</div>'
                  '</td>')
    return '<div style="border-top:1px solid #1e2840;"><table style="width:100%;border-collapse:collapse;"><tr>' + items + '</tr></table></div>'

def macro_row():
    if not macro:
        return ""
    items = ""
    for name, q in macro.items():
        col = '#10d9a0' if q['dp']>=0 else '#f43f5e'
        items += ('<td style="padding:9px 12px;border-right:1px solid #1e2840;text-align:center;">'
                  '<div style="font-size:10px;color:#6b7280;margin-bottom:2px;">' + name + '</div>'
                  '<div style="font-family:monospace;font-size:13px;font-weight:700;color:#e2e8f8;">' + str(round(q['c'],2)) + '</div>'
                  '<div style="font-family:monospace;font-size:10px;color:' + col + ';">' + ("+" if q['dp']>=0 else "") + str(round(q['dp'],2)) + '%</div>'
                  '</td>')
    return '<div style="border-top:1px solid #1e2840;"><table style="width:100%;border-collapse:collapse;"><tr>' + items + '</tr></table></div>'

def port_table():
    if not portfolio or not market_data:
        return '<p style="color:#6b7280;padding:16px;">No data.</p>'
    rows = ""
    total_val = 0
    total_cost = 0
    for h in portfolio:
        q = market_data.get(h.get('ticker',''))
        if not q or not h.get('shares'):
            continue
        val = q['c'] * h['shares']
        cost = (h.get('avg_buy_price',0) or 0) * h['shares']
        gain = val - cost
        pct = (gain/cost*100) if cost > 0 else 0
        day = q['d'] * h['shares']
        total_val += val
        total_cost += cost
        gc = '#10d9a0' if gain>=0 else '#f43f5e'
        dc = '#10d9a0' if day>=0 else '#f43f5e'
        rows += ('<tr>'
                 '<td style="padding:9px 12px;border-bottom:1px solid #1e2840;font-family:monospace;font-weight:700;color:#e2e8f8;font-size:12px;">' + h['ticker'] + '<div style="font-size:10px;color:#6b7280;">' + str(h['shares']) + ' sh</div></td>'
                 '<td style="padding:9px 12px;border-bottom:1px solid #1e2840;font-family:monospace;color:#e2e8f8;font-size:12px;">$' + str(round(q['c'],2)) + '</td>'
                 '<td style="padding:9px 12px;border-bottom:1px solid #1e2840;font-family:monospace;color:' + dc + ';font-size:12px;">' + ('+' if day>=0 else '') + '$' + str(round(day,2)) + '</td>'
                 '<td style="padding:9px 12px;border-bottom:1px solid #1e2840;font-family:monospace;color:#e2e8f8;font-size:12px;">$' + str(round(val,2)) + '</td>'
                 '<td style="padding:9px 12px;border-bottom:1px solid #1e2840;font-family:monospace;color:' + gc + ';font-size:12px;">' + ('+' if gain>=0 else '') + '$' + str(round(abs(gain),2)) + '<div style="font-size:10px;">' + ('+' if pct>=0 else '') + str(round(pct,2)) + '%</div></td>'
                 '</tr>')
    if not rows:
        return '<p style="color:#6b7280;padding:16px;">No holdings data.</p>'
    pnl = total_val - total_cost
    pct = (pnl/total_cost*100) if total_cost > 0 else 0
    pc = '#10d9a0' if pnl>=0 else '#f43f5e'
    rows += ('<tr style="background:#141928;">'
             '<td colspan="3" style="padding:10px 12px;font-family:monospace;font-weight:700;color:#e2e8f8;font-size:12px;">TOTAL</td>'
             '<td style="padding:10px 12px;font-family:monospace;font-weight:700;color:#e2e8f8;font-size:13px;">$' + str(round(total_val,2)) + '</td>'
             '<td style="padding:10px 12px;font-family:monospace;font-weight:700;color:' + pc + ';font-size:12px;">' + ('+' if pnl>=0 else '') + '$' + str(round(abs(pnl),2)) + '<div style="font-size:10px;">' + ('+' if pct>=0 else '') + str(round(pct,2)) + '%</div></td>'
             '</tr>')
    return ('<table style="width:100%;border-collapse:collapse;">'
            '<thead><tr style="background:#141928;">'
            '<th style="padding:8px 12px;text-align:left;font-family:monospace;font-size:9px;color:#6b7280;letter-spacing:1px;text-transform:uppercase;">Position</th>'
            '<th style="padding:8px 12px;text-align:left;font-family:monospace;font-size:9px;color:#6b7280;letter-spacing:1px;text-transform:uppercase;">Price</th>'
            '<th style="padding:8px 12px;text-align:left;font-family:monospace;font-size:9px;color:#6b7280;letter-spacing:1px;text-transform:uppercase;">Today</th>'
            '<th style="padding:8px 12px;text-align:left;font-family:monospace;font-size:9px;color:#6b7280;letter-spacing:1px;text-transform:uppercase;">Value</th>'
            '<th style="padding:8px 12px;text-align:left;font-family:monospace;font-size:9px;color:#6b7280;letter-spacing:1px;text-transform:uppercase;">Total P&amp;L</th>'
            '</tr></thead><tbody>' + rows + '</tbody></table>')

def earn_table():
    if not earnings:
        return '<p style="color:#6b7280;font-size:13px;padding:14px 16px;">No earnings from your holdings this week.</p>'
    rows = ""
    for e in earnings:
        rows += ('<tr><td style="padding:9px 12px;border-bottom:1px solid #1e2840;font-family:monospace;font-weight:700;color:#f59e0b;">' + e['symbol'] + '</td>'
                 '<td style="padding:9px 12px;border-bottom:1px solid #1e2840;font-family:monospace;color:#e2e8f8;">' + e['date'] + '</td>'
                 '<td style="padding:9px 12px;border-bottom:1px solid #1e2840;font-family:monospace;color:#8892a8;">' + str(e['hour']).upper() + '</td>'
                 '<td style="padding:9px 12px;border-bottom:1px solid #1e2840;font-family:monospace;color:#10d9a0;">$' + str(e['eps']) + '</td></tr>')
    return ('<table style="width:100%;border-collapse:collapse;">'
            '<thead><tr style="background:#141928;">'
            '<th style="padding:7px 12px;text-align:left;font-family:monospace;font-size:9px;color:#6b7280;text-transform:uppercase;">Ticker</th>'
            '<th style="padding:7px 12px;text-align:left;font-family:monospace;font-size:9px;color:#6b7280;text-transform:uppercase;">Date</th>'
            '<th style="padding:7px 12px;text-align:left;font-family:monospace;font-size:9px;color:#6b7280;text-transform:uppercase;">Time</th>'
            '<th style="padding:7px 12px;text-align:left;font-family:monospace;font-size:9px;color:#6b7280;text-transform:uppercase;">EPS Est</th>'
            '</tr></thead><tbody>' + rows + '</tbody></table>')

def news_items():
    if not all_news:
        return '<p style="color:#6b7280;font-size:13px;padding:14px 16px;">No recent news.</p>'
    items = ""
    for n in all_news[:6]:
        items += ('<div style="padding:11px 16px;border-bottom:1px solid #1e2840;">'
                  '<div style="display:flex;gap:8px;align-items:flex-start;">'
                  '<span style="font-family:monospace;font-size:10px;font-weight:700;color:#4f8ef7;background:rgba(79,142,247,0.1);padding:2px 7px;border-radius:4px;white-space:nowrap;margin-top:1px;">' + n['symbol'] + '</span>'
                  '<div><div style="font-size:13px;color:#e2e8f8;line-height:1.5;margin-bottom:2px;">' + n['headline'] + '</div>'
                  '<div style="font-family:monospace;font-size:10px;color:#6b7280;">' + n['source'] + '</div></div></div></div>')
    return items

def weather_table():
    if not weather_forecast:
        return '<p style="color:#6b7280;padding:14px 16px;">' + weather_info + '</p>'
    rows = ""
    for d in weather_forecast:
        rain = str(d['rain']) + "mm" if d['rain'] > 0 else "Dry"
        rows += ('<tr><td style="padding:9px 12px;border-bottom:1px solid #1e2840;font-family:monospace;color:#e2e8f8;font-size:12px;font-weight:600;">' + d['day'] + '</td>'
                 '<td style="padding:9px 12px;border-bottom:1px solid #1e2840;color:#8892a8;font-size:12px;">' + d['condition'] + '</td>'
                 '<td style="padding:9px 12px;border-bottom:1px solid #1e2840;font-family:monospace;color:#f59e0b;font-size:12px;">' + str(d['max']) + 'C / ' + str(d['min']) + 'C</td>'
                 '<td style="padding:9px 12px;border-bottom:1px solid #1e2840;font-family:monospace;color:#6b7280;font-size:11px;">' + rain + '</td></tr>')
    return ('<table style="width:100%;border-collapse:collapse;">'
            '<thead><tr style="background:#141928;">'
            '<th style="padding:7px 12px;text-align:left;font-family:monospace;font-size:9px;color:#6b7280;text-transform:uppercase;">Day</th>'
            '<th style="padding:7px 12px;text-align:left;font-family:monospace;font-size:9px;color:#6b7280;text-transform:uppercase;">Conditions</th>'
            '<th style="padding:7px 12px;text-align:left;font-family:monospace;font-size:9px;color:#6b7280;text-transform:uppercase;">Temp</th>'
            '<th style="padding:7px 12px;text-align:left;font-family:monospace;font-size:9px;color:#6b7280;text-transform:uppercase;">Rain</th>'
            '</tr></thead><tbody>' + rows + '</tbody></table>')

h = NOW.hour
greeting = "Good morning" if h < 12 else "Good afternoon" if h < 17 else "Good evening"

verdict = ""
if S.get('verdict'):
    verdict = ('<tr><td style="padding-bottom:14px;">'
               '<div style="background:linear-gradient(135deg,#1d4ed8,#2563eb);border-radius:12px;padding:22px;">'
               '<div style="font-family:monospace;font-size:10px;letter-spacing:3px;color:rgba(255,255,255,0.5);text-transform:uppercase;margin-bottom:10px;">SHADOW VERDICT</div>'
               '<div style="font-size:15px;color:#fff;line-height:1.75;font-weight:500;">' + fmt(S['verdict']) + '</div>'
               '</div></td></tr>')

earn_block = ""
if earnings:
    earn_block = ('<tr><td style="padding-bottom:14px;">'
                  '<div style="background:#0e1220;border:1px solid #f59e0b;border-radius:12px;overflow:hidden;">'
                  '<div style="padding:11px 18px;background:#141928;border-bottom:1px solid #1e2840;">'
                  '<span style="font-family:monospace;font-size:11px;letter-spacing:2px;color:#f59e0b;text-transform:uppercase;font-weight:700;">EARNINGS THIS WEEK</span>'
                  '</div>' + earn_table() + '</div></td></tr>')

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
    '<div style="font-family:monospace;font-size:12px;color:#7889a8;">' + TODAY_STR + ' &nbsp;|&nbsp; ' + TIME_STR + ' &nbsp;|&nbsp; Abu Dhabi GMT+4</div>'
    '</div></td></tr>'

    '<tr><td style="padding-bottom:14px;">'
    '<div style="background:#0e1220;border:1px solid #1e2840;border-radius:12px;padding:18px 22px;">'
    '<div style="font-size:20px;font-weight:700;color:#e2e8f8;margin-bottom:5px;">' + greeting + ', ' + USER_NAME + '.</div>'
    '<div style="font-size:13px;color:#6b7280;line-height:1.6;">Your morning intelligence brief is ready. ' + str(len(portfolio)) + ' holdings tracked &nbsp;|&nbsp; ' + str(len(all_news)) + ' news items &nbsp;|&nbsp; ' + str(sum(1 for v in S.values() if v)) + '/10 sections</div>'
    '</div></td></tr>'

    + verdict +

    '<tr><td style="padding-bottom:14px;">'
    '<div style="background:#0e1220;border:1px solid #1e2840;border-radius:12px;overflow:hidden;">'
    '<div style="padding:11px 18px;background:#141928;border-bottom:1px solid #1e2840;">'
    '<span style="font-family:monospace;font-size:10px;letter-spacing:2px;color:#4f8ef7;text-transform:uppercase;font-weight:700;">US EQUITIES</span>'
    '</div>' + ticker_row() + indices_row() + macro_row() + '</div></td></tr>'

    '<tr><td style="padding-bottom:14px;">'
    '<div style="background:#0e1220;border:1px solid #1e2840;border-radius:12px;overflow:hidden;">'
    '<div style="padding:11px 18px;background:#141928;border-bottom:1px solid #1e2840;">'
    '<span style="font-family:monospace;font-size:11px;letter-spacing:2px;color:#4f8ef7;text-transform:uppercase;font-weight:700;">YOUR PORTFOLIO</span>'
    '</div>' + port_table() + '</div></td></tr>'

    + earn_block +

    '<tr><td style="padding-bottom:14px;">'
    '<div style="background:#0e1220;border:1px solid #1e2840;border-radius:12px;overflow:hidden;">'
    '<div style="padding:11px 18px;background:#141928;border-bottom:1px solid #1e2840;">'
    '<span style="font-family:monospace;font-size:11px;letter-spacing:2px;color:#7889a8;text-transform:uppercase;font-weight:700;">STOCK NEWS</span>'
    '</div>' + news_items() + '</div></td></tr>'

    '<tr><td>'
    + sec('MARKET OPEN ANALYSIS', S.get('market',''), '#4f8ef7')
    + sec('PORTFOLIO INTELLIGENCE', S.get('portfolio',''), '#10d9a0')
    + sec('EARNINGS ANALYSIS', S.get('earnings',''), '#f59e0b')
    + sec('AI & TECHNOLOGY', S.get('ai',''), '#a855f7')
    + sec('GEOPOLITICAL INTELLIGENCE', S.get('geo',''), '#f59e0b')
    + '</td></tr>'

    '<tr><td style="padding-bottom:14px;">'
    '<div style="background:#0e1220;border:1px solid #1e2840;border-radius:12px;overflow:hidden;">'
    '<div style="padding:11px 18px;background:#141928;border-bottom:1px solid #1e2840;">'
    '<span style="font-family:monospace;font-size:11px;letter-spacing:2px;color:#10d9a0;text-transform:uppercase;font-weight:700;">ABU DHABI WEATHER</span>'
    '</div>' + weather_table() + '</div></td></tr>'

    '<tr><td>'
    + sec('TASKS & PRIORITIES', S.get('tasks',''), '#10d9a0')
    + sec('TRAVEL INTELLIGENCE', S.get('travel',''), '#f59e0b')
    + '</td></tr>'

    '<tr><td style="text-align:center;padding:20px 0;">'
    '<a href="https://aistudioaj.github.io/project-shadow/" style="display:inline-block;background:linear-gradient(135deg,#1d4ed8,#4f8ef7);color:#fff;text-decoration:none;padding:13px 32px;border-radius:10px;font-family:monospace;font-size:12px;font-weight:700;letter-spacing:2px;text-transform:uppercase;">OPEN SHADOW</a>'
    '</td></tr>'

    '<tr><td style="padding:16px;text-align:center;border-top:1px solid #1e2840;">'
    '<div style="font-family:monospace;font-size:10px;color:#3d4d6a;">PROJECT SHADOW &nbsp;|&nbsp; ' + TODAY_STR + ' &nbsp;|&nbsp; Abu Dhabi UAE</div>'
    '</td></tr>'

    '</table></td></tr></table></body></html>'
)

print("Sending via Resend...")
plain = "Shadow Morning Brief " + TODAY_STR + "\n\n" + "\n\n".join([k.upper() + ":\n" + v for k,v in S.items() if v])
plain += "\n\nOpen Shadow: https://aistudioaj.github.io/project-shadow/"

try:
    r = requests.post(
        "https://api.resend.com/emails",
        headers={"Authorization": "Bearer " + RESEND_KEY, "Content-Type": "application/json"},
        json={"from": "Shadow AI <onboarding@resend.dev>", "to": [EMAIL_TO], "subject": "Shadow Brief " + DATE_SHORT + " | " + str(len(portfolio)) + " Holdings | " + str(len(all_news)) + " News", "text": plain, "html": html},
        timeout=30
    )
    if r.status_code in [200,201]:
        print("Email sent to " + EMAIL_TO)
    else:
        print("Resend error: " + str(r.status_code) + " " + r.text)
        raise Exception("Resend failed: " + r.text)
except Exception as e:
    print("Email error: " + str(e))
    raise

print("Shadow Morning Brief v2 complete! " + TODAY_STR)
