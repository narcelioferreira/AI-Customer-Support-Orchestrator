import streamlit as st
import sys, os
sys.path.insert(0, os.path.join(os.path.dirname(__file__), ".."))

from datetime import datetime
from database import get_protocols, get_messages, update_protocol_status, init_db
from seed import seed

st.set_page_config(page_title="Protocolos · AI Orchestrator", page_icon="📋", layout="wide")
init_db(); seed()

st.markdown("""
<style>
[data-testid="stAppViewContainer"] { background:#0F172A; }
[data-testid="stSidebar"] { background:#1E293B!important; border-right:1px solid #334155; }
h1,h2,h3,h4 { color:#F1F5F9!important; }
p,.stMarkdown,label { color:#CBD5E1!important; }
.proto-card {
    background:#1E293B; border:1px solid #334155;
    border-radius:12px; padding:16px 20px; margin-bottom:10px;
}
.pill { display:inline-block; padding:3px 10px; border-radius:99px;
        font-size:.75rem; font-weight:600; }
.pill-financeiro{background:#FEF3C7;color:#92400E;}
.pill-logistica {background:#DBEAFE;color:#1E40AF;}
.pill-comercial {background:#D1FAE5;color:#065F46;}
.pill-juridico  {background:#FEE2E2;color:#991B1B;}
.pill-geral     {background:#EDE9FE;color:#5B21B6;}
.pill-urgente   {background:#FEE2E2;color:#991B1B;}
.pill-alta      {background:#FEF3C7;color:#92400E;}
.pill-media     {background:#DBEAFE;color:#1E40AF;}
.pill-baixa     {background:#D1FAE5;color:#065F46;}
.pill-aberto    {background:#FEF3C7;color:#92400E;}
.pill-fechado   {background:#D1FAE5;color:#065F46;}
.stButton>button {
    background:linear-gradient(135deg,#6366F1,#8B5CF6);
    color:white;border:none;border-radius:8px;font-weight:600;
}
</style>""", unsafe_allow_html=True)

SECTOR_EMOJI = {"financeiro":"💰","logistica":"🚚","comercial":"🤝","juridico":"⚖️","geral":"📋"}
PRIO_EMOJI   = {"urgente":"🔴","alta":"🟠","media":"🟡","baixa":"🟢"}
ACTION_LABELS= {"responder":"✅ IA Respondeu","pedir_info":"❓ Aguardando","escalar":"👤 Humano"}

def pill(text, cls):
    return f'<span class="pill pill-{cls}">{text.capitalize()}</span>'

# ── Header ────────────────────────────────────────────────────────────────────
st.markdown("# 📋 Gestão de Protocolos")
st.markdown("Visualize, filtre e gerencie todos os atendimentos registrados.")

# ── Filters ───────────────────────────────────────────────────────────────────
col1, col2, col3, col4 = st.columns([2, 2, 2, 1])
with col1:
    sector_filter = st.selectbox(
        "Setor", ["Todos","financeiro","logistica","comercial","juridico","geral"]
    )
with col2:
    status_filter = st.selectbox("Status", ["Todos","aberto","fechado"])
with col3:
    search_term = st.text_input("🔍 Buscar cliente / protocolo", placeholder="Ex: TechVision")
with col4:
    st.markdown("<br>", unsafe_allow_html=True)
    if st.button("🔄 Atualizar", use_container_width=True):
        st.rerun()

# ── Load protocols ────────────────────────────────────────────────────────────
protocols = get_protocols(
    sector=sector_filter if sector_filter != "Todos" else None,
    status=status_filter if status_filter != "Todos" else None,
)

if search_term:
    st._lower = search_term.lower()
    protocols = [
        p for p in protocols
        if search_term.lower() in (p.get("client_name","") + p.get("protocol_id","")).lower()
    ]

# ── Summary row ───────────────────────────────────────────────────────────────
total  = len(protocols)
aberto = sum(1 for p in protocols if p.get("status") == "aberto")
fechado= total - aberto

m1, m2, m3 = st.columns(3)
m1.metric("Total filtrado", total)
m2.metric("🟡 Em aberto",  aberto)
m3.metric("✅ Fechados",    fechado)

st.markdown("---")

# ── Protocol list ─────────────────────────────────────────────────────────────
if not protocols:
    st.info("Nenhum protocolo encontrado com os filtros aplicados.")
else:
    for p in protocols:
        sector   = p.get("sector","geral")
        priority = p.get("priority","media")
        status   = p.get("status","aberto")
        action   = p.get("action","responder")
        prid     = p.get("protocol_id","")

        # Parse SLA
        try:
            deadline = datetime.fromisoformat(p.get("sla_deadline",""))
            now      = datetime.now()
            sla_ok   = now <= deadline if status == "aberto" else True
            sla_str  = deadline.strftime("%d/%m %H:%M")
            sla_icon = "✅" if sla_ok else "🔴"
        except Exception:
            sla_str  = "N/D"
            sla_icon = "⚪"
            sla_ok   = True

        # Created at
        try:
            created = datetime.fromisoformat(p.get("created_at","")).strftime("%d/%m/%Y %H:%M")
        except Exception:
            created = "—"

        with st.expander(
            f"{SECTOR_EMOJI.get(sector,'📋')} {prid}  |  "
            f"{p.get('client_name','Anônimo')}  |  "
            f"{PRIO_EMOJI.get(priority,'⚪')} {priority.capitalize()}  |  "
            f"{'🔴 ABERTO' if status=='aberto' else '✅ FECHADO'}"
        ):
            c1, c2, c3 = st.columns([3, 3, 2])

            with c1:
                st.markdown(f"""
**🏢 Cliente:** {p.get('client_name','—')}  
**📄 CNPJ:** `{p.get('cnpj','—')}`  
**🗂️ Protocolo:** `{prid}`  
**📅 Abertura:** {created}
""")
            with c2:
                st.markdown(
                    f"**Setor:** {pill(sector, sector)} "
                    f"**Prioridade:** {pill(priority, priority)} "
                    f"**Status:** {pill(status, status)}",
                    unsafe_allow_html=True,
                )
                st.markdown(f"""
**🎯 Intenção:** {p.get('intent','—')}  
**⚙️ Ação:** {ACTION_LABELS.get(action, action)}  
**{sla_icon} SLA Deadline:** {sla_str}  
**🔧 Resolvido por:** {p.get('resolved_by','—').capitalize()}
""")
            with c3:
                if status == "aberto":
                    if st.button("✅ Fechar protocolo", key=f"close_{prid}"):
                        update_protocol_status(prid, "fechado")
                        st.success(f"Protocolo {prid} fechado!")
                        st.rerun()
                else:
                    if st.button("🔄 Reabrir", key=f"reopen_{prid}"):
                        update_protocol_status(prid, "aberto")
                        st.warning(f"Protocolo {prid} reaberto.")
                        st.rerun()

            # Messages
            msgs = get_messages(prid)
            if msgs:
                st.markdown("**💬 Histórico de Mensagens:**")
                for m in msgs:
                    role = "🧑 Cliente" if m["role"] == "user" else "🤖 IA"
                    try:
                        ts = datetime.fromisoformat(m["timestamp"]).strftime("%d/%m %H:%M")
                    except Exception:
                        ts = ""
                    bg = "#2D3748" if m["role"] == "user" else "#1A2744"
                    st.markdown(
                        f'<div style="background:{bg};border-radius:8px;padding:10px 14px;'
                        f'margin:4px 0;font-size:.88rem;">'
                        f'<b style="color:#94A3B8;">{role}</b> '
                        f'<span style="color:#475569;font-size:.78rem;">{ts}</span><br>'
                        f'<span style="color:#E2E8F0;">{m["content"]}</span></div>',
                        unsafe_allow_html=True,
                    )
            else:
                st.caption("Nenhuma mensagem registrada para este protocolo.")

            if p.get("summary"):
                st.markdown(f"**📝 Resumo:** {p['summary']}")

# ── Footer ─────────────────────────────────────────────────────────────────────
st.markdown("---")
st.markdown(
    "<p style='text-align:center;color:#475569;font-size:.8rem;'>"
    "AI Customer Support Orchestrator · Projeto Acadêmico · Powered by Groq + LLaMA 3.1"
    "</p>",
    unsafe_allow_html=True,
)
