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
    page_title="AI Support Orchestrator",
    page_icon="🤖",
    layout="wide",
    initial_sidebar_state="expanded",
)
init_db()
seed()

# ── Constantes ────────────────────────────────────────────────────────────────
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
    "escalar":    ("👤", "Escalado p/ humano"),
}
DEMO_SCENARIOS = [
    {"label": "💰 Boleto vencido",        "cnpj": "12.345.678/0001-90", "msg": "Olá, meu boleto venceu ontem no valor de R$ 3.200. Preciso de uma prorrogação urgente."},
    {"label": "🚚 Pedido atrasado",       "cnpj": "98.765.432/0001-10", "msg": "Meu pedido #4521 estava previsto para chegar há 3 dias e não apareceu. Podem verificar?"},
    {"label": "📄 Erro na nota fiscal",   "cnpj": "11.222.333/0001-44", "msg": "A nota fiscal desta semana veio com valor errado. Cobrou R$ 500 a mais do que o contrato prevê."},
    {"label": "⚖️ Distrato de contrato",  "cnpj": "33.444.555/0001-22", "msg": "Precisamos formalizar o distrato do contrato CT-2024-001 antes do vencimento."},
    {"label": "🤝 Desconto não aplicado", "cnpj": "66.777.888/0001-33", "msg": "O vendedor prometeu 15% de desconto e isso não foi aplicado no último pedido."},
    {"label": "🔍 Rastrear entrega",      "cnpj": "55.666.777/0001-88", "msg": "Preciso do código de rastreamento do pedido feito na semana passada."},
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
for k, v in {
    "messages": [],
    "protocol_id": None,
    "last_output": None,
    "session_client": None,
}.items():
    if k not in st.session_state:
        st.session_state[k] = v

# ── CSS mínimo e confiável ────────────────────────────────────────────────────
st.markdown("""
<style>
/* Bolha do assistente */
[data-testid="stChatMessage"]:has([data-testid="chatAvatarIcon-assistant"])
  [data-testid="stChatMessageContent"] {
    background: #ffffff;
    border: 1px solid #E2E8F0;
    border-radius: 0px 16px 16px 16px;
    padding: 12px 16px;
    box-shadow: 0 1px 4px rgba(0,0,0,0.07);
}

/* Bolha do usuário */
[data-testid="stChatMessage"]:has([data-testid="chatAvatarIcon-user"])
  [data-testid="stChatMessageContent"] {
    background: linear-gradient(135deg, #6366F1, #4F46E5);
    border-radius: 16px 0px 16px 16px;
    padding: 12px 16px;
}
[data-testid="stChatMessage"]:has([data-testid="chatAvatarIcon-user"])
  [data-testid="stChatMessageContent"] p {
    color: #ffffff !important;
}

/* Card de protocolo */
.proto-card {
    background: #F8FAFF;
    border-left: 3px solid #6366F1;
    border-radius: 8px;
    padding: 10px 14px;
    margin: 4px 0 12px 52px;
    font-size: 12px;
}
.proto-row { display: flex; flex-wrap: wrap; gap: 5px; margin-bottom: 5px; }
.ptag {
    font-size: 10px; font-weight: 600;
    padding: 2px 8px; border-radius: 99px; border: 1px solid;
}
.proto-id { font-size: 10px; color: #94A3B8; font-family: monospace; }

/* Input de chat */
[data-testid="stChatInput"] textarea {
    border-radius: 24px !important;
    border: 1.5px solid #E2E8F0 !important;
    font-size: 14px !important;
}
[data-testid="stChatInput"] textarea:focus {
    border-color: #6366F1 !important;
    box-shadow: 0 0 0 3px rgba(99,102,241,.1) !important;
}
</style>
""", unsafe_allow_html=True)

# ╔══════════════════════════════════════════════════════╗
# ║                    SIDEBAR NATIVA                    ║
# ╚══════════════════════════════════════════════════════╝
with st.sidebar:
    st.markdown("## 🤖 AI Support Orchestrator")
    st.caption("Powered by Groq · LLaMA 3.1 · SQLite · RAG")
    st.divider()

    # ── API Key ──────────────────────────────────────
    st.markdown("#### 🔑 Groq API Key")
    api_key = st.text_input(
        "key", value=os.getenv("GROQ_API_KEY", ""),
        type="password",
        placeholder="gsk_... · console.groq.com (grátis)",
        label_visibility="collapsed",
    )
    if api_key:
        os.environ["GROQ_API_KEY"] = api_key
        st.success("✔ API Key configurada", icon="🔑")
    else:
        st.warning("Insira sua chave para conversar", icon="⚠️")

    st.divider()

    # ── Selecionar cliente ───────────────────────────
    st.markdown("#### 🏢 Simular como cliente")
    sel = st.selectbox("cli", list(CLIENT_OPTIONS.keys()), label_visibility="collapsed")
    cnpj = CLIENT_OPTIONS[sel]
    client_info = get_client(cnpj) if cnpj else None

    if client_info:
        seg = client_info.get("segment", "")
        cts = len(client_info.get("contracts", []))
        st.info(
            f"**{client_info['name']}**\n\n"
            f"CNPJ: `{client_info['cnpj']}`\n\n"
            f"👤 {client_info.get('contact_name', '')}  \n"
            f"📄 {cts} contrato(s)  \n"
            f"🏷️ {seg}"
        )
    else:
        st.caption("Nenhum cliente selecionado — atendimento anônimo.")

    st.divider()

    # ── Cenários de demo ─────────────────────────────
    st.markdown("#### ⚡ Cenários de demonstração")
    st.caption("Clique para disparar uma mensagem de exemplo:")

    for sc in DEMO_SCENARIOS:
        if st.button(sc["label"], key=f"sc_{sc['label']}", use_container_width=True):
            st.session_state.messages = []
            st.session_state.protocol_id = None
            st.session_state.last_output = None
            st.session_state.session_client = get_client(sc["cnpj"]) if sc["cnpj"] else None
            st.session_state["_fire"] = sc["msg"]
            st.rerun()

    st.divider()

    # ── Controles ────────────────────────────────────
    if st.session_state.messages:
        if st.button("🔄 Nova conversa", use_container_width=True, type="secondary"):
            st.session_state.messages = []
            st.session_state.protocol_id = None
            st.session_state.last_output = None
            st.session_state.session_client = None
            st.rerun()

    st.divider()

    # ── Navegação ────────────────────────────────────
    st.markdown("#### 🔗 Navegação")
    st.page_link("pages/1_dashboard.py",   label="📊 Dashboard operacional")
    st.page_link("pages/2_protocols.py",   label="📋 Gestão de protocolos")
    st.page_link("pages/3_arquitetura.py", label="🏗️ Arquitetura do sistema")

    st.divider()
    st.caption("Projeto Acadêmico · 2025\nAI Customer Support Orchestrator")

# ╔══════════════════════════════════════════════════════╗
# ║                    ÁREA PRINCIPAL                    ║
# ╚══════════════════════════════════════════════════════╝

# ── Header dinâmico ───────────────────────────────────
out = st.session_state.last_output
eff_client = client_info or st.session_state.get("session_client")
client_label = eff_client["name"] if eff_client else "Visitante"

if out:
    s_bg, s_fg, s_em = SECTOR_COLORS.get(out.setor, SECTOR_COLORS["geral"])
    p_bg, p_fg, p_em = PRIORITY_COLORS.get(out.prioridade, PRIORITY_COLORS["media"])
    a_em, a_lbl = ACTION_LABELS.get(out.acao, ACTION_LABELS["responder"])

    col_title, col_b1, col_b2, col_b3 = st.columns([3, 1, 1, 1])
    col_title.markdown(f"### 🤖 Assistente de Suporte &nbsp; · &nbsp; `{client_label}`")
    col_b1.markdown(
        f'<div style="background:{s_bg};color:{s_fg};border:1px solid {s_fg}40;'
        f'border-radius:99px;padding:4px 10px;text-align:center;font-size:12px;font-weight:600;margin-top:14px">'
        f'{s_em} {out.setor.capitalize()}</div>', unsafe_allow_html=True)
    col_b2.markdown(
        f'<div style="background:{p_bg};color:{p_fg};border:1px solid {p_fg}40;'
        f'border-radius:99px;padding:4px 10px;text-align:center;font-size:12px;font-weight:600;margin-top:14px">'
        f'{p_em} {out.prioridade.capitalize()}</div>', unsafe_allow_html=True)
    col_b3.markdown(
        f'<div style="background:#F1F5F9;color:#475569;border:1px solid #CBD5E1;'
        f'border-radius:99px;padding:4px 10px;text-align:center;font-size:12px;font-weight:600;margin-top:14px">'
        f'{a_em} {a_lbl}</div>', unsafe_allow_html=True)
else:
    st.markdown(f"### 🤖 Assistente de Suporte &nbsp; · &nbsp; `{client_label}`")
    st.caption("🟢 IA online · Resposta em ~3s · Classificação automática + RAG por setor")

st.divider()

# ── Tela de boas-vindas ───────────────────────────────
if not st.session_state.messages:
    st.markdown("""
    <div style="text-align:center; padding: 40px 20px;">
        <div style="font-size:56px; margin-bottom:16px">🤖</div>
        <h2 style="color:#1E293B; margin-bottom:8px">Como posso te ajudar hoje?</h2>
        <p style="color:#64748B; font-size:15px; max-width:480px; margin:0 auto; line-height:1.7">
            Sou um assistente de suporte inteligente com IA.<br>
            Digite sua solicitação abaixo ou escolha um
            <strong>cenário de demonstração</strong> no painel à esquerda.
        </p>
    </div>
    """, unsafe_allow_html=True)

    # Quick chips
    st.markdown("")
    cols = st.columns(3)
    quick = [
        ("💰", "Prorrogar boleto vencido"),
        ("🚚", "Rastrear pedido atrasado"),
        ("📄", "Corrigir nota fiscal"),
        ("⚖️", "Cancelar contrato"),
        ("🤝", "Desconto não aplicado"),
        ("❓", "Falar com atendente"),
    ]
    for i, (em, txt) in enumerate(quick):
        with cols[i % 3]:
            if st.button(f"{em} {txt}", use_container_width=True, key=f"quick_{i}"):
                st.session_state["_fire"] = txt
                st.rerun()

# ── Histórico de mensagens ────────────────────────────
for msg in st.session_state.messages:
    with st.chat_message(msg["role"], avatar="🤖" if msg["role"] == "assistant" else "🧑"):
        st.markdown(msg["content"])

    # Card de protocolo após resposta da IA
    if msg["role"] == "assistant" and msg.get("proto"):
        p = msg["proto"]
        s_bg, s_fg, s_em = SECTOR_COLORS.get(p["setor"], SECTOR_COLORS["geral"])
        pr_bg, pr_fg, pr_em = PRIORITY_COLORS.get(p["prio"], PRIORITY_COLORS["media"])
        a_em2, a_lbl2 = ACTION_LABELS.get(p["acao"], ACTION_LABELS["responder"])

        st.markdown(f"""
        <div class="proto-card">
            <div style="font-size:10px;font-weight:700;letter-spacing:.4px;text-transform:uppercase;
                        color:#94A3B8;margin-bottom:7px">🗂️ Protocolo registrado</div>
            <div class="proto-row">
                <span class="ptag" style="background:{s_bg};color:{s_fg};border-color:{s_fg}40">{s_em} {p['setor'].capitalize()}</span>
                <span class="ptag" style="background:{pr_bg};color:{pr_fg};border-color:{pr_fg}40">{pr_em} {p['prio'].capitalize()}</span>
                <span class="ptag" style="background:#F1F5F9;color:#475569;border-color:#E2E8F0">{a_em2} {a_lbl2}</span>
            </div>
            <div class="proto-id">🔖 {p['id']} &nbsp;·&nbsp; 🎯 {p['intent']}</div>
        </div>
        """, unsafe_allow_html=True)

# ── Input do chat ─────────────────────────────────────
user_input = st.chat_input("Digite sua mensagem aqui…")

# Disparo por cenário ou quick chip
fire = st.session_state.pop("_fire", None)
if fire and not user_input:
    user_input = fire

# ── Processar mensagem ────────────────────────────────
if user_input:
    if not os.getenv("GROQ_API_KEY"):
        st.error("⚠️ Configure sua **Groq API Key** no painel lateral para iniciar.", icon="🔑")
        st.stop()

    # Exibe mensagem do usuário
    with st.chat_message("user", avatar="🧑"):
        st.markdown(user_input)
    st.session_state.messages.append({"role": "user", "content": user_input})

    # Gera resposta da IA
    with st.chat_message("assistant", avatar="🤖"):
        with st.spinner("🧠 Classificando e gerando resposta…"):
            eff = client_info or st.session_state.get("session_client")
            history = [
                {"role": m["role"], "content": m["content"]}
                for m in st.session_state.messages[:-1]
            ]
            output = orchestrate(
                user_message=user_input,
                client_info=eff,
                history=history,
            )
        st.markdown(output.resposta)

    # Cria/atualiza protocolo no banco
    if not st.session_state.protocol_id:
        cname = eff["name"] if eff else "Anônimo"
        ccnpj = eff["cnpj"]  if eff else "00.000.000/0000-00"
        pid = create_protocol(
            cnpj=ccnpj,         client_name=cname,
            sector=output.setor, intent=output.intencao,
            priority=output.prioridade, action=output.acao,
            summary=user_input[:200], ai_response=output.resposta,
        )
        st.session_state.protocol_id = pid
        add_message(pid, "user", user_input)
    else:
        add_message(st.session_state.protocol_id, "user", user_input)

    add_message(st.session_state.protocol_id, "assistant", output.resposta)
    st.session_state.last_output = output

    # Salva com dados do protocolo para renderizar o card
    st.session_state.messages.append({
        "role": "assistant",
        "content": output.resposta,
        "proto": {
            "id":    st.session_state.protocol_id,
            "setor": output.setor,
            "prio":  output.prioridade,
            "acao":  output.acao,
            "intent": output.intencao,
        },
    })
    st.rerun()
