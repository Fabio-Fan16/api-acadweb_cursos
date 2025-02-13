
# INSERINDO SCRIPT ACAD

from fastapi import FastAPI, HTTPException, Query
import requests
import base64
from pyngrok import ngrok
import time

app = FastAPI()

# Configurações da API do AcadWeb
BASE_URL = "https://api.acadweb.com.br/fan"
AUTH_URL = f"{BASE_URL}/auth/token"  # Endpoint para autenticação
TOKEN = None  # Token inicial
HEADERS = {}

# Função para autenticação básica (Authorization: Basic)
def gerar_auth_basic_header(usuario: str, senha: str):
    credenciais = f"{usuario}:{senha}"
    token_base64 = base64.b64encode(credenciais.encode()).decode()
    return {"Authorization": f"Basic {token_base64}"}

# Função para autenticação e geração de novos tokens
def gerar_novo_token(login: str, senha: str):
    global TOKEN, HEADERS
    try:
        data = {"login": login, "senha": senha}
        response = requests.post(AUTH_URL, json=data, headers={"Content-Type": "application/json"})
        print(f"Requisição para gerar token. Status Code: {response.status_code}")
        if response.status_code == 200:
            novo_token = response.json().get("token")
            if novo_token:
                TOKEN = novo_token
                HEADERS = {"Authorization": f"Bearer {TOKEN}"}
                print("Novo token gerado com sucesso!")
            else:
                raise HTTPException(status_code=500, detail="Token não encontrado na resposta.")
        else:
            raise HTTPException(status_code=response.status_code, detail=f"Erro ao gerar token: {response.text}")
    except Exception as e:
        raise HTTPException(status_code=500, detail=f"Erro ao gerar novo token: {str(e)}")

# Função para fazer requisições à API do AcadWeb
def get_data(endpoint: str, params: dict = None, use_basic_auth: bool = False, usuario: str = None, senha: str = None):
    global TOKEN
    url = f"{BASE_URL}/{endpoint}"
    headers = HEADERS

    # Verifica se deve usar autenticação básica
    if use_basic_auth and usuario and senha:
        headers = gerar_auth_basic_header(usuario, senha)

    response = requests.get(url, headers=headers, params=params)
    print(f"URL chamada: {response.url}")
    print(f"Status Code: {response.status_code}")
    print(f"Resposta bruta: {response.text}")  # Exibe a resposta crua no terminal

    if response.status_code == 401:  # Token expirado ou inválido
        print("Token expirado. Gerando um novo token...")
        gerar_novo_token("qualinfo", "abc123")
        headers = HEADERS
        response = requests.get(url, headers=headers, params=params)
        if response.status_code != 200:
            raise HTTPException(status_code=response.status_code, detail=f"Erro ao acessar {endpoint} após renovação do token: {response.text}")

    if response.status_code == 200:
        try:
            return response.json()
        except Exception as e:
            raise HTTPException(status_code=500, detail=f"Erro ao converter resposta para JSON: {e}")
    else:
        raise HTTPException(status_code=response.status_code, detail=f"Erro ao acessar {endpoint}: {response.text}")

# Endpoints da API intermediária
@app.post("/auth/token")
def autenticar(login: str, senha: str):
    gerar_novo_token(login, senha)
    return {"message": "Novo token gerado com sucesso."}

@app.get("/tokens")
def listar_tokens():
    return get_data("tokens", use_basic_auth=True, usuario="qualinfo", senha="abc123")

@app.get("/alunos")
def listar_alunos(data_inicial: str = Query(None), data_final: str = Query(None), pagina: int = Query(1), quantidade: int = Query(10), matricula: str = Query(None), ativo: str = Query(None)):
    params = {
        "dataInicial": data_inicial,
        "dataFinal": data_final,
        "pagina": pagina,
        "quantidade": quantidade,
        "matricula": matricula,
        "ativo": ativo
    }
    return get_data("alunos", params=params)

@app.get("/matriculas")
def listar_matriculas():
    return get_data("matriculas")

@app.get("/status")
def listar_status():
    return get_data("status")

@app.get("/mensalidades")
def listar_mensalidades():
    return get_data("mensalidades")

@app.get("/cursos")
def listar_cursos():
    return get_data("cursos")

@app.get("/boletos")
def listar_boletos():
    return get_data("boletos")

@app.get("/turmas")
def listar_turmas(data_inicial: str = Query(None), data_final: str = Query(None), pagina: int = Query(1), quantidade: int = Query(10), turma_id: str = Query(None)):
    params = {
        "dataInicial": data_inicial,
        "dataFinal": data_final,
        "pagina": pagina,
        "quantidade": quantidade,
        "turma_id": turma_id
    }
    return get_data("turmas", params=params)

@app.get("/financeiro/titulos")
def listar_titulos(data_inicial: str = Query(None), data_final: str = Query(None), pagina: int = Query(1), quantidade: int = Query(10), vencimento_inicial: str = Query(None), vencimento_final: str = Query(None), situacao: str = Query(None), matricula: str = Query(None), titulo: str = Query(None)):
    params = {
        "dataInicial": data_inicial,
        "dataFinal": data_final,
        "pagina": pagina,
        "quantidade": quantidade,
        "vencimentoInicial": vencimento_inicial,
        "vencimentoFinal": vencimento_final,
        "situacao": situacao,
        "matricula": matricula,
        "titulo": titulo
    }
    return get_data("financeiro/titulos", params=params)

@app.get("/financeiro/formas-pagamento")
def listar_formas_pagamento():
    return get_data("financeiro/formas-pagamento")

@app.get("/custom_endpoint")
def custom_endpoint(use_basic_auth: bool = False, usuario: str = None, senha: str = None):
    return get_data("custom_endpoint", use_basic_auth=use_basic_auth, usuario=usuario, senha=senha)
