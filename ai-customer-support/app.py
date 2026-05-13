import streamlit as st
import os, sys
from datetime import datetime

sys.path.insert(0, os.path.dirname(__file__))
from dotenv import load_dotenv
load_dotenv()

from database import init_db, get_client, create_protocol, add_message
from orchestrator import orchestrate
from seed import seed

# ── Page config ───────────────────────────────────────────────────────────────
st.set_page_config(
    page_title="Suporte Inteligente · AI Orchestrator",
    page_icon="🤖",
    layout="wide",
    initial_sidebar_state="collapsed",
)
init_db()
seed()

# ── Helpers ───────────────────────────────────────────────────────────────────
SECTOR_COLORS = {
    "financeiro": ("#FEF3C7", "#92400E", "💰"),
    "logistica":  ("#DBEAFE", "#1E40AF", "🚚"),
    "comercial":  ("#D1FAE5", "#065F46", "🤝"),
    "juridico":   ("#FEE2E2", "#991B1B", "⚖️"),
    "geral":      ("#EDE9FE", "#5B21B6", "📋"),
}
PRIORITY_COLORS = {
    "urgente": ("#FEE2E2", "#991B1B", "🔴"),
    "alta":    ("#FEF3C7", "#92400E", "🟠"),
    "media":   ("#DBEAFE", "#1E40AF", "🟡"),
    "baixa":   ("#D1FAE5", "#065F46", "🟢"),
}
ACTION_LABELS = {
    "responder":  ("✅", "Resolvido pela IA"),
    "pedir_info": ("❓", "Aguardando informação"),
    "escalar":    ("👤", "Escalado para humano"),
}
DEMO_SCENARIOS = [
    {"label": "💰 Boleto vencido",      "cnpj": "12.345.678/0001-90", "msg": "Olá, meu boleto venceu ontem no valor de R$ 3.200. Preciso de uma prorrogação urgente."},
    {"label": "🚚 Pedido atrasado",     "cnpj": "98.765.432/0001-10", "msg": "Meu pedido #4521 estava previsto para chegar há 3 dias e não apareceu. Podem verificar?"},
    {"label": "📄 Erro na nota fiscal", "cnpj": "11.222.333/0001-44", "msg": "A nota fiscal desta semana veio com o valor errado. Cobrou R$ 500 a mais do que o contrato prevê."},
    {"label": "⚖️ Distrato contrato",   "cnpj": "33.444.555/0001-22", "msg": "Precisamos formalizar o distrato do contrato CT-2024-001 antes do vencimento."},
    {"label": "🤝 Desconto não aplicado","cnpj": "66.777.888/0001-33", "msg": "O vendedor prometeu 15% de desconto e isso não foi aplicado no último pedido."},
    {"label": "🔍 Rastrear entrega",    "cnpj": "55.666.777/0001-88", "msg": "Preciso do código de rastreamento do pedido feito na semana passada."},
]
CLIENT_OPTIONS = {
    "👤 Anônimo (sem cadastro)":   "",
    "TechVision Enterprise":       "12.345.678/0001-90",
    "Distribuidora Omega":         "98.765.432/0001-10",
    "Indústria Alfa S/A":          "11.222.333/0001-44",
    "Grupo Sigma Enterprise":      "33.444.555/0001-22",
    "Varejão Norte":               "66.777.888/0001-33",
    "Startap Inovações":           "77.888.999/0001-66",
}

# ── Session state ─────────────────────────────────────────────────────────────
for k, v in {"messages": [], "protocol_id": None, "last_output": None, "session_client": None}.items():
    if k not in st.session_state:
        st.session_state[k] = v

# ─────────────────────────────────────────────────────────────────────────────
# CSS  — design iMessage/WhatsApp para o chat, sidebar escura
# ─────────────────────────────────────────────────────────────────────────────
st.markdown("""
<style>
/* ── Reset global ── */
*, *::before, *::after { box-sizing: border-box; }
[data-testid="stHeader"]  { display: none !important; }
[data-testid="stSidebar"] { display: none !important; }
.block-container { padding: 0 !important; max-width: 100% !important; }
section[data-testid="stMain"] > div { padding: 0 !important; }
[data-testid="stAppViewContainer"] { background: #F1F5F9; }

/* ── Coluna esquerda (sidebar custom) ── */
div[data-testid="column"]:first-child > div {
    background: #0F172A !important;
    height: 100vh;
    overflow-y: auto;
    padding: 0 !important;
}
div[data-testid="column"]:first-child > div::-webkit-scrollbar { width: 3px; }
div[data-testid="column"]:first-child > div::-webkit-scrollbar-thumb { background: #334155; }

/* ── Coluna direita (chat) ── */
div[data-testid="column"]:last-child > div {
    background: #F8FAFC !important;
    height: 100vh;
    overflow: hidden;
    padding: 0 !important;
    display: flex;
    flex-direction: column;
}

/* ── Textos gerais na sidebar ── */
div[data-testid="column"]:first-child label,
div[data-testid="column"]:first-child p,
div[data-testid="column"]:first-child .stMarkdown p,
div[data-testid="column"]:first-child span {
    color: #94A3B8 !important;
    font-size: 12px !important;
}
div[data-testid="column"]:first-child h1,
div[data-testid="column"]:first-child h2,
div[data-testid="column"]:first-child h3 {
    color: #F1F5F9 !important;
}

/* ── Inputs e selects na sidebar ── */
div[data-testid="column"]:first-child input,
div[data-testid="column"]:first-child [data-baseweb="input"] input,
div[data-testid="column"]:first-child [data-baseweb="select"] div {
    background: #1E293B !important;
    color: #CBD5E1 !important;
    border-color: #334155 !important;
    font-size: 12px !important;
}

/* ── Botões na sidebar ── */
div[data-testid="column"]:first-child .stButton > button {
    background: #1E293B !important;
    color: #94A3B8 !important;
    border: 1px solid #334155 !important;
    border-radius: 8px !important;
    font-size: 12px !important;
    font-weight: 500 !important;
    padding: 6px 10px !important;
    text-align: left !important;
    justify-content: flex-start !important;
    width: 100%;
    transition: all .15s !important;
}
div[data-testid="column"]:first-child .stButton > button:hover {
    background: #1E3A5F !important;
    color: #F1F5F9 !important;
    border-color: #6366F1 !important;
}

/* ── Botão "Nova conversa" ── */
.reset-btn .stButton > button {
    background: transparent !important;
    border-color: #EF4444 !important;
    color: #EF4444 !important;
}
.reset-btn .stButton > button:hover {
    background: #FEE2E2 !important;
    color: #991B1B !important;
}

/* ── page_link na sidebar ── */
div[data-testid="column"]:first-child [data-testid="stPageLink"] a {
    color: #64748B !important;
    font-size: 12px !important;
    text-decoration: none;
}
div[data-testid="column"]:first-child [data-testid="stPageLink"] a:hover {
    color: #F1F5F9 !important;
}

/* ── Chat input ── */
[data-testid="stChatInput"] {
    background: white !important;
    border-top: 1px solid #E2E8F0 !important;
    padding: 12px 20px !important;
}
[data-testid="stChatInput"] textarea {
    background: #F8FAFC !important;
    border: 1.5px solid #E2E8F0 !important;
    border-radius: 24px !important;
    color: #1E293B !important;
    font-size: 13.5px !important;
    padding: 10px 18px !important;
}
[data-testid="stChatInput"] textarea:focus {
    border-color: #6366F1 !important;
    box-shadow: 0 0 0 3px rgba(99,102,241,.12) !important;
    background: white !important;
}

/* ── Chat message area ── */
[data-testid="stChatMessageContent"] p {
    font-size: 13.5px !important;
    line-height: 1.6 !important;
    margin: 0 !important;
}
[data-testid="stChatMessage"] {
    padding: 4px 20px !important;
    background: transparent !important;
}

/* assistente */
[data-testid="stChatMessage"]:has([data-testid="chatAvatarIcon-assistant"]) [data-testid="stChatMessageContent"] {
    background: white !important;
    border: 1px solid #E2E8F0 !important;
    border-radius: 16px 16px 16px 4px !important;
    box-shadow: 0 1px 3px rgba(0,0,0,.06) !important;
    color: #1E293B !important;
    padding: 12px 16px !important;
}

/* usuário */
[data-testid="stChatMessage"]:has([data-testid="chatAvatarIcon-user"]) [data-testid="stChatMessageContent"] {
    background: linear-gradient(135deg, #6366F1, #4F46E5) !important;
    border-radius: 16px 16px 4px 16px !important;
    color: white !important;
    padding: 12px 16px !important;
}
[data-testid="stChatMessage"]:has([data-testid="chatAvatarIcon-user"]) [data-testid="stChatMessageContent"] p {
    color: white !important;
}

/* avatares */
[data-testid="chatAvatarIcon-assistant"] {
    background: linear-gradient(135deg, #6366F1, #8B5CF6) !important;
    border-radius: 50% !important;
}
[data-testid="chatAvatarIcon-user"] {
    background: #1E293B !important;
    border-radius: 50% !important;
}

/* ── Protocol / info cards ── */
.proto-card {
    background: white;
    border: 1px solid #E2E8F0;
    border-left: 3px solid #6366F1;
    border-radius: 10px;
    padding: 10px 14px;
    margin: 4px 20px 8px 72px;
    box-shadow: 0 1px 2px rgba(0,0,0,.05);
    font-size: 12px;
}
.proto-title {
    font-size: 10px; font-weight: 700; letter-spacing: .4px;
    text-transform: uppercase; color: #94A3B8; margin-bottom: 6px;
}
.proto-tags { display: flex; flex-wrap: wrap; gap: 4px; margin-bottom: 5px; }
.proto-tag {
    font-size: 10px; font-weight: 600; padding: 2px 8px;
    border-radius: 99px; border: 1px solid;
}
.proto-id { font-size: 10px; color: #94A3B8; font-family: monospace; }

/* ── Chat header ── */
.chat-header {
    background: white;
    border-bottom: 1px solid #E2E8F0;
    padding: 12px 20px;
    display: flex;
    align-items: center;
    justify-content: space-between;
    flex-shrink: 0;
    box-shadow: 0 1px 3px rgba(0,0,0,.05);
}
.agent-info { display: flex; align-items: center; gap: 12px; }
.agent-avatar {
    width: 40px; height: 40px; border-radius: 50%;
    background: linear-gradient(135deg, #6366F1, #8B5CF6);
    display: flex; align-items: center; justify-content: center;
    font-size: 20px; flex-shrink: 0;
}
.agent-name   { font-size: 14px; font-weight: 600; color: #1E293B; margin: 0; }
.agent-status { font-size: 11px; color: #22C55E; display: flex; align-items: center; gap: 4px; margin: 0; }
.status-dot   { width: 6px; height: 6px; border-radius: 50%; background: #22C55E; flex-shrink:0; }
.header-badges { display: flex; gap: 5px; align-items: center; }
.hbadge {
    font-size: 10px; font-weight: 600; padding: 3px 9px;
    border-radius: 99px; border: 1px solid;
}

/* ── Welcome screen ── */
.welcome-wrap {
    flex: 1;
    display: flex; flex-direction: column;
    align-items: center; justify-content: center;
    padding: 40px 24px; text-align: center;
}
.welcome-icon  { font-size: 52px; margin-bottom: 16px; }
.welcome-title { font-size: 20px; font-weight: 600; color: #1E293B; margin-bottom: 8px; }
.welcome-sub   { font-size: 13px; color: #64748B; max-width: 400px; line-height: 1.6; }

/* ── Sidebar brand header ── */
.brand-block {
    padding: 18px 16px 14px;
    border-bottom: 1px solid #1E293B;
}
.brand-row { display: flex; align-items: center; gap: 8px; margin-bottom: 3px; }
.brand-pulse {
    width: 9px; height: 9px; border-radius: 50%;
    background: #22C55E; box-shadow: 0 0 6px #22C55E;
    animation: pulse 2s infinite; flex-shrink: 0;
}
@keyframes pulse { 0%,100%{opacity:1} 50%{opacity:.4} }
.brand-name { font-size: 14px !important; font-weight: 700 !important; color: #F1F5F9 !important; letter-spacing: -.2px; }
.brand-sub  { font-size: 10px !important; color: #475569 !important; margin-left: 17px; }

/* ── Client info card ── */
.client-card {
    background: #1E293B;
    border: 1px solid #334155;
    border-radius: 10px;
    padding: 10px 12px;
    margin-top: 8px;
}
.cn { font-size: 13px !important; font-weight: 600 !important; color: #F1F5F9 !important; margin: 0 0 2px; }
.cm { font-size: 11px !important; color: #64748B !important; margin: 0; line-height: 1.5; }
.cbadge {
    display: inline-block; font-size: 9px !important; font-weight: 700 !important;
    padding: 2px 7px; border-radius: 99px; margin-top: 5px; letter-spacing: .3px;
}
.be { background:#4F46E5; color:#EDE9FE !important; }
.bm { background:#0F766E; color:#CCFBF1 !important; }
.bs { background:#92400E; color:#FEF3C7 !important; }

/* ── Divider ── */
.sdiv { border: none; border-top: 1px solid #1E293B; margin: 12px 0; }

/* ── Section label ── */
.slabel {
    font-size: 9px !important; font-weight: 700 !important;
    letter-spacing: .6px; text-transform: uppercase;
    color: #475569 !important; margin-bottom: 6px;
}
</style>
""", unsafe_allow_html=True)

# ─────────────────────────────────────────────────────────────────────────────
# LAYOUT  — sidebar | chat
# ─────────────────────────────────────────────────────────────────────────────
left, right = st.columns([1, 3], gap="small")

# ╔══════════════════════════════════════════════════════╗
# ║                  PAINEL ESQUERDO                     ║
# ╚══════════════════════════════════════════════════════╝
with left:
    # Brand
    st.markdown("""
    <div class="brand-block">
      <div class="brand-row">
        <div class="brand-pulse"></div>
        <span class="brand-name">AI Support Orchestrator</span>
      </div>
      <div class="brand-sub">Groq · LLaMA 3.1 · SQLite · RAG</div>
    </div>
    """, unsafe_allow_html=True)

    st.markdown('<div style="padding:12px 14px 0">', unsafe_allow_html=True)

    # API Key
    st.markdown('<div class="slabel">🔑 Groq API Key</div>', unsafe_allow_html=True)
    api_key = st.text_input(
        "api", value=os.getenv("GROQ_API_KEY", ""),
        type="password", placeholder="gsk_... · console.groq.com (grátis)",
        label_visibility="collapsed", key="api_key_in",
    )
    if api_key:
        os.environ["GROQ_API_KEY"] = api_key
        st.markdown('<div style="color:#22C55E;font-size:11px;margin-top:4px">✔ API Key configurada</div>', unsafe_allow_html=True)
    else:
        st.markdown('<div style="color:#EF4444;font-size:11px;margin-top:4px">⚠ Insira sua chave para conversar</div>', unsafe_allow_html=True)

    st.markdown('<hr class="sdiv">', unsafe_allow_html=True)

    # Client selector
    st.markdown('<div class="slabel">🏢 Simular como cliente</div>', unsafe_allow_html=True)
    sel = st.selectbox("cli", list(CLIENT_OPTIONS.keys()), label_visibility="collapsed", key="client_sel")
    cnpj = CLIENT_OPTIONS[sel]

    client_info = get_client(cnpj) if cnpj else None

    # Show client card
    if client_info:
        seg = client_info.get("segment", "")
        badge = "be" if seg == "Enterprise" else "bm" if seg == "Mid-Market" else "bs"
        cts = len(client_info.get("contracts", []))
        st.markdown(f"""
        <div class="client-card">
          <p class="cn">{client_info['name']}</p>
          <p class="cm">{client_info.get('cnpj','')}</p>
          <p class="cm">👤 {client_info.get('contact_name','')} &nbsp;·&nbsp; 📄 {cts} contrato(s)</p>
          <p class="cm">{client_info.get('email','')}</p>
          <span class="cbadge {badge}">{seg}</span>
        </div>
        """, unsafe_allow_html=True)

    st.markdown('<hr class="sdiv">', unsafe_allow_html=True)

    # Demo scenarios
    st.markdown('<div class="slabel">⚡ Cenários de demonstração</div>', unsafe_allow_html=True)
    for sc in DEMO_SCENARIOS:
        if st.button(sc["label"], key=f"sc_{sc['label']}", use_container_width=True):
            st.session_state.messages = []
            st.session_state.protocol_id = None
            st.session_state.last_output = None
            st.session_state.session_client = get_client(sc["cnpj"]) if sc["cnpj"] else None
            st.session_state["_fire"] = sc["msg"]
            st.rerun()

    st.markdown('<hr class="sdiv">', unsafe_allow_html=True)

    # Reset
    if st.session_state.messages:
        st.markdown('<div class="reset-btn">', unsafe_allow_html=True)
        if st.button("🔄 Nova conversa", use_container_width=True, key="reset_btn"):
            st.session_state.messages = []
            st.session_state.protocol_id = None
            st.session_state.last_output = None
            st.session_state.session_client = None
            st.rerun()
        st.markdown('</div>', unsafe_allow_html=True)

    # Nav
    st.markdown('<div class="slabel" style="margin-top:8px">🔗 Páginas</div>', unsafe_allow_html=True)
    st.page_link("pages/1_dashboard.py",  label="📊 Dashboard operacional")
    st.page_link("pages/2_protocols.py",  label="📋 Gestão de protocolos")
    st.page_link("pages/3_arquitetura.py",label="🏗️ Arquitetura")

    st.markdown('</div>', unsafe_allow_html=True)

# ╔══════════════════════════════════════════════════════╗
# ║                    ÁREA DE CHAT                      ║
# ╚══════════════════════════════════════════════════════╝
with right:
    out   = st.session_state.last_output
    eff_client = client_info or st.session_state.get("session_client")

    # Header badges
    if out:
        s_bg, s_fg, s_em = SECTOR_COLORS.get(out.setor, SECTOR_COLORS["geral"])
        p_bg, p_fg, p_em = PRIORITY_COLORS.get(out.prioridade, PRIORITY_COLORS["media"])
        a_em, a_lbl      = ACTION_LABELS.get(out.acao, ACTION_LABELS["responder"])
        badges_html = f"""
        <div class="header-badges">
          <span class="hbadge" style="background:{s_bg};color:{s_fg};border-color:{s_fg}50">{s_em} {out.setor.capitalize()}</span>
          <span class="hbadge" style="background:{p_bg};color:{p_fg};border-color:{p_fg}50">{p_em} {out.prioridade.capitalize()}</span>
          <span class="hbadge" style="background:#F1F5F9;color:#475569;border-color:#CBD5E1">{a_em} {a_lbl}</span>
          <span class="hbadge" style="background:#F1F5F9;color:#475569;border-color:#CBD5E1">🗂️ {st.session_state.protocol_id or '—'}</span>
        </div>
        """
    else:
        badges_html = '<div class="header-badges"><span class="hbadge" style="background:#F0FDF4;color:#15803D;border-color:#86EFAC">● Sistema online</span></div>'

    client_label = eff_client["name"] if eff_client else "Visitante"

    st.markdown(f"""
    <div class="chat-header">
      <div class="agent-info">
        <div class="agent-avatar">🤖</div>
        <div>
          <p class="agent-name">Assistente de Suporte · {client_label}</p>
          <p class="agent-status"><span class="status-dot"></span> IA ativa &nbsp;·&nbsp; resposta em ~3s</p>
        </div>
      </div>
      {badges_html}
    </div>
    """, unsafe_allow_html=True)

    # ── Mensagens ─────────────────────────────────────
    msgs = st.session_state.messages

    if not msgs:
        st.markdown("""
        <div class="welcome-wrap">
          <div class="welcome-icon">🤖</div>
          <div class="welcome-title">Como posso te ajudar hoje?</div>
          <div class="welcome-sub">
            Sou um assistente de suporte inteligente com IA. Descreva sua
            solicitação ou escolha um cenário de demo no painel ao lado.
          </div>
        </div>
        """, unsafe_allow_html=True)
    else:
        for msg in msgs:
            role = msg["role"]
            with st.chat_message(role, avatar="🤖" if role == "assistant" else "🧑"):
                st.markdown(msg["content"])

            # Protocol card logo após primeira resposta da IA
            if role == "assistant" and msg.get("proto"):
                p = msg["proto"]
                s_bg, s_fg, s_em = SECTOR_COLORS.get(p["setor"], SECTOR_COLORS["geral"])
                pr_bg, pr_fg, pr_em = PRIORITY_COLORS.get(p["prio"], PRIORITY_COLORS["media"])
                a_em2, a_lbl2 = ACTION_LABELS.get(p["acao"], ACTION_LABELS["responder"])
                st.markdown(f"""
                <div class="proto-card">
                  <div class="proto-title">🗂️ Protocolo registrado automaticamente</div>
                  <div class="proto-tags">
                    <span class="proto-tag" style="background:{s_bg};color:{s_fg};border-color:{s_fg}40">{s_em} {p['setor'].capitalize()}</span>
                    <span class="proto-tag" style="background:{pr_bg};color:{pr_fg};border-color:{pr_fg}40">{pr_em} {p['prio'].capitalize()}</span>
                    <span class="proto-tag" style="background:#F1F5F9;color:#475569;border-color:#E2E8F0">{a_em2} {a_lbl2}</span>
                  </div>
                  <div class="proto-id">🔖 {p['id']} &nbsp;·&nbsp; 🎯 {p['intent']}</div>
                </div>
                """, unsafe_allow_html=True)

    # ── Input ─────────────────────────────────────────
    user_input = st.chat_input("Digite sua mensagem…", key="main_input")

    # Scenario auto-fire
    fire = st.session_state.pop("_fire", None)
    if fire and not user_input:
        user_input = fire

    # ── Processar mensagem ────────────────────────────
    if user_input:
        if not os.getenv("GROQ_API_KEY"):
            st.error("⚠️ Configure sua Groq API Key no painel esquerdo para iniciar o atendimento.")
            st.stop()

        # Exibe mensagem do usuário imediatamente
        with st.chat_message("user", avatar="🧑"):
            st.markdown(user_input)
        st.session_state.messages.append({"role": "user", "content": user_input})

        # Thinking + resposta IA
        with st.chat_message("assistant", avatar="🤖"):
            with st.spinner("Analisando sua solicitação…"):
                eff = client_info or st.session_state.get("session_client")
                history = [{"role": m["role"], "content": m["content"]}
                           for m in st.session_state.messages[:-1]]
                output = orchestrate(
                    user_message=user_input,
                    client_info=eff,
                    history=history,
                )
            st.markdown(output.resposta)

        # Protocolo
        if not st.session_state.protocol_id:
            cname = eff["name"] if eff else "Anônimo"
            ccnpj = eff["cnpj"]  if eff else "00.000.000/0000-00"
            pid = create_protocol(
                cnpj=ccnpj, client_name=cname,
                sector=output.setor,    intent=output.intencao,
                priority=output.prioridade, action=output.acao,
                summary=user_input[:200], ai_response=output.resposta,
            )
            st.session_state.protocol_id = pid
            add_message(pid, "user", user_input)
        else:
            add_message(st.session_state.protocol_id, "user", user_input)

        add_message(st.session_state.protocol_id, "assistant", output.resposta)
        st.session_state.last_output = output

        proto_data = {
            "id":     st.session_state.protocol_id,
            "setor":  output.setor,
            "prio":   output.prioridade,
            "acao":   output.acao,
            "intent": output.intencao,
        }
        st.session_state.messages.append({
            "role": "assistant",
            "content": output.resposta,
            "proto": proto_data,
        })
        st.rerun()
