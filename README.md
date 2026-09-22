# Brazil Commerce OS — AI Agent MVP

这是一个真正可运行的 Project 6 MVP，不只是静态 HTML。

## 它做什么

一个主 Agent / Orchestrator，下面挂四个工具：

1. **Market & Product Intelligence**
   - 输入 Country / Product / Objective
   - 可调用 Serper Search API
   - 强制 Source Policy
   - 输出 research plan / evidence / findings / next actions

2. **E-commerce Operations**
   - 读取 approved product facts
   - 生成 Brazil Portuguese listing draft
   - 检查 SKU / price / inventory / cost / platform 字段
   - 不允许 AI 猜认证、库存、平台费用

3. **Marketing / Creator / Content**
   - 上传 creator CSV
   - Python 先做 deterministic filter / scoring
   - LLM 再解释 creator fit
   - 生成 creator brief / content brief
   - 不允许凭空创造 creator

4. **Financial & Performance Intelligence**
   - 上传 CSV / XLSX
   - Python 计算 Net Sales / AOV / CTR / Conversion / ROAS / Contribution Profit
   - 缺关键成本 => Profitability = Incomplete
   - LLM 只负责解释和建议，不负责自由计算数字

## 最快运行方式

### 1. 安装 Python 3.11+
建议在 VS Code Terminal：

```bash
python -m venv .venv
.venv\Scripts\activate
pip install -r requirements.txt
```

Mac/Linux:

```bash
python -m venv .venv
source .venv/bin/activate
pip install -r requirements.txt
```

### 2. 复制配置

把 `.env.example` 复制成 `.env`。

如果没有任何 API Key，也可以运行：系统会使用 Demo fallback。

### 3. 启动

```bash
streamlit run app.py
```

浏览器会打开本地页面。

## Live AI

可选环境变量：

- `LLM_API_URL`
- `LLM_API_KEY`
- `LLM_MODEL`

项目使用 OpenAI-compatible `chat/completions` 请求格式。

## Live Search

如果配置：

- `SERPER_API_KEY`

Market Research 会尝试调用 Serper；否则使用 Demo evidence。

## 文件结构

```text
Brazil_Commerce_AI_Agent/
├── app.py
├── agent.py
├── llm.py
├── config.py
├── requirements.txt
├── .env.example
├── skills/
│   ├── MARKET_SKILL.md
│   ├── OPERATIONS_SKILL.md
│   ├── MARKETING_SKILL.md
│   └── FINANCE_SKILL.md
├── tools/
│   ├── market.py
│   ├── operations.py
│   ├── marketing.py
│   └── finance.py
└── data/
    ├── creator_sample.csv
    └── finance_sample.csv
```

## 核心原则

- LLM 负责理解、解释、生成文本。
- 确定性数字 / 财务公式 / 校验由 Python 完成。
- Missing 不当作 0。
- Creator 不由 AI 凭空创造。
- Market 数字必须区分 evidence / estimate / missing。
- 高影响动作保留人工审批。
