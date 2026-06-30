import importlib
import os
import sys
from pathlib import Path

PROJECT_ROOT = Path(__file__).resolve().parents[1]
if str(PROJECT_ROOT) not in sys.path:
    sys.path.insert(0, str(PROJECT_ROOT))

from fastapi.testclient import TestClient


def criar_cliente(tmp_path: Path) -> TestClient:
    os.environ["ACHEI_DB_PATH"] = str(tmp_path / "teste_achei.db")
    sys.modules.pop("app.db", None)
    sys.modules.pop("app.main", None)
    main = importlib.import_module("app.main")
    client = TestClient(main.app)
    client.__enter__()
    return client


def test_fluxo_crud_complexo_retirada(tmp_path):
    client = criar_cliente(tmp_path)

    posto = client.post(
        "/postos",
        json={
            "nome": "Biblioteca Central",
            "local": "Prédio da Biblioteca",
            "horario": "08h às 22h",
        },
    )
    assert posto.status_code == 201
    id_posto = posto.json()["id_posto"]

    item = client.post(
        "/itens/entregues",
        json={
            "descricao": "Chave com chaveiro azul",
            "categoria": "Chave",
            "id_posto": id_posto,
        },
    )
    assert item.status_code == 201
    id_item = item.json()["id_item"]
    assert item.json()["status"] == "Disponível para Retirada"

    retirada = client.post(
        "/retiradas",
        json={
            "id_item": id_item,
            "id_posto": id_posto,
            "cpf_retirante": "12345678901",
            "email_retirante": "aluno@ufla.br",
        },
    )
    assert retirada.status_code == 201
    id_termo = retirada.json()["id_termo"]
    assert retirada.json()["item_status"] == "Retornado"
    assert retirada.json()["posto_nome"] == "Biblioteca Central"

    item_atualizado = client.get(f"/itens/{id_item}")
    assert item_atualizado.status_code == 200
    assert item_atualizado.json()["status"] == "Retornado"

    correcao = client.put(
        f"/retiradas/{id_termo}",
        json={"email_retirante": "corrigido@ufla.br"},
    )
    assert correcao.status_code == 200
    assert correcao.json()["email_retirante"] == "corrigido@ufla.br"
    assert correcao.json()["fk_item"] == id_item
    assert correcao.json()["fk_posto"] == id_posto

    exclusao = client.delete(f"/retiradas/{id_termo}")
    assert exclusao.status_code == 204

    item_revertido = client.get(f"/itens/{id_item}")
    assert item_revertido.status_code == 200
    assert item_revertido.json()["status"] == "Disponível para Retirada"


def test_bloqueia_exclusao_de_posto_com_item_vinculado(tmp_path):
    client = criar_cliente(tmp_path)

    posto = client.post(
        "/postos",
        json={"nome": "Portaria", "local": "Entrada", "horario": "24h"},
    )
    assert posto.status_code == 201
    id_posto = posto.json()["id_posto"]

    item = client.post(
        "/itens/entregues",
        json={"descricao": "Celular", "categoria": "Eletrônico", "id_posto": id_posto},
    )
    assert item.status_code == 201

    resposta = client.delete(f"/postos/{id_posto}")
    assert resposta.status_code == 409
    assert "itens vinculados" in resposta.json()["detail"]


def test_bloqueia_retirada_de_item_perdido(tmp_path):
    client = criar_cliente(tmp_path)

    posto = client.post(
        "/postos",
        json={"nome": "Cantina", "local": "Bloco A", "horario": "08h às 18h"},
    )
    assert posto.status_code == 201
    id_posto = posto.json()["id_posto"]

    item = client.post(
        "/itens/perdidos",
        json={"descricao": "Carteira preta", "categoria": "Documento"},
    )
    assert item.status_code == 201
    id_item = item.json()["id_item"]

    retirada = client.post(
        "/retiradas",
        json={
            "id_item": id_item,
            "id_posto": id_posto,
            "cpf_retirante": "12345678901",
            "email_retirante": "aluno@ufla.br",
        },
    )
    assert retirada.status_code == 409
    assert "Somente itens disponíveis" in retirada.json()["detail"]


def test_consultas_de_itens_nao_quebram_com_filtros(tmp_path):
    client = criar_cliente(tmp_path)

    posto = client.post(
        "/postos",
        json={"nome": "Secretaria", "local": "Bloco B", "horario": "08h às 17h"},
    )
    assert posto.status_code == 201
    id_posto = posto.json()["id_posto"]

    item_disponivel = client.post(
        "/itens/entregues",
        json={"descricao": "Fone preto", "categoria": "Eletrônico", "id_posto": id_posto},
    )
    assert item_disponivel.status_code == 201

    item_perdido = client.post(
        "/itens/perdidos",
        json={"descricao": "Caderno azul", "categoria": "Material escolar"},
    )
    assert item_perdido.status_code == 201

    perdidos = client.get("/itens/perdidos")
    assert perdidos.status_code == 200
    assert len(perdidos.json()) == 1
    assert perdidos.json()[0]["status"] == "Perdido"

    disponiveis = client.get("/itens/disponiveis")
    assert disponiveis.status_code == 200
    assert len(disponiveis.json()) == 1
    assert disponiveis.json()[0]["status"] == "Disponível para Retirada"

    por_posto = client.get(f"/postos/{id_posto}/itens")
    assert por_posto.status_code == 200
    assert len(por_posto.json()) == 1
    assert por_posto.json()[0]["fk_posto"] == id_posto

    filtro = client.get("/itens", params={"status": "Disponível para Retirada", "id_posto": id_posto})
    assert filtro.status_code == 200
    assert len(filtro.json()) == 1
