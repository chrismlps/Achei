from __future__ import annotations

import os
import sqlite3
import hashlib
from contextlib import contextmanager
from pathlib import Path
from typing import Iterator

BASE_DIR = Path(__file__).resolve().parent.parent
DB_PATH = Path(os.getenv("ACHEI_DB_PATH", BASE_DIR / "achei.db"))


def gerar_hash_senha(senha: str) -> str:
    """Hash simples para o login didático da aplicação."""
    return hashlib.sha256(f"achei::{senha}".encode("utf-8")).hexdigest()


@contextmanager
def get_connection() -> Iterator[sqlite3.Connection]:
    """Abre uma conexão SQLite com integridade referencial ativada."""
    conn = sqlite3.connect(DB_PATH)
    conn.row_factory = sqlite3.Row
    conn.execute("PRAGMA foreign_keys = ON;")
    try:
        yield conn
        conn.commit()
    except Exception:
        conn.rollback()
        raise
    finally:
        conn.close()


def init_db() -> None:
    """Cria as três tabelas principais do CRUD complexo, caso ainda não existam."""
    DB_PATH.parent.mkdir(parents=True, exist_ok=True)
    with get_connection() as conn:
        conn.executescript(
            """
            CREATE TABLE IF NOT EXISTS usuario (
                user_id INTEGER PRIMARY KEY AUTOINCREMENT,
                nome TEXT NOT NULL CHECK (length(trim(nome)) > 0),
                email TEXT NOT NULL UNIQUE CHECK (instr(email, '@') > 1),
                senha_hash TEXT NOT NULL,
                perfil TEXT NOT NULL CHECK (perfil IN ('Aluno', 'Funcionário', 'Administrador'))
            );

            CREATE TABLE IF NOT EXISTS posto_apoio (
                id_posto INTEGER PRIMARY KEY AUTOINCREMENT,
                nome TEXT NOT NULL CHECK (length(trim(nome)) > 0),
                local TEXT NOT NULL CHECK (length(trim(local)) > 0),
                horario TEXT NOT NULL CHECK (length(trim(horario)) > 0)
            );

            CREATE TABLE IF NOT EXISTS item (
                id_item INTEGER PRIMARY KEY AUTOINCREMENT,
                descricao TEXT NOT NULL CHECK (length(trim(descricao)) > 0),
                categoria TEXT NOT NULL CHECK (length(trim(categoria)) > 0),
                status TEXT NOT NULL CHECK (
                    status IN ('Perdido', 'Disponível para Retirada', 'Retornado')
                ),
                fk_posto INTEGER,
                data_registro TEXT NOT NULL DEFAULT (datetime('now', 'localtime')),
                FOREIGN KEY (fk_posto)
                    REFERENCES posto_apoio(id_posto)
                    ON UPDATE CASCADE
                    ON DELETE RESTRICT
            );

            CREATE TABLE IF NOT EXISTS termo_retirada (
                id_termo INTEGER PRIMARY KEY AUTOINCREMENT,
                fk_item INTEGER NOT NULL UNIQUE,
                fk_posto INTEGER NOT NULL,
                cpf_retirante TEXT NOT NULL CHECK (length(trim(cpf_retirante)) >= 11),
                email_retirante TEXT NOT NULL CHECK (instr(email_retirante, '@') > 1),
                data_retirada TEXT NOT NULL DEFAULT (datetime('now', 'localtime')),
                FOREIGN KEY (fk_item)
                    REFERENCES item(id_item)
                    ON UPDATE CASCADE
                    ON DELETE RESTRICT,
                FOREIGN KEY (fk_posto)
                    REFERENCES posto_apoio(id_posto)
                    ON UPDATE CASCADE
                    ON DELETE RESTRICT
            );

            CREATE INDEX IF NOT EXISTS idx_item_status ON item(status);
            CREATE INDEX IF NOT EXISTS idx_item_posto ON item(fk_posto);
            CREATE INDEX IF NOT EXISTS idx_termo_item ON termo_retirada(fk_item);
            CREATE INDEX IF NOT EXISTS idx_termo_posto ON termo_retirada(fk_posto);
            """
        )

        usuarios_demo = [
            ("Aluno Demonstração", "aluno@achei.com", gerar_hash_senha("aluno123"), "Aluno"),
            ("Funcionário Demonstração", "funcionario@achei.com", gerar_hash_senha("func123"), "Funcionário"),
            ("Administrador Demonstração", "admin@achei.com", gerar_hash_senha("admin123"), "Administrador"),
        ]
        conn.executemany(
            """
            INSERT OR IGNORE INTO usuario (nome, email, senha_hash, perfil)
            VALUES (?, ?, ?, ?)
            """,
            usuarios_demo,
        )
