"""Popula o banco com dados mock para demonstração."""
import sqlite3
import random
import uuid
from datetime import datetime, timedelta
from database import get_conn, init_db, is_seeded

CLIENTS = [
    ("12.345.678/0001-90", "TechVision Soluções LTDA",   "contato@techvision.com.br",   "(11) 3000-1001", "Enterprise", "Carlos Mendes"),
    ("98.765.432/0001-10", "Distribuidora Omega S/A",    "omega@omega.com.br",           "(21) 3000-2002", "Mid-Market", "Fernanda Lima"),
    ("11.222.333/0001-44", "Indústria Alfa LTDA",        "financeiro@alfa.com.br",       "(51) 3000-3003", "Enterprise", "Roberto Souza"),
    ("55.666.777/0001-88", "Comércio Beta ME",           "contato@beta.com.br",          "(41) 3000-4004", "SMB",        "Ana Paula"),
    ("33.444.555/0001-22", "Grupo Sigma Participações",  "admin@sigma.com.br",           "(31) 3000-5005", "Enterprise", "Marcos Vieira"),
    ("77.888.999/0001-66", "Startap Inovações LTDA",     "hello@startap.io",             "(11) 9000-6006", "SMB",        "Julia Torres"),
    ("22.333.444/0001-55", "Construções Delta S/A",      "obras@delta.com.br",           "(62) 3000-7007", "Mid-Market", "Pedro Alves"),
    ("66.777.888/0001-33", "Varejão Norte LTDA",         "norte@varejao.com.br",         "(85) 3000-8008", "SMB",        "Maria Santos"),
]

PRODUCTS = [
    ("Sistema ERP Módulo Financeiro", 8500.00, "30 dias"),
    ("Plataforma Logística Pro",       5200.00, "60 dias"),
    ("CRM Enterprise Suite",          12000.00, "30 dias"),
    ("BI Analytics Dashboard",         3800.00, "30 dias"),
    ("Módulo RH Completo",             6700.00, "60 dias"),
]

PROTOCOLS_MOCK = [
    ("financeiro", "negociação boleto",   "alta",    "responder", "ia",     "fechado"),
    ("logistica",  "rastreio pedido",     "media",   "responder", "ia",     "fechado"),
    ("comercial",  "divergência pedido",  "alta",    "escalar",   "humano", "fechado"),
    ("juridico",   "distrato contrato",   "urgente", "escalar",   "humano", "aberto"),
    ("financeiro", "prorrogação boleto",  "media",   "responder", "ia",     "fechado"),
    ("logistica",  "atraso entrega",      "alta",    "responder", "ia",     "aberto"),
    ("comercial",  "desconto acordado",   "media",   "responder", "ia",     "fechado"),
    ("financeiro", "erro em nota fiscal", "alta",    "escalar",   "humano", "aberto"),
    ("logistica",  "avaria mercadoria",   "urgente", "escalar",   "humano", "fechado"),
    ("comercial",  "contato vendedor",    "baixa",   "responder", "ia",     "fechado"),
    ("financeiro", "segunda via boleto",  "baixa",   "responder", "ia",     "fechado"),
    ("juridico",   "análise contrato",    "alta",    "escalar",   "humano", "aberto"),
    ("logistica",  "entrega parcial",     "media",   "pedir_info","ia",     "fechado"),
    ("comercial",  "proposta comercial",  "media",   "responder", "ia",     "fechado"),
    ("financeiro", "parcelamento débito", "alta",    "escalar",   "humano", "aberto"),
]

def seed():
    init_db()
    if is_seeded():
        return

    conn = get_conn()
    c = conn.cursor()

    # Insert clients
    for cnpj, name, email, phone, segment, contact_name in CLIENTS:
        c.execute(
            "INSERT OR IGNORE INTO clients (cnpj, name, email, phone, segment, contact_name) VALUES (?,?,?,?,?,?)",
            (cnpj, name, email, phone, segment, contact_name)
        )

    # Insert contracts
    for i, (cnpj, *_) in enumerate(CLIENTS):
        num_contracts = random.randint(1, 3)
        for j in range(num_contracts):
            product, value, terms = random.choice(PRODUCTS)
            start = datetime.now() - timedelta(days=random.randint(30, 365))
            end   = start + timedelta(days=random.randint(180, 730))
            c.execute("""
            INSERT OR IGNORE INTO contracts
              (cnpj, contract_number, product, value, status, start_date, end_date, payment_day, payment_terms)
            VALUES (?,?,?,?,?,?,?,?,?)""",
            (cnpj,
             f"CT-{2024+i:04d}-{j+1:03d}",
             product, value,
             random.choice(["ativo", "ativo", "ativo", "encerrado"]),
             start.strftime("%Y-%m-%d"),
             end.strftime("%Y-%m-%d"),
             random.randint(5, 25),
             terms))

    # Insert mock protocols (past 30 days)
    sla_map = {"urgente": 2, "alta": 8, "media": 24, "baixa": 48}
    for i, (sector, intent, priority, action, resolved_by, status) in enumerate(PROTOCOLS_MOCK):
        created = datetime.now() - timedelta(hours=random.randint(1, 720))
        sla_hours = sla_map[priority]
        sla_deadline = created + timedelta(hours=sla_hours)
        updated = created + timedelta(hours=random.randint(1, sla_hours + 5))
        protocol_id = f"PROT-{created.strftime('%Y%m%d')}-{str(uuid.uuid4())[:6].upper()}"
        client = random.choice(CLIENTS)

        c.execute("""
        INSERT OR IGNORE INTO protocols
          (protocol_id, cnpj, client_name, sector, intent, priority, action,
           sla_hours, sla_deadline, created_at, updated_at, status, resolved_by,
           summary, ai_response)
        VALUES (?,?,?,?,?,?,?,?,?,?,?,?,?,?,?)""",
        (protocol_id, client[0], client[1], sector, intent, priority, action,
         sla_hours, sla_deadline.isoformat(),
         created.isoformat(), updated.isoformat(),
         status, resolved_by,
         f"Cliente solicitou: {intent}",
         "Protocolo registrado automaticamente pelo sistema."))

    conn.commit()
    conn.close()
    print("✅ Banco de dados populado com sucesso!")

if __name__ == "__main__":
    seed()
