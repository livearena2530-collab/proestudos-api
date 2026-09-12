import os
import psycopg2
from psycopg2.extras import RealDictCursor
from fastapi import FastAPI, HTTPException, Request
from fastapi.middleware.cors import CORSMiddleware
from fastapi.responses import FileResponse
from pydantic import BaseModel
from typing import Optional, Dict
import httpx
import json
import re
import urllib.parse
import socket
import datetime

app = FastAPI(title="ProEstudos - 3.0 (Cloud Database)")

app.add_middleware(
    CORSMiddleware,
    allow_origins=["*"], 
    allow_credentials=True,
    allow_methods=["*"],
    allow_headers=["*"],
)

# 🔐 Puxando as chaves do Cofre do Render!
DB_URL = os.environ.get("DATABASE_URL")

def get_db_connection():
    if not DB_URL:
        print("⚠️ ERRO CRÍTICO: DATABASE_URL não encontrada no painel do Render!")
    return psycopg2.connect(DB_URL)

def init_db():
    if not DB_URL:
        return
        
    conn = get_db_connection()
    cursor = conn.cursor()
    
    # Criando as tabelas no Supabase (PostgreSQL)
    cursor.execute('''
        CREATE TABLE IF NOT EXISTS disciplinas (
            id SERIAL PRIMARY KEY,
            nome TEXT UNIQUE NOT NULL
        )
    ''')
    
    cursor.execute('''
        CREATE TABLE IF NOT EXISTS questoes (
            id SERIAL PRIMARY KEY,
            disciplina_id INTEGER REFERENCES disciplinas(id) ON DELETE CASCADE,
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

    cursor.execute('''
        CREATE TABLE IF NOT EXISTS progresso (
            id SERIAL PRIMARY KEY,
            questao_id INTEGER REFERENCES questoes(id) ON DELETE CASCADE,
            acertou BOOLEAN,
            resposta_usuario TEXT,
            data_resolucao TIMESTAMP DEFAULT CURRENT_TIMESTAMP
        )
    ''')
    
    # Injetando as matérias genéricas que servem para qualquer concurso do Brasil
    disciplinas_padrao = [
        "Língua Portuguesa", "Matemática", "Raciocínio Lógico", "Informática",
        "Direito Constitucional", "Direito Administrativo", "Direito Penal", 
        "Direito Processual Penal", "Legislação Extravagante", "Direitos Humanos",
        "Conhecimentos Pedagógicos", "Legislação Educacional", 
        "Administração Pública", "Administração Financeira e Orçamentária (AFO)",
        "Atualidades", "Redação Oficial", "Física", "Química", "Biologia",
        "História", "Geografia", "Filosofia", "Sociologia"
    ]
    for d in disciplinas_padrao:
        # ON CONFLICT DO NOTHING evita duplicar as matérias
        cursor.execute("INSERT INTO disciplinas (nome) VALUES (%s) ON CONFLICT (nome) DO NOTHING", (d,))
        
    conn.commit()
    conn.close()

# Inicializa o banco ao ligar o servidor
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
    key = os.environ.get("GROQ_API_KEY")
    if not key:
        raise HTTPException(status_code=400, detail="Chave da Groq não configurada nas variáveis de ambiente do Render.")
    return key.strip()

async def conversar_ia(prompt: str) -> str:
    api_key = await get_groq_key()
    headers = {"Authorization": f"Bearer {api_key}", "Content-Type": "application/json"}
    
    try:
        async with httpx.AsyncClient(timeout=60.0) as client:
            models_response = await client.get("https://api.groq.com/openai/v1/models", headers=headers)
            if models_response.status_code != 200:
                raise HTTPException(status_code=500, detail="Erro ao listar modelos Groq.")
            
            modelos_brutos = models_response.json().get("data", [])
            modelos_disponiveis = [m["id"] for m in modelos_brutos if "whisper" not in m["id"].lower() and "guard" not in m["id"].lower() and "deepseek" not in m["id"].lower()]
            
            if not modelos_disponiveis:
                raise HTTPException(status_code=500, detail="Nenhum modelo válido encontrado.")

            for modelo in modelos_disponiveis:
                payload = {
                    "model": modelo,
                    "messages": [{"role": "user", "content": prompt}],
                    "temperature": 0.7
                }
                resposta = await client.post("https://api.groq.com/openai/v1/chat/completions", headers=headers, json=payload)
                if resposta.status_code == 200:
                    texto = resposta.json()["choices"][0]["message"]["content"]
                    texto = re.sub(r'<think>.*?</think>', '', texto, flags=re.DOTALL).strip()
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
            
        conn = get_db_connection()
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
                              VALUES (%s, %s, %s, %s, %s, %s, %s, %s, %s, %s)''', 
                           (disciplina_id, enunciado, json.dumps(alts_limpas), gabarito, explicacao, f"https://www.youtube.com/results?search_query={query}", banca, ano, concurso, topico_especifico))

        conn.commit()
        conn.close()
    except Exception as e:
        print(f"Erro ao processar lote da IA: {e}")
        if 'conn' in locals(): conn.close()

# Mantém a rota /api/config funcionando silenciosamente para o frontend antigo não dar erro
@app.get("/api/config")
def get_config():
    return {"groq_key": "Gerenciada na Nuvem (Invisível e Segura)"}

@app.post("/api/config")
def set_config(req: ConfigAPI):
    return {"status": "A chave agora é lida direto do painel do Render!"}

@app.post("/api/reset_db")
def reset_db():
    conn = get_db_connection()
    cursor = conn.cursor()
    # TRUNCATE é a forma profissional de limpar bancos PostgreSQL e zerar o ID (CASCADE apaga as dependências)
    cursor.execute("TRUNCATE TABLE progresso, questoes, disciplinas RESTART IDENTITY CASCADE;")
    conn.commit()
    conn.close()
    init_db()
    return {"status": "Limpo."}

@app.get("/api/backup")
def backup_db():
    file_path = "backup_info.txt"
    with open(file_path, "w") as f:
        f.write("Seu banco de dados agora esta blindado na nuvem (Supabase).\nOs backups sao feitos automaticamente pelo painel do Supabase, voce nunca mais perdera nada!")
    return FileResponse(file_path, media_type="text/plain", filename="Aviso_Backup.txt")

@app.post("/api/disciplina")
def criar_disciplina(disciplina: DisciplinaCreate):
    try:
        conn = get_db_connection()
        cursor = conn.cursor()
        cursor.execute("INSERT INTO disciplinas (nome) VALUES (%s)", (disciplina.nome,))
        conn.commit()
        conn.close()
        return {"status": "sucesso"}
    except Exception:
        raise HTTPException(status_code=400, detail="Já existe ou erro ao criar.")

@app.get("/api/dados")
def get_dados():
    conn = get_db_connection()
    cursor = conn.cursor(cursor_factory=RealDictCursor)
    
    cursor.execute("SELECT id, nome FROM disciplinas ORDER BY nome")
    disciplinas = cursor.fetchall()
    
    cursor.execute("SELECT COUNT(*) as count FROM questoes")
    tot = cursor.fetchone()['count']
    
    cursor.execute("SELECT COUNT(*) as count FROM progresso WHERE acertou = TRUE")
    ac = cursor.fetchone()['count']
    
    cursor.execute("SELECT COUNT(*) as count FROM progresso WHERE acertou = FALSE")
    er = cursor.fetchone()['count']
    
    cursor.execute("SELECT DATE(data_resolucao) as data, acertou, COUNT(*) as qtd FROM progresso GROUP BY DATE(data_resolucao), acertou ORDER BY DATE(data_resolucao) ASC")
    datas_raw = cursor.fetchall()
    
    historico_dias = {}
    hoje = datetime.date.today()
    for i in range(6, -1, -1):
        d = (hoje - datetime.timedelta(days=i)).strftime('%Y-%m-%d')
        historico_dias[d] = {"acertos": 0, "erros": 0}
        
    for r in datas_raw:
        data_val = r['data']
        data_str = data_val.strftime('%Y-%m-%d') if hasattr(data_val, 'strftime') else str(data_val)
        if data_str in historico_dias:
            if r['acertou'] is True or r['acertou'] == 1:
                historico_dias[data_str]['acertos'] += r['qtd']
            else:
                historico_dias[data_str]['erros'] += r['qtd']
            
    lista_historico = [{"data": k, "acertos": v["acertos"], "erros": v["erros"]} for k, v in historico_dias.items()]

    # Streak (Ofensiva)
    cursor.execute("SELECT DATE(data_resolucao) as data FROM progresso GROUP BY DATE(data_resolucao) ORDER BY DATE(data_resolucao) DESC")
    datas_unicas = cursor.fetchall()
    streak = 0
    data_check = hoje
    
    if datas_unicas:
        primeira_data_val = datas_unicas[0]['data']
        primeira_data = primeira_data_val if hasattr(primeira_data_val, 'strftime') else datetime.datetime.strptime(str(primeira_data_val), '%Y-%m-%d').date()
        
        if primeira_data == hoje or primeira_data == (hoje - datetime.timedelta(days=1)):
            for r in datas_unicas:
                d_val = r['data']
                d = d_val if hasattr(d_val, 'strftime') else datetime.datetime.strptime(str(d_val), '%Y-%m-%d').date()
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
        cursor.execute("SELECT p.acertou, COUNT(*) as qtd FROM progresso p JOIN questoes q ON p.questao_id = q.id WHERE q.disciplina_id = %s GROUP BY p.acertou", (d_id,))
        res = cursor.fetchall()
        d_acertos = 0
        d_erros = 0
        for r in res:
            if r['acertou'] is True or r['acertou'] == 1: d_acertos = r['qtd']
            else: d_erros = r['qtd']
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
    conn = get_db_connection()
    cursor = conn.cursor(cursor_factory=RealDictCursor)
    cursor.execute("SELECT nome FROM disciplinas WHERE id = %s", (req.disciplina_id,))
    row = cursor.fetchone()
    conn.close()
    if not row: raise HTTPException(status_code=404)
    
    topico_txt = f" Foco/Assunto Específico exigido: {req.topico}." if req.topico else ""
    concurso_txt = f" CONCURSO EXIGIDO: Traga OBRIGATORIAMENTE questões que foram aplicadas NO CONCURSO DO SEGUINTE ÓRGÃO/CARGO: '{req.orgao}'. ISSO É UMA REGRA CRÍTICA." if req.orgao else ""
    
    if req.tipo == "reais":
        banca_exigida = req.banca if req.banca else "qualquer banca real"
        prompt = f"""Você é um banco de dados rigoroso de concursos públicos.
Sua tarefa é recuperar EXATAMENTE {req.quantidade} questões REAIS de provas anteriores da disciplina '{row['nome']}'.
Nível de escolaridade: {req.nivel}. Banca exigida: {banca_exigida}.{concurso_txt}{topico_txt}

REGRAS CRÍTICAS (PUNIÇÃO SE DESCUMPRIR):
1. DIVERSIDADE EXTREMA: NENHUMA questão pode ser repetida. Puxe temas diferentes.
2. DADOS DA PROVA REAIS: É PROIBIDO usar a palavra "Simulado". Preencha "concurso" obrigatoriamente com o nome do ÓRGÃO E O CARGO correspondentes àquele solicitado.
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
        prompt = f"""Crie {req.quantidade} questões INÉDITAS sobre '{row['nome']}'. 
Nível: {req.nivel}. Foco: {req.topico if req.topico else 'Geral'}. 
NENHUMA QUESTÃO PODE SER REPETIDA. Regra: Escreva o TEXTO COMPLETO em cada alternativa.
{concurso_txt}

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
            "concurso": "{req.orgao if req.orgao else 'Questão Inédita'}",
            "ano": 2024
        }}
    ]
}}"""

    await gerar_lote_questoes_ia(prompt, req.disciplina_id, req.topico)
    return {"status": "sucesso"}

@app.post("/api/gerar_simulado")
async def api_gerar_simulado(req: GerarSimuladoRequest):
    conn = get_db_connection()
    cursor = conn.cursor(cursor_factory=RealDictCursor)
    cursor.execute("SELECT id, nome FROM disciplinas")
    disciplinas = cursor.fetchall()
    conn.close()
    if not disciplinas: raise HTTPException(status_code=400)
    qtd = max(1, req.quantidade // len(disciplinas))
    
    concurso_txt = f" CONCURSO EXIGIDO: Traga OBRIGATORIAMENTE questões que foram aplicadas NO CONCURSO DO SEGUINTE ÓRGÃO/CARGO: '{req.orgao}'." if req.orgao else ""
    banca_exigida = req.banca if req.banca else "qualquer banca real"
    
    for d in disciplinas:
        d_id = d['id']
        nome = d['nome']
        if req.tipo == "reais":
            prompt = f"""Recupere {qtd} questões REAIS de concursos passados da disciplina '{nome}'. 
Nível: {req.nivel}. Banca exigida: {banca_exigida}.{concurso_txt} PROIBIDO INVENTAR. AS QUESTÕES DEVEM SER DIFERENTES ENTRE SI.
REGRAS: PROIBIDO usar "Simulado". Preencha "concurso" com Órgão e Cargo reais. O texto das alternativas deve ser COMPLETO (proibido apenas letras soltas).
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
            prompt = f"""Gere {qtd} questões INÉDITAS de '{nome}'. Nível: {req.nivel}. DIVERSIDADE TOTAL ENTRE ELAS. O texto das alternativas deve ser COMPLETO. {concurso_txt}
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
    conn = get_db_connection()
    cursor = conn.cursor(cursor_factory=RealDictCursor)
    q = "SELECT q.*, d.nome as disciplina, p.acertou, p.resposta_usuario, (CASE WHEN p.id IS NOT NULL THEN 1 ELSE 0 END) as respondida FROM questoes q JOIN disciplinas d ON q.disciplina_id = d.id LEFT JOIN progresso p ON q.id = p.questao_id WHERE 1=1"
    p = []
    
    if disciplina_id: 
        q += " AND q.disciplina_id = %s"
        p.append(disciplina_id)
    if apenas_pendentes: 
        q += " AND p.id IS NULL"
    if apenas_erros: 
        q += " AND p.acertou = FALSE"
    if apenas_acertos: 
        q += " AND p.acertou = TRUE"
    if busca: 
        q += " AND (q.enunciado ILIKE %s OR q.explicacao ILIKE %s)"
        p.extend([f"%{busca}%", f"%{busca}%"])
        
    order_clause = "ORDER BY RANDOM()" if apenas_erros else "ORDER BY q.id DESC"
    q += f" {order_clause} LIMIT %s"
    p.append(limit)
    
    cursor.execute(q, tuple(p))
    questoes = []
    for r in cursor.fetchall():
        d = dict(r)
        d["alternativas"] = json.loads(d["alternativas"])
        questoes.append(d)
        
    conn.close()
    return questoes

@app.post("/api/responder")
def responder(req: ResponderRequest):
    conn = get_db_connection()
    cursor = conn.cursor(cursor_factory=RealDictCursor)
    cursor.execute("SELECT gabarito, explicacao, video_url FROM questoes WHERE id=%s", (req.questao_id,))
    row = cursor.fetchone()
    if not row: raise HTTPException(status_code=404)
    
    acertou = req.resposta.upper().strip()[0] == row['gabarito']
    cursor.execute("DELETE FROM progresso WHERE questao_id=%s", (req.questao_id,))
    cursor.execute("INSERT INTO progresso (questao_id, acertou, resposta_usuario) VALUES (%s, %s, %s)", (req.questao_id, acertou, req.resposta.upper().strip()[0]))
    conn.commit()
    conn.close()
    return {"acertou": acertou, "gabarito_correto": row['gabarito'], "explicacao": row['explicacao'], "video_url": row['video_url']}

@app.post("/api/responder_lote")
def responder_lote(req: ResponderLoteRequest):
    conn = get_db_connection()
    cursor = conn.cursor(cursor_factory=RealDictCursor)
    for q_id_str, resposta in req.respostas.items():
        q_id = int(q_id_str)
        cursor.execute("SELECT gabarito FROM questoes WHERE id=%s", (q_id,))
        row = cursor.fetchone()
        if row:
            acertou = resposta.upper().strip()[0] == row['gabarito']
            cursor.execute("DELETE FROM progresso WHERE questao_id=%s", (q_id,))
            cursor.execute("INSERT INTO progresso (questao_id, acertou, resposta_usuario) VALUES (%s, %s, %s)", (q_id, acertou, resposta.upper().strip()[0]))
    conn.commit()
    conn.close()
    return {"status": "sucesso"}

@app.post("/api/refazer")
def refazer_questao(req: RefazerRequest):
    conn = get_db_connection()
    cursor = conn.cursor()
    cursor.execute("DELETE FROM progresso WHERE questao_id = %s", (req.questao_id,))
    conn.commit()
    conn.close()
    return {"status": "sucesso"}

@app.post("/api/refazer_lote")
def refazer_lote(req: dict):
    ids = req.get("ids", [])
    if not ids: return {"status": "ok"}
    conn = get_db_connection()
    cursor = conn.cursor()
    cursor.executemany("DELETE FROM progresso WHERE questao_id = %s", [(i,) for i in ids])
    conn.commit()
    conn.close()
    return {"status": "sucesso"}

@app.post("/api/questao/html")
def salvar_html(req: SalvarHtmlRequest):
    conn = get_db_connection()
    cursor = conn.cursor()
    cursor.execute("UPDATE questoes SET enunciado_html = %s WHERE id = %s", (req.html, req.questao_id))
    conn.commit()
    conn.close()
    return {"status": "sucesso"}

@app.post("/api/questao/anotacao")
def salvar_anotacao(req: SalvarAnotacaoRequest):
    conn = get_db_connection()
    cursor = conn.cursor()
    cursor.execute("UPDATE questoes SET anotacao = %s WHERE id = %s", (req.anotacao, req.questao_id))
    conn.commit()
    conn.close()
    return {"status": "sucesso"}

@app.post("/api/chat_duvida")
async def chat_duvida(req: ChatDuvidaRequest):
    conn = get_db_connection()
    cursor = conn.cursor(cursor_factory=RealDictCursor)
    cursor.execute("SELECT enunciado, alternativas, gabarito, explicacao, disciplina_id FROM questoes WHERE id=%s", (req.questao_id,))
    row = cursor.fetchone()
    conn.close()
    if not row: raise HTTPException(status_code=404)
    
    contexto = f"Enunciado: {row['enunciado']}\nAlternativas: {row['alternativas']}\nGabarito: {row['gabarito']}\nExplicação do sistema: {row['explicacao']}"
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
    print("🚀 SERVIDOR (PostgreSQL) INICIADO COM SUCESSO! (VERSÃO 3.0)")
    print("="*70)
    print("💻 ACESSE NO COMPUTADOR: 👉 http://127.0.0.1:8000")
    print("📱 ACESSE NO CELULAR:     👉 http://" + ip + ":8000")
    print("="*70 + "\n")
    
    uvicorn.run("main:app", host="0.0.0.0", port=8000, reload=True)
