import os
import json
import numpy as np
from groq import Groq
from pydantic import BaseModel
from knowledge_base import KNOWLEDGE_BASE

# ─── Pydantic Output Model ───────────────────────────────────────────────────

class AtendimentoOutput(BaseModel):
    setor: str          # financeiro | logistica | comercial | juridico | geral
    intencao: str
    prioridade: str     # urgente | alta | media | baixa
    acao: str           # responder | pedir_info | escalar
    resposta: str


# ─── Groq Client ─────────────────────────────────────────────────────────────

def get_groq_client():
    key = os.getenv("GROQ_API_KEY", "")
    if not key:
        raise ValueError("GROQ_API_KEY não configurada.")
    return Groq(api_key=key)


def chat(messages: list[dict], model="llama-3.1-8b-instant", temperature=0.3, max_tokens=1024) -> str:
    client = get_groq_client()
    resp = client.chat.completions.create(
        model=model,
        messages=messages,
        temperature=temperature,
        max_tokens=max_tokens,
    )
    return resp.choices[0].message.content.strip()


# ─── Simple Keyword-Based RAG (no embeddings needed) ─────────────────────────

def retrieve_context(query: str, sector: str, top_k: int = 4) -> str:
    """Retrieves relevant knowledge base snippets using keyword overlap."""
    docs = KNOWLEDGE_BASE.get(sector, []) + KNOWLEDGE_BASE.get("geral", [])
    query_words = set(query.lower().split())

    scored = []
    for doc in docs:
        doc_words = set(doc.lower().split())
        score = len(query_words & doc_words)
        scored.append((score, doc))

    scored.sort(key=lambda x: x[0], reverse=True)
    top = [doc for _, doc in scored[:top_k] if _ >= 0]
    return "\n".join(f"• {d}" for d in top) if top else "Sem regras específicas encontradas."


# ─── Step 1: Classification ───────────────────────────────────────────────────

CLASSIFICATION_PROMPT = """Você é um classificador especialista de atendimento B2B.
Analise a mensagem do cliente e retorne APENAS um JSON válido com este formato exato:
{
  "setor": "<financeiro|logistica|comercial|juridico|geral>",
  "intencao": "<descrição curta da intenção>",
  "prioridade": "<urgente|alta|media|baixa>",
  "acao": "<responder|pedir_info|escalar>"
}

Regras de prioridade:
- urgente: ameaça jurídica, operação parada, grande impacto financeiro
- alta: atraso significativo, erro em cobrança, cliente insatisfeito
- media: dúvidas, solicitações normais
- baixa: informações gerais, dúvidas simples

Regras de ação:
- responder: você pode resolver com as informações disponíveis
- pedir_info: precisa de mais dados do cliente (número de pedido, valor, etc.)
- escalar: situação complexa que requer análise humana especializada

Retorne SOMENTE o JSON, sem explicações."""


def classify(message: str, client_context: str = "") -> dict:
    user_content = f"Mensagem do cliente: {message}"
    if client_context:
        user_content += f"\n\nContexto do cliente: {client_context}"

    raw = chat([
        {"role": "system", "content": CLASSIFICATION_PROMPT},
        {"role": "user",   "content": user_content},
    ], temperature=0.1)

    # Extract JSON robustly
    raw = raw.strip()
    if "```" in raw:
        raw = raw.split("```")[1]
        if raw.startswith("json"):
            raw = raw[4:]
    try:
        return json.loads(raw)
    except Exception:
        return {
            "setor": "geral",
            "intencao": "não identificada",
            "prioridade": "media",
            "acao": "escalar"
        }


# ─── Step 2: Specialist Agent Response ───────────────────────────────────────

AGENT_PROMPTS = {
    "financeiro": """Você é o agente especialista financeiro de uma empresa B2B.
Responda de forma clara, profissional e empática.
Use as regras fornecidas para embasar sua resposta.
Seja objetivo: máximo 3 parágrafos. Ofereça uma solução concreta.""",

    "logistica": """Você é o agente especialista de logística de uma empresa B2B.
Responda com precisão sobre prazos, rastreamento e entregas.
Use as regras fornecidas. Seja direto e tranquilizador.
Máximo 3 parágrafos com passos claros.""",

    "comercial": """Você é o agente especialista comercial de uma empresa B2B.
Responda com foco em relacionamento e soluções.
Use as regras fornecidas. Seja cordial e propositivo.
Máximo 3 parágrafos.""",

    "juridico": """Você é o agente especialista jurídico de uma empresa B2B.
Responda com clareza sobre processos e documentação necessária.
Use as regras fornecidas. Seja formal e preciso.
Indique sempre os próximos passos. Máximo 3 parágrafos.""",

    "geral": """Você é o agente de atendimento geral de uma empresa B2B.
Responda de forma cordial e redirecione para o setor correto se necessário.
Máximo 2 parágrafos.""",
}


def generate_response(
    message: str,
    classification: dict,
    client_info: dict | None,
    history: list[dict],
    acao: str,
) -> str:
    sector = classification.get("setor", "geral")
    intent = classification.get("intencao", "")

    context = retrieve_context(message, sector)

    client_str = ""
    if client_info:
        contracts = client_info.get("contracts", [])
        ct_str = "; ".join(
            f"{c.get('product','?')} (#{c.get('contract_number','?')}, R${c.get('value',0):,.2f}, vence {c.get('end_date','?')})"
            for c in contracts
        ) or "Nenhum contrato ativo"
        client_str = (
            f"Cliente: {client_info.get('name','?')} | CNPJ: {client_info.get('cnpj','?')}\n"
            f"Segmento: {client_info.get('segment','?')} | Contatos: {client_info.get('contact_name','?')}\n"
            f"Contratos: {ct_str}"
        )

    if acao == "escalar":
        return (
            "Entendemos a complexidade da sua solicitação. "
            "Um especialista humano do nosso time entrará em contato em até 2 horas úteis "
            "para analisar seu caso com prioridade. Seu protocolo já foi registrado."
        )

    if acao == "pedir_info":
        ask_prompt = f"""O cliente enviou: "{message}"
Intenção identificada: {intent}
Faça UMA pergunta objetiva para obter a informação necessária para resolver o caso.
Seja cordial. Máximo 2 frases."""
        return chat([
            {"role": "system", "content": AGENT_PROMPTS.get(sector, AGENT_PROMPTS["geral"])},
            {"role": "user",   "content": ask_prompt},
        ])

    system = AGENT_PROMPTS.get(sector, AGENT_PROMPTS["geral"])

    user_content = f"""Mensagem do cliente: {message}
Intenção: {intent}

{f"Dados do cliente:{chr(10)}{client_str}" if client_str else ""}

Regras e políticas relevantes:
{context}

Responda diretamente ao cliente de forma profissional e resolutiva."""

    messages = [{"role": "system", "content": system}]

    # Include recent history
    for h in history[-6:]:
        messages.append({"role": h["role"], "content": h["content"]})

    messages.append({"role": "user", "content": user_content})

    return chat(messages, temperature=0.4, max_tokens=512)


# ─── Main Orchestrator ────────────────────────────────────────────────────────

def orchestrate(
    user_message: str,
    client_info: dict | None,
    history: list[dict],
) -> AtendimentoOutput:
    """Full pipeline: classify → retrieve → respond."""

    client_context = ""
    if client_info:
        client_context = (
            f"Nome: {client_info.get('name')} | "
            f"Segmento: {client_info.get('segment')} | "
            f"Contratos ativos: {len(client_info.get('contracts', []))}"
        )

    classification = classify(user_message, client_context)
    sector   = classification.get("setor", "geral")
    intent   = classification.get("intencao", "não identificada")
    priority = classification.get("prioridade", "media")
    action   = classification.get("acao", "responder")

    response = generate_response(
        message=user_message,
        classification=classification,
        client_info=client_info,
        history=history,
        acao=action,
    )

    return AtendimentoOutput(
        setor=sector,
        intencao=intent,
        prioridade=priority,
        acao=action,
        resposta=response,
    )
