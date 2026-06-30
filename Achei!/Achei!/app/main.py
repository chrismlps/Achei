from __future__ import annotations

from contextlib import asynccontextmanager
from typing import Any, Optional

from fastapi import FastAPI, HTTPException, Query, Request, Response, status
from fastapi.middleware.cors import CORSMiddleware
from sqlite3 import IntegrityError, Row

from .db import gerar_hash_senha, get_connection, init_db
from .schemas import (
    EntregaItemExistente,
    ItemEntregueCreate,
    ItemPerdidoCreate,
    ItemUpdate,
    LoginRequest,
    PostoCreate,
    PostoUpdate,
    StatusItem,
    TermoCreate,
    TermoUpdate,
)


@asynccontextmanager
async def lifespan(app: FastAPI):
    init_db()
    yield


app = FastAPI(
    title="Achei! - CRUD de Três Tabelas",
    description="CRUD de Item, Posto de Apoio e Termo de Retirada.",
    version="1.0.0",
    lifespan=lifespan,
)

# Permite que o frontend local consuma a API durante a apresentação do trabalho.
app.add_middleware(
    CORSMiddleware,
    allow_origins=["*"],
    allow_credentials=False,
    allow_methods=["*"],
    allow_headers=["*"],
)


ROLE_PERMISSIONS = {
    "Aluno": {"rf10", "rf11", "rf12", "rf13", "rf15"},
    "Funcionário": {"rf03", "rf06", "rf07", "rf10", "rf11", "rf12", "rf13", "rf14", "rf15"},
    "Administrador": {"rf02", "rf03", "rf04", "rf05", "rf06", "rf07", "rf08", "rf09", "rf10", "rf11", "rf12", "rf13", "rf14", "rf15"},
}


def verificar_permissao(request: Request, *codigos: str) -> None:
    """Validação simples por perfil.

    Se a chamada vier sem cabeçalho de perfil, a API continua aceitando a requisição
    para manter a documentação /docs e os testes automatizados fáceis de executar.
    Quando o frontend envia X-Achei-Perfil, a permissão é validada.
    """
    perfil = request.headers.get("X-Achei-Perfil")
    if not perfil:
        return
    permissoes = ROLE_PERMISSIONS.get(perfil, set())
    if any(codigo in permissoes for codigo in codigos):
        return
    raise HTTPException(status_code=403, detail="Perfil sem permissão para esta funcionalidade.")


def row_to_dict(row: Row | None) -> Optional[dict[str, Any]]:
    return dict(row) if row is not None else None


def buscar_posto_ou_404(conn, id_posto: int) -> dict[str, Any]:
    row = conn.execute(
        "SELECT id_posto, nome, local, horario FROM posto_apoio WHERE id_posto = ?",
        (id_posto,),
    ).fetchone()
    posto = row_to_dict(row)
    if posto is None:
        raise HTTPException(status_code=404, detail="Posto de apoio não encontrado.")
    return posto


def buscar_item_ou_404(conn, id_item: int) -> dict[str, Any]:
    row = conn.execute(
        """
        SELECT id_item, descricao, categoria, status, fk_posto, data_registro
        FROM item
        WHERE id_item = ?
        """,
        (id_item,),
    ).fetchone()
    item = row_to_dict(row)
    if item is None:
        raise HTTPException(status_code=404, detail="Item não encontrado.")
    return item


def buscar_termo_ou_404(conn, id_termo: int) -> dict[str, Any]:
    row = conn.execute(
        """
        SELECT
            t.id_termo,
            t.fk_item,
            t.fk_posto,
            t.cpf_retirante,
            t.email_retirante,
            t.data_retirada,
            i.descricao AS item_descricao,
            i.categoria AS item_categoria,
            i.status AS item_status,
            p.nome AS posto_nome,
            p.local AS posto_local,
            p.horario AS posto_horario
        FROM termo_retirada t
        JOIN item i ON i.id_item = t.fk_item
        JOIN posto_apoio p ON p.id_posto = t.fk_posto
        WHERE t.id_termo = ?
        """,
        (id_termo,),
    ).fetchone()
    termo = row_to_dict(row)
    if termo is None:
        raise HTTPException(status_code=404, detail="Termo de retirada não encontrado.")
    return termo


@app.get("/health")
def health_check() -> dict[str, str]:
    return {"status": "ok"}




# ============================================================
# RF01: LOGIN SIMPLES
# ============================================================


@app.post("/auth/login")
def realizar_login(dados: LoginRequest) -> dict[str, Any]:
    with get_connection() as conn:
        row = conn.execute(
            """
            SELECT user_id, nome, email, perfil
            FROM usuario
            WHERE email = ? AND senha_hash = ?
            """,
            (dados.email, gerar_hash_senha(dados.senha)),
        ).fetchone()

        usuario = row_to_dict(row)
        if usuario is None:
            raise HTTPException(status_code=401, detail="Credenciais inválidas.")

        # Token didático: usado apenas pelo frontend para identificar a sessão local.
        usuario["token"] = f"achei-demo-{usuario['user_id']}-{usuario['perfil']}"
        return usuario


@app.get("/auth/usuarios-demo")
def listar_usuarios_demo() -> list[dict[str, str]]:
    return [
        {"perfil": "Aluno", "email": "aluno@achei.com", "senha": "aluno123"},
        {"perfil": "Funcionário", "email": "funcionario@achei.com", "senha": "func123"},
        {"perfil": "Administrador", "email": "admin@achei.com", "senha": "admin123"},
    ]

# ============================================================
# CRUD 1: POSTO DE APOIO
# ============================================================


@app.post("/postos", status_code=status.HTTP_201_CREATED)
def cadastrar_posto(dados: PostoCreate, request: Request) -> dict[str, Any]:
    verificar_permissao(request, "rf02")
    with get_connection() as conn:
        cursor = conn.execute(
            "INSERT INTO posto_apoio (nome, local, horario) VALUES (?, ?, ?)",
            (dados.nome, dados.local, dados.horario),
        )
        id_posto = cursor.lastrowid
        return buscar_posto_ou_404(conn, id_posto)


@app.get("/postos")
def consultar_postos(request: Request) -> list[dict[str, Any]]:
    verificar_permissao(request, "rf03", "rf12")
    with get_connection() as conn:
        rows = conn.execute(
            """
            SELECT
                p.id_posto,
                p.nome,
                p.local,
                p.horario,
                COALESCE(SUM(CASE
                    WHEN i.status = 'Disponível para Retirada' THEN 1
                    ELSE 0
                END), 0) AS quantidade_itens_disponiveis
            FROM posto_apoio p
            LEFT JOIN item i ON i.fk_posto = p.id_posto
            GROUP BY p.id_posto, p.nome, p.local, p.horario
            ORDER BY p.nome
            """
        ).fetchall()
        return [dict(row) for row in rows]


@app.get("/postos/{id_posto}")
def consultar_posto_por_id(id_posto: int, request: Request) -> dict[str, Any]:
    verificar_permissao(request, "rf03", "rf12")
    with get_connection() as conn:
        posto = buscar_posto_ou_404(conn, id_posto)
        row = conn.execute(
            """
            SELECT COUNT(*) AS total
            FROM item
            WHERE fk_posto = ? AND status = 'Disponível para Retirada'
            """,
            (id_posto,),
        ).fetchone()
        posto["quantidade_itens_disponiveis"] = row["total"]
        return posto


@app.put("/postos/{id_posto}")
def atualizar_posto(id_posto: int, dados: PostoUpdate, request: Request) -> dict[str, Any]:
    verificar_permissao(request, "rf04")
    with get_connection() as conn:
        buscar_posto_ou_404(conn, id_posto)
        conn.execute(
            """
            UPDATE posto_apoio
            SET nome = ?, local = ?, horario = ?
            WHERE id_posto = ?
            """,
            (dados.nome, dados.local, dados.horario, id_posto),
        )
        return buscar_posto_ou_404(conn, id_posto)


@app.delete("/postos/{id_posto}", status_code=status.HTTP_204_NO_CONTENT)
def excluir_posto(id_posto: int, request: Request) -> Response:
    verificar_permissao(request, "rf05")
    with get_connection() as conn:
        buscar_posto_ou_404(conn, id_posto)
        total_itens = conn.execute(
            "SELECT COUNT(*) AS total FROM item WHERE fk_posto = ?",
            (id_posto,),
        ).fetchone()["total"]
        if total_itens > 0:
            raise HTTPException(
                status_code=409,
                detail="Não é permitido excluir posto com itens vinculados.",
            )
        conn.execute("DELETE FROM posto_apoio WHERE id_posto = ?", (id_posto,))
        return Response(status_code=status.HTTP_204_NO_CONTENT)


# ============================================================
# CRUD 2: ITEM
# ============================================================


@app.post("/itens/perdidos", status_code=status.HTTP_201_CREATED)
def registrar_item_perdido(dados: ItemPerdidoCreate, request: Request) -> dict[str, Any]:
    verificar_permissao(request, "rf10")
    with get_connection() as conn:
        cursor = conn.execute(
            """
            INSERT INTO item (descricao, categoria, status, fk_posto)
            VALUES (?, ?, 'Perdido', NULL)
            """,
            (dados.descricao, dados.categoria),
        )
        return buscar_item_ou_404(conn, cursor.lastrowid)


@app.post("/itens/entregues", status_code=status.HTTP_201_CREATED)
def registrar_item_entregue_em_posto(dados: ItemEntregueCreate, request: Request) -> dict[str, Any]:
    verificar_permissao(request, "rf14")
    with get_connection() as conn:
        buscar_posto_ou_404(conn, dados.id_posto)
        cursor = conn.execute(
            """
            INSERT INTO item (descricao, categoria, status, fk_posto)
            VALUES (?, ?, 'Disponível para Retirada', ?)
            """,
            (dados.descricao, dados.categoria, dados.id_posto),
        )
        return buscar_item_ou_404(conn, cursor.lastrowid)


@app.patch("/itens/{id_item}/entrega")
def entregar_item_existente_em_posto(
    id_item: int,
    dados: EntregaItemExistente,
    request: Request,
) -> dict[str, Any]:
    verificar_permissao(request, "rf14")
    with get_connection() as conn:
        item = buscar_item_ou_404(conn, id_item)
        buscar_posto_ou_404(conn, dados.id_posto)

        if item["status"] == "Retornado":
            raise HTTPException(
                status_code=409,
                detail="Item retornado não pode ser entregue novamente em posto.",
            )

        conn.execute(
            """
            UPDATE item
            SET status = 'Disponível para Retirada', fk_posto = ?
            WHERE id_item = ?
            """,
            (dados.id_posto, id_item),
        )
        return buscar_item_ou_404(conn, id_item)


def listar_itens(
    status_item: Optional[StatusItem] = None,
    id_posto: Optional[int] = None,
) -> list[dict[str, Any]]:
    sql = """
        SELECT
            i.id_item,
            i.descricao,
            i.categoria,
            i.status,
            i.fk_posto,
            i.data_registro,
            p.nome AS posto_nome,
            p.local AS posto_local
        FROM item i
        LEFT JOIN posto_apoio p ON p.id_posto = i.fk_posto
        WHERE 1 = 1
    """
    params: list[Any] = []

    if status_item is not None:
        sql += " AND i.status = ?"
        params.append(str(status_item))

    if id_posto is not None:
        sql += " AND i.fk_posto = ?"
        params.append(id_posto)

    sql += " ORDER BY i.id_item DESC"

    with get_connection() as conn:
        rows = conn.execute(sql, params).fetchall()
        return [dict(row) for row in rows]


@app.get("/itens")
def consultar_itens(
    request: Request,
    status_item: Optional[StatusItem] = Query(default=None, alias="status"),
    id_posto: Optional[int] = Query(default=None, gt=0),
) -> list[dict[str, Any]]:
    verificar_permissao(request, "rf11", "rf12", "rf13")
    return listar_itens(status_item=status_item, id_posto=id_posto)


@app.get("/itens/perdidos")
def consultar_itens_perdidos(request: Request) -> list[dict[str, Any]]:
    verificar_permissao(request, "rf11")
    return listar_itens(status_item="Perdido")


@app.get("/itens/disponiveis")
def consultar_itens_disponiveis(request: Request) -> list[dict[str, Any]]:
    verificar_permissao(request, "rf13")
    return listar_itens(status_item="Disponível para Retirada")


@app.get("/postos/{id_posto}/itens")
def consultar_itens_por_posto(id_posto: int, request: Request) -> list[dict[str, Any]]:
    verificar_permissao(request, "rf12")
    with get_connection() as conn:
        buscar_posto_ou_404(conn, id_posto)
    return listar_itens(id_posto=id_posto)


@app.get("/itens/{id_item}")
def consultar_item_por_id(id_item: int, request: Request) -> dict[str, Any]:
    verificar_permissao(request, "rf11", "rf12", "rf13")
    with get_connection() as conn:
        item = buscar_item_ou_404(conn, id_item)
        if item["fk_posto"] is not None:
            posto = buscar_posto_ou_404(conn, item["fk_posto"])
            item["posto"] = posto
        return item


@app.put("/itens/{id_item}")
def atualizar_item(id_item: int, dados: ItemUpdate, request: Request) -> dict[str, Any]:
    verificar_permissao(request, "rf15")
    with get_connection() as conn:
        buscar_item_ou_404(conn, id_item)
        conn.execute(
            """
            UPDATE item
            SET descricao = ?, categoria = ?
            WHERE id_item = ?
            """,
            (dados.descricao, dados.categoria, id_item),
        )
        return buscar_item_ou_404(conn, id_item)


@app.delete("/itens/{id_item}", status_code=status.HTTP_204_NO_CONTENT)
def excluir_item(id_item: int, request: Request) -> Response:
    verificar_permissao(request, "rf15")
    with get_connection() as conn:
        buscar_item_ou_404(conn, id_item)
        termo = conn.execute(
            "SELECT id_termo FROM termo_retirada WHERE fk_item = ?",
            (id_item,),
        ).fetchone()
        if termo is not None:
            raise HTTPException(
                status_code=409,
                detail="Não é permitido excluir item com termo de retirada vinculado.",
            )
        conn.execute("DELETE FROM item WHERE id_item = ?", (id_item,))
        return Response(status_code=status.HTTP_204_NO_CONTENT)


# ============================================================
# CRUD 3: TERMO DE RETIRADA
# Este CRUD é o fluxo complexo porque cria, consulta, atualiza e exclui
# termo usando JOIN/transação com Item e Posto de Apoio.
# ============================================================


@app.post("/retiradas", status_code=status.HTTP_201_CREATED)
def registrar_retirada(dados: TermoCreate, request: Request) -> dict[str, Any]:
    verificar_permissao(request, "rf06")
    with get_connection() as conn:
        item = buscar_item_ou_404(conn, dados.id_item)
        buscar_posto_ou_404(conn, dados.id_posto)

        if item["status"] != "Disponível para Retirada":
            raise HTTPException(
                status_code=409,
                detail="Somente itens disponíveis para retirada podem ser retirados.",
            )

        if item["fk_posto"] != dados.id_posto:
            raise HTTPException(
                status_code=409,
                detail="O item não está vinculado ao posto informado.",
            )

        try:
            cursor = conn.execute(
                """
                INSERT INTO termo_retirada
                    (fk_item, fk_posto, cpf_retirante, email_retirante)
                VALUES (?, ?, ?, ?)
                """,
                (
                    dados.id_item,
                    dados.id_posto,
                    dados.cpf_retirante,
                    dados.email_retirante,
                ),
            )
        except IntegrityError as exc:
            raise HTTPException(
                status_code=409,
                detail="Já existe termo de retirada para este item.",
            ) from exc

        conn.execute(
            "UPDATE item SET status = 'Retornado' WHERE id_item = ?",
            (dados.id_item,),
        )

        return buscar_termo_ou_404(conn, cursor.lastrowid)


@app.get("/retiradas")
def consultar_retiradas(request: Request) -> list[dict[str, Any]]:
    verificar_permissao(request, "rf07")
    with get_connection() as conn:
        rows = conn.execute(
            """
            SELECT
                t.id_termo,
                t.fk_item,
                t.fk_posto,
                t.cpf_retirante,
                t.email_retirante,
                t.data_retirada,
                i.descricao AS item_descricao,
                i.categoria AS item_categoria,
                i.status AS item_status,
                p.nome AS posto_nome,
                p.local AS posto_local,
                p.horario AS posto_horario
            FROM termo_retirada t
            JOIN item i ON i.id_item = t.fk_item
            JOIN posto_apoio p ON p.id_posto = t.fk_posto
            ORDER BY t.data_retirada DESC, t.id_termo DESC
            """
        ).fetchall()
        return [dict(row) for row in rows]


@app.get("/retiradas/{id_termo}")
def consultar_retirada_por_id(id_termo: int, request: Request) -> dict[str, Any]:
    verificar_permissao(request, "rf07")
    with get_connection() as conn:
        return buscar_termo_ou_404(conn, id_termo)


@app.put("/retiradas/{id_termo}")
def atualizar_retirada(id_termo: int, dados: TermoUpdate, request: Request) -> dict[str, Any]:
    verificar_permissao(request, "rf08")
    if dados.cpf_retirante is None and dados.email_retirante is None:
        raise HTTPException(
            status_code=400,
            detail="Informe CPF e/ou e-mail para atualização.",
        )

    with get_connection() as conn:
        termo_atual = buscar_termo_ou_404(conn, id_termo)
        novo_cpf = dados.cpf_retirante or termo_atual["cpf_retirante"]
        novo_email = dados.email_retirante or termo_atual["email_retirante"]

        conn.execute(
            """
            UPDATE termo_retirada
            SET cpf_retirante = ?, email_retirante = ?
            WHERE id_termo = ?
            """,
            (novo_cpf, novo_email, id_termo),
        )
        return buscar_termo_ou_404(conn, id_termo)


@app.delete("/retiradas/{id_termo}", status_code=status.HTTP_204_NO_CONTENT)
def excluir_retirada(id_termo: int, request: Request) -> Response:
    verificar_permissao(request, "rf09")
    with get_connection() as conn:
        termo = buscar_termo_ou_404(conn, id_termo)

        conn.execute("DELETE FROM termo_retirada WHERE id_termo = ?", (id_termo,))
        conn.execute(
            """
            UPDATE item
            SET status = 'Disponível para Retirada', fk_posto = ?
            WHERE id_item = ?
            """,
            (termo["fk_posto"], termo["fk_item"]),
        )
        return Response(status_code=status.HTTP_204_NO_CONTENT)
