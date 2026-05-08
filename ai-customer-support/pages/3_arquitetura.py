import streamlit as st
import sys, os
sys.path.insert(0, os.path.join(os.path.dirname(__file__), ".."))

st.set_page_config(page_title="Arquitetura · AI Orchestrator", page_icon="🏗️", layout="wide")

st.markdown("""
<style>
[data-testid="stAppViewContainer"] { background:#0F172A; }
[data-testid="stSidebar"] { background:#1E293B!important; border-right:1px solid #334155; }
h1,h2,h3,h4,h5 { color:#F1F5F9!important; }
p,.stMarkdown,label,li { color:#CBD5E1!important; }
.arch-card {
    background:#1E293B; border:1px solid #334155;
    border-radius:12px; padding:20px; margin:10px 0;
}
.arch-card h4 { margin-top:0; }
.tag {
    display:inline-block; padding:2px 8px; border-radius:99px;
    font-size:.72rem; font-weight:700; margin:2px;
}
.tag-green  { background:#D1FAE5; color:#065F46; }
.tag-blue   { background:#DBEAFE; color:#1E40AF; }
.tag-purple { background:#EDE9FE; color:#5B21B6; }
.tag-orange { background:#FEF3C7; color:#92400E; }
.tag-red    { background:#FEE2E2; color:#991B1B; }
</style>""", unsafe_allow_html=True)

st.markdown("# 🏗️ Arquitetura do Sistema")
st.markdown("Documentação técnica do AI Customer Support Orchestrator.")

# ── Flow Diagram ──────────────────────────────────────────────────────────────
st.markdown("## 🔁 Fluxo de Processamento")
st.markdown("""
```
                    ┌─────────────────────────────────────────────────────────┐
                    │               AI CUSTOMER SUPPORT ORCHESTRATOR          │
                    └─────────────────────────────────────────────────────────┘

  ┌──────────┐     ┌──────────────┐     ┌──────────────┐     ┌──────────────┐
  │  Cliente │────▶│   Webchat    │────▶│ Classificador│────▶│Busca Cliente │
  │  (User)  │     │  (Streamlit) │     │  LLM Groq    │     │  SQLite      │
  └──────────┘     └──────────────┘     └──────────────┘     └──────────────┘
                                               │                     │
                                         ┌─────▼─────┐              │
                                         │   Setor   │◀─────────────┘
                                         │ Prioridade│
                                         │   Ação    │
                                         └─────┬─────┘
                                               │
                        ┌──────────────────────┼───────────────────────┐
                        ▼                      ▼                       ▼
                 ┌────────────┐        ┌─────────────┐        ┌──────────────┐
                 │    RAG     │        │  Agente     │        │  Criação de  │
                 │ (keywords) │───────▶│ Especialista│───────▶│  Protocolo   │
                 │  por setor │        │  LLM Groq   │        │   SQLite     │
                 └────────────┘        └─────────────┘        └──────────────┘
                                               │
                              ┌────────────────┼────────────────┐
                              ▼                ▼                ▼
                        ┌──────────┐   ┌─────────────┐  ┌────────────┐
                        │Responder │   │ Pedir Info  │  │  Escalar   │
                        │   (IA)   │   │    (IA)     │  │  (Humano)  │
                        └──────────┘   └─────────────┘  └────────────┘
```
""")

# ── Tech Stack ────────────────────────────────────────────────────────────────
st.markdown("## 🛠️ Stack Tecnológico")

col1, col2 = st.columns(2)

with col1:
    st.markdown("""
<div class="arch-card">
<h4>🤖 Camada de IA</h4>
<span class="tag tag-purple">Groq API</span>
<span class="tag tag-purple">LLaMA 3.1 8B Instant</span>
<span class="tag tag-blue">Pydantic v2</span>
<span class="tag tag-green">RAG por Keywords</span>
<br><br>
<b>Modelo:</b> llama-3.1-8b-instant<br>
<b>Latência média:</b> ~800ms<br>
<b>Custo:</b> Gratuito (tier free Groq)<br>
<b>Classificação:</b> Prompt estruturado → JSON<br>
<b>RAG:</b> Keyword overlap scoring
</div>
""", unsafe_allow_html=True)

    st.markdown("""
<div class="arch-card">
<h4>🗄️ Camada de Dados</h4>
<span class="tag tag-orange">SQLite</span>
<span class="tag tag-blue">Python sqlite3</span>
<br><br>
<b>Tabelas:</b><br>
• <code>clients</code> — Cadastro de empresas<br>
• <code>contracts</code> — Contratos por CNPJ<br>
• <code>protocols</code> — Atendimentos gerados<br>
• <code>messages</code> — Histórico de mensagens<br>
<br>
<b>SLA:</b> Urgente 2h | Alta 8h | Média 24h | Baixa 48h
</div>
""", unsafe_allow_html=True)

with col2:
    st.markdown("""
<div class="arch-card">
<h4>🖥️ Camada de Interface</h4>
<span class="tag tag-red">Streamlit</span>
<span class="tag tag-purple">Plotly</span>
<span class="tag tag-blue">Pandas</span>
<br><br>
<b>Páginas:</b><br>
• <b>Webchat</b> — Interface do cliente<br>
• <b>Dashboard</b> — KPIs e gráficos<br>
• <b>Protocolos</b> — Gestão de casos<br>
• <b>Arquitetura</b> — Esta página
</div>
""", unsafe_allow_html=True)

    st.markdown("""
<div class="arch-card">
<h4>🧩 Taxonomia de Intents</h4>
<span class="tag tag-orange">Financeiro</span>
<span class="tag tag-blue">Logística</span>
<span class="tag tag-green">Comercial</span>
<span class="tag tag-red">Jurídico</span>
<br><br>
<b>💰 Financeiro:</b> boleto, NF, desconto, prorrogação<br>
<b>🚚 Logística:</b> rastreio, atraso, avaria<br>
<b>🤝 Comercial:</b> divergência, desconto, contato<br>
<b>⚖️ Jurídico:</b> distrato, rescisão, análise<br>
</div>
""", unsafe_allow_html=True)

# ── Decision Model ────────────────────────────────────────────────────────────
st.markdown("## 🧠 Modelo de Decisão")
st.code("""
class AtendimentoOutput(BaseModel):
    setor:     str  # financeiro | logistica | comercial | juridico | geral
    intencao:  str  # descrição livre da intenção detectada
    prioridade:str  # urgente | alta | media | baixa
    acao:      str  # responder | pedir_info | escalar
    resposta:  str  # texto final para o cliente
""", language="python")

# ── Roadmap ───────────────────────────────────────────────────────────────────
st.markdown("## 📅 Roadmap de Execução")

phases = [
    ("✅ Fase 1", "Fundação",        "Estrutura, SQLite, modelos de dados, CRUD",          "green"),
    ("✅ Fase 2", "Classificação",   "Prompt LLM, Pydantic, detecção de intents",           "green"),
    ("✅ Fase 3", "RAG",             "Base de conhecimento por setor, keyword retrieval",    "green"),
    ("✅ Fase 4", "Orquestração",    "Pipeline classify → retrieve → respond",               "green"),
    ("✅ Fase 5", "Agentes",         "Prompts especializados por setor",                     "green"),
    ("✅ Fase 6", "Interface",       "Webchat Streamlit + exemplos rápidos",                 "green"),
    ("✅ Fase 7", "Dashboard",       "KPIs, gráficos Plotly, SLA, IA vs Humano",            "green"),
    ("🔜 Fase 8", "Testes",         "Cenários reais, métricas de classificação",             "blue"),
    ("🔜 Fase 9", "Deploy",         "GitHub + Streamlit Cloud + README",                    "blue"),
]

for phase, name, desc, color in phases:
    tag_cls = f"tag-{color}"
    st.markdown(
        f'<div class="arch-card" style="margin:6px 0;padding:12px 18px;">'
        f'<span class="tag {tag_cls}" style="font-size:.85rem;">{phase}</span> '
        f'<b style="color:#F1F5F9;font-size:1rem;"> {name}</b>'
        f'<span style="color:#94A3B8;font-size:.88rem;"> — {desc}</span>'
        f'</div>',
        unsafe_allow_html=True,
    )

# ── Footer ─────────────────────────────────────────────────────────────────────
st.markdown("---")
st.markdown(
    "<p style='text-align:center;color:#475569;font-size:.8rem;'>"
    "AI Customer Support Orchestrator · Projeto Acadêmico · Powered by Groq + LLaMA 3.1"
    "</p>",
    unsafe_allow_html=True,
)
