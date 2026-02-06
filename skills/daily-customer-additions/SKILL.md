---
name: daily-customer-additions
description: 查询每日新增客户信息，可按销售人员筛选，支持自然语言日期（昨天、今天、本周、本月等）。
---

# 每日新增客户查询 Skill

此 Skill 用于从 CRM 系统中获取每日新增客户信息，并按销售人员进行汇总，支持自然语言日期输入，例如“昨天”“今天”“本周”“本月”，也可指定具体销售姓名进行筛选。

## 工具

### daily_customer_additions.py

一个 Python 脚本，直接调用 `/skill/daily_customer_additions` 接口，返回每位销售的新增客户列表及跟进情况，并生成自然语言总结。

**文件位置：** `skills/daily-customer-additions/daily_customer_additions.py`

**用法：**

命令行直接运行：

```bash
# 查询昨天所有销售新增客户
python skills/daily-customer-additions/daily_customer_additions.py

# 查询昨天张小琴新增客户
python skills/daily-customer-additions/daily_customer_additions.py "昨天" "张小琴"

# 查询本周王强新增客户
python skills/daily-customer-additions/daily_customer_additions.py "本周" "王强"
```
