"""安全护栏：转账前做风险分级，映射到方案书 L0–L4 五级模型。"""
import sqlite3
from datetime import datetime
import os

DB_PATH = os.path.join(os.path.dirname(__file__), "..", "data", "bank.db")


def _contacts():
    conn = sqlite3.connect(DB_PATH)
    rows = conn.execute("SELECT phone FROM contacts").fetchall()
    conn.close()
    return {r[0] for r in rows}


def check_transfer(to_phone: str, amount: float):
    """返回 (level, risks)，level ∈ L0/L2/L3/L4。"""
    risks = []
    if amount >= 500:
        risks.append(f"大额转账 {amount:.0f} 元")
    if to_phone not in _contacts():
        risks.append("收款人不在常用通讯录")
    h = datetime.now().hour
    if h >= 23 or h < 7:
        risks.append("当前是深夜交易时段")

    if amount >= 5000 and to_phone not in _contacts():
        return "L4", risks + ["超大额向新收款人转账，建议转人工坐席核验"]
    if len(risks) >= 2:
        return "L3", risks
    if len(risks) == 1 and amount >= 1000:
        return "L3", risks
    if risks:
        return "L2", risks
    return "L0", []
