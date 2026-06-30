# Achei! — Achados e Perdidos

Aplicação web acadêmica com backend em **FastAPI + SQLite** e frontend simples em **HTML/CSS/JavaScript**.

A versão inclui:

- tema visual em azul suave;
- login simples com três perfis;
- permissões diferentes para Aluno, Funcionário e Administrador;
- CRUD simples de Posto de Apoio;
- CRUD complexo envolvendo Item, Posto de Apoio e Termo de Retirada;
- telas funcionais para todos os casos de uso RF01 a RF15.

## Usuários de demonstração

| Perfil | E-mail | Senha |
|---|---|---|
| Aluno | `aluno@achei.com` | `aluno123` |
| Funcionário | `funcionario@achei.com` | `func123` |
| Administrador | `admin@achei.com` | `admin123` |

## Como rodar o backend

Entre na pasta do projeto e rode:

```cmd
py -m venv .venv
.venv\Scripts\activate.bat
pip install -r requirements.txt
.venv\Scripts\python.exe -m uvicorn app.main:app --reload
```

O backend ficará disponível em:

```text
http://127.0.0.1:8000
```

A documentação automática da API fica em:

```text
http://127.0.0.1:8000/docs
```

## Como rodar o frontend

Com o backend já ligado, abra outro terminal:

```cmd
cd frontend
py -m http.server 5500
```

Depois acesse:

```text
http://127.0.0.1:5500
```

Também é possível abrir diretamente o arquivo `frontend/index.html`, mas o servidor local é mais recomendado.

## Permissões por perfil

### Aluno

- RF10: Registrar item perdido
- RF11: Consultar itens perdidos
- RF12: Consultar registros de itens por posto de apoio
- RF13: Consultar itens disponíveis para retirada
- RF15: Excluir item

### Funcionário

- RF03: Consultar postos de apoio
- RF06: Registrar termo de retirada
- RF07: Consultar termos de retirada
- RF10: Registrar item perdido
- RF11: Consultar itens perdidos
- RF12: Consultar registros de itens por posto de apoio
- RF13: Consultar itens disponíveis para retirada
- RF14: Registrar entrega de item em posto de apoio
- RF15: Excluir item

### Administrador

- RF02: Cadastrar postos de apoio
- RF03: Consultar postos de apoio
- RF04: Atualizar postos de apoio
- RF05: Excluir postos de apoio
- RF06: Registrar termo de retirada
- RF07: Consultar termos de retirada
- RF08: Atualizar termo de retirada
- RF09: Excluir termo de retirada
- RF10: Registrar item perdido
- RF11: Consultar itens perdidos
- RF12: Consultar registros de itens por posto de apoio
- RF13: Consultar itens disponíveis para retirada
- RF14: Registrar entrega de item em posto de apoio
- RF15: Excluir item

## Testes

```cmd
pytest
```
