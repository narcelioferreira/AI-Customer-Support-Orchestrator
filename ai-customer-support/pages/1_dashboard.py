import streamlit as st
import sys, os
sys.path.insert(0, os.path.join(os.path.dirname(__file__), ".."))

import plotly.graph_objects as go
import plotly.express as px
import pandas as pd
from database import get_stats
from seed import seed
from database import init_db

st.set_page_config(page_title="Dashboard · AI Orchestrator", page_icon="📊", layout="wide")
init_db(); seed()

st.markdown("""
<style>
[data-testid="stAppViewContainer"] { background:#0F172A; }
[data-testid="stSidebar"] { background:#1E293B!important; border-right:1px solid #334155; }
h1,h2,h3,h4 { color:#F1F5F9!important; }
p,.stMarkdown,label { color:#CBD5E1!important; }
[data-testid="metric-container"] {
    background:#1E293B; border:1px solid #334155;
    border-radius:12px; padding:16px;
}
</style>""", unsafe_allow_html=True)

PLOTLY_LAYOUT = dict(
    paper_bgcolor="rgba(0,0,0,0)",
    plot_bgcolor="rgba(0,0,0,0)",
    font=dict(color="#CBD5E1", family="Inter, sans-serif"),
    margin=dict(l=20, r=20, t=40, b=20),
)

SECTOR_COLORS = {
    "financeiro": "#F59E0B",
    "logistica":  "#3B82F6",
    "comercial":  "#10B981",
    "juridico":   "#EF4444",
    "geral":      "#8B5CF6",
}

PRIO_COLORS = {
    "urgente": "#EF4444",
    "alta":    "#F59E0B",
    "media":   "#3B82F6",
    "baixa":   "#10B981",
}

# ── Header ────────────────────────────────────────────────────────────────────
st.markdown("# 📊 Dashboard Operacional")
st.markdown("Visão em tempo real de protocolos, SLA e performance da IA.")

if st.button("🔄 Atualizar"):
    st.rerun()

stats = get_stats()

# ── KPI Row ───────────────────────────────────────────────────────────────────
c1, c2, c3, c4, c5, c6 = st.columns(6)
c1.metric("📋 Total Protocolos", stats["total"])
c2.metric("🟡 Em Aberto",        stats["aberto"])
c3.metric("✅ Fechados",          stats["fechado"])
c4.metric("🤖 Resolvidos por IA", stats["ia"],
          f"{stats['ia']/max(stats['total'],1)*100:.0f}%")
c5.metric("👤 Escalados",         stats["humano"],
          f"{stats['humano']/max(stats['total'],1)*100:.0f}%")
sla_rate = stats["sla_ok"] / max(stats["sla_ok"]+stats["sla_breach"], 1) * 100
c6.metric("⏱️ SLA Cumprido",      f"{sla_rate:.0f}%",
          delta=f"{sla_rate-85:.1f}pp vs meta 85%",
          delta_color="normal")

st.markdown("---")

# ── Row 1: Sector + Priority ───────────────────────────────────────────────────
col_a, col_b = st.columns(2)

with col_a:
    st.markdown("#### 📂 Protocolos por Setor")
    if stats["by_sector"]:
        labels = list(stats["by_sector"].keys())
        values = list(stats["by_sector"].values())
        colors = [SECTOR_COLORS.get(s, "#8B5CF6") for s in labels]

        fig = go.Figure(go.Pie(
            labels=[l.capitalize() for l in labels],
            values=values,
            marker=dict(colors=colors, line=dict(color="#0F172A", width=2)),
            hole=.55,
            textfont=dict(size=13),
        ))
        fig.update_layout(**PLOTLY_LAYOUT, height=320,
                          legend=dict(orientation="h", y=-0.15))
        st.plotly_chart(fig, use_container_width=True)
    else:
        st.info("Sem dados ainda.")

with col_b:
    st.markdown("#### 🎯 Distribuição por Prioridade")
    if stats["by_priority"]:
        labels = list(stats["by_priority"].keys())
        values = list(stats["by_priority"].values())
        colors = [PRIO_COLORS.get(p, "#64748B") for p in labels]

        fig = go.Figure(go.Bar(
            x=[l.capitalize() for l in labels],
            y=values,
            marker=dict(color=colors, line=dict(color="#0F172A", width=1)),
            text=values, textposition="outside",
            textfont=dict(color="#CBD5E1"),
        ))
        fig.update_layout(
            **PLOTLY_LAYOUT, height=320,
            xaxis=dict(gridcolor="#1E293B"),
            yaxis=dict(gridcolor="#334155"),
        )
        st.plotly_chart(fig, use_container_width=True)

# ── Row 2: IA vs Humano + SLA ─────────────────────────────────────────────────
col_c, col_d = st.columns(2)

with col_c:
    st.markdown("#### 🤖 IA vs Humano")
    fig = go.Figure(go.Bar(
        x=["Resolvido por IA", "Escalado para Humano"],
        y=[stats["ia"], stats["humano"]],
        marker=dict(
            color=["#6366F1", "#F59E0B"],
            line=dict(color="#0F172A", width=1)
        ),
        text=[stats["ia"], stats["humano"]],
        textposition="outside",
        textfont=dict(color="#CBD5E1"),
    ))
    fig.update_layout(
        **PLOTLY_LAYOUT, height=280,
        xaxis=dict(gridcolor="#1E293B"),
        yaxis=dict(gridcolor="#334155"),
    )
    st.plotly_chart(fig, use_container_width=True)

with col_d:
    st.markdown("#### ⏱️ SLA — Cumprimento")
    ok     = stats["sla_ok"]
    breach = stats["sla_breach"]

    fig = go.Figure(go.Pie(
        labels=["Dentro do SLA", "SLA Estourado"],
        values=[ok if ok > 0 else 0, breach if breach > 0 else 0],
        marker=dict(
            colors=["#10B981", "#EF4444"],
            line=dict(color="#0F172A", width=2)
        ),
        hole=.55,
        textfont=dict(size=13),
    ))
    fig.update_layout(**PLOTLY_LAYOUT, height=280,
                      legend=dict(orientation="h", y=-0.15))
    st.plotly_chart(fig, use_container_width=True)

# ── Row 3: Timeline ───────────────────────────────────────────────────────────
st.markdown("#### 📅 Volume de Protocolos — Últimos 30 dias")
if stats["recent"]:
    df = pd.DataFrame(stats["recent"])
    df["date"] = pd.to_datetime(df["created_at"]).dt.date
    daily = df.groupby(["date","sector"]).size().reset_index(name="count")

    fig = px.area(
        daily, x="date", y="count", color="sector",
        color_discrete_map=SECTOR_COLORS,
        labels={"date":"Data","count":"Protocolos","sector":"Setor"},
    )
    fig.update_traces(line_width=2)
    fig.update_layout(
        **PLOTLY_LAYOUT, height=300,
        xaxis=dict(gridcolor="#334155"),
        yaxis=dict(gridcolor="#334155"),
        legend=dict(orientation="h", y=-0.2),
    )
    st.plotly_chart(fig, use_container_width=True)
else:
    st.info("Nenhum protocolo registrado ainda. Inicie uma conversa no Webchat.")

# ── Footer ─────────────────────────────────────────────────────────────────────
st.markdown("---")
st.markdown(
    "<p style='text-align:center;color:#475569;font-size:.8rem;'>"
    "AI Customer Support Orchestrator · Projeto Acadêmico · Powered by Groq + LLaMA 3.1"
    "</p>",
    unsafe_allow_html=True,
)
