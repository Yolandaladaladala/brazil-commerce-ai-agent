from pathlib import Path
import streamlit as st
import pandas as pd

from agent import route_request, explain_route
from tools.market import run_market_research
from tools.operations import run_operations
from tools.marketing import load_creator_file, score_creators, explain_creator_fit
from tools.finance import load_finance_file, analyse_finance
from llm import chat
from config import DEMO_MODE

BASE = Path(__file__).resolve().parent

st.set_page_config(
    page_title="Brazil Commerce OS",
    page_icon="🇧🇷",
    layout="wide",
)

st.markdown("""
<style>
.block-container{max-width:1500px;padding-top:1.25rem;padding-bottom:3rem}
[data-testid="stSidebar"]{background:#071a35}
[data-testid="stSidebar"] *{color:#eef4ff}
h1,h2,h3{letter-spacing:-.02em}
.bcos-card{border:1px solid #e6e9ef;border-radius:16px;padding:16px;background:white}
.small{font-size:12px;color:#69768b}
.orange{color:#ff5b00}
</style>
""", unsafe_allow_html=True)

if "history" not in st.session_state:
    st.session_state.history = []

def save_history(module, title, detail):
    st.session_state.history.insert(0, {
        "module": module,
        "title": title,
        "detail": detail,
    })

def required_label(name, tip):
    return f"{name} *"

with st.sidebar:
    st.markdown("## 🇧🇷 Brazil Commerce OS")
    st.caption("AI Commerce Agent MVP")
    module = st.radio(
        "Workspace",
        [
            "Command Center",
            "01 Market Intelligence",
            "02 E-commerce Operations",
            "03 Marketing / Creator",
            "04 Finance & Performance",
            "Audit Trail",
        ],
    )
    st.divider()
    st.caption("AI mode")
    st.success("Demo fallback" if DEMO_MODE else "Live LLM")

if module == "Command Center":
    st.title("Brazil Commerce OS")
    st.write("一个主 Agent + 四个独立工具。模块可以单独运行，需要时通过稳定 ID 和数据结构连接。")

    c1,c2,c3,c4 = st.columns(4)
    with c1:
        st.metric("Market", "Source-first")
        st.caption("先 research dimensions，再检索 evidence")
    with c2:
        st.metric("Operations", "Approved facts")
        st.caption("Listing 可以生成，事实不能猜")
    with c3:
        st.metric("Marketing", "Real creators only")
        st.caption("CSV / FastMoss / verified source")
    with c4:
        st.metric("Finance", "Deterministic math")
        st.caption("Missing ≠ 0")

    st.subheader("Orchestrator")
    q = st.text_area(
        "告诉系统你想做什么 *",
        placeholder="例如：我想把一个咖啡器具卖到巴西，不知道应该先做什么",
    )
    if st.button("Route my request", type="primary"):
        if not q.strip():
            st.warning("请输入一个目标。")
        else:
            d = route_request(q)
            st.success(f"Route → {d.module}")
            st.write(explain_route(q))
            save_history("Orchestrator", q[:60], f"Routed to {d.module}")

    st.subheader("AI Copilot")
    cq = st.text_input("随便问一个问题", placeholder="例如：ROAS 是什么？SKU 为什么重要？")
    if st.button("Ask Copilot"):
        if cq.strip():
            st.write(chat(cq))
        else:
            st.info("随便输入一点内容也可以，我会至少给你一个兜底回答。")

elif module == "01 Market Intelligence":
    st.title("01 Market & Product Intelligence")
    st.caption("目标：像咨询公司的市场研究团队一样，帮助客户判断卖什么、去哪里卖、值不值得试。")

    with st.expander("术语说明 / Rules", expanded=False):
        st.markdown("""
- **Research Objective**：你真正要做的商业决策，不是“帮我研究一下”。
- **Research Dimensions**：开始搜索前先决定要研究哪些维度。
- **Evidence**：结论背后的来源记录。
- **Source priority**：政府/监管 > 行业协会 > 公司披露 > 专业研究机构 > 可靠媒体 > Marketplace evidence。
""")

    c1,c2 = st.columns(2)
    with c1:
        country = st.selectbox("Country / Market *", ["Brazil", "Mexico", "Chile"])
        product = st.text_input("Product / Category *", placeholder="例如：家用咖啡器具")
    with c2:
        platform = st.selectbox("Platform（选填）", ["", "Mercado Livre", "TikTok Shop", "Amazon BR", "Shopee BR"])
        price = st.text_input("Expected Price Range（选填）", placeholder="R$120-350")

    objective = st.text_area(
        "Research Objective *",
        placeholder="例如：判断该类目是否值得进入巴西，并给出主要竞品、价格带、渠道与低风险验证方式。",
    )

    dims = st.multiselect(
        "Research Dimensions *",
        [
            "Market size & growth",
            "Competition",
            "Pricing",
            "Channels",
            "Consumer need",
            "Regulation",
            "TikTok / social commerce signals",
        ],
        default=[
            "Market size & growth",
            "Competition",
            "Pricing",
            "Channels",
            "Consumer need",
            "Regulation",
        ],
    )

    if st.button("Run Market Research", type="primary"):
        if not product.strip() or not objective.strip() or not dims:
            st.error("请完成所有 * 必填项。")
        else:
            with st.spinner("Building research plan → retrieving evidence → analysing..."):
                r = run_market_research(country, product, objective, platform, dims)
            st.success(r["mode"])
            st.subheader("Research Memo")
            st.write(r["analysis"])

            st.subheader("Evidence Register")
            ev = pd.DataFrame(r["evidence"])
            st.dataframe(ev, use_container_width=True, hide_index=True)

            save_history("Market", product, f"{country} | {r['mode']}")

elif module == "02 E-commerce Operations":
    st.title("02 E-commerce Planning & Operations")
    st.caption("目标：把研究结论变成真正可卖、可下单、可履约的商品与流程。")

    with st.expander("术语说明 / Rules"):
        st.markdown("""
- **Product ID**：产品层稳定 ID。
- **SKU**：具体可库存/销售单元的稳定 ID。
- **Approved Product Facts**：商家已确认的产品事实，是 LLM 唯一允许使用的产品事实底座。
- **Missing**：没有真实值就保持缺失，不自动补 0。
""")

    a,b,c = st.columns(3)
    merchant_id = a.text_input("Merchant ID *", "MER-001")
    product_id = b.text_input("Product ID *", "PRD-001")
    sku = c.text_input("SKU *", "SKU-001")

    a,b = st.columns(2)
    product_name = a.text_input("Product Name *", placeholder="真无线蓝牙耳机")
    platform = b.selectbox("Platform *", ["Mercado Livre", "TikTok Shop", "Amazon BR", "Shopee BR"])

    approved_facts = st.text_area(
        "Approved Product Facts *",
        placeholder="例如：蓝牙5.3；30小时综合续航；Type-C；IPX5；双麦克风通话降噪。",
    )

    a,b,c = st.columns(3)
    price = a.text_input("Selling Price（选填）", placeholder="299")
    inventory = b.text_input("Inventory（选填）", placeholder="500")
    unit_cost = c.text_input("Unit Cost（选填）", placeholder="85")

    if st.button("Generate Launch Pack", type="primary"):
        required = [merchant_id, product_id, sku, product_name, platform, approved_facts]
        if not all(str(x).strip() for x in required):
            st.error("请完成所有 * 必填项。")
        else:
            with st.spinner("Generating localization + launch control pack..."):
                r = run_operations(
                    merchant_id, product_id, sku, product_name, platform,
                    approved_facts, price, inventory, unit_cost
                )
            if r["missing"]:
                st.warning("Missing: " + ", ".join(r["missing"]))
            st.subheader("Launch Pack")
            st.write(r["generated_pack"])
            save_history("Operations", sku, platform)

elif module == "03 Marketing / Creator":
    st.title("03 Marketing / Creator / Content")
    st.caption("目标：真实 Creator 数据 → Python 过滤/评分 → AI 解释 fit → 内容与执行。")

    with st.expander("术语说明 / Rules"):
        st.markdown("""
- **Creator source**：Creator 身份必须来自平台、FastMoss/外部 analytics、客户 CRM 或上传文件。
- **Fit score**：系统根据已有字段做规则化评分，不代表平台官方排名。
- **Human approval**：建联、合同、发布、付款等高影响动作第一版不自动执行。
""")

    campaign_id = st.text_input("Campaign ID *", "CMP-BR-001")
    product = st.text_input("Product / SKU *", placeholder="PRD-SKIN-01 / SKU-001")
    c1,c2,c3 = st.columns(3)
    objective = c1.selectbox("Campaign Objective *", ["Sales / Conversion", "Brand Awareness", "Product Seeding", "LIVE Traffic"])
    category = c2.text_input("Category *", placeholder="Beauty")
    budget = c3.number_input("Creator Budget BRL（选填）", min_value=0.0, value=0.0, step=500.0)

    approved_brief = st.text_area(
        "Approved Product / Brand Brief *",
        placeholder="例如：强调巴西夏季高温场景；内容真实生活化；不能使用未经确认的医学功效表述。",
    )

    creator_file = st.file_uploader("上传 Creator CSV / XLSX *", type=["csv", "xlsx", "xls"])

    if creator_file is not None:
        df = load_creator_file(creator_file)
        st.caption(f"{len(df)} creator rows loaded")
        st.dataframe(df.head(15), use_container_width=True)

        if st.button("Build Creator Shortlist", type="primary"):
            if not product.strip() or not category.strip() or not approved_brief.strip():
                st.error("请完成所有 * 必填项。")
            else:
                ranked = score_creators(df, category, budget if budget > 0 else None)
                st.subheader("Deterministic shortlist")
                st.dataframe(ranked.head(10), use_container_width=True, hide_index=True)

                with st.spinner("AI explaining creator fit..."):
                    explanation = explain_creator_fit(
                        ranked, campaign_id, product, objective, approved_brief
                    )
                st.subheader("AI Fit Analysis")
                st.write(explanation)
                save_history("Marketing", campaign_id, f"{len(df)} creators")

    st.download_button(
        "Download Creator CSV template",
        data=(BASE / "data" / "creator_sample.csv").read_bytes(),
        file_name="creator_sample.csv",
        mime="text/csv",
    )

elif module == "04 Finance & Performance":
    st.title("04 Financial & Performance Intelligence")
    st.caption("目标：先控制数据质量，再算数，再解释。没有真实文件，不生成假的 Profitability。")

    with st.expander("术语说明 / Levels"):
        st.markdown("""
- **Level 1 Basic Sales**：sales / orders / refunds / platform fee。
- **Level 2 Profitability**：再有 product cost / logistics / ads / creator cost。
- **Level 3 Advanced Finance**：未来加入 inventory / AP / AR / budget / forecast。
- **Contribution Profit**：Net Sales 扣除与该业务直接相关的成本后的经营贡献利润。
""")

    finance_file = st.file_uploader("上传 Finance CSV / XLSX / JSON *", type=["csv", "xlsx", "xls", "json"])

    if finance_file is None:
        st.warning("Profitability = Incomplete。请先上传经营数据。")
    else:
        df = load_finance_file(finance_file)
        st.dataframe(df.head(20), use_container_width=True)

        if st.button("Run Financial Analysis", type="primary"):
            try:
                r = analyse_finance(df)
            except Exception as e:
                st.error(str(e))
            else:
                a,b,c,d = st.columns(4)
                a.metric("Net Sales", f"R$ {r['net_sales']:,.0f}")
                b.metric("AOV", "Incomplete" if r["aov"] is None else f"R$ {r['aov']:,.2f}")
                c.metric("ROAS", "Incomplete" if r["roas"] is None else f"{r['roas']:.2f}")
                d.metric(
                    "Contribution Profit",
                    "Incomplete" if r["contribution_profit"] is None else f"R$ {r['contribution_profit']:,.0f}",
                )

                if r["missing_for_profitability"]:
                    st.warning("Profitability = Incomplete. Missing: " + ", ".join(r["missing_for_profitability"]))
                else:
                    st.success(f"Contribution Margin = {r['contribution_margin']:.1%}")

                st.subheader("Field mapping")
                st.json(r["mapping"])

                prompt = f"""
Finance tool already calculated these results:
{r}

Explain:
1. what is available vs incomplete
2. important business drivers
3. maximum 3 next actions

Do NOT recalculate numbers freely.
"""
                st.subheader("AI Advisor")
                st.write(chat(prompt))
                save_history("Finance", finance_file.name, f"{len(df)} rows")

    st.download_button(
        "Download Finance CSV template",
        data=(BASE / "data" / "finance_sample.csv").read_bytes(),
        file_name="finance_sample.csv",
        mime="text/csv",
    )

elif module == "Audit Trail":
    st.title("Audit Trail")
    if not st.session_state.history:
        st.info("还没有运行记录。")
    else:
        st.dataframe(pd.DataFrame(st.session_state.history), use_container_width=True, hide_index=True)
