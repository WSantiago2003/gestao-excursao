# 🚌 Gestão de Romaria — Aparecida do Norte

Aplicação web Full-Stack desenvolvida para facilitar a organização e o gerenciamento de romarias e excursões, permitindo o controle de reservas de poltronas, acompanhamento financeiro dos pagamentos e geração da lista de embarque.

O sistema foi desenvolvido para uma viagem com capacidade de **46 passageiros**, oferecendo um mapa visual interativo do ônibus, controle dos valores recebidos e a receber, além de uma interface responsiva e recursos de segurança para proteger os dados e as operações da aplicação.

🔗 **Acesse o sistema em produção:** [Gestão de Romaria no Render](https://gestao-excursao.onrender.com)

---

## ✨ Funcionalidades

- **Mapa visual do ônibus (46 poltronas):** representação interativa das poltronas, permitindo visualizar e gerenciar as reservas de maneira prática.
  - ⚪ **Livre:** poltrona disponível.
  - 🟡 **Pagamento parcial:** passageiro cadastrado com valor pendente.
  - 🟢 **Quitada:** pagamento integral registrado.

- **Painel financeiro:** acompanhamento automático da quantidade de poltronas livres e ocupadas, total arrecadado e saldo restante a receber.

- **Gerenciamento de passageiros:** cadastro e atualização de informações como nome, telefone, documento, valor total da passagem e valor já pago.

- **Controle de pagamentos:** registro manual dos pagamentos realizados, com cálculo automático do saldo restante.

- **Exportação da lista de embarque:** geração de arquivo CSV compatível com Excel, utilizando codificação UTF-8 com BOM e separador `;`.

- **Validação de dados:** verificações no front-end e no back-end para evitar informações inválidas, valores negativos e pagamentos superiores ao preço da passagem.

---

## 🔐 Segurança e Boas Práticas

O projeto também contempla práticas importantes de segurança no desenvolvimento de aplicações web:

- **Autenticação por sessão:** utilização do sistema de sessões do Flask para controlar o acesso às funcionalidades administrativas.
- **Variáveis de ambiente:** armazenamento de informações sensíveis, como senha de acesso e chave secreta, fora do código-fonte.
- **Configuração de cookies:** utilização das flags `HttpOnly`, `SameSite=Lax` e `Secure`, conforme a configuração do ambiente.
- **Limitação de tentativas de login:** mecanismo de controle para reduzir tentativas consecutivas de autenticação por endereço IP.
- **Prevenção contra XSS:** utilização de `textContent` na criação de elementos dinâmicos no JavaScript, evitando a interpretação indevida de conteúdo como HTML.
- **Proteção na exportação CSV:** tratamento de campos para reduzir o risco de injeção de fórmulas (*CSV Injection*).
- **Consultas parametrizadas:** utilização de parâmetros nas operações SQL para reduzir riscos de SQL Injection.
- **Gerenciamento de transações:** utilização de `commit()` e `rollback()` para controlar as operações no banco de dados, além de `try/finally` para garantir o fechamento das conexões.

---

## 🛠️ Tecnologias Utilizadas

### Back-end
- **Python 3** — linguagem utilizada no desenvolvimento da aplicação.
- **Flask** — microframework responsável pela API e pelas rotas da aplicação.
- **Gunicorn** — servidor WSGI utilizado em produção.
- **Psycopg2** — biblioteca para conexão e interação com PostgreSQL.

### Banco de Dados
- **PostgreSQL** — banco de dados utilizado em produção, hospedado no Neon.
- **SQLite** — banco de dados utilizado no ambiente de desenvolvimento local.

### Front-end
- **HTML5** — estrutura das páginas.
- **CSS3** — estilização e responsividade da interface.
- **JavaScript (Vanilla ES6+)** — interatividade, manipulação dinâmica do mapa de poltronas e comunicação com a API por meio de `fetch`.

### Infraestrutura e Ferramentas
- **Render** — hospedagem e implantação da aplicação.
- **Neon** — hospedagem do banco de dados PostgreSQL.
- **Git e GitHub** — versionamento e gerenciamento do código-fonte.

---

## 🚀 Como Executar o Projeto Localmente

### Pré-requisitos

Antes de começar, certifique-se de ter instalado:

- [Python 3.x](https://www.python.org/downloads/)
- [Git](https://git-scm.com/)

### 1. Clonar o Repositório

```bash
git clone https://github.com/WSantiago2003/gestao-excursao.git
cd gestao-excursao
```

### 2. Criar e Ativar o Ambiente Virtual

**Windows (CMD / PowerShell):**

```bash
python -m venv venv
venv\Scripts\activate
```

**Linux / macOS:**

```bash
python3 -m venv venv
source venv/bin/activate
```

### 3. Instalar as Dependências

Com o ambiente virtual ativado, execute:

```bash
pip install -r requirements.txt
```

### 4. Configurar as Variáveis de Ambiente

Crie um arquivo chamado `.env` na raiz do projeto e configure as seguintes variáveis:

```env
SENHA_SISTEMA=sua_senha_segura_aqui
SECRET_KEY=sua_chave_secreta_aleatoria_longa
```

**Observações:**

- `SENHA_SISTEMA`: senha utilizada para acessar o sistema.
- `SECRET_KEY`: chave utilizada pelo Flask para proteger as sessões.
- `DATABASE_URL`: variável opcional para informar a URL de conexão com o PostgreSQL.

Caso `DATABASE_URL` não seja configurada, a aplicação utilizará automaticamente o banco de dados SQLite local (`excursao.db`).

> **Importante:** o Flask não carrega arquivos `.env` automaticamente. Para utilizar esse arquivo, é necessário que o ambiente de execução carregue suas variáveis antes de iniciar o `app.py`. Caso contrário, configure as variáveis diretamente no ambiente do sistema.

### 5. Iniciar a Aplicação

Com as dependências instaladas e as variáveis de ambiente configuradas, execute:

```bash
python app.py
```

### 6. Acessar o Sistema

Abra o navegador e acesse:

```text
http://127.0.0.1:5000
```

Utilize a senha definida na variável `SENHA_SISTEMA` para realizar a autenticação.

---

## 🌐 Deploy em Produção

A aplicação está hospedada na plataforma **Render**, com o código-fonte versionado no GitHub e o banco de dados PostgreSQL hospedado no **Neon**.

A configuração de produção utiliza as seguintes variáveis de ambiente:

| Variável | Finalidade |
|---|---|
| `DATABASE_URL` | URL de conexão com o PostgreSQL. |
| `SENHA_SISTEMA` | Senha de acesso ao sistema. |
| `SECRET_KEY` | Chave secreta utilizada pelo Flask. |
| `SESSION_COOKIE_SECURE` | Define se os cookies devem ser enviados somente por HTTPS (`true`). |

---

## 👨‍💻 Autor

Desenvolvido por **Wanderson Santiago** como projeto prático de desenvolvimento Full-Stack.

O projeto teve como objetivo aplicar conhecimentos de desenvolvimento back-end, construção de APIs, integração com bancos de dados relacionais, desenvolvimento de interfaces web, validação de dados e implantação de aplicações em ambiente de produção.