# Achei! - Achados e Perdidos

## 1. Contexto do Problema e Solução

### O Problema é:

Em um campus universitário é muito comum que alunos, funcionários e moradores percam pertences. Fones de ouvido, cartão do onibus/RU, chaves, celulares e outros itens. Sem um canal centralizado o processo de recuperação fica desorganizado e mais difícil: avisos informais em grupos de WhatsApp, posts nos Stories do Instagram e dependência da boa vontade de quem encontrou o item. Isso resulta em itens esquecidos em mesas de secretaria, portarias e cantinas sem nenhum registro formal, tornando a devolução ao dono praticamente impossível.

### A solução é:

O **Achei!** é um sistema web que centraliza o processo de registro e devolução de itens no campus. Com ele:

- **Quem perde** um item pode cadastrá-lo no sistema com descrição, categoria e situação, facilitando a busca.
- **Quem encontra** pode registrar o item e informar em qual posto de apoio (Cantina, Biblioteca, Portaria Central etc.) ele foi entregue.
- **A retirada** é formalizada com um Termo de Retirada registrando o CPF e email do retirante, garantindo fidelidade na devolução.
- **Gestores** podem cadastrar e gerenciar os postos de apoio disponíveis no campus.

O sistema requer login de usuário (alunos, funcionários, etc) e oferece operações completas de cadastro, consulta, edição e exclusão (CRUD) tanto para os postos de apoio quanto para o registro completo de devolução de itens.

---

## 2. Instruções para Uso

> Siga este guia se você pretende **apenas usar** o sistema.

### Pré-requisitos

Certifique-se de ter instalado em sua máquina:

- [Python 3.13](https://www.python.org/downloads/) ou superior
- [Git](https://git-scm.com/downloads)
- Um navegador web moderno (Chrome, Firefox, Edge)

Para verificar se o Python está instalado, abra o terminal e execute:

```bash
python --version
```

### Passo 1 — Baixar o sistema

**Opção A — Via Git (recomendado):**

```bash
git clone https://github.com/<usuario>/achados-e-perdidos.git
cd achados-e-perdidos
```

**Opção B — Via download ZIP:**

1. Acesse a página do repositório no GitHub
2. Clique em **Code → Download ZIP**
3. Extraia o arquivo ZIP
4. Abra o terminal e navegue até a pasta extraída:

```bash
cd achados-e-perdidos
```

### Passo 2 — Instalar as dependências

```bash
# Criar o ambiente virtual
python -m venv venv

# Ativar o ambiente virtual
# No Windows:
venv\Scripts\activate
# No Linux/macOS:
source venv/bin/activate

# Instalar as bibliotecas necessárias
pip install -r requirements.txt
```

### Passo 3 — Configurar o Banco de Dados

O sistema cria o banco de dados automaticamente na primeira execução. Nenhuma instalação adicional é necessária para o uso em modo local (SQLite).

Caso deseje usar PostgreSQL (ambiente de produção), edite o arquivo `config.py` e altere a variável:

```python
DATABASE_URL = "postgresql://usuario:senha@localhost:5432/achados_perdidos"
```

Em seguida, crie o banco no PostgreSQL:

```bash
createdb achados_perdidos
```

### Passo 4 — Executar o sistema

```bash
python run.py
```

Abra o navegador e acesse:

```
http://localhost:5000
```

Você verá a tela de login do sistema. Crie seu usuário na opção **"Cadastrar"** e comece a usar.

### Para encerrar

Pressione `Ctrl + C` no terminal para parar o servidor.

---

## 3. Instruções para Devs

> Siga este guia se você vai **contribuir com o desenvolvimento** do sistema.

### Passo 1 — Clonar o repositório

```bash
git clone https://github.com/<usuario>/achados-e-perdidos.git
cd achados-e-perdidos
```

Ou baixe o ZIP conforme descrito na seção anterior e extraia localmente.

### Passo 2 — Preparar o ambiente de desenvolvimento

```bash
# Criar o ambiente virtual
python -m venv venv

# Ativar o ambiente virtual
# Windows:
venv\Scripts\activate
# Linux/macOS:
source venv/bin/activate

# Instalar todas as dependências (incluindo ferramentas de teste)
pip install -r requirements.txt
```

### Passo 3 — Executar o projeto em modo de desenvolvimento

Vá para a raiz do projeto e execute:

```bash
python run.py
```

Acesse no navegador:

```
http://localhost:5000
```

Você deverá ver a tela inicial do sistema **Achei!**.

O arquivo `config.py` na raiz controla o modo de execução. Por padrão, o ambiente é `development`, utilizando SQLite (`achados.db`) gerado automaticamente.

### Passo 4 — Executar os testes

```bash
# Testes de unidade
pytest tests/unit/ -v

# Testes de caixa preta com Selenium (requer navegador instalado)
pytest tests/selenium/ -v
```

### Passo 5 — Registrar suas contribuições no Git

Todo membro da equipe deve commitar a partir de sua própria máquina:

```bash
git add .
git commit -m "descrição clara do que foi feito"
git push origin main
```

---

## 4. Tecnologias

### Frontend

| Tecnologia | Versão | Finalidade |
|---|---|---|
| HTML | 5 (W3C Living Standard) | Estrutura das páginas web |
| CSS | 3 (W3C Living Standard) | Estilização e layout responsivo |
| JavaScript | ES2025 (ECMAScript 16) | Interatividade e requisições assíncronas |

### Backend

| Tecnologia | Versão | Finalidade |
|---|---|---|
| Python | 3.13.13 | Linguagem de programação principal |
| Flask | 3.1.3 | Framework web: rotas, templates, requisições HTTP |
| SQLAlchemy | 2.0.43 | ORM — mapeamento objeto-relacional com o banco de dados |
| psycopg2 | 2.9.x | Driver de conexão Python ↔ PostgreSQL |

### Banco de Dados

| Tecnologia | Versão | Finalidade |
|---|---|---|
| SQLite | 3.53.2 | Banco de dados em desenvolvimento (arquivo local, sem servidor) |
| PostgreSQL | 18.4 | Banco de dados em produção / apresentação |

### Testes

| Tecnologia | Versão | Finalidade |
|---|---|---|
| pytest | 9.0.3 | Testes de unidade (PyUnit — exigido pelo enunciado) |
| Selenium (Python) | 4.44.0 | Testes de caixa preta com automação de browser (exigido pelo enunciado) |

### Outras

| Tecnologia | Versão | Finalidade |
|---|---|---|
| VS Code | 1.123 | IDE de desenvolvimento |
| Git | 2.x | Controle de versão e registro de commits |
| GitHub | — | Hospedagem do repositório e colaboração entre membros |
| pip | (incluso no Python 3.13) | Gerenciador de pacotes Python |
| venv | (incluso no Python 3.13) | Ambiente virtual isolado por projeto |

---

## 5. Organização do Projeto

```
achados-e-perdidos/
│
├── app/                        # Código-fonte principal da aplicação
│   ├── __init__.py             # Inicialização e configuração do Flask
│   ├── models/                 # Modelos do banco de dados (SQLAlchemy)
│   │   ├── usuario.py          # Tabela de usuários (login)
│   │   ├── item_perdido.py     # Tabela de itens perdidos
│   │   ├── posto_apoio.py      # Tabela de postos de apoio (CRUD simples)
│   │   └── termo_retirada.py   # Tabela de termos de retirada (CRUD complexo)
│   ├── routes/                 # Rotas e controladores da aplicação
│   │   ├── auth.py             # Rotas de autenticação (login, logout, cadastro)
│   │   ├── itens.py            # CRUD de itens perdidos
│   │   ├── postos.py           # CRUD de postos de apoio
│   │   └── termos.py           # CRUD de termos de retirada
│   ├── templates/              # Templates HTML (Jinja2)
│   │   ├── base.html           # Layout base herdado por todas as páginas
│   │   ├── login.html
│   │   ├── itens/              # Páginas de listagem, cadastro e edição de itens
│   │   ├── postos/             # Páginas de listagem, cadastro e edição de postos
│   │   └── termos/             # Páginas de listagem, cadastro e edição de termos
│   └── static/                 # Arquivos estáticos servidos diretamente
│       ├── css/                # Folhas de estilo CSS
│       └── js/                 # Scripts JavaScript
│
├── tests/                      # Testes automatizados
│   ├── unit/                   # Testes de unidade (pytest)
│   └── selenium/               # Testes de caixa preta (Selenium WebDriver)
│
├── docs/                       # Documentação do projeto
│   ├── requisitos.md           # Levantamento de requisitos
│   ├── diagrama_er.png         # Diagrama Entidade-Relacionamento
│   └── casos_de_uso.md         # Casos de uso do sistema
│
├── config.py                   # Configurações da aplicação (banco, ambiente)
├── run.py                      # Ponto de entrada para iniciar o servidor
├── requirements.txt            # Lista de dependências Python
└── README.md                   # Este arquivo
```
---
