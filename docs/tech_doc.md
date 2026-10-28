# 技术文档 — 小银 · Guardian Agent

## 1. 概述
基于大语言模型 Function Calling 的 AI 银行智能体。用户自然语言对话完成余额查询、转账、账单分析、理财、挂失等18项业务，系统自动识别风险并拦截。

## 2. 技术栈
- LLM: DeepSeek-Chat (deepseek-chat)，OpenAI SDK兼容
- 前端: Gradio 6.x，中英双语，实时仪表盘
- 数据: SQLite 单文件数据库
- 安全: L0-L4五级风控 + SHA-256哈希链审计
- 配置: python-dotenv

## 3. 架构
用户对话 → Gradio UI → BankingAgent → DeepSeek API → tool_calls → dispatch_tool → 18个银行工具 → SQLite → 审计日志

## 4. 模块
- core/agent.py: 主循环，17条系统规则，审计哈希链
- core/bank_api.py: 18个工具函数，单日限额，重复交易检测
- core/guardrail.py: L0-L4风险分级
- core/tools.py: Function Calling Schema
- app.py: Gradio界面，深蓝hero+6格仪表盘
- data/init_db.py: 模拟数据

## 5. 部署
pip install -r requirements.txt
cp .env.example .env  # 填入DEEPSEEK_API_KEY
python data/init_db.py
python app.py
