# VigiaCampo — atividades de campo do PNCD

Sistema para agentes de combate às endemias e supervisores. A API usa Python/FastAPI. O front usa HTML, CSS e JavaScript, sem etapa de compilação.

## Rodar no seu computador

No terminal, dentro de `pncd-api`:

```powershell
python -m venv .venv
.\.venv\Scripts\python -m pip install -r requirements.txt
.\.venv\Scripts\python iniciar.py
```

O início rápido cria `.env` com uma chave aleatória se o arquivo ainda não existir. Usa o banco `pncd.db` da pasta e cria as tabelas que faltam. Não apaga registros existentes.

- **Sistema:** http://127.0.0.1:8000
- **Swagger:** http://127.0.0.1:8000/docs
- **Documentação alternativa:** http://127.0.0.1:8000/redoc
- **OpenAPI:** http://127.0.0.1:8000/api/v1/openapi.json

Com `SEED_DEMO=true`, estes usuários são criados **somente se não houver usuários no banco**:

| Usuário    | Senha         | Perfil          |
| ---------- | ------------- | --------------- |
| supervisor | supervisor123 | Supervisor      |
| agente     | agente123     | Agente de campo |

Se o banco já tiver usuários, as senhas existentes são preservadas.

## O que está implementado

- Login, renovação de acesso, troca de senha e encerramento da sessão no servidor.
- Gestão dos agentes da própria equipe: cadastro, edição, ativação e desativação.
- Registros diários: criar, consultar, filtrar, editar, duplicar, enviar e excluir.
- Quarteirões e imóveis com validação de vínculo ao registro correto.
- Boletim de reconhecimento por quarteirão: UF, distrito, município, localidade, responsável, função, subdistrito, sublocal, categoria e data.
- Ruas, números, lados e tipos de imóvel (R, C, TB, PE e O), com fechamento automático e PDF para imprimir.
- Inspeções, coletas, espécimes, tratamentos e depósitos eliminados: cadastro, consulta, edição e exclusão.
- Fotos com verificação do arquivo, limite de tamanho, acesso protegido e remoção após exclusão confirmada no banco.
- Resumos automáticos, painel, estatísticas por agente e PDF verdadeiro com quebra de páginas.
- Interface responsiva em português, incluindo estados vazios e mensagens de erro.
- Rascunhos offline dos dados básicos do registro, salvos neste navegador e separados por conta.
- Sincronização em lote com identificador para evitar duplicação em reenvios.

### Regras de acesso

O agente acessa os próprios registros. O supervisor acessa seus registros e os da sua equipe. Registros enviados só podem ser alterados ou excluídos pelo supervisor. O PDF de atividades e as estatísticas são exclusivos do supervisor. O PDF do boletim também está disponível para o agente responsável.

A duplicação copia quarteirões, boletins, imóveis e dados de visita para um novo rascunho de hoje. As fotos não são copiadas. Confira e ajuste as quantidades antes de enviar a cópia.

### Preencher o boletim

Abra um registro e clique em **Novo boletim**. Preencha a identificação do local e do responsável. Depois, use **Adicionar imóvel** para informar rua, número, lado e tipo. Cada imóvel pode abrir sua própria visita; os dados são compartilhados com o registro, sem duplicação. **Baixar PDF / imprimir** gera a ficha com duas colunas, fechamento, nome, data e espaço para assinatura.

### Uso offline

Abra a aplicação e entre na conta antes de sair para campo. Depois que os arquivos da interface forem carregados, a tela pode ser reaberta sem conexão na mesma aba. A sessão fica na aba; os rascunhos ficam no navegador até serem enviados ou excluídos.

Sem conexão, é possível criar e revisar **os dados básicos de registros**. O botão “Revisar e enviar” aparece quando há rascunhos locais. Histórico, fotos, gestão da equipe e cadastro detalhado das visitas pela interface precisam de conexão. Limpar os dados do navegador remove os rascunhos ainda não enviados.

A API de sincronização também aceita visitas completas. Para vincular imóvel e quarteirão criados no mesmo envio, informe `client_id` no quarteirão e esse valor em `quarteirao_client_id` no imóvel. Todo o lote é salvo em uma transação: se um item for inválido, nenhum registro novo do lote é confirmado.

## Testar pelo Swagger

1. Abra `/docs` e execute `POST /api/v1/auth/login` com usuário e senha.
2. Copie o campo `access_token` da resposta.
3. Clique em **Authorize** e cole somente o token.
4. Execute as rotas. Os exemplos, campos, permissões e respostas estão agrupados por assunto.

A senha alterada invalida as sessões anteriores. O logout invalida o acesso e a renovação da sessão atual.

## Organização do código

```text
app/
  api/          Rotas HTTP, organizadas por assunto
  core/         Configurações, autenticação e datas
  db/           Conexão e transações do banco
  models/       Tabelas e relacionamentos
  schemas/      Campos aceitos e respostas da API
  services/     Regras de registros, permissões, totais, PDF e arquivos
frontend/
  app.js        Inicialização do controller principal
  models/       API, sessão, consultas, estado e rascunhos locais
  views/        Templates por tela, componentes e formulários
  controllers/  Navegação, carregamento das telas e ações por assunto
  utils/        Formatação de datas e download de arquivos
  styles.css    Aparência e adaptação ao celular
  sw.js         Cache dos arquivos públicos da interface
migrations/     Histórico de mudanças do banco
scripts/        Administração local
 tests/         Testes da API e do navegador
```

### Padrão de organização

As rotas em `app/api/` recebem e validam as requisições, verificam o acesso e
confirmam a transação. Os serviços em `app/services/` concentram operações
reutilizáveis. Em `services/registros.py`, criação online e sincronização usam
o mesmo fluxo para salvar registros, quarteirões e visitas; a duplicação tem
uma função própria. As consultas completas também são compartilhadas.

Esses serviços podem executar `flush`, mas não fazem `commit`: a rota confirma
a operação somente ao final. Isso mantém o lote offline em uma única transação.
Novas regras devem usar nomes descritivos e funções com uma responsabilidade,
preservando os contratos dos schemas e a cobertura dos testes de API.

### MVC no frontend

O fluxo é **evento → controller → model → view**. `app.js` apenas inicia a
aplicação; os módulos usam JavaScript nativo, sem etapa de compilação.

- **Models:** `models/api.js` cuida de HTTP e sessão; `consultas.js` reúne as
  consultas e a regra de edição; `estado.js` guarda o estado de navegação;
  `rascunhos.js` persiste os registros offline separados por conta.
- **Views:** recebem dados por parâmetros e produzem HTML. Não importam models
  ou controllers, não consultam a API e não alteram o estado da aplicação.
  Há arquivos próprios para início, registros, visitas, equipe, relatórios,
  conta e boletins. Componentes e formulários são compartilhados.
- **Controllers:** carregam os dados, atualizam o estado e chamam as views.
  `aplicacao.js` coordena navegação e eventos; `telas.js` prepara os dados de
  cada tela; `acoes.js` encaminha cada `data-action` ao controller do assunto,
  como `registros-acoes.js`, `visitas-acoes.js` ou `rascunhos-acoes.js`.

Para alterar a apresentação, procure a view da tela. Para mudar o que acontece
em um botão, procure sua ação no controller correspondente. Para reutilizar
uma consulta ou regra de dados, coloque-a no model. Views recebem callbacks
quando precisam vincular formulários, evitando importações circulares.

Cada renderização tem uma versão: respostas antigas são descartadas após
mudanças de página. As chaves da sessão e dos rascunhos foram preservadas.
Ao adicionar um módulo público, inclua seu caminho na lista `ASSETS` de
`sw.js` e atualize a versão do cache. O script AWS publica as subpastas
recursivamente, preservando os caminhos dos imports.

## Banco e evolução

SQLite facilita o desenvolvimento local. Para usar PostgreSQL, configure no `.env`:

```env
DATABASE_URL=databseurl
AUTO_CREATE_TABLES=false
SEED_DEMO=false
SECRET_KEY=chave
```

Em um **banco novo**, execute antes de iniciar:

```powershell
python -m alembic upgrade head
python scripts/criar_supervisor.py
python -m uvicorn app.main:app --host 127.0.0.1 --port 8000
```

Para adotar as migrações em um **banco local já existente**, faça uma cópia de segurança e confira se a estrutura corresponde à revisão inicial antes de executar:

```powershell
python -m alembic stamp 0bc1e56c298d
python -m alembic upgrade head
python -m alembic check
```

Só marque a revisão em um banco correspondente à estrutura inicial. `stamp` registra a versão; não altera tabelas. Em caso de divergência no `check`, revise o banco antes de prosseguir.

Para uma alteração futura nas tabelas:

```powershell
python -m alembic revision --autogenerate -m descricao_da_mudanca
# Revise o arquivo gerado antes de aplicá-lo.
python -m alembic upgrade head
```

Para crescer, mantenha as regras em `services`, use PostgreSQL e migrações no deploy. As consultas de listas têm paginação limitada. Sessões encerradas ficam no banco e funcionam entre processos. Em múltiplas máquinas, a pasta de fotos precisa ser compartilhada ou substituída por armazenamento de objetos. O front pode ser separado do servidor preservando o contrato `/api/v1`.

## Testes

```powershell
python -m pip install -r requirements-dev.txt
python -m pytest -q
```

Os testes criam um banco temporário: não usam os dados reais de `pncd.db`.

Para o teste visual, mantenha uma instância **descartável** na porta 8001:

```powershell
New-Item -ItemType Directory -Force tmp
$env:DATABASE_URL='sqlite:///./tmp/visual.db'
$env:UPLOAD_DIR='./tmp/visual-uploads'
$env:SEED_DEMO='true'
python -m uvicorn app.main:app --host 127.0.0.1 --port 8001
```

Em outro terminal, rode `python tests/check_browser.py`. Requer Chrome instalado. O teste cria dados de demonstração, percorre telas e salva capturas em `tmp/screenshots/`.

O teste `python tests/check_boletim.py` usa a mesma instância descartável e verifica preenchimento, imóveis, PDF, persistência e tela de celular. A conferência do PDF requer `python -m pip install pymupdf`.

## Limites atuais

O relatório de atividades não inclui fotos. O boletim reproduz a organização da ficha de referência, sem logotipo municipal nem assinatura digital. A interface offline cobre rascunhos básicos, conforme descrito acima.

## Publicação na AWS

O front é servido pelo Amazon CloudFront a partir de um S3 privado. A API e o PostgreSQL ficam em uma instância EC2 pequena em `us-east-1`, com acesso privado da distribuição à API. Consulte [o guia de publicação](deploy/README.md) para instalação, administração, custos e evolução.
