"""Importa o banco local em um PostgreSQL vazio, sem expor dados ou senhas nos logs."""
import os
import sys
from pathlib import Path
sys.path.insert(0,str(Path(__file__).resolve().parents[1]))
from sqlalchemy import create_engine, MetaData, select, text, func
from app.db.session import engine, Base
from app.core.security import get_password_hash, verify_password
from app.models.user import User, UserRole
from app.core.datas import agora_utc
import app.models, app.models.sessao


def importar(caminho):
    origem=create_engine('sqlite:///'+str(Path(caminho).resolve()))
    metadados=MetaData();metadados.reflect(origem)
    with engine.begin() as destino, origem.connect() as leitura:
        if destino.scalar(select(func.count()).select_from(User.__table__)):
            print('Banco de destino já possui usuários. Importação não repetida.')
            return
        for tabela in Base.metadata.sorted_tables:
            if tabela.name not in metadados.tables or tabela.name=='sessoes_revogadas':
                continue
            linhas=[{k:v for k,v in row.items() if k in tabela.c} for row in leitura.execute(select(metadados.tables[tabela.name])).mappings()]
            if tabela.name=='users':
                pendentes={row['id']:row for row in linhas};linhas=[];incluidos=set()
                while pendentes:
                    prontos=[row for row in pendentes.values() if row['supervisor_id'] is None or row['supervisor_id'] in incluidos]
                    if not prontos:
                        raise ValueError('Há um vínculo circular ou inexistente entre supervisores no banco de origem')
                    for row in prontos:
                        incluidos.add(row['id']);linhas.append(row);del pendentes[row['id']]
            for row in linhas:
                if tabela.name=='fotos':
                    row['filepath']='./uploads/'+row['filename']
                destino.execute(tabela.insert().values(**row))
            if engine.dialect.name=='postgresql' and 'id' in tabela.c and str(tabela.c.id.type)=='INTEGER':
                nome=tabela.name
                destino.execute(text(f"SELECT setval(pg_get_serial_sequence('{nome}', 'id'), COALESCE((SELECT MAX(id) FROM {nome}), 1), EXISTS(SELECT 1 FROM {nome}))"))
        senha=os.environ.get('BOOTSTRAP_PASSWORD')
        if not senha:
            raise ValueError('Defina BOOTSTRAP_PASSWORD para proteger os acessos de demonstração antes da publicação')
        # Somente senhas públicas da demonstração são substituídas; senhas pessoais permanecem intactas.
        for user in destino.execute(select(User.__table__)).mappings():
            senha_demo={'supervisor':'supervisor123','agente':'agente123'}.get(user['username'])
            if senha_demo and verify_password(senha_demo,user['hashed_password']):
                destino.execute(User.__table__.update().where(User.id==user['id']).values(
                    hashed_password=get_password_hash(senha),is_active=user['username']=='supervisor',updated_at=agora_utc()))
        if not destino.scalar(select(func.count()).select_from(User.__table__)):
            destino.execute(User.__table__.insert().values(username='supervisor',full_name='Supervisor',role=UserRole.SUPERVISOR,
                is_active=True,hashed_password=get_password_hash(senha),created_at=agora_utc(),updated_at=agora_utc()))
    print('Banco importado. Credenciais públicas de demonstração protegidas.')


if __name__=='__main__':
    importar(sys.argv[1])
