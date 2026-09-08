from fastapi import FastAPI, HTTPException, Request
from fastapi.middleware.cors import CORSMiddleware
from fastapi.responses import FileResponse
from pydantic import BaseModel
from typing import Optional, List, Dict
import sqlite3
import httpx
import json
import re
import urllib.parse
import os
import socket
import datetime

app = FastAPI(title="API ProEstudos - 2.0")

app.add_middleware(
    CORSMiddleware,
    allow_origins=["*"], 
    allow_credentials=True,
    allow_methods=["*"],
    allow_headers=["*"],
)

def init_db():
    conn = sqlite3.connect("estudos.db")
    cursor = conn.cursor()
    
    cursor.execute('''
        CREATE TABLE IF NOT EXISTS disciplinas (
            id INTEGER PRIMARY KEY AUTOINCREMENT,
            nome TEXT UNIQUE NOT NULL
        )
    ''')
    
    cursor.execute('''
        CREATE TABLE IF NOT EXISTS questoes (
            id INTEGER PRIMARY KEY AUTOINCREMENT,
            disciplina_id INTEGER,
            enunciado TEXT NOT NULL,
            alternativas TEXT NOT NULL,
            gabarito TEXT NOT NULL,
            explicacao TEXT,
            video_url TEXT,
            banca TEXT DEFAULT 'Inédita',
            ano INTEGER DEFAULT 2026,
            concurso TEXT DEFAULT 'Simulado',
            topico_especifico TEXT DEFAULT '',
            enunciado_html TEXT DEFAULT '',
            anotacao TEXT DEFAULT ''
        )
    ''')
    
    # Atualizações estruturais (Blindagem)
    try: cursor.execute("ALTER TABLE questoes ADD COLUMN banca TEXT DEFAULT 'Inédita'")
    except: pass
    try: cursor.execute("ALTER TABLE questoes ADD COLUMN ano INTEGER DEFAULT 2026")
    except: pass
    try: cursor.execute("ALTER TABLE questoes ADD COLUMN concurso TEXT DEFAULT 'Simulado'")
    except: pass
    try: cursor.execute("ALTER TABLE questoes ADD COLUMN topico_especifico TEXT DEFAULT ''")
    except: pass
    try: cursor.execute("ALTER TABLE questoes ADD COLUMN enunciado_html TEXT DEFAULT ''")
    except: pass
    try: cursor.execute("ALTER TABLE questoes ADD COLUMN anotacao TEXT DEFAULT ''")
    except: pass

    cursor.execute("PRAGMA table_info(progresso)")
    colunas_progresso = [col[1] for col in cursor.fetchall()]
    
    if colunas_progresso and 'data_resolucao' not in colunas_progresso:
        print("\n🔧 [SISTEMA] Atualizando tabela de progresso para suportar Gamificação e Gráficos...")
        cursor.execute("ALTER TABLE progresso RENAME TO progresso_velho")
        cursor.execute('''
            CREATE TABLE progresso (
                id INTEGER PRIMARY KEY AUTOINCREMENT,
                questao_id INTEGER,
                acertou BOOLEAN,
                resposta_usuario TEXT,
                data_resolucao TIMESTAMP DEFAULT CURRENT_TIMESTAMP
            )
        ''')
        cursor.execute("INSERT INTO progresso (id, questao_id, acertou, resposta_usuario) SELECT id, questao_id, acertou, resposta_usuario FROM progresso_velho")
        cursor.execute("DROP TABLE progresso_velho")
        print("✅ [SISTEMA] Atualização do banco de dados concluída!\n")
    elif not colunas_progresso:
        cursor.execute('''
            CREATE TABLE progresso (
                id INTEGER PRIMARY KEY AUTOINCREMENT,
                questao_id INTEGER,
                acertou BOOLEAN,
                resposta_usuario TEXT,
                data_resolucao TIMESTAMP DEFAULT CURRENT_TIMESTAMP
            )
        ''')

    cursor.execute('''
        CREATE TABLE IF NOT EXISTS config (
            id INTEGER PRIMARY KEY AUTOINCREMENT,
            chave TEXT,
            valor TEXT
        )
    ''')
    
    # 👇 AQUI ESTÃO AS NOVAS DISCIPLINAS FOCADAS NO EDITAL DA SEDUC-PA 2026
    disciplinas_padrao = [
        "Professor - Língua Portuguesa", "Professor - Matemática", 
        "Professor - História", "Professor - Geografia", 
        "Professor - Filosofia", "Professor - Sociologia", 
        "Professor - Física", "Professor - Química", 
        "Professor - Biologia", "Professor - Língua Inglesa", 
        "Professor - Artes", "Professor - Educação Física", 
        "Professor - Educação Especial (AEE)", "Professor - Educação Especial (LIBRAS)",
        "Especialista em Educação (Pedagogia)", 
        "Analista - Nutrição", "Analista - Psicologia", "Analista - Serviço Social", 
        "Analista - Arquitetura e Urbanismo", "Analista - Engenharia Civil", 
        "Analista - Engenharia Elétrica", "Analista - Administração", 
        "Analista - Ciências Contábeis", "Analista - Ciências Econômicas", 
        "Analista - Estatística", 
        "Assistente de Gestão Educacional (Nível Médio)"
    ]
    for d in disciplinas_padrao:
        cursor.execute("INSERT OR IGNORE INTO disciplinas (nome) VALUES (?)", (d,))
        
    conn.commit()
    conn.close()

init_db()

class ConfigAPI(BaseModel):
    groq_key: Optional[str] = None

class DisciplinaCreate(BaseModel):
    nome: str

class GerarRequest(BaseModel):
    disciplina_id: int
    nivel: str = "Ensino Médio"
    quantidade: int = 10
    banca: Optional[str] = ""
    orgao: Optional[str] = ""
    topico: Optional[str] = ""
    tipo: str = "reais"

class GerarSimuladoRequest(BaseModel):
    nivel: str = "Ensino Médio"
    quantidade: int = 10
    banca: Optional[str] = ""
    orgao: Optional[str] = ""
    tipo: str = "reais"

class ResponderRequest(BaseModel):
    questao_id: int
    resposta: str

class ResponderLoteRequest(BaseModel):
    respostas: Dict[str, str]

class RefazerRequest(BaseModel):
    questao_id: int

class ChatDuvidaRequest(BaseModel):
    questao_id: int
    mensagem: str

class SalvarAnotacaoRequest(BaseModel):
    questao_id: int
    anotacao: str

class SalvarHtmlRequest(BaseModel):
    questao_id: int
    html: str

@app.get("/")
def index():
    if os.path.exists("index.html"):
        return FileResponse("index.html")
    return {"erro": "Arquivo index.html não encontrado."}

async def get_groq_key():
    conn = sqlite3.connect("estudos.db")
    row = conn.execute("SELECT valor FROM config WHERE chave='groq_key'").fetchone()
    conn.close()
    if not row or not row[0]:
        raise HTTPException(status_code=400, detail="Chave da Groq não configurada no sistema.")
    return row[0].strip()

async def conversar_ia(prompt: str) -> str:
    api_key = await get_groq_key()
    headers = {"Authorization": f"Bearer {api_key}", "Content-Type": "application/json"}
    
    try:
        async with httpx.AsyncClient(timeout=60.0) as client:
            # Busca os modelos que estão online hoje na Groq
            models_response = await client.get("https://api.groq.com/openai/v1/models", headers=headers)
            if models_response.status_code != 200:
                raise HTTPException(status_code=500, detail="Erro ao listar modelos Groq.")
            
            modelos_brutos = models_response.json().get("data", [])
            # Bloqueando modelos de áudio, segurança e modelos DeepSeek (que pensam alto em inglês)
            modelos_disponiveis = [m["id"] for m in modelos_brutos if "whisper" not in m["id"].lower() and "guard" not in m["id"].lower() and "deepseek" not in m["id"].lower()]
            
            if not modelos_disponiveis:
                raise HTTPException(status_code=500, detail="Nenhum modelo válido encontrado.")

            # Tenta conversar usando o primeiro modelo válido disponível
            for modelo in modelos_disponiveis:
                payload = {
                    "model": modelo,
                    "messages": [{"role": "user", "content": prompt}],
                    "temperature": 0.7
                }
                resposta = await client.post("https://api.groq.com/openai/v1/chat/completions", headers=headers, json=payload)
                if resposta.status_code == 200:
                    texto = resposta.json()["choices"][0]["message"]["content"]
                    # Limpa qualquer tag de pensamento residual, caso a IA teime em pensar alto
                    texto = re.sub(r'<think>.*?</think>', '', texto, flags=re.DOTALL).strip()
                    # Limpa "Here's a thinking process:" se ela mandar sem as tags
                    texto = re.sub(r"(?i)(Here's a thinking process:.*?)(?=\n\n|\n[A-Z])", "", texto, flags=re.DOTALL).strip()
                    return texto
                
            raise HTTPException(status_code=500, detail="Erro ao comunicar com a IA.")
    except Exception as e:
        raise HTTPException(status_code=500, detail=str(e))

async def gerar_conteudo_ia(prompt: str) -> str:
    api_key = await get_groq_key()
    headers = {"Authorization": f"Bearer {api_key}", "Content-Type": "application/json"}

    try:
        async with httpx.AsyncClient(timeout=60.0) as client:
            models_response = await client.get("https://api.groq.com/openai/v1/models", headers=headers)
            if models_response.status_code != 200:
                raise HTTPException(status_code=500, detail="Erro ao listar modelos Groq.")
            
            modelos_brutos = models_response.json().get("data", [])
            # Bloqueando modelos DeepSeek também na geração de JSON
            modelos_disponiveis = [m["id"] for m in modelos_brutos if "whisper" not in m["id"].lower() and "guard" not in m["id"].lower() and "deepseek" not in m["id"].lower()]
            
            if not modelos_disponiveis:
                raise HTTPException(status_code=500, detail="Nenhum modelo válido encontrado.")

            for modelo in modelos_disponiveis:
                payload = {
                    "model": modelo,
                    "messages": [{"role": "user", "content": prompt}],
                    "temperature": 0.6, 
                    "response_format": {"type": "json_object"}
                }
                resposta = await client.post("https://api.groq.com/openai/v1/chat/completions", headers=headers, json=payload)
                if resposta.status_code == 200:
                    return resposta.json()["choices"][0]["message"]["content"]
            
            raise HTTPException(status_code=500, detail="Falha ao gerar com todos os modelos.")
    except Exception as e:
        raise HTTPException(status_code=500, detail=str(e))

async def gerar_lote_questoes_ia(prompt: str, disciplina_id: int, topico_especifico: str = ""):
    resultado_texto = await gerar_conteudo_ia(prompt)
    try:
        dados = json.loads(resultado_texto)
        lote = dados.get("questoes", [])
        if not isinstance(lote, list): lote = [dados] if "enunciado" in dados else []
            
        conn = sqlite3.connect("estudos.db")
        cursor = conn.cursor()
        
        for item in lote:
            enunciado = item.get("enunciado", "").strip()
            alts = item.get("alternativas", [])
            gabarito = item.get("gabarito", "A").upper()
            explicacao = item.get("explicacao", "").strip()
            assunto = item.get("assunto_para_busca", "").strip()
            banca = str(item.get("banca", "Inédita")).strip()
            concurso = str(item.get("concurso", "Simulado")).strip()
            
            try: ano = int(item.get("ano", 2026))
            except: ano = 2026
            
            if len(alts) != 5: continue 
                
            alts_limpas = []
            letras_base = ["A", "B", "C", "D", "E"]
            for i, alt in enumerate(alts):
                alt_str = re.sub(r'^([A-Ea-e1-5][)\-.]\s*|\([A-Ea-e1-5]\)\s*)', '', str(alt)).strip()
                alts_limpas.append(f"{letras_base[i]}) {alt_str}")
            
            query = urllib.parse.quote_plus(f"{assunto} concurso aula")
            cursor.execute('''INSERT INTO questoes (disciplina_id, enunciado, alternativas, gabarito, explicacao, video_url, banca, ano, concurso, topico_especifico)
                              VALUES (?, ?, ?, ?, ?, ?, ?, ?, ?, ?)''', 
                           (disciplina_id, enunciado, json.dumps(alts_limpas), gabarito, explicacao, f"https://www.youtube.com/results?search_query={query}", banca, ano, concurso, topico_especifico))
    cursor.execute('''
        CREATE TABLE IF NOT EXISTS config (
            id INTEGER PRIMARY KEY AUTOINCREMENT,
            chave TEXT,
            valor TEXT
        )
    ''')
    
    # 👇 DISCIPLINAS AMPLAS (Para todas as carreiras: Policiais, Educacionais, Administrativas, Tribunais)
    disciplinas_padrao = [
        "Língua Portuguesa", "Matemática", "Raciocínio Lógico", "Informática",
        "Direito Constitucional", "Direito Administrativo", "Direito Penal", 
        "Direito Processual Penal", "Legislação Extravagante", "Direitos Humanos",
        "Conhecimentos Pedagógicos", "Legislação Educacional", 
        "Administração Pública", "Administração Financeira e Orçamentária (AFO)",
        "Atualidades", "Redação Oficial"
    ]
    for d in disciplinas_padrao:
        cursor.execute("INSERT OR IGNORE INTO disciplinas (nome) VALUES (?)", (d,))
        
    conn.commit()
    conn.close()
    return {"status": "sucesso"}

@app.post("/api/reset_db")
def reset_db():
    conn = sqlite3.connect("estudos.db")
    conn.executescript("DELETE FROM progresso; DELETE FROM questoes; DELETE FROM disciplinas;")
    conn.commit()
    init_db()
    return {"status": "Limpo."}

@app.get("/api/backup")
def backup_db():
    if os.path.exists("estudos.db"):
        hoje = datetime.date.today().strftime("%d-%m-%Y")
        return FileResponse("estudos.db", media_type="application/octet-stream", filename=f"ProEstudos_Backup_{hoje}.db")
    raise HTTPException(status_code=404, detail="Banco de dados não encontrado.")

@app.post("/api/disciplina")
def criar_disciplina(disciplina: DisciplinaCreate):
    try:
        conn = sqlite3.connect("estudos.db")
        conn.execute("INSERT INTO disciplinas (nome) VALUES (?)", (disciplina.nome,))
        conn.commit()
        conn.close()
        return {"status": "sucesso"}
    except sqlite3.IntegrityError:
        raise HTTPException(status_code=400, detail="Já existe")

@app.get("/api/dados")
def get_dados():
    conn = sqlite3.connect("estudos.db")
    conn.row_factory = sqlite3.Row
    
    disciplinas = [dict(r) for r in conn.execute("SELECT id, nome FROM disciplinas ORDER BY nome").fetchall()]
    tot = conn.execute("SELECT COUNT(*) FROM questoes").fetchone()[0]
    ac = conn.execute("SELECT COUNT(*) FROM progresso WHERE acertou=1").fetchone()[0]
    er = conn.execute("SELECT COUNT(*) FROM progresso WHERE acertou=0").fetchone()[0]
    
    datas_raw = conn.execute("SELECT date(data_resolucao, 'localtime') as data, acertou, COUNT(*) as qtd FROM progresso GROUP BY date(data_resolucao, 'localtime'), acertou ORDER BY date(data_resolucao, 'localtime') ASC").fetchall()
    
    # Calculando Histórico dos últimos 7 dias para o Gráfico de Linha
    historico_dias = {}
    hoje = datetime.date.today()
    for i in range(6, -1, -1):
        d = (hoje - datetime.timedelta(days=i)).strftime('%Y-%m-%d')
        historico_dias[d] = {"acertos": 0, "erros": 0}
        
    for r in datas_raw:
        data_str = r['data']
        if data_str in historico_dias:
            if r['acertou'] == 1: historico_dias[data_str]['acertos'] += r['qtd']
            else: historico_dias[data_str]['erros'] += r['qtd']
            
    lista_historico = [{"data": k, "acertos": v["acertos"], "erros": v["erros"]} for k, v in historico_dias.items()]

    # Streak (Ofensiva)
    datas_unicas = conn.execute("SELECT date(data_resolucao, 'localtime') FROM progresso GROUP BY date(data_resolucao, 'localtime') ORDER BY date(data_resolucao, 'localtime') DESC").fetchall()
    streak = 0
    data_check = hoje
    
    if datas_unicas:
        primeira_data = datetime.datetime.strptime(datas_unicas[0][0], '%Y-%m-%d').date()
        if primeira_data == hoje or primeira_data == (hoje - datetime.timedelta(days=1)):
            for r in datas_unicas:
                d = datetime.datetime.strptime(r[0], '%Y-%m-%d').date()
                if d == data_check or (streak == 0 and d == hoje - datetime.timedelta(days=1)):
                    if streak == 0 and d != hoje:
                        data_check = hoje - datetime.timedelta(days=1)
                    streak += 1
                    data_check -= datetime.timedelta(days=1)
                else:
                    break

    raio_x = []
    for d in disciplinas:
        d_id = d['id']
        res = conn.execute("SELECT acertou, COUNT(*) FROM progresso p JOIN questoes q ON p.questao_id = q.id WHERE q.disciplina_id = ? GROUP BY acertou", (d_id,)).fetchall()
        d_acertos = 0
        d_erros = 0
        for r in res:
            if r[0] == 1: d_acertos = r[1]
            else: d_erros = r[1]
        d_total = d_acertos + d_erros
        if d_total > 0:
            aproveitamento = round((d_acertos / d_total) * 100, 1)
            raio_x.append({
                "nome": d['nome'],
                "total": d_total,
                "acertos": d_acertos,
                "erros": d_erros,
                "aproveitamento": aproveitamento
            })
    
    raio_x.sort(key=lambda x: x['total'], reverse=True)
    
    conn.close()
    return {
        "disciplinas": disciplinas, 
        "stats": {
            "total": tot, "acertos": ac, "erros": er, 
            "aproveitamento": round((ac/(ac+er)*100) if ac+er>0 else 0, 1),
            "streak": streak,
            "raio_x": raio_x,
            "historico": lista_historico
        }
    }

@app.post("/api/gerar")
async def api_gerar(req: GerarRequest):
    conn = sqlite3.connect("estudos.db")
    row = conn.execute("SELECT nome FROM disciplinas WHERE id = ?", (req.disciplina_id,)).fetchone()
    conn.close()
    if not row: raise HTTPException(status_code=404)
    
    topico_txt = f" Foco/Assunto Específico exigido: {req.topico}." if req.topico else ""
    orgao_txt = f" Órgão/Carreira alvo: {req.orgao}." if req.orgao else ""
    
    if req.tipo == "reais":
        banca_exigida = req.banca if req.banca else "qualquer banca real"
        prompt = f"""Você é um banco de dados rigoroso de concursos públicos.
Sua tarefa é recuperar EXATAMENTE {req.quantidade} questões REAIS de provas anteriores da disciplina '{row[0]}'.
Nível de escolaridade: {req.nivel}. Banca exigida: {banca_exigida}.{orgao_txt}{topico_txt}

REGRAS CRÍTICAS (PUNIÇÃO SE DESCUMPRIR):
1. DIVERSIDADE EXTREMA: NENHUMA questão pode ser repetida. Puxe temas diferentes.
2. DADOS DA PROVA REAIS: É PROIBIDO usar a palavra "Simulado". Preencha "concurso" obrigatoriamente com o nome do ÓRGÃO E O CARGO. (Exemplo correto: "Polícia Federal - Agente", "INSS - Técnico").
3. ANO: Preencha com o ano real da prova (Ex: 2021).
4. TEXTO COMPLETO NAS ALTERNATIVAS: Você deve redigir o texto integral das alternativas. É TERMINANTEMENTE PROIBIDO preencher com apenas a letra "A", "B", etc.

Formato OBRIGATÓRIO (JSON puro):
{{
    "questoes": [
        {{
            "enunciado": "...",
            "alternativas": ["Texto completo da opção A...", "Texto completo da opção B...", "Texto completo da opção C...", "Texto completo da opção D...", "Texto completo da opção E..."],
            "gabarito": "A",
            "explicacao": "Explicação completa...",
            "assunto_para_busca": "...",
            "banca": "{banca_exigida}",
            "concurso": "ÓRGÃO - CARGO",
            "ano": 2022
        }}
    ]
}}"""
    else:
        prompt = f"""Crie {req.quantidade} questões INÉDITAS sobre '{row[0]}'. 
Nível: {req.nivel}. Foco: {req.topico if req.topico else 'Geral'}. 
NENHUMA QUESTÃO PODE SER REPETIDA. Regra: Escreva o TEXTO COMPLETO em cada alternativa.

Siga EXATAMENTE este JSON puro:
{{
    "questoes": [
        {{
            "enunciado": "...",
            "alternativas": ["Texto completo A...", "Texto completo B...", "Texto completo C...", "Texto completo D...", "Texto completo E..."],
            "gabarito": "A",
            "explicacao": "...",
            "assunto_para_busca": "...",
            "banca": "{req.banca if req.banca else 'Banca Inédita (IA)'}",
            "concurso": "Questão Inédita",
            "ano": 2024
        }}
    ]
}}"""

    await gerar_lote_questoes_ia(prompt, req.disciplina_id, req.topico)
    return {"status": "sucesso"}

@app.post("/api/gerar_simulado")
async def api_gerar_simulado(req: GerarSimuladoRequest):
    conn = sqlite3.connect("estudos.db")
    disciplinas = conn.execute("SELECT id, nome FROM disciplinas").fetchall()
    conn.close()
    if not disciplinas: raise HTTPException(status_code=400)
    qtd = max(1, req.quantidade // len(disciplinas))
    
    orgao_txt = f" Órgão/Carreira alvo: {req.orgao}." if req.orgao else ""
    banca_exigida = req.banca if req.banca else "qualquer banca real"
    
    for d_id, nome in disciplinas:
        if req.tipo == "reais":
            prompt = f"""Recupere {qtd} questões REAIS de concursos passados da disciplina '{nome}'. 
Nível: {req.nivel}. Banca exigida: {banca_exigida}.{orgao_txt} PROIBIDO INVENTAR. AS QUESTÕES DEVEM SER DIFERENTES ENTRE SI.
REGRAS: PROIBIDO usar "Simulado". Preencha "concurso" com Órgão e Cargo reais (Ex: TJ-SP - Escrevente). O texto das alternativas deve ser COMPLETO (proibido apenas letras soltas).
Siga EXATAMENTE este JSON:
{{
    "questoes": [
        {{
            "enunciado": "...", "alternativas": ["Texto A", "Texto B", "Texto C", "Texto D", "Texto E"], "gabarito": "A", "explicacao": "...", "assunto_para_busca": "...", 
            "banca": "NOME DA BANCA REAL", "concurso": "NOME DO ÓRGÃO - CARGO REAL", "ano": 2022
        }}
    ]
}}"""
        else:
            prompt = f"""Gere {qtd} questões INÉDITAS de '{nome}'. Nível: {req.nivel}. DIVERSIDADE TOTAL ENTRE ELAS. O texto das alternativas deve ser COMPLETO.
Siga EXATAMENTE este JSON:
{{
    "questoes": [
        {{
            "enunciado": "...", "alternativas": ["Texto A", "Texto B", "Texto C", "Texto D", "Texto E"], "gabarito": "A", "explicacao": "...", "assunto_para_busca": "...", 
            "banca": "Simulada", "concurso": "Simulado Geral - Cargo Genérico", "ano": 2024
        }}
    ]
}}"""
        await gerar_lote_questoes_ia(prompt, d_id)
    return {"status": "sucesso"}

@app.get("/api/questoes")
def get_questoes(disciplina_id: Optional[int]=None, apenas_pendentes: bool=False, apenas_erros: bool=False, apenas_acertos: bool=False, busca: Optional[str]=None, limit: int=50):
    conn = sqlite3.connect("estudos.db")
    conn.row_factory = sqlite3.Row
    q = "SELECT q.*, d.nome as disciplina, p.acertou, p.resposta_usuario, (CASE WHEN p.id IS NOT NULL THEN 1 ELSE 0 END) as respondida FROM questoes q JOIN disciplinas d ON q.disciplina_id = d.id LEFT JOIN progresso p ON q.id = p.questao_id WHERE 1=1"
    p = []
    if disciplina_id: q += " AND q.disciplina_id = ?"; p.append(disciplina_id)
    if apenas_pendentes: q += " AND p.id IS NULL"
    if apenas_erros: q += " AND p.acertou = 0"
    if apenas_acertos: q += " AND p.acertou = 1"
    if busca: q += " AND (q.enunciado LIKE ? OR q.explicacao LIKE ?)"; p.extend([f"%{busca}%", f"%{busca}%"])
    questoes = []
    # Usando ORDER BY RANDOM() no caso do caderno de erros para misturar os erros
    order_clause = "ORDER BY RANDOM()" if apenas_erros else "ORDER BY q.id DESC"
    for r in conn.execute(q + f" {order_clause} LIMIT ?", p + [limit]).fetchall():
        d = dict(r)
        d["alternativas"] = json.loads(d["alternativas"])
        questoes.append(d)
    conn.close()
    return questoes

@app.post("/api/responder")
def responder(req: ResponderRequest):
    conn = sqlite3.connect("estudos.db")
    row = conn.execute("SELECT gabarito, explicacao, video_url FROM questoes WHERE id=?", (req.questao_id,)).fetchone()
    if not row: raise HTTPException(status_code=404)
    acertou = req.resposta.upper().strip()[0] == row[0]
    # Delete previous answer if exists to allow updating (for error notebook)
    conn.execute("DELETE FROM progresso WHERE questao_id=?", (req.questao_id,))
    conn.execute("INSERT INTO progresso (questao_id, acertou, resposta_usuario) VALUES (?, ?, ?)", (req.questao_id, acertou, req.resposta.upper().strip()[0]))
    conn.commit(); conn.close()
    return {"acertou": acertou, "gabarito_correto": row[0], "explicacao": row[1], "video_url": row[2]}

@app.post("/api/responder_lote")
def responder_lote(req: ResponderLoteRequest):
    conn = sqlite3.connect("estudos.db")
    for q_id_str, resposta in req.respostas.items():
        q_id = int(q_id_str)
        row = conn.execute("SELECT gabarito FROM questoes WHERE id=?", (q_id,)).fetchone()
        if row:
            acertou = resposta.upper().strip()[0] == row[0]
            conn.execute("DELETE FROM progresso WHERE questao_id=?", (q_id,))
            conn.execute("INSERT INTO progresso (questao_id, acertou, resposta_usuario) VALUES (?, ?, ?)", (q_id, acertou, resposta.upper().strip()[0]))
    conn.commit()
    conn.close()
    return {"status": "sucesso"}

@app.post("/api/refazer")
def refazer_questao(req: RefazerRequest):
    conn = sqlite3.connect("estudos.db")
    conn.execute("DELETE FROM progresso WHERE questao_id = ?", (req.questao_id,))
    conn.commit()
    conn.close()
    return {"status": "sucesso"}

@app.post("/api/refazer_lote")
def refazer_lote(req: dict):
    # Endpoint to clear progress of an entire list of questions (for Error Notebook)
    ids = req.get("ids", [])
    if not ids: return {"status": "ok"}
    conn = sqlite3.connect("estudos.db")
    conn.executemany("DELETE FROM progresso WHERE questao_id = ?", [(i,) for i in ids])
    conn.commit()
    conn.close()
    return {"status": "sucesso"}

@app.post("/api/questao/html")
def salvar_html(req: SalvarHtmlRequest):
    conn = sqlite3.connect("estudos.db")
    conn.execute("UPDATE questoes SET enunciado_html = ? WHERE id = ?", (req.html, req.questao_id))
    conn.commit()
    conn.close()
    return {"status": "sucesso"}

@app.post("/api/questao/anotacao")
def salvar_anotacao(req: SalvarAnotacaoRequest):
    conn = sqlite3.connect("estudos.db")
    conn.execute("UPDATE questoes SET anotacao = ? WHERE id = ?", (req.anotacao, req.questao_id))
    conn.commit()
    conn.close()
    return {"status": "sucesso"}

@app.post("/api/chat_duvida")
async def chat_duvida(req: ChatDuvidaRequest):
    conn = sqlite3.connect("estudos.db")
    row = conn.execute("SELECT enunciado, alternativas, gabarito, explicacao, disciplina_id FROM questoes WHERE id=?", (req.questao_id,)).fetchone()
    conn.close()
    if not row: raise HTTPException(status_code=404)
    
    contexto = f"Enunciado: {row[0]}\nAlternativas: {row[1]}\nGabarito: {row[2]}\nExplicação do sistema: {row[3]}"
    prompt = f"Você é um professor particular focado em ajudar o aluno a entender uma questão de concurso. Seja amigável, direto e didático.\nREGRA ABSOLUTA: NÃO escreva o seu processo de raciocínio (thinking process) nem use a língua inglesa. Responda APENAS a explicação final, diretamente em português.\nAQUI ESTÁ A QUESTÃO:\n{contexto}\n\nAQUI ESTÁ A DÚVIDA DO ALUNO:\n{req.mensagem}\n\nResponda tirando a dúvida dele de forma clara."
    
    resposta_ia = await conversar_ia(prompt)
    return {"resposta": resposta_ia}

if __name__ == "__main__":
    import uvicorn
    def obter_ip_local():
        try:
            s = socket.socket(socket.AF_INET, socket.SOCK_DGRAM)
            s.connect(("8.8.8.8", 80))
            return s.getsockname()[0]
        except: return "127.0.0.1"

    ip = obter_ip_local()
    print("\n" + "="*70)
    print("🚀 SERVIDOR INICIADO COM SUCESSO! (VERSÃO 2.0)")
    print("="*70)
    print("💻 ACESSE NO COMPUTADOR: 👉 http://127.0.0.1:8000")
    print("📱 ACESSE NO CELULAR:     👉 http://" + ip + ":8000")
    print("="*70 + "\n")
    
    uvicorn.run("main:app", host="0.0.0.0", port=8000, reload=True)
