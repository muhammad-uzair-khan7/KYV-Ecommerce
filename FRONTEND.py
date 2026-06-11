import streamlit as st
import requests
from datetime import datetime

st.set_page_config(
    page_title="KYV - Vendor Screening",
    page_icon="🛡️",
    layout="wide",
    initial_sidebar_state="expanded"
)

st.markdown("""
<style>
.big-header { font-size: 2.2rem; font-weight: 700; color: #1f77b4; }
.metric-box { background: #f8f9fa; padding: 1rem; border-radius: 8px; margin: 0.5rem 0; }
</style>
""", unsafe_allow_html=True)

BACKEND_URL = "http://127.0.0.1:8000"

def check_backend():
    try:
        r = requests.get(f"{BACKEND_URL}/", timeout=2)
        return r.status_code == 200
    except:
        return False

st.markdown("# 🛡️ KYV Vendor Screening Platform")
st.markdown("**Know Your Vendor — AI-Powered Compliance Screening**")
st.markdown("---")

backend_online = check_backend()
if backend_online:
    st.success("✅ Backend Online")
else:
    st.error("❌ Backend Offline — Run: `uvicorn orchestrator:app --host 127.0.0.1 --port 8000`")

# ── Sidebar ────────────────────────────────────────────────────────────────────
with st.sidebar:
    st.header("📋 Vendor Information")
    with st.form("vendor_form"):
        company_name = st.text_input("Company Name *", placeholder="e.g., Global Express Logistics")
        country_iso  = st.selectbox("Country", ["PK", "US", "CN", "IR", "GB", "AE", "SA", "IN"], index=0)
        vendor_type  = st.selectbox("Vendor Type", ["logistics", "saas_software", "data_processor", "financial_service", "default"])
        tenant_id    = st.text_input("Tenant ID", value="tenant_001")
        vendor_id    = st.text_input("Vendor ID", placeholder="Leave blank for auto-generation")
        st.markdown("---")
        submit = st.form_submit_button("🚀 Run Screening", use_container_width=True, disabled=not backend_online)

# ── Main ───────────────────────────────────────────────────────────────────────
if submit and company_name:
    payload = {
        "company_name": company_name,
        "country_iso":  country_iso,
        "vendor_type":  vendor_type,
        "tenant_id":    tenant_id,
        "vendor_id":    vendor_id,
        "kyb_status":   "PENDING",
    }

    with st.spinner("⏳ Running screening pipeline..."):
        try:
            response = requests.post(f"{BACKEND_URL}/evaluate-vendor", json=payload, timeout=60)
        except requests.exceptions.ConnectionError:
            st.error("❌ Cannot connect to backend.")
            st.stop()
        except requests.exceptions.Timeout:
            st.error("❌ Request timed out.")
            st.stop()

    if response.status_code != 200:
        st.error(f"❌ Backend Error (HTTP {response.status_code})")
        st.code(response.text)
        st.stop()

    result      = response.json()
    graph       = result.get("graph_output", {})
    kyb_status  = graph.get("kyb_status", "UNKNOWN")
    risk_vector = graph.get("computed_risk_vector", {})
    overall     = risk_vector.get("overall_score", 0)
    contracts   = graph.get("parsed_contracts", [])
    flags       = graph.get("watchlist_flags", [])
    messages    = graph.get("messages", [])

    # ── KYB Status Banner ──────────────────────────────────────────────────────
    st.markdown("## 📊 Screening Results")
    st.markdown(f"**Vendor ID:** `{graph.get('vendor_id', 'N/A')}` &nbsp;|&nbsp; **Screened:** {datetime.now().strftime('%Y-%m-%d %H:%M:%S')}")
    st.markdown("---")

    if kyb_status == "BLOCKED":
        st.error("## ⛔ VENDOR BLOCKED — Sanctions Match")
    elif kyb_status == "FLAGGED":
        st.warning("## ⚠️ VENDOR FLAGGED — Manual Review Required")
    elif kyb_status == "CLEAN":
        st.success("## ✅ VENDOR APPROVED — Passed Compliance Screening")
    else:
        st.info(f"## ℹ️ KYB Status: {kyb_status}")

    # ── Risk Scores ────────────────────────────────────────────────────────────
    st.markdown("### 🧮 Risk Scores")
    c1, c2, c3, c4, c5 = st.columns(5)
    c1.metric("Overall Score",   f"{overall}/100")
    c2.metric("Cyber",           f"{risk_vector.get('cyber', 0)}/100")
    c3.metric("Sanctions",       f"{risk_vector.get('sanctions', 0)}/100")
    c4.metric("Financial",       f"{risk_vector.get('financial', 0)}/100")
    c5.metric("Operational",     f"{risk_vector.get('operational', 0)}/100")

    # ── Contract Analysis ──────────────────────────────────────────────────────
    st.markdown("### 📄 Contract Analysis")
    st.caption("Note: Contract clause risk reflects individual clause severity, not the vendor's overall risk classification.")
    if contracts:
        for c in contracts:
            analysis = c.get("clause_analysis", {})
            if analysis.get("no_contract_found"):
                st.info("No contract documents found for this vendor.")
            else:
                col_a, col_b = st.columns(2)
                with col_a:
                    risk_color = {"LOW": "✅", "MEDIUM": "⚠️", "HIGH": "🔴"}.get(analysis.get("overall_contract_risk"), "ℹ️")
                    contract_risk = analysis.get('overall_contract_risk', 'N/A')
                    st.markdown(f"**Contract Clause Risk:** {risk_color} {contract_risk} *(clause-level assessment)*")

                    st.markdown(f"**Liability Cap:** {'✅ Found' if analysis.get('liability_cap_found') else '❌ Not found'} — {analysis.get('liability_cap_amount', 'N/A')}")
                    st.markdown(f"**Force Majeure:** {'✅' if analysis.get('force_majeure_present') else '❌'}")
                    st.markdown(f"**Data Processing Agreement:** {'✅' if analysis.get('data_processing_agreement') else '❌'}")
                with col_b:
                    st.markdown(f"**Auto-Renewal Clause:** {'⚠️ Yes' if analysis.get('auto_renewal_clause') else '✅ No'}")
                    st.markdown(f"**Termination for Convenience:** {'✅' if analysis.get('termination_for_convenience') else '❌'}")
                    st.markdown(f"**Indemnification Scope:** {analysis.get('indemnification_scope', 'N/A')}")
                    st.markdown(f"**Governing Law:** {analysis.get('governing_law', 'N/A')}")

                high_risk = analysis.get("high_risk_clauses", [])
                if high_risk:
                    st.markdown("**⚠️ High Risk Clauses:**")
                    for clause in high_risk:
                        st.markdown(f"- {clause}")
    else:
        st.info("No contract analysis available.")

    # ── Watchlist Flags ────────────────────────────────────────────────────────
    if flags:
        st.markdown("### 🚨 Watchlist Flags")
        for f in flags:
            st.error(f"**{f.get('match_name')}** — Score: {f.get('score')} | Datasets: {', '.join(f.get('datasets', []))}")

    # ── Agent Messages ─────────────────────────────────────────────────────────
    st.markdown("### 🤖 Agent Log")
    for msg in messages:
        content = msg.get("content", "") if isinstance(msg, dict) else str(msg)
        st.markdown(f"- {content}")

    # ── Raw Response ───────────────────────────────────────────────────────────
    with st.expander("📄 Full API Response"):
        st.json(result)

elif submit and not company_name:
    st.warning("⚠️ Please enter a company name.")

else:
    st.info("""
    ### 👈 How to Use
    1. Fill in vendor details in the sidebar
    2. Click **🚀 Run Screening**
    3. View KYB status, risk scores, and contract analysis here

    **Test cases:**
    - Any name → CLEAN
    - Name containing "Suspicious" → FLAGGED
    - Name containing "Blacklisted" → BLOCKED
    """)