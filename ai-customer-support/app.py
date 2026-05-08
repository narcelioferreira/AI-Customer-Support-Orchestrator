import streamlit as st
import os
import sys

# ── Bootstrap ─────────────────────────────────────────────────────────────────
sys.path.insert(0, os.path.dirname(__file__))
from dotenv import load_dotenv
load_dotenv()

from database import init_db, get_client, create_protocol, add_message, get_messages
from orchestrator import orchestrate
from seed import seed

# ── Page Config ───────────────────────────────────────────────────────────────
st.set_page_config(
    page_title="AI Customer Support Orchestrator",
    page_icon="🧠",
    layout="wide",
    initial_sidebar_state="expanded",
)

# ── Init ──────────────────────────────────────────────────────────────────────
init_db()
seed()

# ── CSS ───────────────────────────────────────────────────────────────────────
st.markdown("""
<style>
/* ── Global ── */
[data-testid="stAppViewContainer"] { background: #0F172A; }
[data-testid="stSidebar"] { background: #1E293B !important; border-right: 1px solid #334155; }
h1,h2,h3,h4 { color: #F1F5F9 !important; }
p, label, .stMarkdown { color: #CBD5E1 !important; }

/* ── Metric cards ── */
[data-testid="metric-container"] {
    background: #1E293B; border: 1px solid #334155;
    border-radius: 12px; padding: 16px;
}

/* ── Buttons ── */
.stButton > button {
    background: linear-gradient(135deg, #6366F1, #8B5CF6);
    color: white; border: none; border-radius: 8px;
    font-weight: 600; padding: 8px 20px;
    transition: all .2s;
}
.stButton > button:hover { opacity: .85; transform: translateY(-1px); }

/* ── Chat bubbles ── */
.bubble-user {
    background: linear-gradient(135deg, #6366F1, #4F46E5);
    color: white; border-radius: 18px 18px 4px 18px;
    padding: 12px 16px; margin: 6px 0 6px 15%;
    display: inline-block; max-width: 85%; font-size: .93rem;
}
.bubble-ai {
    background: #1E293B; border: 1px solid #334155;
    color: #E2E8F0; border-radius: 18px 18px 18px 4px;
    padding: 12px 16px; margin: 6px 15% 6px 0;
    display: inline-block; max-width: 85%; font-size: .93rem;
}
.bubble-wrap-user { text-align: right; }
.bubble-wrap-ai   { text-align: left; }

/* ── Tag pills ── */
.pill {
    display: inline-block; padding: 3px 10px;
    border-radius: 99px; font-size: .75rem;
    font-weight: 600; letter-spacing: .3px;
}
.pill-financeiro { background:#FEF3C7; color:#92400E; }
.pill-logistica  { background:#DBEAFE; color:#1E40AF; }
.pill-comercial  { background:#D1FAE5; color:#065F46; }
.pill-juridico   { background:#FEE2E2; color:#991B1B; }
.pill-geral      { background:#EDE9FE; color:#5B21B6; }
.pill-urgente    { background:#FEE2E2; color:#991B1B; }
.pill-alta       { background:#FEF3C7; color:#92400E; }
.pill-media      { background:#DBEAFE; color:#1E40AF; }
.pill-baixa      { background:#D1FAE5; color:#065F46; }

/* ── Protocol card ── */
.proto-card {
    background: #1E293B; border: 1px solid #334155;
    border-radius: 12px; padding: 14px 18px; margin: 8px 0;
}

/* ── Input override ── */
textarea, input[type="text"] {
    background: #1E293B !important; color: #F1F5F9 !important;
    border: 1px solid #475569 !important; border-radius: 8px !important;
}
</style>
""", unsafe_allow_html=True)

# ── Helpers ───────────────────────────────────────────────────────────────────
SECTOR_EMOJI  = {"financeiro":"💰","logistica":"🚚","comercial":"🤝","juridico":"⚖️","geral":"📋"}
ACTION_LABELS = {"responder":"✅ Respondido pela IA","pedir_info":"❓ Aguardando info","escalar":"👤 Escalado para humano"}
PRIO_EMOJI    = {"urgente":"🔴","alta":"🟠","media":"🟡","baixa":"🟢"}

def pill(text, cls):
    return f'<span class="pill pill-{text}">{text.capitalize()}</span>'

# ── Sidebar ───────────────────────────────────────────────────────────────────
with st.sidebar:
    st.markdown("## 🧠 AI Orchestrator")
    st.markdown("---")

    # API key
    api_key = st.text_input(
        "🔑 Groq API Key",
        value=os.getenv("GROQ_API_KEY", ""),
        type="password",
        help="Obtenha grátis em console.groq.com",
    )
    if api_key:
        os.environ["GROQ_API_KEY"] = api_key

    st.markdown("---")

    # CNPJ lookup
    st.markdown("#### 🏢 Identificação do Cliente")
    cnpj_input = st.text_input(
        "CNPJ",
        placeholder="12.345.678/0001-90",
        key="cnpj_input",
    )

    DEMO_CNPJS = {
        "TechVision (Enterprise)": "12.345.678/0001-90",
        "Distribuidora Omega":     "98.765.432/0001-10",
        "Indústria Alfa":          "11.222.333/0001-44",
        "Grupo Sigma":             "33.444.555/0001-22",
        "Anônimo (sem cadastro)":  "",
    }
    demo_label = st.selectbox("🎭 Demo rápido", list(DEMO_CNPJS.keys()))
    if st.button("Carregar cliente demo"):
        st.session_state["cnpj_input"] = DEMO_CNPJS[demo_label]
        st.rerun()

    # Resolve client
    client_info = None
    if cnpj_input:
        client_info = get_client(cnpj_input)
        if client_info:
            st.success(f"✅ {client_info['name']}")
            st.caption(f"Segmento: **{client_info['segment']}** | Contratos: **{len(client_info['contracts'])}**")
        else:
            st.warning("⚠️ CNPJ não encontrado")

    st.markdown("---")
    st.markdown("#### 🔗 Navegação")
    st.page_link("app.py",               label="💬 Webchat",   icon="💬")
    st.page_link("pages/1_dashboard.py", label="📊 Dashboard", icon="📊")
    st.page_link("pages/2_protocols.py", label="📋 Protocolos",icon="📋")

    st.markdown("---")
    st.markdown(
        "<div style='color:#64748B;font-size:.75rem;'>"
        "Powered by <b>Groq + LLaMA 3.1</b><br>"
        "Projeto Acadêmico · 2025"
        "</div>",
        unsafe_allow_html=True,
    )

# ── Main Area ─────────────────────────────────────────────────────────────────
st.markdown("# 💬 Atendimento Inteligente")
st.markdown("Descreva sua solicitação abaixo. A IA classificará e responderá automaticamente.")

# ── Session state ─────────────────────────────────────────────────────────────
if "messages"     not in st.session_state: st.session_state.messages     = []
if "protocol_id"  not in st.session_state: st.session_state.protocol_id  = None
if "last_output"  not in st.session_state: st.session_state.last_output  = None

# ── Chat History ──────────────────────────────────────────────────────────────
chat_area = st.container()
with chat_area:
    if not st.session_state.messages:
        st.markdown("""
        <div style="text-align:center;padding:40px 20px;color:#475569;">
            <div style="font-size:3rem;">🤖</div>
            <h3 style="color:#94A3B8!important;">Olá! Como posso ajudar?</h3>
            <p>Digite sua mensagem abaixo ou escolha um exemplo rápido.</p>
        </div>
        """, unsafe_allow_html=True)
    else:
        for msg in st.session_state.messages:
            if msg["role"] == "user":
                st.markdown(
                    f'<div class="bubble-wrap-user"><div class="bubble-user">{msg["content"]}</div></div>',
                    unsafe_allow_html=True,
                )
            else:
                st.markdown(
                    f'<div class="bubble-wrap-ai"><div class="bubble-ai">{msg["content"]}</div></div>',
                    unsafe_allow_html=True,
                )

# ── Current Protocol Info ─────────────────────────────────────────────────────
if st.session_state.last_output and st.session_state.protocol_id:
    out = st.session_state.last_output
    cols = st.columns(4)
    cols[0].markdown(f"**Setor** {SECTOR_EMOJI.get(out.setor,'📋')}<br>{out.setor.capitalize()}", unsafe_allow_html=True)
    cols[1].markdown(f"**Intenção**<br>{out.intencao}", unsafe_allow_html=True)
    cols[2].markdown(f"**Prioridade** {PRIO_EMOJI.get(out.prioridade,'⚪')}<br>{out.prioridade.capitalize()}", unsafe_allow_html=True)
    cols[3].markdown(f"**Ação**<br>{ACTION_LABELS.get(out.acao, out.acao)}", unsafe_allow_html=True)
    st.caption(f"🗂️ Protocolo: `{st.session_state.protocol_id}`")

# ── Quick Examples ────────────────────────────────────────────────────────────
st.markdown("**Exemplos rápidos:**")
ex_cols = st.columns(4)
EXAMPLES = [
    ("💰 Boleto vencido",    "Preciso prorrogar meu boleto que venceu ontem, valor de R$ 3.200"),
    ("🚚 Rastrear pedido",   "Meu pedido #4521 deveria ter chegado há 3 dias e não apareceu"),
    ("📄 Erro na NF",        "A nota fiscal emitida tem o valor errado, cobrou R$ 500 a mais"),
    ("⚖️ Cancelar contrato", "Quero fazer o distrato do contrato CT-2024-001 antes do prazo"),
]
for i, (label, text) in enumerate(EXAMPLES):
    with ex_cols[i]:
        if st.button(label, use_container_width=True):
            st.session_state["_prefill"] = text
            st.rerun()

# ── Chat Input ────────────────────────────────────────────────────────────────
prefill = st.session_state.pop("_prefill", "")
user_input = st.chat_input("Digite sua mensagem...", key="chat_input")

# Use prefill if no direct input
if prefill and not user_input:
    user_input = prefill

if user_input:
    if not os.getenv("GROQ_API_KEY"):
        st.error("⚠️ Configure sua Groq API Key na barra lateral para começar.")
        st.stop()

    st.session_state.messages.append({"role": "user", "content": user_input})

    with st.spinner("🧠 Analisando e processando..."):
        history = st.session_state.messages[:-1]
        out = orchestrate(
            user_message=user_input,
            client_info=client_info,
            history=history,
        )

        client_name = client_info["name"] if client_info else "Anônimo"
        cnpj = client_info["cnpj"] if client_info else "00.000.000/0000-00"

        # Create or update protocol
        if not st.session_state.protocol_id:
            pid = create_protocol(
                cnpj=cnpj,
                client_name=client_name,
                sector=out.setor,
                intent=out.intencao,
                priority=out.prioridade,
                action=out.acao,
                summary=user_input[:200],
                ai_response=out.resposta,
            )
            st.session_state.protocol_id = pid
            add_message(pid, "user", user_input)
        else:
            add_message(st.session_state.protocol_id, "user", user_input)

        add_message(st.session_state.protocol_id, "assistant", out.resposta)

    st.session_state.messages.append({"role": "assistant", "content": out.resposta})
    st.session_state.last_output = out
    st.rerun()

# ── Reset button ──────────────────────────────────────────────────────────────
if st.session_state.messages:
    st.markdown("---")
    col1, col2 = st.columns([6, 1])
    with col2:
        if st.button("🔄 Nova conversa"):
            st.session_state.messages    = []
            st.session_state.protocol_id = None
            st.session_state.last_output = None
            st.rerun()
