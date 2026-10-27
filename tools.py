"""给 DeepSeek 看的 function calling schema。"""

BANK_TOOLS = [
    {
        "type": "function",
        "function": {
            "name": "get_balance",
            "description": "查询当前用户的账户余额",
            "parameters": {"type": "object", "properties": {}},
        },
    },
    {
        "type": "function",
        "function": {
            "name": "transfer",
            "description": "向指定收款人转账。高风险时先返回 need_confirm，用户确认后若再返回 need_password，必须索要交易密码并填入 pay_password 才能完成。",
            "parameters": {
                "type": "object",
                "properties": {
                    "to_name": {"type": "string", "description": "收款人姓名"},
                    "to_phone": {"type": "string", "description": "收款人手机号"},
                    "amount": {"type": "number", "description": "转账金额"},
                    "note": {"type": "string", "description": "转账备注，可选"},
                    "confirmed": {"type": "boolean", "description": "用户是否已确认风险，默认 false"},
                    "pay_password": {"type": "string", "description": "交易密码（高风险操作必填），用户从对话中提供后原样填入"},
                },
                "required": ["to_name", "to_phone", "amount"],
            },
        },
    },
    {
        "type": "function",
        "function": {
            "name": "get_bill_summary",
            "description": "查询账单分类汇总。month 形如 2026-10，不传返回全部。",
            "parameters": {
                "type": "object",
                "properties": {
                    "month": {"type": "string", "description": "月份，如 2026-10"},
                },
            },
        },
    },
    {
        "type": "function",
        "function": {
            "name": "monthly_report",
            "description": "生成月度账单报告：总收入、总支出、分类明细、环比、最大几笔开销。",
            "parameters": {
                "type": "object",
                "properties": {
                    "month": {"type": "string", "description": "月份，如 2026-10"},
                },
                "required": ["month"],
            },
        },
    },
    {
        "type": "function",
        "function": {
            "name": "detect_anomalies",
            "description": "识别可疑交易：大额单笔、深夜交易、陌生商户、异常扣费。",
            "parameters": {"type": "object", "properties": {}},
        },
    },
    {
        "type": "function",
        "function": {
            "name": "list_subscriptions",
            "description": "查询当前生效的自动续费订阅列表。",
            "parameters": {"type": "object", "properties": {}},
        },
    },
    {
        "type": "function",
        "function": {
            "name": "cancel_subscription",
            "description": "取消指定自动续费。",
            "parameters": {
                "type": "object",
                "properties": {
                    "sub_id": {"type": "string", "description": "订阅ID，如 s1"},
                },
                "required": ["sub_id"],
            },
        },
    },
    {
        "type": "function",
        "function": {
            "name": "lock_fund",
            "description": "锁定一笔预算作为专款（如生日预算），避免被其他消费占用。",
            "parameters": {
                "type": "object",
                "properties": {
                    "amount": {"type": "number"},
                    "purpose": {"type": "string"},
                },
                "required": ["amount", "purpose"],
            },
        },
    },
    {
        "type": "function",
        "function": {
            "name": "book_flower",
            "description": "代订鲜花。",
            "parameters": {
                "type": "object",
                "properties": {
                    "recipient": {"type": "string"},
                    "budget": {"type": "number"},
                },
                "required": ["recipient", "budget"],
            },
        },
    },
    {
        "type": "function",
        "function": {
            "name": "recommend_products",
            "description": "按风险偏好推荐理财产品。risk_level: 低风险/中风险/高风险。",
            "parameters": {
                "type": "object",
                "properties": {
                    "risk_level": {"type": "string"},
                },
                "required": ["risk_level"],
            },
        },
    },
    {
        "type": "function",
        "function": {
            "name": "buy_product",
            "description": "申购理财产品（L3，需确认+交易密码）。确认后若返回need_password，索要交易密码填入pay_password。",
            "parameters": {
                "type": "object",
                "properties": {
                    "product_name": {"type": "string"},
                    "amount": {"type": "number"},
                    "confirmed": {"type": "boolean"},
                    "pay_password": {"type": "string"},
                },
                "required": ["product_name", "amount"],
            },
        },
    },
    {
        "type": "function",
        "function": {
            "name": "list_holdings",
            "description": "查询当前持有的理财产品。",
            "parameters": {"type": "object", "properties": {}},
        },
    },
    {
        "type": "function",
        "function": {
            "name": "redeem_product",
            "description": "赎回理财产品（L3，需确认+交易密码）。确认后若返回need_password，索要交易密码填入pay_password。",
            "parameters": {
                "type": "object",
                "properties": {
                    "product_name": {"type": "string"},
                    "confirmed": {"type": "boolean"},
                    "pay_password": {"type": "string"},
                },
                "required": ["product_name"],
            },
        },
    },
    {
        "type": "function",
        "function": {
            "name": "send_lost_sms",
            "description": "发起卡片挂失，发送短信验证码到预留手机。",
            "parameters": {
                "type": "object",
                "properties": {
                    "card_last4": {"type": "string", "description": "卡片尾号4位"},
                },
                "required": ["card_last4"],
            },
        },
    },
    {
        "type": "function",
        "function": {
            "name": "report_lost",
            "description": "执行卡片挂失，需填入用户提供的短信验证码（演示码654321）。",
            "parameters": {
                "type": "object",
                "properties": {
                    "card_last4": {"type": "string"},
                    "sms_code": {"type": "string"},
                },
                "required": ["card_last4", "sms_code"],
            },
        },
    },
    {
        "type": "function",
        "function": {
            "name": "split_bill",
            "description": "AA 拆分账单。",
            "parameters": {
                "type": "object",
                "properties": {
                    "total_amount": {"type": "number"},
                    "num_people": {"type": "integer"},
                },
                "required": ["total_amount", "num_people"],
            },
        },
    },
    {
        "type": "function",
        "function": {
            "name": "schedule_transfer",
            "description": "设定定时/预约转账。",
            "parameters": {
                "type": "object",
                "properties": {
                    "to_name": {"type": "string"},
                    "to_phone": {"type": "string"},
                    "amount": {"type": "number"},
                    "schedule_date": {"type": "string", "description": "日期如 2026-11-05"},
                },
                "required": ["to_name", "to_phone", "amount", "schedule_date"],
            },
        },
    },
    {
        "type": "function",
        "function": {
            "name": "list_scheduled",
            "description": "查询所有定时转账。",
            "parameters": {"type": "object", "properties": {}},
        },
    },
    {
        "type": "function",
        "function": {
            "name": "risk_quiz",
            "description": "风险测评，根据分数(0-100)返回风险偏好等级。",
            "parameters": {
                "type": "object",
                "properties": {
                    "score": {"type": "integer"},
                },
                "required": ["score"],
            },
        },
    },
    {
        "type": "function",
        "function": {
            "name": "set_night_lock",
            "description": "开关夜间锁卡（23:00-07:00限制刷卡）。",
            "parameters": {
                "type": "object",
                "properties": {
                    "enable": {"type": "boolean"},
                },
                "required": ["enable"],
            },
        },
    },
    {
        "type": "function",
        "function": {
            "name": "transfer_to_human",
            "description": "转接人工坐席。",
            "parameters": {
                "type": "object",
                "properties": {
                    "reason": {"type": "string"},
                },
            },
        },
    },
    {
        "type": "function",
        "function": {
            "name": "cancel_last_transfer",
            "description": "撤销最近一笔成功转账。",
            "parameters": {"type": "object", "properties": {}},
        },
    },
]
