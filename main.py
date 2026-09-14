import os
import psycopg2
from psycopg2.extras import RealDictCursor
from fastapi import FastAPI, HTTPException, Request
from fastapi.middleware.cors import CORSMiddleware
from fastapi.responses import FileResponse
from pydantic import BaseModel
from typing import Optional, Dict, List
import httpx
import json
import re
import urllib.parse
import socket
import datetime

app = FastAPI(title="ProEstudos - 4.0 (Netflix Profiles + Cloud)")

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
    
    # 1. Tabelas Base
    cursor.execute('''
        CREATE TABLE IF NOT EXISTS perfis (
            id SERIAL PRIMARY KEY,
            nome TEXT NOT NULL,
            avatar TEXT NOT NULL,
            cor TEXT NOT NULL
        )
    ''')

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
    
    # Adicionando o Perfil ID no progresso caso não exista (Para a separação estilo Netflix)
    cursor.execute('''
        DO $$
        BEGIN
            IF NOT EXISTS (SELECT 1 FROM information_schema.columns WHERE table_name='progresso' AND column_name='perfil_id') THEN
                ALTER TABLE progresso ADD COLUMN perfil_id INTEGER REFERENCES perfis(id) ON DELETE CASCADE;
            END IF;
        END $$;
    ''')
    
    # Injetando matérias genéricas (Universal)
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
        cursor.execute("INSERT INTO disciplinas (nome) VALUES (%s) ON CONFLICT (nome) DO NOTHING", (d,))
        
    conn.commit()
    conn.close()

init_db()

# --- MODELOS DE DADOS ---
class ConfigAPI(BaseModel): groq_key: Optional[str] = None
class DisciplinaCreate(BaseModel): nome: str
class PerfilCreate(BaseModel): nome: str; avatar: str; cor: str
class ResponderRequest(BaseModel): questao_id: int; resposta: str; perfil_id: int
class ResponderLoteRequest(BaseModel): respostas: Dict[str, str]; perfil_id: int
class RefazerRequest(BaseModel): questao_id: int; perfil_id: int
class RefazerLoteRequest(BaseModel): ids: List[int]; perfil_id: int
class ChatDuvidaRequest(BaseModel): questao_id: int; mensagem: str
class SalvarAnotacaoRequest(BaseModel): questao_id: int; anotacao: str
class SalvarHtmlRequest(BaseModel): questao_id: int; html: str

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

@app.get("/")
def index():
    if os.path.exists("index.html"):
        return FileResponse("index.html")
    return {"erro": "Arquivo index.html não encontrado."}

# --- ROTAS DE PERFIS (NETFLIX STYLE) ---
@app.get("/api/perfis")
def get_perfis():
    conn = get_db_connection()
    cursor = conn.cursor(cursor_factory=RealDictCursor)
    cursor.execute("SELECT * FROM perfis ORDER BY id")
    perfis = cursor.fetchall()
    conn.close()
    return perfis

@app.post("/api/perfis")
def criar_perfil(req: PerfilCreate):
    conn = get_db_connection()
    cursor = conn.cursor()
    cursor.execute("INSERT INTO perfis (nome, avatar, cor) VALUES (%s, %s, %s) RETURNING id", (req.nome, req.avatar, req.cor))
    p_id = cursor.fetchone()[0]
    conn.commit()
    conn.close()
    return {"id": p_id, "nome": req.nome, "avatar": req.avatar, "cor": req.cor}

@app.delete("/api/perfis/{perfil_id}")
def deletar_perfil(perfil_id: int):
    conn = get_db_connection()
    cursor = conn.cursor()
    cursor.execute("DELETE FROM perfis WHERE id = %s", (perfil_id,))
    conn.commit()
    conn.close()
    return {"status": "sucesso"}

# --- IA GROQ ---
async def get_groq_key():
    key = os.environ.get("GROQ_API_KEY")
    if not key: raise HTTPException(status_code=400, detail="Chave da Groq não configurada no Render.")
    return key.strip()

async def conversar_ia(prompt: str) -> str:
    api_key = await get_groq_key()
    headers = {"Authorization": f"Bearer {api_key}", "Content-Type": "application/json"}
    
    try:
        async with httpx.AsyncClient(timeout=60.0) as client:
            models_response = await client.get("https://api.groq.com/openai/v1/models", headers=headers)
            modelos_brutos = models_response.json().get("data", [])
            modelos_disponiveis = [m["id"] for m in modelos_brutos if "whisper" not in m["id"].lower() and "guard" not in m["id"].lower() and "deepseek" not in m["id"].lower()]
            
            for modelo in modelos_disponiveis:
                payload = {"model": modelo, "messages": [{"role": "user", "content": prompt}], "temperature": 0.7}
                resposta = await client.post("https://api.groq.com/openai/v1/chat/completions", headers=headers, json=payload)
                if resposta.status_code == 200:
                    texto = resposta.json()["choices"][0]["message"]["content"]
                    texto = re.sub(r'<think>.*?</think>', '', texto, flags=re.DOTALL).strip()
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
            modelos_brutos = models_response.json().get("data", [])
            modelos_disponiveis = [m["id"] for m in modelos_brutos if "whisper" not in m["id"].lower() and "guard" not in m["id"].lower() and "deepseek" not in m["id"].lower()]
            
            for modelo in modelos_disponiveis:
                payload = {"model": modelo, "messages": [{"role": "user", "content": prompt}], "temperature": 0.6, "response_format": {"type": "json_object"}}
                resposta = await client.post("https://api.groq.com/openai/v1/chat/completions", headers=headers, json=payload)
                if resposta.status_code == 200:
                    return resposta.json()["choices"][0]["message"]["content"]
            raise HTTPException(status_code=500, detail="Falha ao gerar com IA.")
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

# --- DADOS E ROTAS ---
@app.get("/api/config")
def get_config(): return {"groq_key": "Gerenciada na Nuvem (Invisível e Segura)"}

@app.post("/api/config")
def set_config(req: ConfigAPI): return {"status": "Ok"}

@app.post("/api/reset_db")
def reset_db():
    conn = get_db_connection()
    cursor = conn.cursor()
    cursor.execute("TRUNCATE TABLE progresso, questoes, disciplinas RESTART IDENTITY CASCADE;")
    conn.commit()
    conn.close()
    init_db()
    return {"status": "Limpo."}

@app.get("/api/backup")
def backup_db():
    return FileResponse("backup_info.txt", media_type="text/plain", filename="Aviso_Backup.txt")

@app.post("/api/disciplina")
def criar_disciplina(disciplina: DisciplinaCreate):
    conn = get_db_connection()
    cursor = conn.cursor()
    cursor.execute("INSERT INTO disciplinas (nome) VALUES (%s) ON CONFLICT DO NOTHING", (disciplina.nome,))
    conn.commit()
    conn.close()
    return {"status": "sucesso"}

@app.get("/api/dados")
def get_dados(perfil_id: int = 0):
    conn = get_db_connection()
    cursor = conn.cursor(cursor_factory=RealDictCursor)
    
    cursor.execute("SELECT id, nome FROM disciplinas ORDER BY nome")
    disciplinas = cursor.fetchall()
    
    cursor.execute("SELECT COUNT(*) as count FROM questoes")
    tot = cursor.fetchone()['count']
    
    # Buscando acertos do Perfil logado
    cursor.execute("SELECT COUNT(*) as count FROM progresso WHERE acertou = TRUE AND perfil_id = %s", (perfil_id,))
    ac = cursor.fetchone()['count']
    
    cursor.execute("SELECT COUNT(*) as count FROM progresso WHERE acertou = FALSE AND perfil_id = %s", (perfil_id,))
    er = cursor.fetchone()['count']
    
    cursor.execute("SELECT DATE(data_resolucao) as data, acertou, COUNT(*) as qtd FROM progresso WHERE perfil_id = %s GROUP BY DATE(data_resolucao), acertou ORDER BY DATE(data_resolucao) ASC", (perfil_id,))
    datas_raw = cursor.fetchall()
    
    historico_dias = {}
    hoje = datetime.date.today()
    for i in range(6, -1, -1):
        d = (hoje - datetime.timedelta(days=i)).strftime('%Y-%m-%d')
        historico_dias[d] = {"acertos": 0, "erros": 0}
        
    for r in datas_raw:
        data_str = r['data'].strftime('%Y-%m-%d') if hasattr(r['data'], 'strftime') else str(r['data'])
        if data_str in historico_dias:
            if r['acertou'] is True or r['acertou'] == 1: historico_dias[data_str]['acertos'] += r['qtd']
            else: historico_dias[data_str]['erros'] += r['qtd']
            
    lista_historico = [{"data": k, "acertos": v["acertos"], "erros": v["erros"]} for k, v in historico_dias.items()]

    cursor.execute("SELECT DATE(data_resolucao) as data FROM progresso WHERE perfil_id = %s GROUP BY DATE(data_resolucao) ORDER BY DATE(data_resolucao) DESC", (perfil_id,))
    datas_unicas = cursor.fetchall()
    streak = 0
    data_check = hoje
    
    if datas_unicas:
        primeira_data = datas_unicas[0]['data']
        if not hasattr(primeira_data, 'strftime'): primeira_data = datetime.datetime.strptime(str(primeira_data), '%Y-%m-%d').date()
        
        if primeira_data == hoje or primeira_data == (hoje - datetime.timedelta(days=1)):
            for r in datas_unicas:
                d = r['data']
                if not hasattr(d, 'strftime'): d = datetime.datetime.strptime(str(d), '%Y-%m-%d').date()
                if d == data_check or (streak == 0 and d == hoje - datetime.timedelta(days=1)):
                    if streak == 0 and d != hoje: data_check = hoje - datetime.timedelta(days=1)
                    streak += 1
                    data_check -= datetime.timedelta(days=1)
                else: break

    raio_x = []
    for d in disciplinas:
        cursor.execute("SELECT p.acertou, COUNT(*) as qtd FROM progresso p JOIN questoes q ON p.questao_id = q.id WHERE q.disciplina_id = %s AND p.perfil_id = %s GROUP BY p.acertou", (d['id'], perfil_id))
        res = cursor.fetchall()
        d_acertos = 0; d_erros = 0
        for r in res:
            if r['acertou'] is True or r['acertou'] == 1: d_acertos = r['qtd']
            else: d_erros = r['qtd']
        d_total = d_acertos + d_erros
        if d_total > 0:
            raio_x.append({"nome": d['nome'], "total": d_total, "acertos": d_acertos, "erros": d_erros, "aproveitamento": round((d_acertos / d_total) * 100, 1)})
    
    raio_x.sort(key=lambda x: x['total'], reverse=True)
    conn.close()
    
    return {
        "disciplinas": disciplinas, 
        "stats": {
            "total": tot, "acertos": ac, "erros": er, 
            "aproveitamento": round((ac/(ac+er)*100) if ac+er>0 else 0, 1),
            "streak": streak, "raio_x": raio_x, "historico": lista_historico
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
    
    topico_txt = f" Foco Específico exigido: {req.topico}." if req.topico else ""
    concurso_txt = f" OBRIGATÓRIO SER DO CONCURSO/ÓRGÃO/CARGO: '{req.orgao}'." if req.orgao else ""
    banca_exigida = req.banca if req.banca else "qualquer banca real"
    
    prompt = f"""Você é um banco de dados de concursos. Nível: {req.nivel}.
Recupere {req.quantidade} questões {'REAIS de provas anteriores' if req.tipo == 'reais' else 'INÉDITAS criadas por você'} da disciplina '{row['nome']}'.
{concurso_txt} Banca exigida: {banca_exigida}.{topico_txt}

DIVERSIDADE TOTAL (NÃO REPITA). Escreva o texto completo das alternativas.
JSON Exato:
{{
    "questoes": [
        {{
            "enunciado": "...",
            "alternativas": ["A) ...", "B) ...", "C) ...", "D) ...", "E) ..."],
            "gabarito": "A",
            "explicacao": "...",
            "assunto_para_busca": "...",
            "banca": "{banca_exigida}",
            "concurso": "{req.orgao if req.orgao else 'Concurso Real'}",
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
    concurso_txt = f" OBRIGATÓRIO CONCURSO: '{req.orgao}'." if req.orgao else ""
    
    for d in disciplinas:
        prompt = f"""Gere {qtd} questões {'REAIS' if req.tipo == 'reais' else 'INÉDITAS'} de '{d['nome']}'. Nível: {req.nivel}. {concurso_txt}
JSON: {{"questoes": [{{"enunciado": "...", "alternativas": ["A)","B)","C)","D)","E)"], "gabarito": "A", "explicacao": "...", "assunto_para_busca": "...", "banca": "{req.banca}", "concurso": "{req.orgao}", "ano": 2024}}]}}"""
        await gerar_lote_questoes_ia(prompt, d['id'])
    return {"status": "sucesso"}

@app.get("/api/questoes")
def get_questoes(perfil_id: int = 0, disciplina_id: Optional[int]=None, apenas_pendentes: bool=False, apenas_erros: bool=False, apenas_acertos: bool=False, busca: Optional[str]=None, limit: int=50):
    conn = get_db_connection()
    cursor = conn.cursor(cursor_factory=RealDictCursor)
    q = "SELECT q.*, d.nome as disciplina, p.acertou, p.resposta_usuario, (CASE WHEN p.id IS NOT NULL THEN 1 ELSE 0 END) as respondida FROM questoes q JOIN disciplinas d ON q.disciplina_id = d.id LEFT JOIN progresso p ON q.id = p.questao_id AND p.perfil_id = %s WHERE 1=1"
    p = [perfil_id]
    
    if disciplina_id: q += " AND q.disciplina_id = %s"; p.append(disciplina_id)
    if apenas_pendentes: q += " AND p.id IS NULL"
    if apenas_erros: q += " AND p.acertou = FALSE"
    if apenas_acertos: q += " AND p.acertou = TRUE"
    if busca: q += " AND (q.enunciado ILIKE %s OR q.explicacao ILIKE %s)"; p.extend([f"%{busca}%", f"%{busca}%"])
        
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
    cursor.execute("DELETE FROM progresso WHERE questao_id=%s AND perfil_id=%s", (req.questao_id, req.perfil_id))
    cursor.execute("INSERT INTO progresso (questao_id, perfil_id, acertou, resposta_usuario) VALUES (%s, %s, %s, %s)", (req.questao_id, req.perfil_id, acertou, req.resposta.upper().strip()[0]))
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
            cursor.execute("DELETE FROM progresso WHERE questao_id=%s AND perfil_id=%s", (q_id, req.perfil_id))
            cursor.execute("INSERT INTO progresso (questao_id, perfil_id, acertou, resposta_usuario) VALUES (%s, %s, %s, %s)", (q_id, req.perfil_id, acertou, resposta.upper().strip()[0]))
    conn.commit()
    conn.close()
    return {"status": "sucesso"}

@app.post("/api/refazer_lote")
def refazer_lote(req: RefazerLoteRequest):
    if not req.ids: return {"status": "ok"}
    conn = get_db_connection()
    cursor = conn.cursor()
    cursor.executemany("DELETE FROM progresso WHERE questao_id = %s AND perfil_id = %s", [(i, req.perfil_id) for i in req.ids])
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
    cursor.execute("SELECT enunciado, alternativas, gabarito, explicacao FROM questoes WHERE id=%s", (req.questao_id,))
    row = cursor.fetchone()
    conn.close()
    if not row: raise HTTPException(status_code=404)
    
    contexto = f"Enunciado: {row['enunciado']}\nAlternativas: {row['alternativas']}\nGabarito: {row['gabarito']}\nExplicação: {row['explicacao']}"
    prompt = f"Seja um professor direto. Explique em português. QUESTÃO:\n{contexto}\n\nDÚVIDA DO ALUNO:\n{req.mensagem}"
    resposta_ia = await conversar_ia(prompt)
    return {"resposta": resposta_ia}

if __name__ == "__main__":
    import uvicorn
    uvicorn.run("main:app", host="0.0.0.0", port=8000, reload=True)
