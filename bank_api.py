"""模拟银行核心系统：Agent 可调用的全部工具函数。"""
import sqlite3
from datetime import datetime
import os

from core.guardrail import check_transfer

DB_PATH = os.path.join(os.path.dirname(__file__), "..", "data", "bank.db")


def _conn():
    return sqlite3.connect(DB_PATH)


# 记录上次成功转账，用于重复交易防护和撤销
_last_transfer = {"to_phone": None, "to_name": None, "amount": None, "note": None}

# 单日累计限额
DAILY_LIMIT = 10000.0
_daily_transferred = {"date": None, "total": 0.0}

# 演示用交易密码
DEMO_PAY_PASSWORD = "8888"


def _mask_phone(p):
    s = str(p)
    if len(s) >= 11:
        return s[:3] + "****" + s[-4:]
    return s


def get_balance():
    conn = _conn()
    row = conn.execute("SELECT name, balance FROM users WHERE user_id='u001'").fetchone()
    conn.close()
    return {"name": row[0], "balance": row[1]}


def transfer(to_name, to_phone, amount, note="", confirmed=False, pay_password=""):
    level, risks = check_transfer(to_phone, amount)

    if level in ("L3", "L4") and not confirmed:
        return {"status": "need_confirm", "risk_level": level, "risks": risks,
                "message": f"检测到风险（{level}）：{'；'.join(risks)}。请向用户解释并确认后，还需输入交易密码才能放行。"}

    if level in ("L3", "L4") and confirmed and pay_password != DEMO_PAY_PASSWORD:
        return {"status": "need_password",
                "message": "高风险操作需要交易密码二次验证。请用户输入6位交易密码（演示密码：8888）。"}

    conn = _conn()
    row = conn.execute("SELECT balance FROM users WHERE user_id='u001'").fetchone()
    balance = row[0]
    if amount >= 50000:
        conn.close()
        return {"status": "amount_too_large",
                "message": f"单笔转账 {amount:.0f} 元超过系统单笔上限 5 万元，已拦截。"}
    if amount > balance * 0.5 and not confirmed:
        conn.close()
        return {"status": "amount_over_half_balance",
                "message": f"本次转账 {amount:.0f} 元超过当前余额 {balance:.2f} 的一半，请确认是否为误操作。"}

    today = datetime.now().strftime("%Y-%m-%d")
    if _daily_transferred["date"] != today:
        _daily_transferred["date"] = today
        _daily_transferred["total"] = 0.0
    if _daily_transferred["total"] + amount > DAILY_LIMIT and not confirmed:
        conn.close()
        return {"status": "exceed_daily_limit",
                "message": f"今日已累计转账 {_daily_transferred['total']:.0f} 元，加上本次将超过单日限额 {DAILY_LIMIT:.0f} 元。需二次确认或转人工。"}

    if (_last_transfer["to_phone"] == to_phone
            and _last_transfer["amount"] == amount and not confirmed):
        conn.close()
        return {"status": "duplicate_warning",
                "message": f"这笔转账（{to_name} {amount:.0f}元）跟您上一笔完全相同，可能是重复操作。"}

    if amount > balance:
        conn.close()
        return {"status": "insufficient_funds",
                "message": f"余额不足：当前可用余额 {balance:.2f} 元，无法转账 {amount:.2f} 元。"}

    conn.execute("UPDATE users SET balance = balance - ? WHERE user_id='u001'", (amount,))
    conn.commit()
    conn.close()

    _last_transfer["to_phone"] = to_phone
    _last_transfer["to_name"] = to_name
    _last_transfer["amount"] = amount
    _last_transfer["note"] = note
    _daily_transferred["total"] += amount

    return {"status": "success", "risk_level": level,
            "message": f"已向 {to_name}({_mask_phone(to_phone)}) 转账 {amount:.0f} 元"
                       + (f"，备注：{note}" if note else "")
                       + (f"（{level} 级风险，交易密码已核验放行）" if level in ("L3", "L4") else "")}


def cancel_last_transfer():
    if not _last_transfer["amount"]:
        return {"status": "nothing_to_cancel", "message": "最近没有可撤销的转账记录。"}
    amt = _last_transfer["amount"]
    name = _last_transfer["to_name"]
    conn = _conn()
    conn.execute("UPDATE users SET balance = balance + ? WHERE user_id='u001'", (amt,))
    conn.commit()
    conn.close()
    _last_transfer["amount"] = None
    _daily_transferred["total"] -= amt
    return {"status": "cancelled", "message": f"已撤销向 {name} 的转账 {amt:.0f} 元，资金已退回您的账户。"}


def get_bill_summary(month=None):
    conn = _conn()
    if month:
        rows = conn.execute("SELECT category, SUM(amount) FROM txns WHERE date LIKE ? GROUP BY category",
                           (month + "%",)).fetchall()
    else:
        rows = conn.execute("SELECT category, SUM(amount) FROM txns GROUP BY category").fetchall()
    conn.close()
    return {"month": month or "全部", "by_category": {c: round(a, 2) for c, a in rows}}


def list_subscriptions():
    conn = _conn()
    rows = conn.execute("SELECT sub_id, name, amount, next_charge FROM subs WHERE active=1").fetchall()
    conn.close()
    return {"subscriptions": [{"sub_id": s, "name": n, "amount": a, "next_charge": d}
                               for s, n, a, d in rows]}


def cancel_subscription(sub_id):
    conn = _conn()
    conn.execute("UPDATE subs SET active=0 WHERE sub_id=?", (sub_id,))
    conn.commit()
    row = conn.execute("SELECT name FROM subs WHERE sub_id=?", (sub_id,)).fetchone()
    conn.close()
    return {"status": "success", "message": f"已取消「{row[0]}」的自动续费。"}


def lock_fund(amount, purpose):
    return {"status": "success",
            "message": f"已锁定 {amount:.0f} 元作为「{purpose}」专款，使用前不会被其他消费占用。"}


def book_flower(recipient, budget):
    return {"status": "success",
            "message": f"已为 {recipient} 预订一束花（预算 {budget:.0f} 元内），将在指定日期送达。"}


def monthly_report(month):
    conn = _conn()
    rows = conn.execute("SELECT category, SUM(amount) FROM txns WHERE date LIKE ? GROUP BY category",
                       (month + "%",)).fetchall()
    prev = conn.execute("SELECT category, SUM(amount) FROM txns WHERE date LIKE ? GROUP BY category",
                       ("2026-09%",)).fetchall()
    top = conn.execute("SELECT date, merchant, amount FROM txns WHERE date LIKE ? AND amount<0 ORDER BY amount ASC LIMIT 3",
                      (month + "%",)).fetchall()
    conn.close()
    expense_by_cat = {c: round(a, 2) for c, a in rows if a < 0}
    income = sum(a for c, a in rows if a > 0)
    total_expense = -sum(a for c, a in rows if a < 0)
    prev_expense = -sum(a for c, a in prev if a < 0)
    return {"month": month, "total_income": round(income, 2),
            "total_expense": round(total_expense, 2),
            "expense_by_category": expense_by_cat,
            "vs_prev_month_delta": round(total_expense - prev_expense, 2),
            "top3_large_expense": [{"date": d, "merchant": n, "amount": round(a, 2)} for d, n, a in top]}


def detect_anomalies():
    from collections import Counter
    conn = _conn()
    rows = conn.execute("SELECT date, time, merchant, category, amount FROM txns ORDER BY date DESC, time DESC").fetchall()
    conn.close()
    merchant_count = Counter(r[2] for r in rows)
    anomalies = []
    for date, time, merchant, cat, amount in rows:
        reasons = []
        if amount <= -2000:
            reasons.append("大额单笔交易")
        h = int(time.split(":")[0]) if time else 12
        if h >= 23 or h < 7:
            reasons.append("深夜时段交易")
        if merchant_count[merchant] == 1:
            reasons.append("陌生商户首笔交易")
        if reasons:
            anomalies.append({"date": date, "time": time, "merchant": merchant,
                              "amount": round(amount, 2), "reasons": reasons})
    return {"anomaly_count": len(anomalies), "anomalies": anomalies}


def recommend_products(risk_level="低风险"):
    conn = _conn()
    rows = conn.execute("SELECT name, risk, annual_rate, period, min_buy FROM products WHERE risk=?",
                       (risk_level,)).fetchall()
    if not rows:
        rows = conn.execute("SELECT name, risk, annual_rate, period, min_buy FROM products").fetchall()
    conn.close()
    return {"risk_level": risk_level,
            "recommended": [{"name": n, "risk": r, "annual_rate": a, "period": p, "min_buy": m}
                            for n, r, a, p, m in rows]}


def buy_product(product_name, amount, confirmed=False, pay_password=""):
    conn = _conn()
    row = conn.execute("SELECT name, min_buy, annual_rate, period FROM products WHERE name=?",
                       (product_name,)).fetchone()
    if not row:
        conn.close()
        return {"status": "error", "message": f"未找到产品「{product_name}」"}
    name, min_buy, rate, period = row
    if amount < min_buy:
        conn.close()
        return {"status": "need_more_funds",
                "message": f"该产品起购金额 {min_buy} 元，您申购 {amount:.0f} 元不足。"}
    if not confirmed:
        conn.close()
        return {"status": "need_confirm", "risk_level": "L3",
                "risks": [f"申购理财 {product_name} {amount:.0f}元（历史年化{rate}%）"],
                "message": f"您正在申购「{product_name}」{amount:.0f}元，期限{period}，历史年化{rate}%。历史业绩不代表未来，确认申购吗？"}
    if pay_password != DEMO_PAY_PASSWORD:
        conn.close()
        return {"status": "need_password",
                "message": "理财申购为高风险操作，请输入6位交易密码（演示密码：8888）。"}
    bal = conn.execute("SELECT balance FROM users WHERE user_id='u001'").fetchone()[0]
    if amount > bal:
        conn.close()
        return {"status": "insufficient_funds",
                "message": f"可用余额 {bal:.2f} 元，不足以申购 {amount:.0f} 元。"}
    conn.execute("UPDATE users SET balance = balance - ? WHERE user_id='u001'", (amount,))
    conn.execute("CREATE TABLE IF NOT EXISTS holdings(product_name TEXT, amount REAL, buy_date TEXT)")
    conn.execute("INSERT INTO holdings(product_name, amount, buy_date) VALUES(?,?,?)",
                 (name, amount, datetime.now().strftime("%Y-%m-%d")))
    conn.commit()
    conn.close()
    return {"status": "success",
            "message": f"已申购「{name}」{amount:.0f} 元（交易密码已核验），预计到期收益约 {amount*rate/100:.0f} 元。"}


def list_holdings():
    conn = _conn()
    try:
        rows = conn.execute("SELECT product_name, amount, buy_date FROM holdings").fetchall()
    except sqlite3.OperationalError:
        rows = []
    conn.close()
    return {"holdings": [{"product": n, "amount": a, "buy_date": d} for n, a, d in rows]}


def redeem_product(product_name, confirmed=False, pay_password=""):
    conn = _conn()
    row = conn.execute("SELECT amount FROM holdings WHERE product_name=?", (product_name,)).fetchone()
    if not row:
        conn.close()
        return {"status": "error", "message": f"您没有持有「{product_name}」"}
    amount = row[0]
    if not confirmed:
        conn.close()
        return {"status": "need_confirm", "risk_level": "L3",
                "risks": [f"赎回「{product_name}」本金 {amount:.0f}元"],
                "message": f"赎回「{product_name}」{amount:.0f} 元，资金回到活期。确认赎回吗？确认后需输入交易密码。"}
    if pay_password != DEMO_PAY_PASSWORD:
        conn.close()
        return {"status": "need_password",
                "message": "赎回为高风险操作，请输入6位交易密码（演示密码：8888）。"}
    conn.execute("DELETE FROM holdings WHERE product_name=?", (product_name,))
    conn.execute("UPDATE users SET balance = balance + ? WHERE user_id='u001'", (amount,))
    conn.commit()
    conn.close()
    return {"status": "success", "message": f"已赎回「{product_name}」{amount:.0f} 元（交易密码已核验），资金已回到活期。"}


def send_lost_sms(card_last4):
    return {"status": "sms_sent",
            "message": f"已向尾号0001的预留手机发送6位验证码（演示验证码：654321）。请用户查收后调用 report_lost。"}


def report_lost(card_last4, sms_code):
    DEMO_SMS = "654321"
    if sms_code != DEMO_SMS:
        return {"status": "verify_failed", "message": "短信验证码不正确，挂失未执行。"}
    conn = _conn()
    row = conn.execute("SELECT card_id, status FROM cards WHERE last4=?", (card_last4,)).fetchone()
    if not row:
        conn.close()
        return {"status": "error", "message": f"尾号{card_last4}的卡片不存在"}
    if row[1] == "已挂失":
        conn.close()
        return {"status": "already_lost", "message": "该卡已挂失"}
    conn.execute("UPDATE cards SET status='已挂失' WHERE card_id=?", (row[0],))
    conn.commit()
    conn.close()
    return {"status": "success", "message": f"尾号{card_last4}的卡片已挂失，全部交易功能已冻结。"}


def split_bill(total_amount, num_people):
    per = round(total_amount / num_people, 2)
    return {"status": "success", "total": total_amount, "people": num_people, "per_person": per,
            "message": f"{num_people}人AA，每人应付 {per:.2f} 元。"}


def schedule_transfer(to_name, to_phone, amount, schedule_date):
    conn = _conn()
    conn.execute("CREATE TABLE IF NOT EXISTS scheduled(id INTEGER PRIMARY KEY AUTOINCREMENT, to_name TEXT, to_phone TEXT, amount REAL, schedule_date TEXT, status TEXT DEFAULT '待执行')")
    conn.execute("INSERT INTO scheduled(to_name, to_phone, amount, schedule_date) VALUES(?,?,?,?)",
                 (to_name, to_phone, amount, schedule_date))
    conn.commit()
    conn.close()
    return {"status": "scheduled",
            "message": f"已设定时转账：{schedule_date} 向 {to_name} 转 {amount:.0f} 元。执行前可撤销。"}


def list_scheduled():
    conn = _conn()
    try:
        rows = conn.execute("SELECT to_name, to_phone, amount, schedule_date, status FROM scheduled").fetchall()
    except sqlite3.OperationalError:
        rows = []
    conn.close()
    return {"scheduled": [{"to_name": n, "to_phone": p, "amount": a, "date": d, "status": s}
                          for n, p, a, d, s in rows]}


def risk_quiz(score):
    if score >= 70:
        return {"risk_level": "高风险", "advice": "可考虑权益类、指数增强产品",
                "message": "测评结果：您的风险承受能力为「高风险」。"}
    elif score >= 40:
        return {"risk_level": "中风险", "advice": "股债平衡型产品较适合",
                "message": "测评结果：您的风险承受能力为「中风险」。"}
    else:
        return {"risk_level": "低风险", "advice": "建议从货币基金、稳健理财起步",
                "message": "测评结果：您的风险承受能力为「低风险」。"}


def set_night_lock(enable=True):
    mode = "已开启" if enable else "已关闭"
    return {"status": "success", "night_lock": enable,
            "message": f"夜间锁卡{mode}：23:00–07:00 期间线上/境外交易将被拒绝。"}


def transfer_to_human(reason=""):
    return {"status": "human_queued",
            "message": f"已为您转接人工坐席。转接原因：{reason or '超权限操作'}。上下文已同步给坐席。"}


# ---------- 工具路由 ----------
import json

TOOL_FUNCS = {
    "get_balance": get_balance,
    "transfer": transfer,
    "get_bill_summary": get_bill_summary,
    "list_subscriptions": list_subscriptions,
    "cancel_subscription": cancel_subscription,
    "lock_fund": lock_fund,
    "book_flower": book_flower,
    "monthly_report": monthly_report,
    "detect_anomalies": detect_anomalies,
    "recommend_products": recommend_products,
    "buy_product": buy_product,
    "list_holdings": list_holdings,
    "redeem_product": redeem_product,
    "send_lost_sms": send_lost_sms,
    "report_lost": report_lost,
    "split_bill": split_bill,
    "schedule_transfer": schedule_transfer,
    "list_scheduled": list_scheduled,
    "risk_quiz": risk_quiz,
    "set_night_lock": set_night_lock,
    "transfer_to_human": transfer_to_human,
    "cancel_last_transfer": cancel_last_transfer,
}


def dispatch_tool(name, arguments_json):
    try:
        args = json.loads(arguments_json) if arguments_json else {}
        return TOOL_FUNCS[name](**args)
    except Exception as e:
        return {"status": "error", "message": f"工具 {name} 执行失败：{e}"}
