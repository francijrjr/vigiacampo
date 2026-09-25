"""Publicação em us-east-1. Recusa criar recursos fora do plano FREE ativo.

Uso: python deploy/aws.py preparar | origem | publicar | status
Credenciais vêm do perfil AWS local. Estado privado fica em tmp/, nunca no Git.
"""
import io,json,mimetypes,secrets,sqlite3,sys,tarfile,time
from pathlib import Path

RAIZ=Path(__file__).resolve().parents[1]
sys.path.insert(0,str(RAIZ/'tmp/aws-sdk'))
import boto3
from botocore.config import Config

REGIAO='us-east-1'
PROJETO='vigiacampo'
PASTA=RAIZ/'tmp/deploy'
PASTA.mkdir(parents=True,exist_ok=True)
ARQUIVO=PASTA/'estado.json'
estado=json.loads(ARQUIVO.read_text()) if ARQUIVO.exists() else {}
sessao=boto3.Session(region_name=REGIAO)
config=Config(connect_timeout=10,read_timeout=60,retries={'max_attempts':3})
def cliente(nome): return sessao.client(nome,config=config)
def salvar(): ARQUIVO.write_text(json.dumps(estado,indent=2),encoding='utf-8')


def plano_gratuito():
    plano=cliente('freetier').get_account_plan_state()
    if plano['accountPlanType']!='FREE' or plano['accountPlanStatus']!='ACTIVE':
        raise SystemExit('Operação interrompida: a conta não está no plano FREE ativo.')
    if plano.get('accountPlanRemainingCredits',{}).get('amount',0)<15:
        raise SystemExit('Operação interrompida: créditos disponíveis abaixo da reserva de US$ 15.')
    estado['conta']=plano['accountId']
    estado['expiracao_plano']=str(plano.get('accountPlanExpirationDate'))
    salvar()


def bucket(nome):
    s3=cliente('s3')
    try:s3.head_bucket(Bucket=nome)
    except s3.exceptions.ClientError as erro:
        if erro.response['Error']['Code'] not in ['404','NoSuchBucket']:raise
        s3.create_bucket(Bucket=nome)
    s3.put_public_access_block(Bucket=nome,PublicAccessBlockConfiguration={
        'BlockPublicAcls':True,'IgnorePublicAcls':True,'BlockPublicPolicy':True,'RestrictPublicBuckets':True})
    s3.put_bucket_encryption(Bucket=nome,ServerSideEncryptionConfiguration={'Rules':[{'ApplyServerSideEncryptionByDefault':{'SSEAlgorithm':'AES256'}}]})
    s3.put_bucket_tagging(Bucket=nome,Tagging={'TagSet':[{'Key':'Project','Value':PROJETO}]})


def pacote():
    s3=cliente('s3');nome=estado['bucket_deploy']
    with tarfile.open(PASTA/'app.tar.gz','w:gz') as tar:
        for item in ['app','migrations','scripts','Dockerfile','requirements.txt','alembic.ini']:
            caminho=RAIZ/item
            arquivos=caminho.rglob('*') if caminho.is_dir() else [caminho]
            for arquivo in arquivos:
                if arquivo.is_file() and '__pycache__' not in arquivo.parts:
                    tar.add(arquivo,arcname=str(arquivo.relative_to(RAIZ)).replace('\\','/'))
    s3.upload_file(str(PASTA/'app.tar.gz'),nome,'release/app.tar.gz')


def pacote_e_banco():
    pacote()
    s3=cliente('s3');nome=estado['bucket_deploy']
    with sqlite3.connect(RAIZ/'pncd.db') as origem,sqlite3.connect(PASTA/'pncd.db') as destino:
        origem.backup(destino)
    s3.upload_file(str(PASTA/'pncd.db'),nome,'private/pncd.db')
    if (RAIZ/'uploads').exists():
        with tarfile.open(PASTA/'uploads.tar.gz','w:gz') as tar:
            for arquivo in (RAIZ/'uploads').iterdir():
                if arquivo.is_file():tar.add(arquivo,arcname=arquivo.name)
        s3.upload_file(str(PASTA/'uploads.tar.gz'),nome,'private/uploads.tar.gz')
    if not (PASTA/'app.env').exists():
        senha_db=secrets.token_hex(24);senha_acesso=secrets.token_urlsafe(20)
        (PASTA/'app.env').write_text(
            f'DATABASE_URL=postgresql+psycopg://vigiacampo:{senha_db}@vigiacampo-db:5432/vigiacampo\n'
            f'SECRET_KEY={secrets.token_urlsafe(48)}\nBOOTSTRAP_PASSWORD={senha_acesso}\n'
            'AUTO_CREATE_TABLES=false\nSEED_DEMO=false\nCORS_ORIGINS=[]\nPROJECT_NAME=VigiaCampo\nUPLOAD_DIR=./uploads\n',encoding='utf-8')
        (PASTA/'db.env').write_text(f'POSTGRES_USER=vigiacampo\nPOSTGRES_DB=vigiacampo\nPOSTGRES_PASSWORD={senha_db}\n',encoding='utf-8')
        (PASTA/'ACESSO.txt').write_text(f'VigiaCampo — acesso inicial\nUsuário: supervisor\nSenha: {senha_acesso}\nTroque a senha na primeira entrada.\n',encoding='utf-8')
    for nome_env in ['app.env','db.env']:
        s3.upload_file(str(PASTA/nome_env),nome,'private/'+nome_env)


def preparar():
    plano_gratuito()
    ec2=cliente('ec2');iam=cliente('iam');ssm=cliente('ssm')
    for chave,sufixo in [('bucket_deploy','deploy'),('bucket_front','front')]:
        if chave not in estado:estado[chave]=f'{PROJETO}-{sufixo}-{estado["conta"]}';salvar()
        bucket(estado[chave])
    pacote_e_banco()
    role=PROJETO+'-ec2'
    try:iam.get_role(RoleName=role)
    except iam.exceptions.NoSuchEntityException:
        iam.create_role(RoleName=role,AssumeRolePolicyDocument=json.dumps({'Version':'2012-10-17','Statement':[{'Effect':'Allow','Principal':{'Service':'ec2.amazonaws.com'},'Action':'sts:AssumeRole'}]}))
    iam.attach_role_policy(RoleName=role,PolicyArn='arn:aws:iam::aws:policy/AmazonSSMManagedInstanceCore')
    iam.put_role_policy(RoleName=role,PolicyName='LerPublicacaoVigiaCampo',PolicyDocument=json.dumps({'Version':'2012-10-17','Statement':[{'Effect':'Allow','Action':'s3:GetObject','Resource':f'arn:aws:s3:::{estado["bucket_deploy"]}/*'}]}))
    try:iam.get_instance_profile(InstanceProfileName=role)
    except iam.exceptions.NoSuchEntityException:
        iam.create_instance_profile(InstanceProfileName=role)
        iam.add_role_to_instance_profile(InstanceProfileName=role,RoleName=role)
    if 'vpc' not in estado:
        vpcs=ec2.describe_vpcs(Filters=[{'Name':'is-default','Values':['true']}])['Vpcs']
        if not vpcs:raise SystemExit('Nenhuma VPC padrão. Nenhuma rede nova foi criada automaticamente.')
        estado['vpc']=vpcs[0]['VpcId']
        subnets=ec2.describe_subnets(Filters=[{'Name':'vpc-id','Values':[estado['vpc']]}])['Subnets']
        estado['subnet']=next(s['SubnetId'] for s in subnets if s['AvailabilityZoneId']!='use1-az3' and s['AvailableIpAddressCount']>5)
        salvar()
    if 'sg' not in estado:
        estado['sg']=ec2.create_security_group(GroupName=PROJETO+'-api',Description='Somente origem privada CloudFront; sem SSH e sem banco publico',VpcId=estado['vpc'])['GroupId'];salvar()
        ec2.create_tags(Resources=[estado['sg']],Tags=[{'Key':'Project','Value':PROJETO}])
    if 'instance' not in estado:
        ami=ssm.get_parameter(Name='/aws/service/ami-amazon-linux-latest/al2023-ami-kernel-default-x86_64')['Parameter']['Value']
        bootstrap=(RAIZ/'deploy/bootstrap.sh').read_text(encoding='utf-8').replace('#!/bin/bash',f'#!/bin/bash\nexport PROJECT_BUCKET={estado["bucket_deploy"]}\nexport AWS_REGION={REGIAO}',1)
        time.sleep(10)
        inst=ec2.run_instances(ImageId=ami,InstanceType='t3.micro',MinCount=1,MaxCount=1,
            IamInstanceProfile={'Name':role},UserData=bootstrap,
            NetworkInterfaces=[{'DeviceIndex':0,'SubnetId':estado['subnet'],'Groups':[estado['sg']],'AssociatePublicIpAddress':True}],
            MetadataOptions={'HttpTokens':'required','HttpPutResponseHopLimit':2},CreditSpecification={'CpuCredits':'standard'},
            BlockDeviceMappings=[{'DeviceName':'/dev/xvda','Ebs':{'VolumeSize':12,'VolumeType':'gp3','Encrypted':True,'DeleteOnTermination':False}}],
            TagSpecifications=[{'ResourceType':'instance','Tags':[{'Key':'Name','Value':PROJETO},{'Key':'Project','Value':PROJETO}]}],
            ClientToken=PROJETO+'-primeira-publicacao')['Instances'][0]
        estado['instance']=inst['InstanceId'];salvar()
    print('Instância preparada:',estado['instance'],'Região:',REGIAO)


def origem():
    plano_gratuito();ec2=cliente('ec2');cf=cliente('cloudfront')
    inst=ec2.describe_instances(InstanceIds=[estado['instance']])['Reservations'][0]['Instances'][0]
    if inst['State']['Name']!='running':raise SystemExit('Instância ainda não está em execução. Tente novamente em instantes.')
    estado['dns_privado']=inst['PrivateDnsName'];salvar()
    if 'vpc_origin' not in estado:
        res=cf.create_vpc_origin(VpcOriginEndpointConfig={'Name':PROJETO,'Arn':f'arn:aws:ec2:{REGIAO}:{estado["conta"]}:instance/{estado["instance"]}',
            'HTTPPort':8000,'HTTPSPort':443,'OriginProtocolPolicy':'http-only','OriginSslProtocols':{'Quantity':1,'Items':['TLSv1.2']}})
        estado['vpc_origin']=res['VpcOrigin']['Id'];salvar()
    grupos=ec2.describe_security_groups(Filters=[{'Name':'vpc-id','Values':[estado['vpc']]},{'Name':'group-name','Values':['CloudFront-VPCOrigins-Service-SG*']}])['SecurityGroups']
    for grupo in grupos:
        try:ec2.authorize_security_group_ingress(GroupId=estado['sg'],IpPermissions=[{'IpProtocol':'tcp','FromPort':8000,'ToPort':8000,'UserIdGroupPairs':[{'GroupId':grupo['GroupId'],'Description':'CloudFront origem privada'}]}])
        except ec2.exceptions.ClientError as erro:
            if erro.response['Error']['Code']!='InvalidPermission.Duplicate':raise
    print('Origem privada:',estado['vpc_origin'],cf.get_vpc_origin(Id=estado['vpc_origin'])['VpcOrigin']['Status'])


def enviar_front():
    s3=cliente('s3')
    for arquivo in (RAIZ/'frontend').rglob('*'):
        if not arquivo.is_file():continue
        relativo=arquivo.relative_to(RAIZ/'frontend').as_posix()
        chave=relativo if relativo in ['index.html','sw.js'] else 'static/'+relativo
        tipo=mimetypes.guess_type(arquivo.name)[0] or 'application/octet-stream'
        if arquivo.suffix=='.js':tipo='application/javascript'
        s3.upload_file(str(arquivo),estado['bucket_front'],chave,ExtraArgs={'ContentType':tipo+'; charset=utf-8','CacheControl':'no-cache' if arquivo.name in ['index.html','sw.js'] else 'public,max-age=3600'})


def publicar():
    plano_gratuito();cf=cliente('cloudfront');s3=cliente('s3')
    if cf.get_vpc_origin(Id=estado['vpc_origin'])['VpcOrigin']['Status']!='Deployed':
        raise SystemExit('A origem privada ainda está sendo preparada. Aguarde a AWS concluir.')
    enviar_front()
    if 'oac' not in estado:
        estado['oac']=cf.create_origin_access_control(OriginAccessControlConfig={'Name':PROJETO,'SigningProtocol':'sigv4','SigningBehavior':'always','OriginAccessControlOriginType':'s3'})['OriginAccessControl']['Id'];salvar()
    if 'distribution' not in estado:
        policies=cf.list_cache_policies(Type='managed')['CachePolicyList']['Items']
        policies={p['CachePolicy']['CachePolicyConfig']['Name']:p['CachePolicy']['Id'] for p in policies}
        requests=cf.list_origin_request_policies(Type='managed')['OriginRequestPolicyList']['Items']
        requests={p['OriginRequestPolicy']['OriginRequestPolicyConfig']['Name']:p['OriginRequestPolicy']['Id'] for p in requests}
        default={'TargetOriginId':'frontend','ViewerProtocolPolicy':'redirect-to-https','AllowedMethods':{'Quantity':3,'Items':['GET','HEAD','OPTIONS'],'CachedMethods':{'Quantity':2,'Items':['GET','HEAD']}},'Compress':True,'CachePolicyId':policies['Managed-CachingOptimized']}
        api={'TargetOriginId':'api','ViewerProtocolPolicy':'https-only','AllowedMethods':{'Quantity':7,'Items':['GET','HEAD','OPTIONS','PUT','POST','PATCH','DELETE'],'CachedMethods':{'Quantity':2,'Items':['GET','HEAD']}},'Compress':True,'CachePolicyId':policies['Managed-CachingDisabled'],'OriginRequestPolicyId':requests['Managed-AllViewer']}
        cfg={'CallerReference':PROJETO+'-2026','Comment':'VigiaCampo: front privado S3 e API em origem VPC','Enabled':True,'DefaultRootObject':'index.html','PriceClass':'PriceClass_100',
            'Origins':{'Quantity':2,'Items':[{'Id':'frontend','DomainName':f'{estado["bucket_front"]}.s3.{REGIAO}.amazonaws.com','S3OriginConfig':{'OriginAccessIdentity':''},'OriginAccessControlId':estado['oac']},
                {'Id':'api','DomainName':estado['dns_privado'],'VpcOriginConfig':{'VpcOriginId':estado['vpc_origin'],'OriginReadTimeout':60,'OriginKeepaliveTimeout':5}}]},
            'DefaultCacheBehavior':default,'CacheBehaviors':{'Quantity':4,'Items':[{'PathPattern':path,**api} for path in ['/api/*','/docs','/redoc','/health']]},
            'ViewerCertificate':{'CloudFrontDefaultCertificate':True},'HttpVersion':'http2','IsIPV6Enabled':True}
        dist=cf.create_distribution(DistributionConfig=cfg)['Distribution']
        estado['distribution']=dist['Id'];estado['url']='https://'+dist['DomainName'];salvar()
    policy={'Version':'2012-10-17','Statement':[{'Sid':'SomenteCloudFront','Effect':'Allow','Principal':{'Service':'cloudfront.amazonaws.com'},'Action':'s3:GetObject','Resource':f'arn:aws:s3:::{estado["bucket_front"]}/*','Condition':{'StringEquals':{'AWS:SourceArn':f'arn:aws:cloudfront::{estado["conta"]}:distribution/{estado["distribution"]}'}}}]}
    s3.put_bucket_policy(Bucket=estado['bucket_front'],Policy=json.dumps(policy))
    cf.create_invalidation(DistributionId=estado['distribution'],InvalidationBatch={'Paths':{'Quantity':1,'Items':['/*']},'CallerReference':str(time.time())})
    print('Endereço:',estado['url'])


def status():
    if 'instance' in estado:
        lista=cliente('ssm').describe_instance_information(Filters=[{'Key':'InstanceIds','Values':[estado['instance']]}])['InstanceInformationList']
        print('SSM:',[(i['InstanceId'],i['PingStatus']) for i in lista])
    if 'vpc_origin' in estado:print('Origem:',cliente('cloudfront').get_vpc_origin(Id=estado['vpc_origin'])['VpcOrigin']['Status'])
    if 'distribution' in estado:print('CloudFront:',cliente('cloudfront').get_distribution(Id=estado['distribution'])['Distribution']['Status'],estado['url'])


def diagnostico():
    ssm=cliente('ssm')
    if 'diagnostico' not in estado:
        estado['diagnostico']=ssm.send_command(InstanceIds=[estado['instance']],DocumentName='AWS-RunShellScript',Parameters={'commands':['docker ps --format "table {{.Names}}\t{{.Status}}"; tail -n 35 /var/log/cloud-init-output.log; curl -fsS http://127.0.0.1:8000/health']})['Command']['CommandId'];salvar()
        time.sleep(3)
    res=ssm.get_command_invocation(CommandId=estado['diagnostico'],InstanceId=estado['instance'])
    print(res['Status']);print(res.get('StandardOutputContent',''));print(res.get('StandardErrorContent',''))
    if res['Status'] in ['Success','Failed','TimedOut','Cancelled']:
        del estado['diagnostico'];salvar()


def servidor():
    plano_gratuito();pacote()
    script=(RAIZ/'deploy/update.sh').read_text(encoding='utf-8').replace('#!/bin/bash',f'#!/bin/bash\nexport PROJECT_BUCKET={estado["bucket_deploy"]}\nexport AWS_REGION={REGIAO}',1)
    estado['atualizacao']=cliente('ssm').send_command(InstanceIds=[estado['instance']],DocumentName='AWS-RunShellScript',Parameters={'commands':[script],'executionTimeout':['1800']})['Command']['CommandId'];salvar()
    print('Atualização enviada. Acompanhe com servidor_status.')


def servidor_status():
    res=cliente('ssm').get_command_invocation(CommandId=estado['atualizacao'],InstanceId=estado['instance'])
    print(res['Status']);print(res.get('StandardOutputContent','')[-3000:]);print(res.get('StandardErrorContent','')[-3000:])


if __name__=='__main__':
    {'preparar':preparar,'origem':origem,'publicar':publicar,'status':status,'diagnostico':diagnostico,'servidor':servidor,'servidor_status':servidor_status}[sys.argv[1]]()
