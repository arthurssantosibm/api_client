# 📊 Banco Javer – API Data (Porta 8001)

Esta API faz parte do ecossistema **Banco Javer** e é responsável por **operações diretas no banco de dados**, como:

* Cadastro e manutenção de usuários
* Login e validações de status de conta
* Suspensão e reativação de contas
* Transações financeiras internas
* Depósitos
* Comunicação segura com a API Core (porta 8000)

A **API Data NÃO deve ser acessada diretamente pelo frontend**, exceto em cenários controlados.
Ela atua como **camada de persistência**.

---

## 🧱 Arquitetura Geral

```
Frontend (HTML / JS)
        |
        v
API Core (porta 8000)
        |
        |  (X-Internal-Key)
        v
API Data (porta 8001)
        |
        v
Banco de Dados MySQL (AWS RDS)
```

### 📌 Responsabilidades

| Componente      | Função                               |
| --------------- | ------------------------------------ |
| Frontend        | Interface do usuário                 |
| API Core (8000) | Autenticação, JWT, regras de negócio |
| API Data (8001) | CRUD, transações, persistência       |
| MySQL           | Armazenamento dos dados              |

---

## 🚪 Porta utilizada

| Serviço  | Porta    |
| -------- | -------- |
| API Data | **8001** |

---

## 🔐 Segurança

### 🔑 Autenticação interna

Algumas rotas exigem o header:

```
X-Internal-Key: INTERNAL_SECRET
```

Isso impede chamadas externas indevidas.

---

### 🔑 Autenticação JWT

Algumas rotas utilizam o token JWT enviado no header:

```
Authorization: Bearer <access_token>
```

O token é validado usando:

* `python-jose`
* `OAuth2PasswordBearer`

---

## 🗂 Estrutura do Projeto (API Data)

```
api_data/
├── api/
│   ├── connection.py        # Conexão com MySQL
│   ├── jwt.py               # JWT (validação interna)
│   └── routes.py            # Rotas da API Data
│
├── schemas/
│   └── schemas.py           # Pydantic Schemas
│
├── main.py                  # Inicialização do FastAPI
├── requirements.txt
└── README.md
```

---

## ⚙️ Inicialização do Projeto
## Executar no terminal
```bash
Set-ExecutionPolicy -Scope Process -ExecutionPolicy Bypass
```
### 1️⃣ Criar ambiente virtual


```bash
python -m venv venv
```

### 2️⃣ Ativar ambiente virtual

**Windows**

```bash
venv\Scripts\activate
```

**Linux / Mac**

```bash
source venv/bin/activate
```

---

### 3️⃣ Instalar dependências

```bash
pip install -r requirements.txt
```

---

### 4️⃣ Configurar variáveis de ambiente

Crie um arquivo `.env`:

```env
DB_HOST=seu_host_mysql
DB_USER=seu_usuario
DB_PASSWORD=sua_senha
DB_NAME=nome_do_banco
SECRET_KEY=sua_chave_jwt
```

---

### 5️⃣ Subir a API Data

```bash
uvicorn main:app --reload --port 8001
```

---

## 📄 Documentação automática

Após iniciar a API, acesse:

```
http://127.0.0.1:8001/docs
```

Documentação interativa via **Swagger (OpenAPI)**.

---

## 🧾 Rotas Disponíveis

### 👤 Usuários

#### ➕ Criar usuário

```
POST /usuarios
```

**Body:**

```json
{
  "nome": "Arthur",
  "email": "arthur@email.com",
  "telefone": "11999999999",
  "senha": "123456"
}
```

---

#### 🔐 Login (uso interno)

```
POST /loginUsuarios
```

**Body:**

```json
{
  "email": "arthur@email.com",
  "senha": "123456"
}
```

**Possíveis respostas:**

* `200` → Login válido
* `403` → Conta suspensa (`CONTA_INATIVA`)
* `404` → Usuário não encontrado

---

#### ✏️ Atualizar usuário

```
PUT /updateUsuarios/{user_id}
```

---

#### ⛔ Suspender conta

```
PUT /updateUsuarios/suspender/{user_id}
```

> 🔒 Requer JWT válido

---

#### ♻️ Reativar conta

```
PUT /updateUsuarios/reativar/{user_id}
```

---

### 💸 Transações

#### 🔁 Executar transação

```
POST /transacoesUsuarios
```

**Headers obrigatórios:**

```
X-Internal-Key: INTERNAL_SECRET
```

**Body:**

```json
{
  "email_origin": "a@email.com",
  "email_destination": "b@email.com",
  "valor": 100,
  "mensagem": "Pagamento",
  "user_origin_id": 1
}
```

---

### 💰 Depósito

#### ➕ Realizar depósito

```
POST /deposito
```

**Headers:**

```
X-Internal-Key: INTERNAL_SECRET
```

**Body:**

```json
{
  "email": "arthur@email.com",
  "valor": 200
}
```

---

## 🔄 Comunicação entre APIs

* A **API Core (8000)** chama a **API Data (8001)** usando `requests`
* O header `X-Internal-Key` valida chamadas internas
* A API Data **não gera JWT**, apenas valida

---

## 🧪 Testes manuais

* Swagger (`/docs`)
* Postman
* Frontend integrado

---

## ⚠️ Observações Importantes

* A API Data **não deve ser exposta publicamente**
* Sempre execute junto da API Core
* O banco de dados deve estar ativo antes de iniciar a API

---

## 🚀 Tecnologias Utilizadas

* **FastAPI**
* **MySQL (AWS RDS)**
* **Python 3.12+**
* **JWT**
* **Pydantic**
* **SQLAlchemy**
* **Uvicorn**

---

## 📌 Autor

Projeto desenvolvido por **Arthur Santana dos Santos**
Banco Javer – Desafio Técnico 🚀