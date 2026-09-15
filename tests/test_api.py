"""Testes dos fluxos reais, sempre em banco temporário, sem tocar no pncd.db."""
import io
import pytest
from fastapi.testclient import TestClient
from sqlalchemy import create_engine
from sqlalchemy.orm import sessionmaker
from PIL import Image
from app.main import app
from app.db.session import Base, get_db
from app.models.user import User, UserRole
from app.core.security import get_password_hash
from app.core.config import settings


@pytest.fixture
def cliente(tmp_path, monkeypatch):
    engine = create_engine(f"sqlite:///{tmp_path / 'teste.db'}", connect_args={"check_same_thread": False})
    Base.metadata.create_all(engine)
    banco = sessionmaker(bind=engine)
    with banco() as db:
        for id, nome, papel, supervisor in [(1,'chefe',UserRole.SUPERVISOR,None),(2,'agente',UserRole.AGENTE,1),
                                           (3,'outro',UserRole.SUPERVISOR,None),(4,'externo',UserRole.AGENTE,3)]:
            db.add(User(id=id,username=nome, full_name=nome.title(), role=papel, supervisor_id=supervisor,
                        hashed_password=get_password_hash('senha123'), municipio='Fortaleza'))
        db.commit()
    def banco_teste():
        with banco() as db:
            try:
                yield db
            except Exception:
                db.rollback()
                raise
    app.dependency_overrides[get_db] = banco_teste
    monkeypatch.setattr(settings, 'UPLOAD_DIR', str(tmp_path))
    # Sem contexto: o lifespan de produção não é executado sobre o banco real.
    client = TestClient(app)
    yield client
    client.close()
    app.dependency_overrides.clear()
    engine.dispose()


def entrar(cliente, nome='agente'):
    resposta = cliente.post('/api/v1/auth/login', json={'username':nome,'password':'senha123'})
    assert resposta.status_code == 200, resposta.text
    return resposta.json()


def headers(cliente, nome='agente'):
    return {'Authorization':'Bearer '+entrar(cliente,nome)['access_token']}


def registro(cliente, h, **extras):
    dados = dict(municipio='Fortaleza', codigo_area='01', ciclo='03', data='2026-09-15', atividade='LI')
    resposta=cliente.post('/api/v1/registros/', headers=h, json={**dados, **extras})
    assert resposta.status_code == 201, resposta.text
    return resposta.json()


def test_swagger_e_front(cliente):
    assert cliente.get('/').status_code == 200
    assert cliente.get('/static/app.js').status_code == 200
    assert cliente.get('/docs').status_code == 200
    schema=cliente.get('/api/v1/openapi.json').json()
    assert schema['components']['securitySchemes']['HTTPBearer']['scheme']=='bearer'
    assert '/api/v1/registros/{registro_id}/imoveis/{imovel_id}/inspecoes' in schema['paths']


def test_sessao_logout_e_senha(cliente):
    sessao=entrar(cliente)
    h={'Authorization':'Bearer '+sessao['access_token']}
    assert cliente.post('/api/v1/auth/refresh',json={'refresh_token':sessao['refresh_token']}).status_code==200
    assert cliente.post('/api/v1/auth/logout',headers=h).status_code==200
    assert cliente.get('/api/v1/auth/me',headers=h).status_code==401
    assert cliente.post('/api/v1/auth/refresh',json={'refresh_token':sessao['refresh_token']}).status_code==401
    h=headers(cliente)
    assert cliente.post('/api/v1/auth/change-password',headers=h,json={'current_password':'senha123','new_password':'nova1234'}).status_code==200
    assert cliente.get('/api/v1/auth/me',headers=h).status_code==401


def test_fluxo_visita_e_totais(cliente):
    h=headers(cliente)
    r=registro(cliente,h)
    base=f"/api/v1/registros/{r['id']}"
    q=cliente.post(base+'/quarteiroes',headers=h,json={'numero':'10','logradouro':'Rua das Flores'}).json()
    im=cliente.post(base+'/imoveis',headers=h,json={'numero':'100','quarteirao_id':q['id']}).json()
    visita=base+f"/imoveis/{im['id']}"
    casos=[('inspecoes',{'a1':2,'b':3}), ('coletas',{'numero_amostra':'X','tubito_inicial':1,'tubito_final':3}),
           ('especimes',{'especie':'Aedes','larvas':4}),('tratamentos',{'categoria':'LARVICIDA_1','depositos_tratados':2}),
           ('depositos-eliminados',{'tipo':'Pneu','quantidade':2})]
    for nome,dados in casos:
        criado=cliente.post(visita+'/'+nome,headers=h,json=dados)
        assert criado.status_code==201,criado.text
        item=criado.json()
        assert cliente.put(visita+f"/{nome}/{item['id']}",headers=h,json=dados).status_code==200
        assert len(cliente.get(visita+'/'+nome,headers=h).json())==1
    resumo=cliente.get(base,headers=h).json()
    assert resumo['resumo_depositos_inspecionados']==5
    assert resumo['resumo_exemplares']==4
    assert resumo['resumo_totais_tratamento']==1
    assert cliente.delete(base+f"/quarteiroes/{q['id']}",headers=h).status_code==409
    duplicado=cliente.post(base+'/duplicar',headers=h)
    assert duplicado.status_code==201,duplicado.text
    assert duplicado.json()['imoveis'][0]['quarteirao_id']!=q['id']
    assert cliente.delete(visita,headers=h).status_code==204
    assert cliente.get(base,headers=h).json()['resumo_depositos_inspecionados']==0
    assert cliente.delete(base,headers=h).status_code==204
    assert cliente.get(base,headers=h).status_code==404
    assert cliente.delete(f"/api/v1/registros/{duplicado.json()['id']}",headers=h).status_code==204


def test_isolamento_e_bloqueio(cliente):
    agente=headers(cliente); chefe=headers(cliente,'chefe'); outro=headers(cliente,'outro')
    r=registro(cliente,agente); base=f"/api/v1/registros/{r['id']}"
    assert cliente.get(base,headers=chefe).status_code==200
    assert cliente.get(base,headers=outro).status_code==403
    assert cliente.get('/api/v1/registros/',headers=outro).json()==[]
    assert cliente.get('/api/v1/painel',headers=outro).json()['total_registros']==0
    assert cliente.patch('/api/v1/users/2',headers=outro,json={'full_name':'Intruso'}).status_code==403
    assert cliente.get('/api/v1/users/2',headers=outro).status_code==403
    assert cliente.post('/api/v1/users/',headers=agente,json={}).status_code in [403,422]
    assert cliente.patch(base,headers=agente,json={'status':'SYNCED'}).status_code==200
    assert cliente.post(base+'/imoveis',headers=agente,json={'numero':'1'}).status_code==409
    assert cliente.post(base+'/quarteiroes',headers=agente,json={'numero':'1'}).status_code==409
    assert cliente.delete(base,headers=agente).status_code==409
    assert cliente.get('/api/v1/relatorios/estatisticas',headers=outro).json()==[]
    assert len(cliente.get('/api/v1/relatorios/estatisticas',headers=chefe).json())==1


def test_validacao_e_vinculos(cliente):
    h=headers(cliente); r=registro(cliente,h); outro=registro(cliente,h)
    base=f"/api/v1/registros/{r['id']}"
    q=cliente.post(base+'/quarteiroes',headers=h,json={'numero':'1'}).json()
    assert cliente.post(f"/api/v1/registros/{outro['id']}/imoveis",headers=h,json={'numero':'1','quarteirao_id':q['id']}).status_code==422
    assert cliente.patch(base,headers=h,json={'municipio':None}).status_code==422
    assert cliente.post(base+'/imoveis',headers=h,json={'numero':'1','inspecoes':[{'a1':-1}]}).status_code==422
    assert cliente.post(base+'/imoveis',headers=h,json={'numero':'1','coletas':[{'numero_amostra':'1','tubito_inicial':5,'tubito_final':1}]}).status_code==422
    assert cliente.get('/api/v1/registros/?limit=-1',headers=h).status_code==422


def test_sync_idempotente(cliente):
    h=headers(cliente)
    dados=dict(municipio='Fortaleza',codigo_area='1',ciclo='1',data='2026-09-15',atividade='LI',client_id='offline-1')
    for esperado in ['created','skipped']:
        resposta=cliente.post('/api/v1/registros/sync',headers=h,json={'registros':[dados]})
        assert resposta.status_code==200,resposta.text
        assert resposta.json()['results'][0]['status']==esperado
    assert len(cliente.get('/api/v1/registros/',headers=h).json())==1
    assert cliente.post('/api/v1/registros/sync',headers=headers(cliente,'externo'),json={'registros':[dados]}).status_code==409
    dados.pop('client_id')
    assert cliente.post('/api/v1/registros/sync',headers=h,json={'registros':[dados]}).status_code==422


def test_fotos_e_pdf(cliente):
    h=headers(cliente); r=registro(cliente,h,observacoes='<teste> & observações')
    im=cliente.post(f"/api/v1/registros/{r['id']}/imoveis",headers=h,json={'numero':'100'}).json()
    caminho=f"/api/v1/fotos/imovel/{im['id']}"
    assert cliente.post(caminho,headers=h,files={'file':('fake.jpg',b'falso','image/jpeg')}).status_code==422
    imagem=io.BytesIO();Image.new('RGB',(30,30),'green').save(imagem,format='PNG')
    resposta=cliente.post(caminho,headers=h,files={'file':('foto.png',imagem.getvalue(),'image/png')})
    assert resposta.status_code==201,resposta.text
    foto=resposta.json()
    assert cliente.get(f"/api/v1/fotos/{foto['id']}/arquivo",headers=h).status_code==200
    assert cliente.get(f"/api/v1/fotos/{foto['id']}/arquivo",headers=headers(cliente,'externo')).status_code==403
    pdf=cliente.get(f"/api/v1/relatorios/registro/{r['id']}/pdf",headers=headers(cliente,'chefe'))
    assert pdf.status_code==200,pdf.text
    assert pdf.content.startswith(b'%PDF-')
    assert cliente.get(f"/api/v1/relatorios/registro/{r['id']}/pdf",headers=headers(cliente,'outro')).status_code==403
    assert cliente.delete(f"/api/v1/fotos/{foto['id']}",headers=h).status_code==204
    from pathlib import Path
    assert not (Path(settings.UPLOAD_DIR)/foto['filename']).exists()


def test_sync_atomico_e_quarteirao_local(cliente):
    h=headers(cliente)
    dados=dict(municipio='Fortaleza',codigo_area='1',ciclo='1',data='2026-09-15',atividade='LI',client_id='local-1',
               quarteiroes=[{'client_id':'quad-local','numero':'10'}],
               imoveis=[{'numero':'100','quarteirao_client_id':'quad-local','inspecoes':[{'a1':2}]}])
    resposta=cliente.post('/api/v1/registros/sync',headers=h,json={'registros':[dados]})
    assert resposta.status_code==200,resposta.text
    id=resposta.json()['results'][0]['server_id']
    recebido=cliente.get(f'/api/v1/registros/{id}',headers=h).json()
    assert recebido['imoveis'][0]['quarteirao_id']==recebido['quarteiroes'][0]['id']
    assert recebido['resumo_depositos_inspecionados']==2
    primeiro={**dados,'client_id':'local-2','quarteiroes':[],'imoveis':[]}
    segundo={**dados,'client_id':'local-3','quarteiroes':[],'imoveis':[{'numero':'9','quarteirao_id':999999}]}
    assert cliente.post('/api/v1/registros/sync',headers=h,json={'registros':[primeiro,segundo]}).status_code==422
    assert len(cliente.get('/api/v1/registros/',headers=h).json())==1


def test_conflito_sem_salvamento_parcial(cliente):
    h=headers(cliente)
    registro(cliente,h,client_id='unico')
    dados=dict(municipio='Fortaleza',codigo_area='1',ciclo='1',data='2026-09-15',atividade='LI',client_id='unico')
    assert cliente.post('/api/v1/registros/',headers=h,json=dados).status_code==409
    dados['client_id']='novo'
    dados['imoveis']=[{'numero':'1','quarteirao_id':99999}]
    assert cliente.post('/api/v1/registros/',headers=h,json=dados).status_code==422
    assert len(cliente.get('/api/v1/registros/',headers=h).json())==1


def test_agentes_sem_email(cliente):
    h=headers(cliente,'chefe')
    for nome in ['novo1','novo2']:
        resposta=cliente.post('/api/v1/users/',headers=h,json={
            'username':nome,'full_name':'Novo Agente','password':'senha123','email':''})
        assert resposta.status_code==201,resposta.text
        assert resposta.json()['email'] is None


def dados_boletim():
    return dict(uf='CE',distrito='20ª CRES',municipio='Crato',localidade='Centro',
                responsavel='Agente de teste',funcao_responsavel='AGENTE',subdistrito='301',
                sublocal='Setor 1',categoria='Urbana',quarteirao_numero='02',data='2026-09-15')


def test_boletim_campos_imoveis_fechamento_e_pdf(cliente):
    h=headers(cliente);r=registro(cliente,h)
    base=f"/api/v1/registros/{r['id']}"
    resposta=cliente.post(base+'/boletins',headers=h,json=dados_boletim())
    assert resposta.status_code==201,resposta.text
    b=resposta.json()
    for i,tipo in enumerate(['RESIDENCIAL','COMERCIAL','TERRENO','PONTO_ESTRATEGICO','OUTRO']):
        im=cliente.post(base+'/imoveis',headers=h,json={'numero':str(i+1),'logradouro':'Rua São João',
            'lado':str(i%4+1),'tipo':tipo,'quarteirao_id':b['quarteirao_id']})
        assert im.status_code==201,im.text
    recebido=cliente.get(base+f"/boletins/{b['id']}",headers=h).json()
    assert recebido['fechamento']==dict(residencial=1,comercial=1,terreno_baldio=1,ponto_estrategico=1,outros=1,total=5)
    assert recebido['imoveis'][0]['logradouro']=='Rua São João'
    assert recebido['imoveis'][0]['lado']=='1'
    pdf=cliente.get(base+f"/boletins/{b['id']}/pdf",headers=h)
    assert pdf.status_code==200,pdf.text
    assert pdf.content.startswith(b'%PDF')
    assert cliente.post(base+'/boletins',headers=h,json=dados_boletim()).status_code==409
    assert cliente.put(base+f"/boletins/{b['id']}",headers=h,json={**dados_boletim(),'subdistrito':'302'}).status_code==200
    duplicado=cliente.post(base+'/duplicar',headers=h).json()
    copia=cliente.get(f"/api/v1/registros/{duplicado['id']}/boletins",headers=h).json()
    assert copia[0]['fechamento']['total']==5
    assert copia[0]['imoveis'][0]['logradouro']=='Rua São João'
    assert cliente.delete(base+f"/imoveis/{recebido['imoveis'][0]['id']}",headers=h).status_code==204
    assert cliente.get(base+f"/boletins/{b['id']}",headers=h).json()['fechamento']['total']==4


def test_boletim_permissoes_e_validacao(cliente):
    h=headers(cliente);r=registro(cliente,h)
    base=f"/api/v1/registros/{r['id']}"
    assert cliente.post(base+'/boletins',headers=h,json={**dados_boletim(),'uf':'XX'}).status_code==422
    b=cliente.post(base+'/boletins',headers=h,json=dados_boletim()).json()
    outro=headers(cliente,'externo')
    assert cliente.get(base+'/boletins',headers=outro).status_code==403
    assert cliente.get(base+f"/boletins/{b['id']}/pdf",headers=outro).status_code==403
    assert cliente.patch(base,headers=h,json={'status':'SYNCED'}).status_code==200
    assert cliente.put(base+f"/boletins/{b['id']}",headers=h,json=dados_boletim()).status_code==409
    assert not cliente.get(base+f"/boletins/{b['id']}",headers=h).json()['editavel']
    assert cliente.get(base+f"/boletins/{b['id']}/pdf",headers=h).status_code==200


def test_boletim_reaproveita_quarteirao_e_endereco_antigos(cliente):
    h=headers(cliente);r=registro(cliente,h);base=f"/api/v1/registros/{r['id']}"
    q=cliente.post(base+'/quarteiroes',headers=h,json={'numero':'02','logradouro':'Rua Antiga','lado':'3'}).json()
    cliente.post(base+'/imoveis',headers=h,json={'numero':'15','quarteirao_id':q['id']})
    b=cliente.post(base+'/boletins',headers=h,json=dados_boletim()).json()
    assert b['quarteirao_id']==q['id']
    assert b['imoveis'][0]['logradouro']=='Rua Antiga'
    assert b['imoveis'][0]['lado']=='3'
