# 🧠 AI Customer Support Orchestrator

Sistema inteligente de atendimento B2B que classifica automaticamente solicitações de clientes, responde demandas simples e roteia corretamente para setores responsáveis.

**Projeto Acadêmico** | Powered by **Groq + LLaMA 3.1 8B** (gratuito)

---

## 🚀 Demo Rápido

[![Streamlit App](https://ai-customer-support-orchestrator-lq2achxetekhhwm9wnjflt.streamlit.app/dashboard)

---

## 🎯 Problema que resolve

| Problema | Antes | Depois |
|---|---|---|
| Erro de classificação | ~20% | < 5% |
| Volume humano | 100% | 50–70% |
| Rastreabilidade | Manual | Automática |
| SLA | Estourado | Monitorado |

---

## 🏗️ Arquitetura

```
Cliente → Webchat → Classificação LLM → Busca Cliente → RAG → Agente Especialista
                                                                      ↓
                                              Responder | Pedir Info | Escalar → Protocolo
```

**Stack:**
- 🤖 **Groq API** (LLaMA 3.1 8B Instant) — classificação e respostas
- 🧩 **Pydantic v2** — validação de outputs estruturados
- 📚 **RAG** — base de conhecimento por setor (keyword scoring)
- 🗄️ **SQLite** — clientes, contratos, protocolos, histórico
- 🖥️ **Streamlit** — interface do cliente e dashboard

---

## 📦 Instalação Local

```bash
git clone https://github.com/seu-usuario/ai-customer-support
cd ai-customer-support
pip install -r requirements.txt

# Configure sua chave Groq (gratuita em console.groq.com)
cp .env.example .env
# Edite .env e adicione sua GROQ_API_KEY

streamlit run app.py
```

---

## 🔑 Configuração da API Key

1. Acesse [console.groq.com](https://console.groq.com)
2. Crie uma conta gratuita
3. Gere uma API Key
4. Cole no campo lateral do app **ou** no arquivo `.env`

---

## 📱 Páginas do Sistema

| Página | Descrição |
|---|---|
| 💬 **Webchat** | Interface de atendimento do cliente |
| 📊 **Dashboard** | KPIs, gráficos de SLA, IA vs Humano |
| 📋 **Protocolos** | Gestão e histórico de atendimentos |
| 🏗️ **Arquitetura** | Documentação técnica do sistema |

---

## 🧩 Taxonomia de Intents

| Setor | Intents |
|---|---|
| 💰 Financeiro | boleto, NF, desconto, prorrogação, parcelamento |
| 🚚 Logística | rastreio, atraso, avaria, devolução |
| 🤝 Comercial | divergência, desconto acordado, contato vendedor |
| ⚖️ Jurídico | distrato, rescisão, análise contratual |

---

## 🧠 Modelo de Decisão

```python
class AtendimentoOutput(BaseModel):
    setor:      str  # financeiro | logistica | comercial | juridico | geral
    intencao:   str  # descrição livre
    prioridade: str  # urgente | alta | media | baixa
    acao:       str  # responder | pedir_info | escalar
    resposta:   str  # resposta final ao cliente
```

---

## 📅 Roadmap

- [x] Fase 1 — Fundação (SQLite, modelos de dados)
- [x] Fase 2 — Classificação (LLM + Pydantic)
- [x] Fase 3 — RAG (base de conhecimento por setor)
- [x] Fase 4 — Orquestração (pipeline completo)
- [x] Fase 5 — Agentes Especialistas (prompts por setor)
- [x] Fase 6 — Interface (Webchat Streamlit)
- [x] Fase 7 — Dashboard (KPIs + Plotly)
- [ ] Fase 8 — Testes e métricas
- [ ] Fase 9 — Deploy público

---

## ⚠️ Riscos e Mitigações

| Risco | Mitigação |
|---|---|
| Erro de classificação | Prompt estruturado + fallback para "geral" |
| Latência da API | Modelo 8B rápido (Groq ~800ms) |
| Dados inconsistentes | Pydantic valida todos os outputs |
| Dependência de prompt | Prompt versionado e testado |

---

## 👨‍💻 Autor

Projeto acadêmico desenvolvido para demonstrar sistemas de IA aplicada em atendimento B2B.

**Tecnologias:** Python · Streamlit · Groq · LLaMA 3.1 · SQLite · Pydantic · Plotly
