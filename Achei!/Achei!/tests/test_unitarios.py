import pytest
from pydantic import ValidationError

from app.db import gerar_hash_senha
from app.schemas import LoginRequest, PostoCreate, TermoCreate


def test_gerar_hash_senha_retorna_hash_deterministico_e_nao_texto_puro():
    senha = "admin123"

    primeiro_hash = gerar_hash_senha(senha)
    segundo_hash = gerar_hash_senha(senha)

    assert primeiro_hash == segundo_hash
    assert primeiro_hash != senha
    assert len(primeiro_hash) == 64


def test_posto_create_remove_espacos_e_valida_campos_obrigatorios():
    posto = PostoCreate(
        nome="  Biblioteca Central  ",
        local="  Prédio da Biblioteca  ",
        horario="  08h às 22h  ",
    )

    assert posto.nome == "Biblioteca Central"
    assert posto.local == "Prédio da Biblioteca"
    assert posto.horario == "08h às 22h"

    with pytest.raises(ValidationError):
        PostoCreate(nome="   ", local="Prédio da Biblioteca", horario="08h às 22h")


def test_termo_create_normaliza_cpf_email_e_rejeita_dados_invalidos():
    termo = TermoCreate(
        id_item=1,
        id_posto=1,
        cpf_retirante="123.456.789-01",
        email_retirante="  ALUNO@UFLA.BR  ",
    )

    assert termo.cpf_retirante == "12345678901"
    assert termo.email_retirante == "aluno@ufla.br"

    with pytest.raises(ValidationError):
        TermoCreate(
            id_item=1,
            id_posto=1,
            cpf_retirante="123",
            email_retirante="aluno@ufla.br",
        )

    with pytest.raises(ValidationError):
        TermoCreate(
            id_item=1,
            id_posto=1,
            cpf_retirante="12345678901",
            email_retirante="email-invalido",
        )


def test_login_request_normaliza_email_e_rejeita_email_invalido():
    login = LoginRequest(email="  ADMIN@ACHEI.COM  ", senha="admin123")

    assert login.email == "admin@achei.com"
    assert login.senha == "admin123"

    with pytest.raises(ValidationError):
        LoginRequest(email="admin-sem-arroba", senha="admin123")
