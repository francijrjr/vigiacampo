# Publicação na AWS

## Estrutura

- CloudFront fornece HTTPS e distribui o front.
- S3 guarda os arquivos do front sem acesso público direto.
- CloudFront encaminha `/api/*`, `/docs`, `/redoc` e `/health` para a API por uma origem privada na VPC.
- EC2 `t3.micro` executa a API e PostgreSQL 16 em contêineres separados. O banco não publica portas.
- O disco gp3 de 12 GB é criptografado. A exclusão da instância não exclui automaticamente esse disco.
- Systems Manager administra a máquina sem abrir SSH.

É uma instalação inicial de baixo consumo. A API e o banco compartilham uma máquina, portanto uma falha nela interrompe ambos. Para crescer, mova o banco para um serviço dedicado, as fotos para armazenamento de objetos e distribua a API entre máquinas.

## Gratuidade

O script exige uma conta no plano **FREE ativo**, com pelo menos US$ 15 de créditos disponíveis. Ele não muda o plano da conta. Os recursos consomem créditos, inclusive disco, transferência e endereço IPv4. Isso não significa hospedagem gratuita permanente: o serviço pode ser interrompido quando o prazo ou os créditos acabarem. Confira o painel de faturamento antes de manter os recursos por longos períodos. Não migre para o plano pago se quiser manter a restrição de não haver cobrança.

## Primeira instalação

Requer Python, credenciais AWS configuradas e permissão para EC2, IAM, S3, CloudFront, Systems Manager e consulta ao Free Tier.

Na raiz do projeto:

```powershell
python -m pip install boto3
python deploy/aws.py preparar
python deploy/aws.py origem
python deploy/aws.py status
# Depois que a origem aparecer como Deployed:
python deploy/aws.py origem
python deploy/aws.py publicar
```

`preparar` copia o banco local `pncd.db` e as fotos para um bucket privado. A primeira inicialização aplica as migrações e importa os dados em um PostgreSQL vazio. A importação não é repetida se o destino já possui usuários. As senhas conhecidas da demonstração são protegidas antes de disponibilizar o sistema; a conta de agente de demonstração é desativada.

O estado e o acesso inicial ficam em `tmp/deploy/`. Essa pasta, os bancos, fotos e arquivos `.env` são excluídos do Git. Guarde uma cópia privada do estado e das credenciais. Troque a senha inicial após entrar.

## Acompanhar

```powershell
python deploy/aws.py status
python deploy/aws.py diagnostico
```

A criação da origem privada e a distribuição do CloudFront podem levar vários minutos. O diagnóstico verifica a instalação, os contêineres e `/health` sem exibir os arquivos de configuração privados.

## Atualizações

Para atualizar apenas o front, execute `python deploy/aws.py publicar`. O comando envia os arquivos e invalida o cache da distribuição existente.

Para atualizar a API, execute `python deploy/aws.py servidor` e acompanhe com `python deploy/aws.py servidor_status`. O comando salva um backup local do banco, constrói uma nova imagem, aplica migrações e reinicia somente a API. A imagem anterior recebe a etiqueta `previous`. Há uma breve interrupção durante o reinício. O backup local deve ser copiado para armazenamento privado separado. Nunca execute `preparar` como restauração de um banco em uso: a cópia de origem é apenas para a primeira instalação.

## Backup e restauração

O volume persistente do PostgreSQL sobrevive à recriação do contêiner, mas não substitui backup. Pelo Systems Manager, use `docker exec vigiacampo-db pg_dump -U vigiacampo -Fc vigiacampo` e guarde o resultado em armazenamento privado. Inclua `/opt/vigiacampo/uploads` no backup. Restaure com `pg_restore` em um banco separado e verifique antes de substituir o atual.

Antes do fim do plano gratuito, exporte os dados. Para encerrar a hospedagem, desative/exclua a distribuição e a origem privada, encerre a instância e revise os discos e buckets preservados. Só remova os dados depois de confirmar que existe uma cópia recuperável.
