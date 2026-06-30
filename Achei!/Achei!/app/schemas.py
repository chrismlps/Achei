from __future__ import annotations

import re
from typing import Literal, Optional

from pydantic import BaseModel, Field, field_validator

StatusItem = Literal["Perdido", "Disponível para Retirada", "Retornado"]


class PostoCreate(BaseModel):
    nome: str = Field(..., min_length=1, max_length=100)
    local: str = Field(..., min_length=1, max_length=150)
    horario: str = Field(..., min_length=1, max_length=50)

    @field_validator("nome", "local", "horario")
    @classmethod
    def limpar_texto(cls, value: str) -> str:
        value = value.strip()
        if not value:
            raise ValueError("campo obrigatório")
        return value


class PostoUpdate(PostoCreate):
    pass


class ItemPerdidoCreate(BaseModel):
    descricao: str = Field(..., min_length=1)
    categoria: str = Field(..., min_length=1, max_length=50)

    @field_validator("descricao", "categoria")
    @classmethod
    def limpar_texto(cls, value: str) -> str:
        value = value.strip()
        if not value:
            raise ValueError("campo obrigatório")
        return value


class ItemEntregueCreate(ItemPerdidoCreate):
    id_posto: int = Field(..., gt=0)


class ItemUpdate(ItemPerdidoCreate):
    pass


class EntregaItemExistente(BaseModel):
    id_posto: int = Field(..., gt=0)


class TermoCreate(BaseModel):
    id_item: int = Field(..., gt=0)
    id_posto: int = Field(..., gt=0)
    cpf_retirante: str = Field(..., min_length=11, max_length=14)
    email_retirante: str = Field(..., min_length=5, max_length=100)

    @field_validator("cpf_retirante")
    @classmethod
    def validar_cpf(cls, value: str) -> str:
        somente_numeros = re.sub(r"\D", "", value)
        if len(somente_numeros) != 11:
            raise ValueError("CPF deve conter 11 dígitos")
        return somente_numeros

    @field_validator("email_retirante")
    @classmethod
    def validar_email(cls, value: str) -> str:
        value = value.strip().lower()
        if not re.fullmatch(r"[^@\s]+@[^@\s]+\.[^@\s]+", value):
            raise ValueError("e-mail inválido")
        return value


class TermoUpdate(BaseModel):
    cpf_retirante: Optional[str] = Field(None, min_length=11, max_length=14)
    email_retirante: Optional[str] = Field(None, min_length=5, max_length=100)

    @field_validator("cpf_retirante")
    @classmethod
    def validar_cpf(cls, value: Optional[str]) -> Optional[str]:
        if value is None:
            return value
        somente_numeros = re.sub(r"\D", "", value)
        if len(somente_numeros) != 11:
            raise ValueError("CPF deve conter 11 dígitos")
        return somente_numeros

    @field_validator("email_retirante")
    @classmethod
    def validar_email(cls, value: Optional[str]) -> Optional[str]:
        if value is None:
            return value
        value = value.strip().lower()
        if not re.fullmatch(r"[^@\s]+@[^@\s]+\.[^@\s]+", value):
            raise ValueError("e-mail inválido")
        return value


class LoginRequest(BaseModel):
    email: str = Field(..., min_length=5, max_length=100)
    senha: str = Field(..., min_length=1, max_length=100)

    @field_validator("email")
    @classmethod
    def validar_email_login(cls, value: str) -> str:
        value = value.strip().lower()
        if not re.fullmatch(r"[^@\s]+@[^@\s]+\.[^@\s]+", value):
            raise ValueError("e-mail inválido")
        return value
