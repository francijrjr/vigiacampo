"""Início rápido local: python iniciar.py"""
from pathlib import Path
import secrets
import uvicorn


if __name__ == '__main__':
    import os
    os.chdir(Path(__file__).resolve().parent)
    arquivo = Path('.env')
    if not arquivo.exists():
        arquivo.write_text(
            f'SECRET_KEY={secrets.token_urlsafe(48)}\n'
            'DATABASE_URL=sqlite:///./pncd.db\n'
            'SEED_DEMO=true\nAUTO_CREATE_TABLES=true\n', encoding='utf-8')
        print('Configuração local criada em .env.')
    print('Sistema: http://127.0.0.1:8000 | Swagger: http://127.0.0.1:8000/docs')
    uvicorn.run('app.main:app', host='127.0.0.1', port=8000)
