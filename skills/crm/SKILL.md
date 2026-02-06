---
name: crm
description: 查询每日新增客户，返回销售的新增客户列表、跟进情况、来源和成交信息
---

# CRM客户管理技能

## 功能

查询每日新增客户，返回每位销售的新增客户列表、跟进情况、来源和成交信息，并生成自然语言总结。

## 接口

### 请求方式

POST `/skill/daily_customer_additions`

### 请求头

```
X-SKILL-TOKEN: <your_skill_token>
Content-Type: application/json
```

### 请求参数（JSON）

| 参数       | 类型 | 必填 | 说明                                |
| ---------- | ---- | ---- | ----------------------------------- |
| date       | str  | 否   | 查询日期，支持自然语言或 YYYY-MM-DD |
| sales_name | str  | 否   | 销售姓名筛选                        |

### 支持自然语言日期

- 今天、昨天、前天
- 本周、上周
- 本月、上月
- YYYY-MM-DD

### 响应示例

```json
{
  "code": 0,
  "msg": "success",
  "date": "2026-02-05",
  "total_customers": 12,
  "sales_count": 3,
  "summary": {
    "王强": 5,
    "李四": 4,
    "未分配": 3
  },
  "detail": {
    "王强": [
      {
        "customer_id": 101,
        "name": "客户A",
        "company": "公司A",
        "phone": "123456789",
        "wechat": "",
        "email": "",
        "status": "contacted",
        "source": "官网",
        "deal_amount": 0.0,
        "deal_time": "",
        "create_time": "2026-02-05 09:00:00",
        "follow_today_count": 1,
        "last_follow": {
          "time": "2026-02-05 10:00:00",
          "type": "phone",
          "content": "已联系",
          "next_time": ""
        }
      }
    ]
  }
}
```

## Skill Python 使用示例

```python
skill = DailyCustomerAdditionsSkill()

# 查询昨天
print(skill.run())

# 查询本周王强新增客户
print(skill.run(date="本周", sales_name="王强"))
```

## 使用场景

1. 每日销售晨会：快速了解昨天新增客户情况
2. 周报月报：统计本周/本月新增客户数据
3. 销售管理：查看特定销售的客户跟进情况
4. 客户分析：了解客户来源和成交情况
