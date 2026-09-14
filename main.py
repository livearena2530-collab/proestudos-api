import os
import json
import psycopg2
from psycopg2.extras import RealDictCursor
from fastapi import FastAPI, HTTPException
from fastapi.middleware.cors import CORSMiddleware
from fastapi.responses import JSONResponse
from pydantic import BaseModel
from typing import List, Optional
import httpx

app = FastAPI(title="ProEstudos API")

# Libera o acesso para o GitHub Pages
app.add_middleware(
    CORSMiddleware,
    allow_origins=["*"],
    allow_credentials=True,
    allow_methods=["*"],
    allow_headers=["*"],
)

# Pega as chaves ocultas do Render
DB_URL = os.environ.get("DATABASE_URL")
GROQ_API_KEY = os.environ.get("GROQ_API_KEY")

# Conexão com o Supabase
def get_db_connection():
    try:
        return psycopg2.connect(DB_URL, cursor_factory=RealDictCursor)
    except Exception as e:
        print(f"Erro ao conectar ao banco: {e}")
        raise e

# Inicialização das Tabelas no Supabase
def init_db():
    conn = get_db_connection()
    cursor = conn.cursor()
    
    cursor.execute('''
        CREATE TABLE IF NOT EXISTS perfis (
            id SERIAL PRIMARY KEY,
            nome TEXT NOT NULL,
            cor TEXT NOT NULL,
            avatar TEXT NOT NULL
        )
    ''')

    cursor.execute('''
        CREATE TABLE IF NOT EXISTS disciplinas (
            id SERIAL PRIMARY KEY,
            nome TEXT NOT NULL UNIQUE
        )
    ''')
    
    cursor.execute('''
        CREATE TABLE IF NOT EXISTS questoes (
            id SERIAL PRIMARY KEY,
            disciplina_id INTEGER REFERENCES disciplinas(id) ON DELETE CASCADE,
            enunciado TEXT NOT NULL,
            opcoes TEXT NOT NULL, 
            correta INTEGER NOT NULL,
            explicacao TEXT NOT NULL
        )
    ''')
    
    cursor.execute('''
        CREATE TABLE IF NOT EXISTS progresso (
            id SERIAL PRIMARY KEY,
            perfil_id INTEGER REFERENCES perfis(id) ON DELETE CASCADE,
            questao_id INTEGER REFERENCES questoes(id) ON DELETE CASCADE,
            acertou BOOLEAN NOT NULL,
            data TIMESTAMP DEFAULT CURRENT_TIMESTAMP
        )
    ''')
    
    # GARANTIA: Adiciona a coluna data se o banco for antigo (Corrige o erro do gráfico)
    cursor.execute('ALTER TABLE progresso ADD COLUMN IF NOT EXISTS data TIMESTAMP DEFAULT CURRENT_TIMESTAMP')

    # Insere matérias iniciais se estiver vazio
    cursor.execute('SELECT COUNT(*) as count FROM disciplinas')
    if cursor.fetchone()['count'] == 0:
        materias = ["Língua Portuguesa", "Matemática", "Raciocínio Lógico", "Informática", "Direito Constitucional", "Direito Administrativo"]
        for m in materias:
            cursor.execute('INSERT INTO disciplinas (nome) VALUES (%s)', (m,))
            
    conn.commit()
    conn.close()

# Inicia o banco ao rodar o servidor
try:
    init_db()
except Exception as e:
    print(f"Aviso: Não foi possível iniciar o DB agora. {e}")

# --- MODELOS DE DADOS ---
class RespostaQuestao(BaseModel):
    perfil_id: int
    acertou: bool

class FiltrosIA(BaseModel):
    disciplina_id: int
    quantidade: int
    estilo: str
    area: str
    banca: str
    cargo: str

class PerfilCreate(BaseModel):
    nome: str
    cor: str
    avatar: str

# --- ROTAS PWA (Aplicativo) ---
@app.get("/manifest.json")
def get_manifest():
    return {
        "name": "ProEstudos Concursos",
        "short_name": "ProEstudos",
        "start_url": "/",
        "display": "standalone",
        "background_color": "#0f172a",
        "theme_color": "#4f46e5",
        "icons": [
            {"src": "https://cdn-icons-png.flaticon.com/512/3534/3534063.png", "sizes": "192x192", "type": "image/png"},
            {"src": "https://cdn-icons-png.flaticon.com/512/3534/3534063.png", "sizes": "512x512", "type": "image/png"}
        ]
    }

# --- ROTAS DA API ---

@app.get("/api/perfis")
def get_perfis():
    conn = get_db_connection()
    cursor = conn.cursor()
    cursor.execute('SELECT * FROM perfis')
    perfis = cursor.fetchall()
    conn.close()
    return perfis

@app.post("/api/perfis")
def criar_perfil(perfil: PerfilCreate):
    conn = get_db_connection()
    cursor = conn.cursor()
    cursor.execute('INSERT INTO perfis (nome, cor, avatar) VALUES (%s, %s, %s) RETURNING id', 
                  (perfil.nome, perfil.cor, perfil.avatar))
    novo_id = cursor.fetchone()['id']
    conn.commit()
    conn.close()
    return {"id": novo_id, "nome": perfil.nome}

@app.get("/api/disciplinas")
def get_disciplinas():
    conn = get_db_connection()
    cursor = conn.cursor()
    cursor.execute('SELECT * FROM disciplinas ORDER BY nome')
    disciplinas = cursor.fetchall()
    conn.close()
    return disciplinas

@app.get("/api/disciplinas/{disciplina_id}/questoes")
def get_questoes(disciplina_id: int, perfil_id: int):
    conn = get_db_connection()
    cursor = conn.cursor()
    
    # Busca as questões da disciplina
    cursor.execute('SELECT * FROM questoes WHERE disciplina_id = %s ORDER BY id DESC', (disciplina_id,))
    questoes_db = cursor.fetchall()
    
    questoes = []
    for q in questoes_db:
        # Busca se este perfil já respondeu esta questão
        cursor.execute('SELECT acertou FROM progresso WHERE questao_id = %s AND perfil_id = %s ORDER BY id DESC LIMIT 1', (q['id'], perfil_id))
        prog = cursor.fetchone()
        
        q_dict = dict(q)
        q_dict['opcoes'] = json.loads(q_dict['opcoes'])
        q_dict['respondida'] = True if prog else False
        q_dict['acertou_ultima'] = prog['acertou'] if prog else None
        questoes.append(q_dict)
        
    conn.close()
    return questoes

@app.post("/api/questoes/{questao_id}/responder")
def responder_questao(questao_id: int, resp: RespostaQuestao):
    conn = get_db_connection()
    cursor = conn.cursor()
    cursor.execute('INSERT INTO progresso (perfil_id, questao_id, acertou) VALUES (%s, %s, %s)',
                   (resp.perfil_id, questao_id, resp.acertou))
    conn.commit()
    conn.close()
    return {"status": "ok"}

@app.get("/api/estatisticas")
def get_estatisticas(perfil_id: int):
    conn = get_db_connection()
    cursor = conn.cursor()
    
    cursor.execute('SELECT COUNT(*) as acertos FROM progresso WHERE perfil_id = %s AND acertou = TRUE', (perfil_id,))
    acertos = cursor.fetchone()['acertos']
    
    cursor.execute('SELECT COUNT(*) as erros FROM progresso WHERE perfil_id = %s AND acertou = FALSE', (perfil_id,))
    erros = cursor.fetchone()['erros']
    
    # Histórico dos últimos 7 dias
    cursor.execute('''
        SELECT DATE(data) as dia, COUNT(*) as total 
        FROM progresso 
        WHERE perfil_id = %s AND data >= CURRENT_DATE - INTERVAL '7 days'
        GROUP BY dia ORDER BY dia
    ''', (perfil_id,))
    historico = cursor.fetchall()
    
    conn.close()
    return {"acertos": acertos, "erros": erros, "total": acertos + erros, "historico": [dict(h) for h in historico]}

@app.post("/api/gerar")
async def gerar_questoes_ia(filtros: FiltrosIA):
    if not GROQ_API_KEY:
        raise HTTPException(status_code=500, detail="Chave da API Groq não configurada no servidor.")
        
    conn = get_db_connection()
    cursor = conn.cursor()
    cursor.execute('SELECT nome FROM disciplinas WHERE id = %s', (filtros.disciplina_id,))
    disc = cursor.fetchone()
    
    if not disc:
        conn.close()
        raise HTTPException(status_code=404, detail="Disciplina não encontrada")
        
    materia_nome = disc['nome']
    
    # Construção do Prompt Baseado nos Filtros da Interface
    prompt = f"Gere {filtros.quantidade} questões de múltipla escolha sobre a disciplina {materia_nome}.\n"
    prompt += f"Estilo: {filtros.estilo}.\n"
    
    if filtros.area != "Geral / Sem Filtro":
        prompt += f"Foco na Área do Concurso: {filtros.area}.\n"
        
    if filtros.banca != "Diversas Bancas":
        prompt += f"Simular o estilo da Banca: {filtros.banca}.\n"
        
    if filtros.cargo != "Qualquer Cargo da Área" and filtros.cargo != "":
        prompt += f"Cargo alvo: {filtros.cargo}.\n"

    prompt += """
    Retorne APENAS um array JSON válido, sem markdown, sem formatação ```json, estritamente neste formato:
    [
      {
        "enunciado": "Texto da pergunta",
        "opcoes": ["A", "B", "C", "D", "E"],
        "correta": 0, 
        "explicacao": "Explicação detalhada"
      }
    ]
    A 'correta' deve ser o índice (0 a 4) da opção certa.
    """
    
    # SISTEMA DE FALLBACK (À Prova de Balas)
    # Se um modelo da Groq falhar, ele automaticamente tenta o próximo da lista!
    modelos_para_testar = [
        "llama3-8b-8192",          # Modelo clássico, super rápido e 100% gratuito.
        "mixtral-8x7b-32768",      # Backup 1: Muito inteligente.
        "gemma-7b-it"              # Backup 2: Criado pelo Google, sempre ativo.
    ]
    
    ultimo_erro = ""
    
    async with httpx.AsyncClient(timeout=60.0) as client:
        for modelo in modelos_para_testar:
            try:
                resposta = await client.post(
                    "https://api.groq.com/openai/v1/chat/completions",
                    headers={
                        "Authorization": f"Bearer {GROQ_API_KEY}",
                        "Content-Type": "application/json"
                    },
                    json={
                        "model": modelo,
                        "messages": [{"role": "user", "content": prompt}],
                        "temperature": 0.3
                    }
                )
                
                resposta.raise_for_status() # Se der erro, pula pro except abaixo
                
                # Se chegou aqui, funcionou!
                dados = resposta.json()
                conteudo_str = dados['choices'][0]['message']['content'].strip()
                
                # Limpeza do JSON
                if conteudo_str.startswith("```"):
                    conteudo_str = conteudo_str.split('\n', 1)[1]
                if conteudo_str.endswith("```"):
                    conteudo_str = conteudo_str.rsplit('\n', 1)[0]
                    
                questoes_geradas = json.loads(conteudo_str)
                
                # Salva no banco e finaliza
                for q in questoes_geradas:
                    cursor.execute(
                        'INSERT INTO questoes (disciplina_id, enunciado, opcoes, correta, explicacao) VALUES (%s, %s, %s, %s, %s)',
                        (filtros.disciplina_id, q['enunciado'], json.dumps(q['opcoes']), q['correta'], q['explicacao'])
                    )
                
                conn.commit()
                conn.close()
                return {"status": "ok", "geradas": len(questoes_geradas), "modelo_usado": modelo}
                
            except httpx.HTTPStatusError as e:
                ultimo_erro = e.response.text
                print(f"Modelo {modelo} falhou: {ultimo_erro}. Tentando o próximo...")
                continue # Tenta o próximo modelo do Array
            except Exception as e:
                ultimo_erro = str(e)
                print(f"Erro no parse com {modelo}: {ultimo_erro}. Tentando o próximo...")
                continue

    # Se todos os modelos falharem, aí sim ele chora e avisa o porquê.
    conn.close()
    raise HTTPException(status_code=500, detail=f"Todos os modelos da Groq falharam. Último erro: {ultimo_erro}")
