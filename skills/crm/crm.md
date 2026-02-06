\# DailyCustomerAdditionsSkill

\## 功能

查询每日新增客户，返回每位销售的新增客户列表、跟进情况、来源和成交信息，并生成自然语言总结。

\## 接口

\### 请求方式

POST `/skill/daily\_customer\_additions`

\### 请求头

X-SKILL-TOKEN: <your_skill_token>

Content-Type: application/json

\### 请求参数（JSON）

| 参数 | 类型 | 必填 | 说明 |

|-------------|-------|-----|-------------------------------------|

| date | str | 否 | 查询日期，支持自然语言或 YYYY-MM-DD |

| sales_name | str | 否 | 销售姓名筛选 |

\### 支持自然语言日期

\- 今天、昨天、前天

\- 本周、上周

\- 本月、上月

\- YYYY-MM-DD

\### 响应示例

````json

{

&nbsp; "code": 0,

&nbsp; "msg": "success",

&nbsp; "date": "2026-02-05",

&nbsp; "total\_customers": 12,

&nbsp; "sales\_count": 3,

&nbsp; "summary": {

&nbsp;   "王强": 5,

&nbsp;   "李四": 4,

&nbsp;   "未分配": 3

&nbsp; },

&nbsp; "detail": {

&nbsp;   "王强": \[

&nbsp;     {

&nbsp;       "customer\_id": 101,

&nbsp;       "name": "客户A",

&nbsp;       "company": "公司A",

&nbsp;       "phone": "123456789",

&nbsp;       "wechat": "",

&nbsp;       "email": "",

&nbsp;       "status": "contacted",

&nbsp;       "source": "官网",

&nbsp;       "deal\_amount": 0.0,

&nbsp;       "deal\_time": "",

&nbsp;       "create\_time": "2026-02-05 09:00:00",

&nbsp;       "follow\_today\_count": 1,

&nbsp;       "last\_follow": {

&nbsp;         "time": "2026-02-05 10:00:00",

&nbsp;         "type": "phone",

&nbsp;         "content": "已联系",

&nbsp;         "next\_time": ""

&nbsp;       }

&nbsp;     }

&nbsp;   ]

&nbsp; }

}



\## Skill Python 使用示例



```python

skill = DailyCustomerAdditionsSkill()



\# 查询昨天

print(skill.run())



\# 查询本周王强新增客户

print(skill.run(date="本周", sales\_name="王强"))





````
