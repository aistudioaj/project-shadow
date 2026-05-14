# -*- coding: utf-8 -*-
#!/usr/bin/env python3
"""
Project Shadow - Proactive Trigger Engine
Runs every hour via GitHub Actions
Checks: price alerts, upcoming trips, exams, overdue tasks
Sends: email via Resend + saves to Supabase shadow_alerts
"""

import os
import json
import requests
from datetime import datetime, timezone, timedelta

ANTHROPIC_KEY = os.environ['ANTHROPIC_KEY']
SUPABASE_URL  = os.environ['SUPABASE_URL']
SUPABASE_KEY  = os.environ['SUPABASE_KEY']
FINNHUB_KEY   = os.environ['FINNHUB_KEY']
EMAIL_TO      = os.environ['EMAIL_TO']
RESEND_KEY    = os.environ['RESEND_KEY']
USER_ID       = os.environ.get('USER_ID', 'abdulrahman')
USER_NAME     = os.environ.get('USER_NAME', 'AJ')

ABU_DHABI_TZ = timezone(timedelta(hours=4))
NOW = datetime.now(ABU_DHABI_TZ)
TODAY_STR = NOW.strftime('%A, %B %d, %Y')
TIME_STR = NOW.strftime('%I:%M %p')

print("Shadow Trigger Engine: " + TODAY_STR + " " + TIME_STR)

# -- HELPERS --

def fetch_supabase(table, filters=""):
    try:
        url = SUPABASE_URL + "/rest/v1/" + table + "?user_id=eq." + USER_ID + filters + "&select=*"
        headers = {'apikey': SUPABASE_KEY, 'Authorization': 'Bearer ' + SUPABASE_KEY}
        r = requests.get(url, headers=headers, timeout=10)
        return r.json()
    except Exception as e:
        print("Supabase error " + table + ": " + str(e))
        return []

def save_alert(alert_type, title, message, priority='normal'):
    try:
        data = {
            "user_id": USER_ID,
            "type": alert_type,
            "title": title,
            "message": message,
            "priority": priority,
            "is_read": False,
            "created_at": NOW.isoformat()
        }
        headers = {
            'apikey': SUPABASE_KEY,
            'Authorization': 'Bearer ' + SUPABASE_KEY,
            'Content-Type': 'application/json'
        }
        r = requests.post(SUPABASE_URL + "/rest/v1/shadow_alerts", headers=headers, json=data, timeout=10)
        if r.status_code in [200, 201]:
            print("  Alert saved: " + title)
            return True
        else:
            print("  Alert save error: " + str(r.status_code))
            return False
    except Exception as e:
        print("  Alert save error: " + str(e))
        return False

def already_alerted(alert_type, identifier):
    try:
        today = NOW.strftime('%Y-%m-%d')
        url = (SUPABASE_URL + "/rest/v1/shadow_alerts?user_id=eq." + USER_ID +
               "&type=eq." + alert_type +
               "&title=like.*" + identifier + "*" +
               "&created_at=gte." + today +
               "T00:00:00&select=id&limit=1")
        headers = {'apikey': SUPABASE_KEY, 'Authorization': 'Bearer ' + SUPABASE_KEY}
        r = requests.get(url, headers=headers, timeout=10)
        data = r.json()
        return len(data) > 0
    except:
        return False

def send_alert_email(subject, body_html, body_plain):
    try:
        r = requests.post(
            "https://api.resend.com/emails",
            headers={"Authorization": "Bearer " + RESEND_KEY, "Content-Type": "application/json"},
            json={
                "from": "Shadow AI <onboarding@resend.dev>",
                "to": [EMAIL_TO],
                "subject": subject,
                "text": body_plain,
                "html": body_html
            },
            timeout=15
        )
        if r.status_code in [200, 201]:
            print("  Email sent: " + subject)
            return True
        else:
            print("  Email error: " + str(r.status_code))
            return False
    except Exception as e:
        print("  Email error: " + str(e))
        return False

def make_alert_email(title, message, alert_type, priority):
    color_map = {'high': '#f43f5e', 'normal': '#4f8ef7', 'low': '#10d9a0'}
    color = color_map.get(priority, '#4f8ef7')
    icon_map = {'price': 'PRICE ALERT', 'travel': 'TRAVEL ALERT', 'exam': 'EXAM ALERT', 'task': 'TASK ALERT', 'market': 'MARKET ALERT'}
    label = icon_map.get(alert_type, 'SHADOW ALERT')

    html = (
        '<!DOCTYPE html><html><head><meta charset="UTF-8"></head>'
        '<body style="margin:0;padding:0;background:#060810;font-family:Arial,sans-serif;">'
        '<table width="100%" cellpadding="0" cellspacing="0" style="background:#060810;">'
        '<tr><td align="center" style="padding:20px;">'
        '<table width="600" cellpadding="0" cellspacing="0" style="max-width:600px;width:100%;">'
        '<tr><td style="background:#0e1220;border:1px solid #1e2840;border-radius:16px;padding:28px;text-align:center;margin-bottom:16px;">'
        '<div style="font-family:monospace;font-size:32px;font-weight:900;letter-spacing:8px;color:#4f8ef7;">SHADOW</div>'
        '<div style="font-family:monospace;font-size:10px;letter-spacing:3px;color:#454d60;text-transform:uppercase;">PROACTIVE ALERT</div>'
        '</td></tr>'
        '<tr><td style="height:12px;"></td></tr>'
        '<tr><td style="background:linear-gradient(135deg,' + color + ',' + color + 'cc);border-radius:12px;padding:24px;">'
        '<div style="font-family:monospace;font-size:10px;letter-spacing:3px;color:rgba(255,255,255,0.6);text-transform:uppercase;margin-bottom:10px;">' + label + '</div>'
        '<div style="font-size:18px;font-weight:700;color:#ffffff;margin-bottom:10px;">' + title + '</div>'
        '<div style="font-size:14px;color:rgba(255,255,255,0.85);line-height:1.7;">' + message.replace('\n','<br>') + '</div>'
        '</td></tr>'
        '<tr><td style="height:12px;"></td></tr>'
        '<tr><td style="text-align:center;padding:16px 0;">'
        '<a href="https://aistudioaj.github.io/project-shadow/" style="display:inline-block;background:linear-gradient(135deg,#1d4ed8,#4f8ef7);color:#fff;text-decoration:none;padding:12px 28px;border-radius:10px;font-family:monospace;font-size:12px;font-weight:700;letter-spacing:2px;text-transform:uppercase;">OPEN SHADOW</a>'
        '</td></tr>'
        '<tr><td style="padding:16px;text-align:center;border-top:1px solid #1e2840;">'
        '<div style="font-family:monospace;font-size:10px;color:#3d4d6a;">PROJECT SHADOW - ' + TIME_STR + ' - ' + TODAY_STR + '</div>'
        '</td></tr>'
        '</table></td></tr></table></body></html>'
    )
    plain = label + "\n\n" + title + "\n\n" + message + "\n\nOpen Shadow: https://aistudioaj.github.io/project-shadow/"
    return html, plain

# -- TRIGGER 1: PRICE ALERTS --

print("\nChecking price alerts...")
WATCHLIST = ['AAPL', 'MSFT', 'NVDA', 'AMZN', 'GOOGL', 'META', 'TSLA', 'JPM', 'SPUS', 'SPWO']
PRICE_ALERT_THRESHOLD = 3.0

for sym in WATCHLIST:
    try:
        url = "https://finnhub.io/api/v1/quote?symbol=" + sym + "&token=" + FINNHUB_KEY
        r = requests.get(url, timeout=10)
        q = r.json()
        if q.get('c', 0) > 0 and abs(q.get('dp', 0)) >= PRICE_ALERT_THRESHOLD:
            direction = "UP" if q['dp'] > 0 else "DOWN"
            pct = round(q['dp'], 2)
            price = round(q['c'], 2)
            title = sym + " " + direction + " " + str(abs(pct)) + "% to $" + str(price)

            if not already_alerted('price', sym):
                print("  ALERT: " + title)
                msg = (sym + " has moved " + direction + " " + str(abs(pct)) + "% today to $" + str(price) + ".\n\n" +
                       "Previous close: $" + str(round(q.get('pc', 0), 2)) + "\n" +
                       "Day range: $" + str(round(q.get('l', 0), 2)) + " - $" + str(round(q.get('h', 0), 2)) + "\n\n" +
                       "This is a significant move. Review your position and consider if action is needed.")
                priority = 'high' if abs(pct) >= 5 else 'normal'
                html, plain = make_alert_email("Price Alert: " + title, msg, 'price', priority)
                send_alert_email("Shadow Alert: " + title, html, plain)
                save_alert('price', title, msg, priority)
            else:
                print("  Already alerted: " + sym)
        else:
            print("  " + sym + ": " + str(round(q.get('dp', 0), 2)) + "% - no alert")
    except Exception as e:
        print("  Price check error " + sym + ": " + str(e))

# -- TRIGGER 2: UPCOMING TRIPS --

print("\nChecking travel alerts...")
memories = fetch_supabase('shadow_memory', '&order=importance.desc&limit=50')
trip_keywords = ['trip', 'travel', 'flight', 'london', 'dubai', 'visit']

for mem in memories:
    key = mem.get('key', '').lower()
    value = mem.get('value', '')

    if any(kw in key for kw in trip_keywords) or any(kw in value.lower() for kw in trip_keywords):
        # Try to extract date from value
        import re
        date_patterns = [
            r'(\w+ \d{1,2},?\s*\d{4})',
            r'(\d{1,2}/\d{1,2}/\d{4})',
            r'(\d{4}-\d{2}-\d{2})',
            r'May (\d{1,2})',
            r'June (\d{1,2})',
            r'July (\d{1,2})',
        ]

        for pattern in date_patterns:
            match = re.search(pattern, value, re.IGNORECASE)
            if match:
                try:
                    date_str = match.group(1)
                    # Try to parse
                    for fmt in ['%B %d, %Y', '%B %d %Y', '%m/%d/%Y', '%Y-%m-%d']:
                        try:
                            trip_date = datetime.strptime(date_str, fmt).replace(tzinfo=ABU_DHABI_TZ)
                            days_away = (trip_date.date() - NOW.date()).days
                            if 0 <= days_away <= 10:
                                identifier = mem['key'][:20]
                                if not already_alerted('travel', identifier):
                                    title = "Trip in " + str(days_away) + " days: " + mem.get('key', 'Upcoming trip')
                                    msg = ("Your trip is " + str(days_away) + " days away.\n\n" +
                                           "Details: " + value + "\n\n" +
                                           "Actions to complete:\n" +
                                           "- Confirm flight and hotel bookings\n" +
                                           "- Pack list preparation\n" +
                                           "- Notify credit cards\n" +
                                           "- Arrange home coverage")
                                    print("  ALERT: " + title)
                                    html, plain = make_alert_email(title, msg, 'travel', 'high' if days_away <= 3 else 'normal')
                                    send_alert_email("Shadow Alert: " + title, html, plain)
                                    save_alert('travel', title, msg, 'high' if days_away <= 3 else 'normal')
                            break
                        except:
                            continue
                except:
                    continue
                break

# -- TRIGGER 3: UPCOMING EXAMS --

print("\nChecking exam alerts...")
exam_keywords = ['exam', 'assessment', 'gl assessment', 'test', 'interview']

for mem in memories:
    key = mem.get('key', '').lower()
    value = mem.get('value', '')

    if any(kw in key for kw in exam_keywords) or any(kw in value.lower() for kw in exam_keywords):
        import re
        date_patterns = [r'May (\d{1,2})', r'June (\d{1,2})', r'(\w+ \d{1,2},?\s*\d{4})']
        for pattern in date_patterns:
            match = re.search(pattern, value, re.IGNORECASE)
            if match:
                try:
                    month_map = {'may': 5, 'june': 6, 'july': 7}
                    date_str = match.group(0)
                    month_match = re.search(r'(may|june|july)\s+(\d{1,2})', date_str, re.IGNORECASE)
                    if month_match:
                        month = month_map.get(month_match.group(1).lower(), 5)
                        day = int(month_match.group(2))
                        exam_date = datetime(NOW.year, month, day, tzinfo=ABU_DHABI_TZ)
                        days_away = (exam_date.date() - NOW.date()).days
                        if 0 <= days_away <= 7:
                            identifier = mem['key'][:20]
                            if not already_alerted('exam', identifier):
                                title = "Exam in " + str(days_away) + " days: " + mem.get('key', 'Upcoming exam')
                                msg = ("Exam is " + str(days_away) + " days away.\n\n" +
                                       "Details: " + value + "\n\n" +
                                       "Today's preparation:\n" +
                                       "- Complete one full practice test section\n" +
                                       "- Review incorrect answers from last session\n" +
                                       "- Focus on weak areas\n" +
                                       "- Ensure 8+ hours sleep before exam day")
                                print("  ALERT: " + title)
                                html, plain = make_alert_email(title, msg, 'exam', 'high')
                                send_alert_email("Shadow Alert: " + title, html, plain)
                                save_alert('exam', title, msg, 'high')
                except:
                    continue
                break

# -- TRIGGER 4: OVERDUE TASKS --

print("\nChecking overdue tasks...")
tasks = fetch_supabase('shadow_tasks', '&status=neq.done')

for task in tasks:
    due = task.get('due_date')
    if due:
        try:
            due_date = datetime.fromisoformat(due.replace('Z','+00:00')).astimezone(ABU_DHABI_TZ)
            days_overdue = (NOW.date() - due_date.date()).days
            if days_overdue >= 2:
                title_str = task.get('title', 'Unnamed task')
                identifier = title_str[:20]
                if not already_alerted('task', identifier):
                    title = "Overdue: " + title_str + " (" + str(days_overdue) + " days)"
                    msg = ("Task is " + str(days_overdue) + " days overdue.\n\n" +
                           "Task: " + title_str + "\n" +
                           "Priority: " + task.get('priority', 'normal').upper() + "\n" +
                           "Due date: " + due_date.strftime('%B %d, %Y') + "\n\n" +
                           "Action: Complete today or reschedule.")
                    print("  ALERT: " + title)
                    html, plain = make_alert_email(title, msg, 'task', 'high' if task.get('priority') == 'high' else 'normal')
                    send_alert_email("Shadow Alert: " + title, html, plain)
                    save_alert('task', title, msg, 'high' if task.get('priority') == 'high' else 'normal')
        except Exception as e:
            print("  Task date error: " + str(e))

print("\nShadow Trigger Engine complete: " + TIME_STR)
