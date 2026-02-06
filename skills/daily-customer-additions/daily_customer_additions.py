import json
import urllib.request
import urllib.parse
import sys
from datetime import datetime, timedelta

# ---------- 配置 ----------
API_BASE_URL = "https://crm.example.com/api/skill/daily_customer_additions"
SKILL_TOKEN = "SKILL-GEMINI-CRM"

# ---------- 日期解析 ----------
def parse_natural_date(date_str: str = None):
    today = datetime.now()
    date_str = (date_str or "昨天").strip()

    if date_str == "今天":
        start_date = end_date = today
    elif date_str == "昨天":
        start_date = end_date = today - timedelta(days=1)
    elif date_str == "前天":
        start_date = end_date = today - timedelta(days=2)
    elif date_str == "本周":
        start_date = today - timedelta(days=today.weekday())
        end_date = today
    elif date_str == "上周":
        start_date = today - timedelta(days=today.weekday() + 7)
        end_date = start_date + timedelta(days=6)
    elif date_str == "本月":
        start_date = today.replace(day=1)
        end_date = today
    elif date_str == "上月":
        first_day_this_month = today.replace(day=1)
        last_day_last_month = first_day_this_month - timedelta(days=1)
        start_date = last_day_last_month.replace(day=1)
        end_date = last_day_last_month
    else:
        # 尝试 YYYY-MM-DD
        try:
            start_date = end_date = datetime.strptime(date_str, "%Y-%m-%d")
        except Exception:
            start_date = end_date = today - timedelta(days=1)

    return start_date.strftime("%Y-%m-%d"), end_date.strftime("%Y-%m-%d")

# ---------- 调用 CRM Skill 接口 ----------
def call_api(date, sales_name=None):
    try:
        url = API_BASE_URL
        payload = {"date": date}
        if sales_name:
            payload["sales_name"] = sales_name

        data = json.dumps(payload).encode("utf-8")
        headers = {
            "X-SKILL-TOKEN": SKILL_TOKEN,
            "Content-Type": "application/json"
        }
        req = urllib.request.Request(url, data=data, headers=headers, method="POST")
        with urllib.request.urlopen(req, timeout=10) as response:
            if response.status != 200:
                return {"code": 500, "msg": f"HTTP {response.status}"}
            return json.loads(response.read().decode("utf-8"))
    except Exception as e:
        return {"code": 500, "msg": str(e)}

# ---------- 聚合数据（多天范围） ----------
def aggregate_data(start_date, end_date, sales_name=None):
    start_dt = datetime.strptime(start_date, "%Y-%m-%d")
    end_dt = datetime.strptime(end_date, "%Y-%m-%d")
    delta = (end_dt - start_dt).days

    aggregated = {}
    for i in range(delta + 1):
        day = (start_dt + timedelta(days=i)).strftime("%Y-%m-%d")
        data = call_api(day, sales_name)
        if data.get("code") != 0:
            continue
        detail = data.get("detail", {})
        for sales, customers in detail.items():
            aggregated.setdefault(sales, []).extend(customers)
    return aggregated

# ---------- 生成自然语言总结 ----------
def summarize(aggregated_data, start_date, end_date):
    summary_lines = []
    total_customers = sum(len(custs) for custs in aggregated_data.values())
    sales_count = len(aggregated_data)
    summary_lines.append(f"{start_date} 至 {end_date} 新增客户总数 {total_customers} 人，涉及 {sales_count} 位销售。")

    for sales_name, customers in aggregated_data.items():
        summary_lines.append(f"{sales_name} 新增 {len(customers)} 个客户：")
        for cust in customers:
            follow_count = cust.get("follow_today_count", 0)
            last_follow = cust.get("last_follow")
            follow_info = ""
            if last_follow:
                follow_info = f"，最近跟进({last_follow.get('type')}) {last_follow.get('time')}"
            summary_lines.append(
                f"  - {cust.get('name')} ({cust.get('company','')}){follow_info}, 跟进次数 {follow_count}"
            )

    return "\n".join(summary_lines)

# ---------- 命令行执行 ----------
if __name__ == "__main__":
    date_arg = sys.argv[1] if len(sys.argv) > 1 else None
    sales_arg = sys.argv[2] if len(sys.argv) > 2 else None

    start_date, end_date = parse_natural_date(date_arg)
    aggregated = aggregate_data(start_date, end_date, sales_arg)
    summary_text = summarize(aggregated, start_date, end_date)

    print(summary_text)
