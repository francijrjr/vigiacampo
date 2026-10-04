# VigiaCampo - PNCD

Sistema para registrar atividades de campo do PNCD, com API em FastAPI e interface web em HTML, CSS e JavaScript nativo. O projeto atende agentes de combate a endemias e supervisores, incluindo uso local, rascunhos offline, sincronizacao em lote, fotos protegidas, relatorios e boletim de reconhecimento por quarteirao.

## Inicio rapido

### Mapa dos quarteirões

Em **Quarteirões → Adicionar**, o formulário solicita a localização do dispositivo
e abre o mapa para marcar os cantos da quadra. Clique/toque em pelo menos três
cantos e use **Concluir contorno**. Arraste os pontos para ajustar ou use
**Desfazer ponto** / **Limpar desenho**. O contorno azul e seu número reaparecem
ao editar; a geometria também acompanha a duplicação e a sincronização de registros.
O desenho é opcional, preservando cadastros antigos e o cadastro sem GPS.

A localização requer permissão do navegador e HTTPS (ou localhost); a precisão
informada pelo aparelho aparece no formulário. Apenas a geometria desenhada é
persistida, sem rastrear o usuário. Sem permissão, navegue manualmente pelo mapa.
O sistema aguarda até 20 segundos por leituras melhores, descarta posições antigas
e encerra a busca ao obter precisão informada de até 50 metros. Uma leitura com
margem maior aparece como uma região aproximada, sem marcador de posição exata.
A busca para ao fechar o formulário; mover o mapa impede recentralizações tardias.
O navegador e o dispositivo podem fornecer uma posição incorreta mesmo com
precisão declarada alta. Confira o local; a aplicação não consegue garantir GPS exato.
As ruas dependem de internet; os mapas não são baixados para uso offline.

**Banco existente:** execute `python -m alembic upgrade head` antes de iniciar a
versão com mapas, seguindo a seção de migrações abaixo caso o banco ainda não
tenha controle de versão. A revisão `91c02_mapa` acrescenta a coluna JSON opcional
`quarteiroes.geometria`, em GeoJSON Polygon (longitude, latitude).

Leaflet 1.9.4 está incluído em `frontend/vendor/leaflet`, com sua licença.
Referências: [API Leaflet](https://leafletjs.com/reference.html) e
[política dos mapas OpenStreetMap](https://operations.osmfoundation.org/policies/tiles/).

### Executar localmente

Na raiz do projeto:

```powershell
python -m venv .venv
.\.venv\Scripts\python -m pip install -r requirements.txt
.\.venv\Scripts\python iniciar.py
```

O script `iniciar.py` cria um `.env` local se ele ainda nao existir, usa `pncd.db` como banco SQLite e cria as tabelas ausentes quando `AUTO_CREATE_TABLES=true`. Ele nao apaga dados existentes.

- Sistema: http://127.0.0.1:8000
- Swagger: http://127.0.0.1:8000/docs
- ReDoc: http://127.0.0.1:8000/redoc
- OpenAPI: http://127.0.0.1:8000/api/v1/openapi.json

Com `SEED_DEMO=true`, o sistema cria usuarios de demonstracao somente quando o banco ainda nao tem usuarios:

| Usuario | Senha | Perfil |
| --- | --- | --- |
| supervisor | supervisor123 | Supervisor |
| agente | agente123 | Agente de campo |

Se ja houver usuarios no banco, as contas e senhas existentes sao preservadas.

## Funcionalidades

- Login, renovacao de token, logout no servidor e troca de senha com invalidacao de sessoes antigas.
- Administracao da equipe pelo supervisor: cadastro, edicao, ativacao e desativacao de agentes.
- Registros diarios com criacao, consulta, filtro, edicao, duplicacao, envio e exclusao.
- Quarteiroes e imoveis vinculados ao registro correto, com validacoes de permissao e consistencia.
- Visitas com inspecoes, coletas, especimes, tratamentos e depositos eliminados.
- Fotos validadas por conteudo, limite de tamanho, acesso autenticado e remocao do arquivo apos exclusao confirmada.
- Boletim de reconhecimento por quarteirao, com identificacao do local, responsavel, imoveis, fechamento e PDF para impressao.
- Painel, estatisticas por agente, resumos automaticos e PDF de atividades com quebra de paginas.
- Interface responsiva em portugues, com estados vazios, mensagens de erro e rascunhos offline por conta.
- Sincronizacao em lote com `client_id` para evitar duplicidade em reenvios.

## Regras de acesso

Agentes acessam os proprios registros. Supervisores acessam os proprios registros e os registros dos agentes da sua equipe. Depois de enviado, um registro so pode ser alterado ou excluido pelo supervisor.

Estatisticas e PDF de atividades sao exclusivos do supervisor. O PDF do boletim tambem fica disponivel para o agente responsavel pelo registro. A duplicacao cria um novo rascunho com a data de hoje e copia quarteiroes, boletins, imoveis e dados das visitas; fotos nao sao copiadas.

## Uso offline

Abra a aplicacao e entre na conta antes de sair para campo. Depois que a interface carregar, os arquivos publicos ficam no cache do navegador. A sessao fica na aba, e os rascunhos ficam salvos no navegador, separados por conta.

Sem conexao, a interface permite criar e revisar os dados basicos de registros. O botao **Revisar e enviar** aparece quando existem rascunhos locais. Historico, fotos, gestao de equipe e preenchimento detalhado das visitas pela interface exigem conexao.

A API de sincronizacao aceita visitas completas. Para vincular itens criados no mesmo lote, informe `client_id` no quarteirao e use esse valor em `quarteirao_client_id` no imovel. O lote inteiro roda em uma unica transacao: se um item for invalido, nada novo do lote e confirmado.

## Boletim de reconhecimento

Abra um registro e clique em **Novo boletim**. Preencha UF, distrito, municipio, localidade, responsavel, funcao, subdistrito, sublocal, categoria, quarteirao e data. Depois use **Adicionar imovel** para informar rua, numero, lado e tipo.

Os imoveis do boletim tambem abrem a tela de visita do registro, sem duplicar dados. O PDF gera a ficha com duas colunas, fechamento por tipo de imovel, nome, data e espaco para assinatura.

## Estrutura do projeto

```text
app/
  api/          Rotas HTTP por assunto
  core/         Configuracoes, seguranca e datas
  db/           Conexao e sessao do banco
  models/       Tabelas e relacionamentos
  schemas/      Entradas e respostas da API
  services/     Regras de negocio, permissoes, PDF e arquivos
frontend/
  app.js        Inicializacao da interface
  controllers/  Navegacao, carregamento de telas e acoes
  models/       API, sessao, estado, consultas e rascunhos
  utils/        Datas e download de arquivos
  views/        Templates HTML por tela
  sw.js         Cache offline dos arquivos publicos
  styles.css    Estilos principais
migrations/     Migracoes Alembic
scripts/        Rotinas administrativas locais
tests/          Testes automatizados e checks visuais
deploy/         Publicacao e atualizacao na AWS
```

## Padroes de codigo

No backend, as rotas em `app/api/` validam entrada, checam permissao, chamam servicos e confirmam a transacao. Os servicos em `app/services/` concentram operacoes reutilizaveis e podem executar `flush`, mas nao devem fazer `commit`; isso permite salvar lotes offline de forma atomica.

No frontend, o fluxo e `evento -> controller -> model -> view`. Views recebem dados e retornam HTML, sem chamar API diretamente. Controllers carregam dados, atualizam o estado e escolhem a view. Models concentram HTTP, sessao, consultas, estado e persistencia local.

Para mudar apresentacao, procure `frontend/views/`. Para mudar o comportamento de um botao, procure o `data-action` em `frontend/controllers/acoes.js` e no controller especifico. Ao adicionar arquivo publico novo, inclua o caminho em `frontend/sw.js` e suba a versao do cache.

## Configuracao

Exemplo de `.env`:

```env
DATABASE_URL=sqlite:///./pncd.db
SECRET_KEY=troque-por-uma-chave-aleatoria
SEED_DEMO=true
AUTO_CREATE_TABLES=true
UPLOAD_DIR=./uploads
CORS_ORIGINS=["http://localhost:8000","http://127.0.0.1:8000"]
```

Para PostgreSQL em ambiente persistente, desative a criacao automatica de tabelas e aplique as migracoes:

```env
DATABASE_URL=postgresql+psycopg://usuario:senha@host:5432/banco
AUTO_CREATE_TABLES=false
SEED_DEMO=false
SECRET_KEY=uma-chave-segura
```

```powershell
python -m alembic upgrade head
python scripts/criar_supervisor.py
python -m uvicorn app.main:app --host 127.0.0.1 --port 8000
```

Para adotar migracoes em um banco local ja existente, faca backup antes e confirme se a estrutura corresponde a revisao inicial:

```powershell
python -m alembic stamp 0bc1e56c298d
python -m alembic upgrade head
python -m alembic check
```

Para criar uma migracao futura:

```powershell
python -m alembic revision --autogenerate -m descricao_da_mudanca
python -m alembic upgrade head
```

Revise o arquivo gerado antes de aplicar em dados reais.

## Testes

```powershell
python -m pip install -r requirements-dev.txt
python -m pytest -q
```

Os testes usam banco temporario e nao alteram `pncd.db`.

Para o check visual com navegador, mantenha uma instancia descartavel na porta 8001:

```powershell
New-Item -ItemType Directory -Force tmp
$env:DATABASE_URL='sqlite:///./tmp/visual.db'
$env:UPLOAD_DIR='./tmp/visual-uploads'
$env:SEED_DEMO='true'
python -m uvicorn app.main:app --host 127.0.0.1 --port 8001
```

Em outro terminal:

```powershell
python tests/check_browser.py
python tests/check_boletim.py
```

`check_browser.py` requer Chrome instalado. `check_boletim.py` usa a mesma instancia descartavel e, para conferir PDF, precisa de `pymupdf`.

## Datas no frontend

Campos `<input type="date">` e a API trabalham com `YYYY-MM-DD`. Por isso `frontend/utils/datas.js` gera a data de hoje nesse formato tecnico sem depender de locale. Para exibicao ao usuario, `dataBr()` formata em `pt-BR`.

## Publicacao

O guia de AWS esta em [deploy/README.md](deploy/README.md). A arquitetura atual usa CloudFront para HTTPS e distribuicao do front, S3 privado para arquivos estaticos, EC2 para API e PostgreSQL em conteineres, e Systems Manager para administracao sem SSH aberto.

Para atualizar apenas o front publicado, use:

```powershell
python deploy/aws.py publicar
```

Para atualizar a API publicada:

```powershell
python deploy/aws.py servidor
python deploy/aws.py servidor_status
```

Antes de operacoes em producao, confira backup do banco e da pasta de uploads.

## Limites atuais

O relatorio de atividades nao inclui fotos. O boletim reproduz a organizacao da ficha de referencia, sem logotipo municipal nem assinatura digital. A interface offline cobre rascunhos basicos; visitas completas podem ser sincronizadas pela API.
