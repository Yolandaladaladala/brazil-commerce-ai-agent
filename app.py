from __future__ import annotations

from datetime import datetime
from html import escape
from pathlib import Path

import pandas as pd
import streamlit as st

from agent import route_request
from tools.market import run_market_research
from tools.operations import run_operations
from tools.marketing import load_creator_file, score_creators, explain_creator_fit
from tools.finance import load_finance_file, analyse_finance
from llm import chat
from config import DEMO_MODE, SERPER_API_KEY


# =========================================================
# App setup
# =========================================================
BASE = Path(__file__).resolve().parent

st.set_page_config(
    page_title="Brazil Commerce OS",
    page_icon="🇧🇷",
    layout="wide",
    initial_sidebar_state="expanded",
)


# =========================================================
# Internationalisation (UI + AI output instruction)
# =========================================================
LANG_OPTIONS = {
    "简体中文": "zh",
    "English": "en",
    "Português (Brasil)": "pt-BR",
}

I18N = {
    "zh": {
        "app_name": "Brazil Commerce OS",
        "tagline": "巴西跨境电商智能运营平台",
        "mvp": "AI Commerce Agent · Working Prototype",
        "language": "语言 / Language",
        "workspace": "工作区",
        "nav_command": "指挥中心",
        "nav_market": "01 市场情报",
        "nav_ops": "02 电商运营",
        "nav_marketing": "03 营销 / 创作者",
        "nav_finance": "04 财务与绩效",
        "nav_audit": "审计追踪",
        "ai_status": "AI 状态",
        "ai_live": "LLM 已连接",
        "ai_demo": "Demo 模式",
        "search_live": "实时搜索已连接",
        "search_offline": "实时搜索未连接",
        "home_title": "从一个商业目标开始",
        "home_subtitle": "Agent 会先判断任务类型，再进入对应工作流。四个模块可独立使用，也可通过稳定 ID 和数据结构连接。",
        "goal_label": "你想完成什么？ *",
        "goal_ph": "例如：我想把猫爬架卖到巴西，先帮我判断市场机会和需要验证的风险。",
        "route": "分析任务",
        "route_to": "建议工作流",
        "open_module": "打开对应模块",
        "copilot": "AI Copilot",
        "copilot_sub": "适合问概念、流程、指标和下一步怎么做。",
        "copilot_label": "输入问题",
        "copilot_ph": "例如：ROAS 和利润有什么区别？",
        "ask": "Ask Copilot",
        "required": "请完成所有必填项。",
        "empty_goal": "请先输入一个目标。",
        "empty_question": "请输入一个问题。",
        "market_card_title": "市场与产品情报",
        "market_card_desc": "实时检索公开证据，分析市场、竞争、价格、渠道、消费者需求与监管。",
        "ops_card_title": "电商规划与运营",
        "ops_card_desc": "基于已批准的商品事实生成本地化 listing 和 launch checklist，不猜关键商业事实。",
        "marketing_card_title": "营销 / Creator / 内容",
        "marketing_card_desc": "读取真实 Creator 数据，规则评分 + AI 解释，并形成 campaign 与内容执行建议。",
        "finance_card_title": "财务与绩效情报",
        "finance_card_desc": "Python 做确定性计算；AI 负责解释利润、漏斗和下一步动作。",
        "market_title": "01 Market & Product Intelligence",
        "market_sub": "先定义研究问题，再检索 evidence；没有证据就明确标记不足，不让 LLM 编数字。",
        "rules": "方法与规则",
        "country": "Country / Market *",
        "product": "Product / Category *",
        "product_ph": "例如：猫爬架 / 家用咖啡机",
        "platform_optional": "Platform（选填）",
        "price_optional": "Expected Price Range（选填）",
        "price_ph": "例如：R$120–350",
        "research_objective": "Research Objective *",
        "research_objective_ph": "例如：判断该类目是否值得进入巴西，并了解市场需求、主要竞争、价格带、渠道和监管风险。",
        "research_dims": "Research Dimensions *",
        "run_market": "Run Market Research",
        "researching": "正在规划检索 → 获取 evidence → 生成研究备忘录…",
        "research_memo": "Research Memo",
        "evidence_register": "Evidence Register",
        "evidence_count": "证据条数",
        "download_memo": "下载研究备忘录 (.md)",
        "mode_live": "LIVE SEARCH",
        "mode_demo": "DEMO SEARCH",
        "ops_title": "02 E-commerce Planning & Operations",
        "ops_sub": "把市场机会转成可上架、可追踪的商品运营包；Listing 可以生成，事实不能猜。",
        "merchant_id": "Merchant ID *",
        "product_id": "Product ID *",
        "sku": "SKU *",
        "product_name": "Product Name *",
        "product_name_ph": "例如：折叠式猫爬架",
        "platform": "Platform *",
        "approved_facts": "Approved Product Facts *",
        "approved_facts_ph": "只填写已确认的产品事实，例如材料、尺寸、功能、包装、已核实认证等。",
        "selling_price": "Selling Price（选填）",
        "inventory": "Inventory（选填）",
        "unit_cost": "Unit Cost（选填）",
        "generate_launch": "Generate Launch Pack",
        "generating_launch": "正在生成本地化 Listing + Launch Control Pack…",
        "missing": "缺失字段",
        "launch_pack": "Launch Pack",
        "ops_language_note": "面向巴西消费者的 Listing 默认以巴西葡萄牙语生成，这是当前 Operations 工具的业务设定。",
        "download_launch": "下载 Launch Pack (.md)",
        "marketing_title": "03 Marketing / Creator / Content",
        "marketing_sub": "真实 Creator 数据 → Python 规则评分 → AI 解释 fit。没有真实数据，不编造达人。",
        "campaign_id": "Campaign ID *",
        "product_sku": "Product / SKU *",
        "campaign_objective": "Campaign Objective *",
        "category": "Category *",
        "category_ph": "例如：Pet / Beauty",
        "creator_budget": "Creator Budget BRL（选填）",
        "brand_brief": "Approved Product / Brand Brief *",
        "brand_brief_ph": "填写已确认的品牌与商品要求、禁用 claims、内容方向等。",
        "upload_creator": "上传 Creator CSV / XLSX *",
        "creator_empty": "请上传真实 Creator 数据后再做 shortlist。第一版支持 CSV / Excel。",
        "rows_loaded": "已载入 Creator 行数",
        "build_shortlist": "Build Creator Shortlist",
        "shortlist": "Deterministic Shortlist",
        "fit_analysis": "AI Fit Analysis",
        "analysing_fit": "AI 正在解释 Creator fit…",
        "download_creator_template": "下载 Creator CSV 模板",
        "download_creator_analysis": "下载 Creator Analysis (.md)",
        "finance_title": "04 Financial & Performance Intelligence",
        "finance_sub": "先检查数据，再计算，再解释。没有真实数据，不生成假的 Profitability。",
        "upload_finance": "上传 Finance CSV / XLSX / JSON *",
        "finance_empty": "Profitability = Incomplete。请先上传经营数据。",
        "run_finance": "Run Financial Analysis",
        "net_sales": "Net Sales",
        "aov": "AOV",
        "roas": "ROAS",
        "contribution_profit": "Contribution Profit",
        "contribution_margin": "Contribution Margin",
        "incomplete": "Incomplete",
        "field_mapping": "Field Mapping",
        "ai_advisor": "AI Advisor",
        "analysing_finance": "正在计算并生成管理层解释…",
        "download_finance_template": "下载 Finance CSV 模板",
        "download_finance_analysis": "下载 Finance Analysis (.md)",
        "audit_title": "Audit Trail",
        "audit_sub": "当前浏览器会话中的运行记录。用于演示与调试，不等同于生产级持久化日志。",
        "no_history": "还没有运行记录。",
        "clear_history": "清空本次会话记录",
        "history_cleared": "已清空。",
        "source_priority": "Source priority：政府/监管 > 行业协会 > 公司披露 > 专业研究机构 > 可靠行业媒体 > Marketplace/Search evidence。",
        "market_rule_1": "关键数字必须有来源；缺少可靠证据时标记 insufficient evidence。",
        "market_rule_2": "公开 Web Search 适合 high-level intelligence；精准平台商业数据仍需 FastMoss / 平台 / 商家数据。",
        "ops_rule_1": "Product / SKU / Order 使用稳定 ID，方便后续 Marketing 与 Finance 关联。",
        "ops_rule_2": "价格、库存、认证、平台费、退款政策等不能由 LLM 猜。",
        "marketing_rule_1": "Creator 身份必须来自真实来源；Fit score 是内部规则评分，不是平台官方排名。",
        "marketing_rule_2": "建联、合同、发布、付款等高影响动作保留人工审批。",
        "finance_rule_1": "财务数字由 Python 计算；LLM 只解释，不自由重算。",
        "finance_rule_2": "关键成本缺失时 Profitability 必须保持 Incomplete，Missing ≠ 0。",
    },
    "en": {
        "app_name": "Brazil Commerce OS",
        "tagline": "AI operating system for cross-border commerce in Brazil",
        "mvp": "AI Commerce Agent · Working Prototype",
        "language": "Language",
        "workspace": "Workspace",
        "nav_command": "Command Center",
        "nav_market": "01 Market Intelligence",
        "nav_ops": "02 E-commerce Operations",
        "nav_marketing": "03 Marketing / Creator",
        "nav_finance": "04 Finance & Performance",
        "nav_audit": "Audit Trail",
        "ai_status": "System status",
        "ai_live": "LLM connected",
        "ai_demo": "Demo mode",
        "search_live": "Live search connected",
        "search_offline": "Live search offline",
        "home_title": "Start with a business objective",
        "home_subtitle": "The agent routes each task into the right workflow. Modules can run independently and connect through stable IDs and shared data structures.",
        "goal_label": "What do you want to achieve? *",
        "goal_ph": "Example: I want to sell cat trees in Brazil. Help me assess the opportunity and key risks first.",
        "route": "Analyse request",
        "route_to": "Recommended workflow",
        "open_module": "Open module",
        "copilot": "AI Copilot",
        "copilot_sub": "Use this for concepts, metrics, workflows and next-step questions.",
        "copilot_label": "Ask a question",
        "copilot_ph": "Example: What is the difference between ROAS and profit?",
        "ask": "Ask Copilot",
        "required": "Please complete all required fields.",
        "empty_goal": "Please enter a business objective first.",
        "empty_question": "Please enter a question.",
        "market_card_title": "Market & Product Intelligence",
        "market_card_desc": "Retrieve live public evidence and analyse market demand, competition, pricing, channels, consumers and regulation.",
        "ops_card_title": "E-commerce Planning & Operations",
        "ops_card_desc": "Generate localised listings and launch controls from approved product facts without inventing commercial facts.",
        "marketing_card_title": "Marketing / Creator / Content",
        "marketing_card_desc": "Use real creator data for deterministic scoring, AI fit explanations and campaign/content planning.",
        "finance_card_title": "Financial & Performance Intelligence",
        "finance_card_desc": "Python handles deterministic calculations; AI explains profit drivers, funnel performance and next actions.",
        "market_title": "01 Market & Product Intelligence",
        "market_sub": "Define the research question first, then retrieve evidence. If evidence is weak, the system says so instead of inventing numbers.",
        "rules": "Method & rules",
        "country": "Country / Market *",
        "product": "Product / Category *",
        "product_ph": "Example: cat tree / home espresso maker",
        "platform_optional": "Platform (optional)",
        "price_optional": "Expected Price Range (optional)",
        "price_ph": "Example: R$120–350",
        "research_objective": "Research Objective *",
        "research_objective_ph": "Example: assess whether this category is worth entering in Brazil and understand demand, competition, pricing, channels and regulatory risks.",
        "research_dims": "Research Dimensions *",
        "run_market": "Run Market Research",
        "researching": "Planning queries → retrieving evidence → generating research memo…",
        "research_memo": "Research Memo",
        "evidence_register": "Evidence Register",
        "evidence_count": "Evidence items",
        "download_memo": "Download research memo (.md)",
        "mode_live": "LIVE SEARCH",
        "mode_demo": "DEMO SEARCH",
        "ops_title": "02 E-commerce Planning & Operations",
        "ops_sub": "Turn an opportunity into a launch-ready commerce package. Listings can be generated; business facts cannot be guessed.",
        "merchant_id": "Merchant ID *",
        "product_id": "Product ID *",
        "sku": "SKU *",
        "product_name": "Product Name *",
        "product_name_ph": "Example: foldable cat tree",
        "platform": "Platform *",
        "approved_facts": "Approved Product Facts *",
        "approved_facts_ph": "Only confirmed facts such as material, dimensions, functions, packaging and verified certifications.",
        "selling_price": "Selling Price (optional)",
        "inventory": "Inventory (optional)",
        "unit_cost": "Unit Cost (optional)",
        "generate_launch": "Generate Launch Pack",
        "generating_launch": "Generating localised listing + launch control pack…",
        "missing": "Missing fields",
        "launch_pack": "Launch Pack",
        "ops_language_note": "Consumer-facing Brazil listings are generated in Brazilian Portuguese by design in the current Operations tool.",
        "download_launch": "Download Launch Pack (.md)",
        "marketing_title": "03 Marketing / Creator / Content",
        "marketing_sub": "Real creator data → deterministic scoring → AI fit explanation. No real data means no invented creators.",
        "campaign_id": "Campaign ID *",
        "product_sku": "Product / SKU *",
        "campaign_objective": "Campaign Objective *",
        "category": "Category *",
        "category_ph": "Example: Pet / Beauty",
        "creator_budget": "Creator Budget BRL (optional)",
        "brand_brief": "Approved Product / Brand Brief *",
        "brand_brief_ph": "Confirmed product/brand requirements, prohibited claims, content direction and constraints.",
        "upload_creator": "Upload Creator CSV / XLSX *",
        "creator_empty": "Upload real creator data before building a shortlist. CSV and Excel are supported.",
        "rows_loaded": "Creator rows loaded",
        "build_shortlist": "Build Creator Shortlist",
        "shortlist": "Deterministic Shortlist",
        "fit_analysis": "AI Fit Analysis",
        "analysing_fit": "AI is explaining creator fit…",
        "download_creator_template": "Download Creator CSV template",
        "download_creator_analysis": "Download Creator Analysis (.md)",
        "finance_title": "04 Financial & Performance Intelligence",
        "finance_sub": "Validate data first, calculate second, explain third. No real file means no fake profitability.",
        "upload_finance": "Upload Finance CSV / XLSX / JSON *",
        "finance_empty": "Profitability = Incomplete. Upload operating data first.",
        "run_finance": "Run Financial Analysis",
        "net_sales": "Net Sales",
        "aov": "AOV",
        "roas": "ROAS",
        "contribution_profit": "Contribution Profit",
        "contribution_margin": "Contribution Margin",
        "incomplete": "Incomplete",
        "field_mapping": "Field Mapping",
        "ai_advisor": "AI Advisor",
        "analysing_finance": "Calculating results and generating management commentary…",
        "download_finance_template": "Download Finance CSV template",
        "download_finance_analysis": "Download Finance Analysis (.md)",
        "audit_title": "Audit Trail",
        "audit_sub": "Run history for the current browser session. This is a prototype audit view, not production-grade persistent logging.",
        "no_history": "No runs recorded yet.",
        "clear_history": "Clear session history",
        "history_cleared": "History cleared.",
        "source_priority": "Source priority: government/regulator > industry association > company disclosure > professional research > reliable industry media > marketplace/search evidence.",
        "market_rule_1": "Important quantitative claims require evidence; weak evidence must be labelled insufficient.",
        "market_rule_2": "Web search supports high-level intelligence; precise commercial data still requires FastMoss, platform or merchant data.",
        "ops_rule_1": "Product / SKU / Order use stable IDs so Marketing and Finance can join later.",
        "ops_rule_2": "Price, inventory, certification, platform fees and refund policies must not be invented by the LLM.",
        "marketing_rule_1": "Creator identities must come from real sources. Fit score is an internal rule score, not a platform ranking.",
        "marketing_rule_2": "Outreach, contracts, publishing and payments remain human-approved in the MVP.",
        "finance_rule_1": "Financial values are calculated by Python. The LLM explains but does not freely recalculate.",
        "finance_rule_2": "If critical costs are missing, Profitability remains Incomplete. Missing ≠ 0.",
    },
    "pt-BR": {
        "app_name": "Brazil Commerce OS",
        "tagline": "Plataforma inteligente para operações de comércio no Brasil",
        "mvp": "AI Commerce Agent · Protótipo Funcional",
        "language": "Idioma",
        "workspace": "Área de trabalho",
        "nav_command": "Central de Comando",
        "nav_market": "01 Inteligência de Mercado",
        "nav_ops": "02 Operações de E-commerce",
        "nav_marketing": "03 Marketing / Criadores",
        "nav_finance": "04 Finanças e Desempenho",
        "nav_audit": "Trilha de Auditoria",
        "ai_status": "Status do sistema",
        "ai_live": "LLM conectado",
        "ai_demo": "Modo demo",
        "search_live": "Busca em tempo real conectada",
        "search_offline": "Busca em tempo real offline",
        "home_title": "Comece com um objetivo de negócio",
        "home_subtitle": "O agente direciona cada tarefa para o fluxo adequado. Os módulos funcionam de forma independente e podem ser conectados por IDs estáveis e estruturas de dados comuns.",
        "goal_label": "O que você quer alcançar? *",
        "goal_ph": "Exemplo: quero vender arranhadores para gatos no Brasil. Primeiro avalie a oportunidade e os principais riscos.",
        "route": "Analisar solicitação",
        "route_to": "Fluxo recomendado",
        "open_module": "Abrir módulo",
        "copilot": "AI Copilot",
        "copilot_sub": "Use para dúvidas sobre conceitos, métricas, fluxos e próximos passos.",
        "copilot_label": "Faça uma pergunta",
        "copilot_ph": "Exemplo: qual é a diferença entre ROAS e lucro?",
        "ask": "Perguntar ao Copilot",
        "required": "Preencha todos os campos obrigatórios.",
        "empty_goal": "Digite primeiro um objetivo de negócio.",
        "empty_question": "Digite uma pergunta.",
        "market_card_title": "Inteligência de Mercado e Produto",
        "market_card_desc": "Busca evidências públicas em tempo real e analisa demanda, concorrência, preços, canais, consumidores e regulamentação.",
        "ops_card_title": "Planejamento e Operações de E-commerce",
        "ops_card_desc": "Gera listings localizados e controles de lançamento a partir de fatos aprovados, sem inventar dados comerciais.",
        "marketing_card_title": "Marketing / Criadores / Conteúdo",
        "marketing_card_desc": "Usa dados reais de criadores para scoring determinístico, análise de fit e planejamento de campanhas e conteúdo.",
        "finance_card_title": "Inteligência Financeira e de Desempenho",
        "finance_card_desc": "Python faz os cálculos determinísticos; a IA explica drivers de lucro, funil e próximos passos.",
        "market_title": "01 Inteligência de Mercado e Produto",
        "market_sub": "Primeiro define a pergunta de pesquisa, depois busca evidências. Se a evidência for fraca, o sistema sinaliza isso em vez de inventar números.",
        "rules": "Método e regras",
        "country": "País / Mercado *",
        "product": "Produto / Categoria *",
        "product_ph": "Exemplo: arranhador para gatos / cafeteira espresso",
        "platform_optional": "Plataforma (opcional)",
        "price_optional": "Faixa de preço esperada (opcional)",
        "price_ph": "Exemplo: R$120–350",
        "research_objective": "Objetivo da Pesquisa *",
        "research_objective_ph": "Exemplo: avaliar se vale a pena entrar nesta categoria no Brasil e entender demanda, concorrência, preços, canais e riscos regulatórios.",
        "research_dims": "Dimensões da Pesquisa *",
        "run_market": "Executar Pesquisa de Mercado",
        "researching": "Planejando buscas → coletando evidências → gerando relatório…",
        "research_memo": "Memorando de Pesquisa",
        "evidence_register": "Registro de Evidências",
        "evidence_count": "Itens de evidência",
        "download_memo": "Baixar memorando (.md)",
        "mode_live": "BUSCA AO VIVO",
        "mode_demo": "BUSCA DEMO",
        "ops_title": "02 Planejamento e Operações de E-commerce",
        "ops_sub": "Transforme uma oportunidade em um pacote pronto para lançamento. O listing pode ser gerado; fatos comerciais não podem ser adivinhados.",
        "merchant_id": "Merchant ID *",
        "product_id": "Product ID *",
        "sku": "SKU *",
        "product_name": "Nome do Produto *",
        "product_name_ph": "Exemplo: arranhador dobrável para gatos",
        "platform": "Plataforma *",
        "approved_facts": "Fatos Aprovados do Produto *",
        "approved_facts_ph": "Somente fatos confirmados: material, dimensões, funções, embalagem e certificações verificadas.",
        "selling_price": "Preço de Venda (opcional)",
        "inventory": "Estoque (opcional)",
        "unit_cost": "Custo Unitário (opcional)",
        "generate_launch": "Gerar Pacote de Lançamento",
        "generating_launch": "Gerando listing localizado + pacote de controle de lançamento…",
        "missing": "Campos ausentes",
        "launch_pack": "Pacote de Lançamento",
        "ops_language_note": "Os listings voltados ao consumidor brasileiro são gerados em português do Brasil por padrão no módulo atual de Operações.",
        "download_launch": "Baixar pacote de lançamento (.md)",
        "marketing_title": "03 Marketing / Criadores / Conteúdo",
        "marketing_sub": "Dados reais de criadores → scoring determinístico → explicação de fit por IA. Sem dados reais, sem criadores inventados.",
        "campaign_id": "Campaign ID *",
        "product_sku": "Produto / SKU *",
        "campaign_objective": "Objetivo da Campanha *",
        "category": "Categoria *",
        "category_ph": "Exemplo: Pet / Beauty",
        "creator_budget": "Orçamento para Criadores em BRL (opcional)",
        "brand_brief": "Brief Aprovado de Produto / Marca *",
        "brand_brief_ph": "Requisitos confirmados, claims proibidos, direção de conteúdo e restrições.",
        "upload_creator": "Enviar Creator CSV / XLSX *",
        "creator_empty": "Envie dados reais de criadores antes de criar a shortlist. CSV e Excel são suportados.",
        "rows_loaded": "Linhas de criadores carregadas",
        "build_shortlist": "Criar Shortlist de Criadores",
        "shortlist": "Shortlist Determinística",
        "fit_analysis": "Análise de Fit por IA",
        "analysing_fit": "A IA está explicando o fit dos criadores…",
        "download_creator_template": "Baixar modelo CSV de Criadores",
        "download_creator_analysis": "Baixar análise de criadores (.md)",
        "finance_title": "04 Inteligência Financeira e de Desempenho",
        "finance_sub": "Valide os dados, calcule e só depois explique. Sem arquivo real, não existe lucratividade falsa.",
        "upload_finance": "Enviar Finance CSV / XLSX / JSON *",
        "finance_empty": "Profitability = Incomplete. Envie primeiro os dados operacionais.",
        "run_finance": "Executar Análise Financeira",
        "net_sales": "Vendas Líquidas",
        "aov": "AOV",
        "roas": "ROAS",
        "contribution_profit": "Lucro de Contribuição",
        "contribution_margin": "Margem de Contribuição",
        "incomplete": "Incompleto",
        "field_mapping": "Mapeamento de Campos",
        "ai_advisor": "AI Advisor",
        "analysing_finance": "Calculando resultados e gerando comentário gerencial…",
        "download_finance_template": "Baixar modelo CSV Financeiro",
        "download_finance_analysis": "Baixar análise financeira (.md)",
        "audit_title": "Trilha de Auditoria",
        "audit_sub": "Histórico de execução da sessão atual do navegador. É uma visão de protótipo, não um log persistente de produção.",
        "no_history": "Nenhuma execução registrada ainda.",
        "clear_history": "Limpar histórico da sessão",
        "history_cleared": "Histórico limpo.",
        "source_priority": "Prioridade de fontes: governo/regulador > associação setorial > divulgação de empresas > pesquisa profissional > mídia setorial confiável > evidência de marketplace/busca.",
        "market_rule_1": "Dados quantitativos importantes exigem evidência; evidência fraca deve ser marcada como insuficiente.",
        "market_rule_2": "Web search serve para inteligência de alto nível; dados comerciais precisos ainda exigem FastMoss, plataforma ou dados do lojista.",
        "ops_rule_1": "Product / SKU / Order usam IDs estáveis para conexão posterior com Marketing e Finance.",
        "ops_rule_2": "Preço, estoque, certificação, taxas de plataforma e política de reembolso não podem ser inventados pela IA.",
        "marketing_rule_1": "A identidade dos criadores deve vir de fontes reais. Fit score é um score interno, não ranking oficial da plataforma.",
        "marketing_rule_2": "Contato, contratos, publicação e pagamentos permanecem com aprovação humana no MVP.",
        "finance_rule_1": "Os valores financeiros são calculados em Python. A IA explica, mas não recalcula livremente.",
        "finance_rule_2": "Se custos críticos estiverem ausentes, Profitability permanece Incomplete. Missing ≠ 0.",
    },
}

AI_LANGUAGE_INSTRUCTION = {
    "zh": "Respond in clear Simplified Chinese. Keep standard business/technical English terms where useful.",
    "en": "Respond in concise professional English.",
    "pt-BR": "Respond in natural Brazilian Portuguese (pt-BR), not European Portuguese.",
}

DIMENSIONS = [
    "Market size & growth",
    "Competition",
    "Pricing",
    "Channels",
    "Consumer need",
    "Regulation",
    "TikTok / social commerce signals",
]

DIMENSION_LABELS = {
    "zh": {
        "Market size & growth": "市场规模与增长",
        "Competition": "竞争格局",
        "Pricing": "定价",
        "Channels": "渠道",
        "Consumer need": "消费者需求",
        "Regulation": "监管 / 合规",
        "TikTok / social commerce signals": "TikTok / 社交电商信号",
    },
    "en": {x: x for x in DIMENSIONS},
    "pt-BR": {
        "Market size & growth": "Tamanho e crescimento do mercado",
        "Competition": "Concorrência",
        "Pricing": "Preços",
        "Channels": "Canais",
        "Consumer need": "Necessidades do consumidor",
        "Regulation": "Regulamentação / compliance",
        "TikTok / social commerce signals": "Sinais de TikTok / social commerce",
    },
}

CAMPAIGN_OBJECTIVES = [
    "Sales / Conversion",
    "Brand Awareness",
    "Product Seeding",
    "LIVE Traffic",
]

CAMPAIGN_OBJECTIVE_LABELS = {
    "zh": {
        "Sales / Conversion": "销售 / 转化",
        "Brand Awareness": "品牌认知",
        "Product Seeding": "产品种草",
        "LIVE Traffic": "直播引流",
    },
    "en": {x: x for x in CAMPAIGN_OBJECTIVES},
    "pt-BR": {
        "Sales / Conversion": "Vendas / Conversão",
        "Brand Awareness": "Reconhecimento de Marca",
        "Product Seeding": "Seeding de Produto",
        "LIVE Traffic": "Tráfego para LIVE",
    },
}


# =========================================================
# Styling
# =========================================================
st.markdown(
    """
<style>
:root {
    --bcos-navy: #071A35;
    --bcos-navy-2: #0B2447;
    --bcos-orange: #FF5A4F;
    --bcos-green: #159A6A;
    --bcos-bg: #F6F8FB;
    --bcos-line: #E7EAF0;
    --bcos-text: #1F2937;
    --bcos-muted: #667085;
}

html, body, [class*="css"] {
    font-family: Inter, -apple-system, BlinkMacSystemFont, "Segoe UI", "PingFang SC",
                 "Hiragino Sans GB", "Microsoft YaHei", Arial, sans-serif;
}

.stApp { background: var(--bcos-bg); }
.block-container {
    max-width: 1280px;
    padding-top: 2.0rem;
    padding-bottom: 4rem;
}

[data-testid="stSidebar"] {
    background: linear-gradient(180deg, #071A35 0%, #081F3F 100%);
    border-right: 1px solid rgba(255,255,255,.06);
}
[data-testid="stSidebar"] [data-testid="stMarkdownContainer"] p,
[data-testid="stSidebar"] label,
[data-testid="stSidebar"] span,
[data-testid="stSidebar"] div {
    color: #EAF0F8;
}
[data-testid="stSidebar"] .stSelectbox label,
[data-testid="stSidebar"] .stRadio label {
    color: #EAF0F8 !important;
}

h1, h2, h3 {
    letter-spacing: -0.025em;
    color: #202634;
}
h1 { font-weight: 760 !important; }
h2 { font-weight: 720 !important; }

.bcos-brand {
    padding: 4px 0 14px 0;
}
.bcos-brand-title {
    font-size: 1.2rem;
    font-weight: 760;
    color: white;
    letter-spacing: -.02em;
}
.bcos-brand-sub {
    font-size: .78rem;
    color: #9FB0C8;
    margin-top: 4px;
}

.bcos-hero {
    background: linear-gradient(135deg, #071A35 0%, #0F315D 70%, #174D74 100%);
    border-radius: 24px;
    padding: 34px 36px;
    color: white;
    margin: 4px 0 24px 0;
    box-shadow: 0 18px 48px rgba(7,26,53,.12);
}
.bcos-hero h1 {
    color: white !important;
    margin: 0 0 8px 0;
    font-size: 2.25rem;
}
.bcos-hero p {
    color: #D8E3F1;
    font-size: 1rem;
    max-width: 850px;
    margin: 0;
    line-height: 1.65;
}

.bcos-kicker {
    display: inline-block;
    font-size: .74rem;
    font-weight: 700;
    letter-spacing: .07em;
    text-transform: uppercase;
    color: #FFB1A8;
    margin-bottom: 10px;
}

.bcos-grid {
    display: grid;
    grid-template-columns: repeat(2, minmax(0, 1fr));
    gap: 16px;
    margin: 18px 0 30px 0;
}
.bcos-card {
    background: #FFFFFF;
    border: 1px solid var(--bcos-line);
    border-radius: 18px;
    padding: 22px 22px 20px 22px;
    min-height: 160px;
    box-shadow: 0 5px 18px rgba(16,24,40,.035);
}
.bcos-card-number {
    color: #FF5A4F;
    font-size: .76rem;
    font-weight: 750;
    letter-spacing: .08em;
    margin-bottom: 10px;
}
.bcos-card-title {
    color: #1F2937;
    font-size: 1.12rem;
    font-weight: 730;
    line-height: 1.3;
    margin-bottom: 8px;
}
.bcos-card-desc {
    color: #667085;
    font-size: .9rem;
    line-height: 1.62;
}

.bcos-panel {
    background: #FFFFFF;
    border: 1px solid var(--bcos-line);
    border-radius: 18px;
    padding: 22px;
    margin: 10px 0 18px 0;
}

.bcos-status-row {
    display: flex;
    gap: 8px;
    flex-wrap: wrap;
    margin-top: 10px;
}
.bcos-chip {
    display: inline-flex;
    align-items: center;
    gap: 7px;
    border-radius: 999px;
    padding: 7px 10px;
    font-size: .76rem;
    font-weight: 650;
    border: 1px solid rgba(255,255,255,.12);
    background: rgba(255,255,255,.06);
    color: #DDE7F3;
}
.bcos-dot-green {
    width: 7px;
    height: 7px;
    border-radius: 50%;
    background: #42D59C;
}
.bcos-dot-amber {
    width: 7px;
    height: 7px;
    border-radius: 50%;
    background: #F5B942;
}

.bcos-section-title {
    font-size: 1.55rem;
    font-weight: 760;
    color: #202634;
    margin: 6px 0 4px 0;
    letter-spacing: -.025em;
}
.bcos-section-sub {
    color: #667085;
    font-size: .94rem;
    margin-bottom: 20px;
    line-height: 1.6;
}
.bcos-eyebrow {
    color: #FF5A4F;
    font-size: .76rem;
    font-weight: 760;
    letter-spacing: .08em;
    text-transform: uppercase;
    margin-bottom: 7px;
}

.bcos-empty {
    border: 1px dashed #C8CFDB;
    background: #FAFBFC;
    border-radius: 16px;
    padding: 22px;
    color: #667085;
    margin: 8px 0 16px 0;
}
.bcos-result-head {
    display: flex;
    align-items: center;
    justify-content: space-between;
    gap: 12px;
    margin: 26px 0 8px 0;
}
.bcos-badge-live {
    display: inline-block;
    padding: 6px 10px;
    border-radius: 999px;
    background: #E9F8F1;
    color: #067647;
    font-size: .75rem;
    font-weight: 720;
}
.bcos-badge-demo {
    display: inline-block;
    padding: 6px 10px;
    border-radius: 999px;
    background: #FFF4E5;
    color: #B54708;
    font-size: .75rem;
    font-weight: 720;
}

div[data-testid="stButton"] > button[kind="primary"] {
    background: #FF5A4F;
    border: 1px solid #FF5A4F;
    color: white;
    border-radius: 10px;
    font-weight: 680;
    min-height: 42px;
    box-shadow: none;
}
div[data-testid="stButton"] > button[kind="primary"]:hover {
    background: #E94C42;
    border-color: #E94C42;
}

div[data-testid="stButton"] > button:not([kind="primary"]) {
    border-radius: 10px;
}

[data-testid="stTextInputRootElement"],
[data-testid="stTextArea"] textarea,
[data-baseweb="select"] > div {
    border-radius: 11px !important;
}

[data-testid="stMetric"] {
    background: white;
    border: 1px solid var(--bcos-line);
    padding: 16px 18px;
    border-radius: 14px;
}

hr { border-color: rgba(255,255,255,.08) !important; }

@media (max-width: 900px) {
    .bcos-grid { grid-template-columns: 1fr; }
    .bcos-hero { padding: 26px 24px; }
    .bcos-hero h1 { font-size: 1.8rem; }
}
</style>
""",
    unsafe_allow_html=True,
)


# =========================================================
# Session state
# =========================================================
DEFAULTS = {
    "history": [],
    "ui_language": "简体中文",
    "workspace": "command",
    "market_result": None,
    "ops_result": None,
    "marketing_result": None,
    "finance_result": None,
}
for key, value in DEFAULTS.items():
    if key not in st.session_state:
        st.session_state[key] = value

lang_code = LANG_OPTIONS.get(st.session_state.ui_language, "zh")
t = I18N[lang_code]


def ai_lang_instruction() -> str:
    return AI_LANGUAGE_INSTRUCTION[lang_code]


def go_to_module(target: str) -> None:
    st.session_state.workspace = target


def save_history(module: str, title: str, detail: str) -> None:
    st.session_state.history.insert(
        0,
        {
            "time": datetime.now().strftime("%Y-%m-%d %H:%M:%S"),
            "module": module,
            "title": title,
            "detail": detail,
        },
    )
    st.session_state.history = st.session_state.history[:100]


def section_header(eyebrow: str, title: str, subtitle: str) -> None:
    st.markdown(
        f"""
        <div class="bcos-eyebrow">{escape(eyebrow)}</div>
        <div class="bcos-section-title">{escape(title)}</div>
        <div class="bcos-section-sub">{escape(subtitle)}</div>
        """,
        unsafe_allow_html=True,
    )


def empty_state(message: str) -> None:
    st.markdown(f'<div class="bcos-empty">{escape(message)}</div>', unsafe_allow_html=True)


def module_cards() -> None:
    cards = [
        ("01", t["market_card_title"], t["market_card_desc"]),
        ("02", t["ops_card_title"], t["ops_card_desc"]),
        ("03", t["marketing_card_title"], t["marketing_card_desc"]),
        ("04", t["finance_card_title"], t["finance_card_desc"]),
    ]
    html = '<div class="bcos-grid">'
    for num, title, desc in cards:
        html += f"""
        <div class="bcos-card">
            <div class="bcos-card-number">MODULE {num}</div>
            <div class="bcos-card-title">{escape(title)}</div>
            <div class="bcos-card-desc">{escape(desc)}</div>
        </div>
        """
    html += "</div>"
    st.markdown(html, unsafe_allow_html=True)


def download_markdown(label: str, content: str, filename: str, key: str) -> None:
    st.download_button(
        label,
        data=content.encode("utf-8"),
        file_name=filename,
        mime="text/markdown",
        key=key,
    )


def safe_template_bytes(path: Path) -> bytes | None:
    try:
        return path.read_bytes()
    except Exception:
        return None


def localized_route_copy(module_name: str) -> str:
    copy = {
        "zh": {
            "market": "先进入市场情报：明确目标市场、产品/类目和研究目标，再调用实时搜索获取 evidence。",
            "operations": "先进入电商运营：准备已确认的商品事实、SKU/产品 ID 和目标平台，再生成本地化 listing 与 launch pack。",
            "marketing": "先进入营销 / Creator：需要真实 Creator 或 campaign 数据，系统先做规则评分，再由 AI 解释 fit 与内容方向。",
            "finance": "先进入财务与绩效：上传订单、销售和成本数据，Python 先计算，AI 再解释利润与绩效驱动因素。",
        },
        "en": {
            "market": "Start with Market Intelligence: define the target market, product/category and decision objective, then retrieve live evidence.",
            "operations": "Start with E-commerce Operations: provide approved product facts, stable product/SKU IDs and the target platform before generating the listing and launch pack.",
            "marketing": "Start with Marketing / Creator: use real creator or campaign data, apply deterministic scoring first, then let AI explain fit and content direction.",
            "finance": "Start with Finance & Performance: upload sales/order/cost data, let Python calculate first, then use AI to explain profit and performance drivers.",
        },
        "pt-BR": {
            "market": "Comece por Inteligência de Mercado: defina mercado-alvo, produto/categoria e objetivo da decisão; depois busque evidências em tempo real.",
            "operations": "Comece por Operações: informe fatos aprovados do produto, IDs estáveis de produto/SKU e plataforma-alvo antes de gerar listing e pacote de lançamento.",
            "marketing": "Comece por Marketing / Criadores: use dados reais de criadores ou campanhas, aplique scoring determinístico e depois use a IA para explicar fit e direção de conteúdo.",
            "finance": "Comece por Finanças e Desempenho: envie dados de vendas, pedidos e custos; Python calcula primeiro e a IA explica os drivers de lucro e desempenho.",
        },
    }
    return copy[lang_code].get(module_name, copy[lang_code]["market"])


# =========================================================
# Sidebar
# =========================================================
NAV_LABEL_KEY = {
    "command": "nav_command",
    "market": "nav_market",
    "operations": "nav_ops",
    "marketing": "nav_marketing",
    "finance": "nav_finance",
    "audit": "nav_audit",
}
NAV_OPTIONS = list(NAV_LABEL_KEY.keys())

with st.sidebar:
    st.markdown(
        f"""
        <div class="bcos-brand">
            <div class="bcos-brand-title">🇧🇷 Brazil Commerce OS</div>
            <div class="bcos-brand-sub">{escape(t['mvp'])}</div>
        </div>
        """,
        unsafe_allow_html=True,
    )

    selected_language = st.selectbox(
        t["language"],
        options=list(LANG_OPTIONS.keys()),
        index=list(LANG_OPTIONS.keys()).index(st.session_state.ui_language),
        key="language_selector",
    )
    if selected_language != st.session_state.ui_language:
        st.session_state.ui_language = selected_language
        st.rerun()

    module = st.radio(
        t["workspace"],
        NAV_OPTIONS,
        format_func=lambda x: t[NAV_LABEL_KEY[x]],
        key="workspace",
        label_visibility="visible",
    )

    st.markdown("---")
    st.caption(t["ai_status"])

    llm_text = t["ai_demo"] if DEMO_MODE else t["ai_live"]
    search_text = t["search_live"] if SERPER_API_KEY else t["search_offline"]
    llm_dot = "bcos-dot-amber" if DEMO_MODE else "bcos-dot-green"
    search_dot = "bcos-dot-green" if SERPER_API_KEY else "bcos-dot-amber"

    st.markdown(
        f"""
        <div class="bcos-status-row">
            <span class="bcos-chip"><span class="{llm_dot}"></span>{escape(llm_text)}</span>
            <span class="bcos-chip"><span class="{search_dot}"></span>{escape(search_text)}</span>
        </div>
        """,
        unsafe_allow_html=True,
    )


# =========================================================
# 00 Command Center
# =========================================================
if module == "command":
    st.markdown(
        f"""
        <div class="bcos-hero">
            <div class="bcos-kicker">AI COMMERCE AGENT</div>
            <h1>{escape(t['app_name'])}</h1>
            <p>{escape(t['tagline'])}</p>
        </div>
        """,
        unsafe_allow_html=True,
    )

    section_header("COMMAND CENTER", t["home_title"], t["home_subtitle"])
    module_cards()

    q = st.text_area(
        t["goal_label"],
        placeholder=t["goal_ph"],
        height=120,
        key="command_goal",
    )

    if st.button(t["route"], type="primary", key="route_request_btn"):
        if not q.strip():
            st.warning(t["empty_goal"])
        else:
            d = route_request(q)
            st.session_state["last_route"] = d.module
            save_history("Orchestrator", q[:80], f"Route → {d.module}")

    if st.session_state.get("last_route"):
        target = st.session_state["last_route"]
        nav_target = target if target in {"market", "operations", "marketing", "finance"} else "market"
        st.markdown(
            f"""
            <div class="bcos-panel">
                <div class="bcos-eyebrow">{escape(t['route_to'])}</div>
                <div class="bcos-card-title">{escape(t[NAV_LABEL_KEY[nav_target]])}</div>
                <div class="bcos-card-desc">{escape(localized_route_copy(nav_target))}</div>
            </div>
            """,
            unsafe_allow_html=True,
        )
        st.button(
            t["open_module"],
            key="open_routed_module",
            on_click=go_to_module,
            args=(nav_target,),
        )

    st.markdown("---")
    section_header("COPILOT", t["copilot"], t["copilot_sub"])
    cq = st.text_input(t["copilot_label"], placeholder=t["copilot_ph"], key="copilot_question")
    if st.button(t["ask"], key="ask_copilot_btn"):
        if not cq.strip():
            st.info(t["empty_question"])
        else:
            with st.spinner("AI…"):
                answer = chat(
                    f"{ai_lang_instruction()}\n\nUser question:\n{cq}\n\n"
                    "Answer as the Brazil Commerce OS business copilot. Be practical and concise."
                )
            st.session_state["copilot_answer"] = answer
            save_history("Copilot", cq[:80], "Answered")

    if st.session_state.get("copilot_answer"):
        st.markdown(st.session_state["copilot_answer"])


# =========================================================
# 01 Market Intelligence
# =========================================================
elif module == "market":
    section_header("01 · MARKET INTELLIGENCE", t["market_title"], t["market_sub"])

    with st.expander(t["rules"], expanded=False):
        st.markdown(
            f"- {t['source_priority']}\n"
            f"- {t['market_rule_1']}\n"
            f"- {t['market_rule_2']}"
        )

    c1, c2 = st.columns(2)
    with c1:
        country = st.selectbox(t["country"], ["Brazil", "Mexico", "Chile"], key="market_country")
        product = st.text_input(t["product"], placeholder=t["product_ph"], key="market_product")
    with c2:
        platform = st.selectbox(
            t["platform_optional"],
            ["", "Mercado Livre", "TikTok Shop", "Amazon BR", "Shopee BR"],
            key="market_platform",
        )
        price = st.text_input(t["price_optional"], placeholder=t["price_ph"], key="market_price")

    objective = st.text_area(
        t["research_objective"],
        placeholder=t["research_objective_ph"],
        height=110,
        key="market_objective",
    )

    dims = st.multiselect(
        t["research_dims"],
        DIMENSIONS,
        default=DIMENSIONS[:6],
        format_func=lambda x: DIMENSION_LABELS[lang_code][x],
        key="market_dimensions",
    )

    if st.button(t["run_market"], type="primary", key="run_market_btn"):
        if not product.strip() or not objective.strip() or not dims:
            st.error(t["required"])
        else:
            objective_for_agent = (
                f"{objective.strip()}\n\n"
                f"OUTPUT LANGUAGE REQUIREMENT: {ai_lang_instruction()}\n"
                "Do not translate source names or URLs."
            )
            if price.strip():
                objective_for_agent += f"\nUSER-PROVIDED EXPECTED PRICE RANGE: {price.strip()}"

            with st.spinner(t["researching"]):
                result = run_market_research(
                    country,
                    product.strip(),
                    objective_for_agent,
                    platform,
                    dims,
                )
            st.session_state.market_result = result
            save_history("Market", product[:80], f"{country} | {result.get('mode', '')}")

    result = st.session_state.market_result
    if result:
        live = result.get("mode") == "LIVE SEARCH"
        badge_class = "bcos-badge-live" if live else "bcos-badge-demo"
        badge_text = t["mode_live"] if live else t["mode_demo"]
        evidence = result.get("evidence") or []

        st.markdown(
            f"""
            <div class="bcos-result-head">
                <div class="bcos-section-title">{escape(t['research_memo'])}</div>
                <span class="{badge_class}">{escape(badge_text)}</span>
            </div>
            """,
            unsafe_allow_html=True,
        )
        st.markdown(result.get("analysis") or "")

        download_markdown(
            t["download_memo"],
            result.get("analysis") or "",
            f"market_research_{country}_{product.strip().replace(' ', '_')[:40]}.md",
            "download_market_memo",
        )

        st.markdown(f"### {t['evidence_register']}")
        st.caption(f"{t['evidence_count']}: {len(evidence)}")

        if evidence:
            ev = pd.DataFrame(evidence)
            preferred = ["title", "source_type", "snippet", "link"]
            cols = [c for c in preferred if c in ev.columns] + [c for c in ev.columns if c not in preferred]
            ev = ev[cols]
            column_config = {}
            if "link" in ev.columns:
                column_config["link"] = st.column_config.LinkColumn("URL", display_text="Open source")
            st.dataframe(
                ev,
                use_container_width=True,
                hide_index=True,
                column_config=column_config,
            )
        else:
            empty_state("No evidence returned.")


# =========================================================
# 02 E-commerce Operations
# =========================================================
elif module == "operations":
    section_header("02 · E-COMMERCE OPERATIONS", t["ops_title"], t["ops_sub"])

    with st.expander(t["rules"], expanded=False):
        st.markdown(f"- {t['ops_rule_1']}\n- {t['ops_rule_2']}")

    st.info(t["ops_language_note"])

    a, b, c = st.columns(3)
    merchant_id = a.text_input(t["merchant_id"], "MER-001", key="ops_merchant_id")
    product_id = b.text_input(t["product_id"], "PRD-001", key="ops_product_id")
    sku = c.text_input(t["sku"], "SKU-001", key="ops_sku")

    a, b = st.columns(2)
    product_name = a.text_input(t["product_name"], placeholder=t["product_name_ph"], key="ops_product_name")
    platform = b.selectbox(
        t["platform"],
        ["Mercado Livre", "TikTok Shop", "Amazon BR", "Shopee BR"],
        key="ops_platform",
    )

    approved_facts = st.text_area(
        t["approved_facts"],
        placeholder=t["approved_facts_ph"],
        height=130,
        key="ops_approved_facts",
    )

    a, b, c = st.columns(3)
    selling_price = a.text_input(t["selling_price"], placeholder="299", key="ops_selling_price")
    inventory = b.text_input(t["inventory"], placeholder="500", key="ops_inventory")
    unit_cost = c.text_input(t["unit_cost"], placeholder="85", key="ops_unit_cost")

    if st.button(t["generate_launch"], type="primary", key="generate_launch_btn"):
        required = [merchant_id, product_id, sku, product_name, platform, approved_facts]
        if not all(str(x).strip() for x in required):
            st.error(t["required"])
        else:
            facts_for_agent = approved_facts.strip()
            if lang_code != "pt-BR":
                facts_for_agent += (
                    "\n\nMETA INSTRUCTION (not a product fact): "
                    + ai_lang_instruction()
                    + " Keep the consumer-facing listing title, bullets and description in Brazilian Portuguese; "
                      "write checklist and warnings in the selected UI language."
                )

            with st.spinner(t["generating_launch"]):
                result = run_operations(
                    merchant_id.strip(),
                    product_id.strip(),
                    sku.strip(),
                    product_name.strip(),
                    platform,
                    facts_for_agent,
                    selling_price.strip(),
                    inventory.strip(),
                    unit_cost.strip(),
                )
            st.session_state.ops_result = result
            save_history("Operations", sku[:80], platform)

    result = st.session_state.ops_result
    if result:
        if result.get("missing"):
            st.warning(f"{t['missing']}: " + ", ".join(result["missing"]))
        st.markdown(f"### {t['launch_pack']}")
        st.markdown(result.get("generated_pack") or "")
        download_markdown(
            t["download_launch"],
            result.get("generated_pack") or "",
            f"launch_pack_{result.get('sku', 'SKU')}.md",
            "download_launch_pack",
        )


# =========================================================
# 03 Marketing / Creator / Content
# =========================================================
elif module == "marketing":
    section_header("03 · MARKETING / CREATOR", t["marketing_title"], t["marketing_sub"])

    with st.expander(t["rules"], expanded=False):
        st.markdown(f"- {t['marketing_rule_1']}\n- {t['marketing_rule_2']}")

    campaign_id = st.text_input(t["campaign_id"], "CMP-BR-001", key="mkt_campaign_id")
    product = st.text_input(t["product_sku"], placeholder="PRD-PET-01 / SKU-001", key="mkt_product")

    c1, c2, c3 = st.columns(3)
    objective = c1.selectbox(
        t["campaign_objective"],
        CAMPAIGN_OBJECTIVES,
        format_func=lambda x: CAMPAIGN_OBJECTIVE_LABELS[lang_code][x],
        key="mkt_objective",
    )
    category = c2.text_input(t["category"], placeholder=t["category_ph"], key="mkt_category")
    budget = c3.number_input(
        t["creator_budget"],
        min_value=0.0,
        value=0.0,
        step=500.0,
        key="mkt_budget",
    )

    approved_brief = st.text_area(
        t["brand_brief"],
        placeholder=t["brand_brief_ph"],
        height=120,
        key="mkt_brief",
    )

    creator_file = st.file_uploader(
        t["upload_creator"],
        type=["csv", "xlsx", "xls"],
        key="creator_file_uploader",
    )

    if creator_file is None:
        empty_state(t["creator_empty"])
    else:
        try:
            creator_df = load_creator_file(creator_file)
        except Exception as e:
            st.error(str(e))
            creator_df = None

        if creator_df is not None:
            st.caption(f"{t['rows_loaded']}: {len(creator_df):,}")
            st.dataframe(creator_df.head(20), use_container_width=True, hide_index=True)

            if st.button(t["build_shortlist"], type="primary", key="build_shortlist_btn"):
                if not product.strip() or not category.strip() or not approved_brief.strip():
                    st.error(t["required"])
                else:
                    ranked = score_creators(creator_df, category.strip(), budget if budget > 0 else None)
                    brief_for_agent = (
                        approved_brief.strip()
                        + "\n\nMETA OUTPUT LANGUAGE: "
                        + ai_lang_instruction()
                    )
                    with st.spinner(t["analysing_fit"]):
                        explanation = explain_creator_fit(
                            ranked,
                            campaign_id.strip(),
                            product.strip(),
                            objective,
                            brief_for_agent,
                        )
                    st.session_state.marketing_result = {
                        "ranked": ranked.head(10),
                        "explanation": explanation,
                        "campaign_id": campaign_id.strip(),
                    }
                    save_history("Marketing", campaign_id[:80], f"{len(creator_df)} creators")

    result = st.session_state.marketing_result
    if result:
        st.markdown(f"### {t['shortlist']}")
        st.dataframe(result["ranked"], use_container_width=True, hide_index=True)
        st.markdown(f"### {t['fit_analysis']}")
        st.markdown(result.get("explanation") or "")
        download_markdown(
            t["download_creator_analysis"],
            result.get("explanation") or "",
            f"creator_analysis_{result.get('campaign_id', 'campaign')}.md",
            "download_creator_analysis",
        )

    template_bytes = safe_template_bytes(BASE / "data" / "creator_sample.csv")
    if template_bytes is not None:
        st.download_button(
            t["download_creator_template"],
            data=template_bytes,
            file_name="creator_sample.csv",
            mime="text/csv",
            key="download_creator_template",
        )


# =========================================================
# 04 Finance & Performance
# =========================================================
elif module == "finance":
    section_header("04 · FINANCE & PERFORMANCE", t["finance_title"], t["finance_sub"])

    with st.expander(t["rules"], expanded=False):
        st.markdown(f"- {t['finance_rule_1']}\n- {t['finance_rule_2']}")

    finance_file = st.file_uploader(
        t["upload_finance"],
        type=["csv", "xlsx", "xls", "json"],
        key="finance_file_uploader",
    )

    if finance_file is None:
        empty_state(t["finance_empty"])
    else:
        try:
            finance_df = load_finance_file(finance_file)
        except Exception as e:
            st.error(str(e))
            finance_df = None

        if finance_df is not None:
            st.dataframe(finance_df.head(20), use_container_width=True, hide_index=True)

            if st.button(t["run_finance"], type="primary", key="run_finance_btn"):
                try:
                    with st.spinner(t["analysing_finance"]):
                        calc = analyse_finance(finance_df)
                        advisor_prompt = f"""
{ai_lang_instruction()}

The deterministic Finance tool already calculated the following results:
{calc}

Explain only from these calculated results and the stated missing fields.
Return:
1. What is available vs incomplete
2. The most important business drivers
3. A maximum of 3 practical next actions

Rules:
- Do NOT freely recalculate or invent numbers.
- Do NOT treat missing cost fields as zero.
- Clearly separate observed/calculated facts from interpretation.
"""
                        advisor = chat(advisor_prompt)
                except Exception as e:
                    st.error(str(e))
                else:
                    st.session_state.finance_result = {
                        "calc": calc,
                        "advisor": advisor,
                        "filename": finance_file.name,
                    }
                    save_history("Finance", finance_file.name[:80], f"{len(finance_df)} rows")

    result = st.session_state.finance_result
    if result:
        calc = result["calc"]
        a, b, c, d = st.columns(4)
        a.metric(t["net_sales"], f"R$ {calc['net_sales']:,.0f}")
        b.metric(t["aov"], t["incomplete"] if calc["aov"] is None else f"R$ {calc['aov']:,.2f}")
        c.metric(t["roas"], t["incomplete"] if calc["roas"] is None else f"{calc['roas']:.2f}")
        d.metric(
            t["contribution_profit"],
            t["incomplete"] if calc["contribution_profit"] is None else f"R$ {calc['contribution_profit']:,.0f}",
        )

        if calc.get("missing_for_profitability"):
            st.warning(
                f"Profitability = {t['incomplete']}. {t['missing']}: "
                + ", ".join(calc["missing_for_profitability"])
            )
        elif calc.get("contribution_margin") is not None:
            st.success(f"{t['contribution_margin']} = {calc['contribution_margin']:.1%}")

        with st.expander(t["field_mapping"], expanded=False):
            st.json(calc.get("mapping", {}))

        st.markdown(f"### {t['ai_advisor']}")
        st.markdown(result.get("advisor") or "")
        download_markdown(
            t["download_finance_analysis"],
            result.get("advisor") or "",
            f"finance_analysis_{result.get('filename', 'analysis')}.md",
            "download_finance_analysis",
        )

    template_bytes = safe_template_bytes(BASE / "data" / "finance_sample.csv")
    if template_bytes is not None:
        st.download_button(
            t["download_finance_template"],
            data=template_bytes,
            file_name="finance_sample.csv",
            mime="text/csv",
            key="download_finance_template",
        )


# =========================================================
# Audit Trail
# =========================================================
elif module == "audit":
    section_header("AUDIT", t["audit_title"], t["audit_sub"])

    if not st.session_state.history:
        empty_state(t["no_history"])
    else:
        st.dataframe(
            pd.DataFrame(st.session_state.history),
            use_container_width=True,
            hide_index=True,
        )
        if st.button(t["clear_history"], key="clear_history_btn"):
            st.session_state.history = []
            st.success(t["history_cleared"])
            st.rerun()
