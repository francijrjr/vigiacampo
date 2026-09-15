"""Cria o primeiro supervisor sem deixar a senha no histórico do terminal."""
import sys
from pathlib import Path
sys.path.insert(0, str(Path(__file__).resolve().parents[1]))
from getpass import getpass
from app.db.session import SessionLocal
from app.models.user import User, UserRole
from app.core.security import get_password_hash
import app.models


def main():
    nome = input("Nome completo: ").strip()
    usuario = input("Usuário: ").strip()
    municipio = input("Município: ").strip()
    senha = getpass("Senha (pelo menos 8 caracteres): ")
    if len(nome)<2 or len(usuario)<3 or len(senha)<8 or not municipio:
        raise SystemExit("Confira os campos. Nome, usuário, município e senha são obrigatórios.")
    if senha != getpass("Repita a senha: "):
        raise SystemExit("As senhas não correspondem.")
    with SessionLocal() as db:
        if db.query(User).filter_by(username=usuario).first():
            raise SystemExit("Este usuário já existe.")
        db.add(User(username=usuario,full_name=nome,municipio=municipio,
                    role=UserRole.SUPERVISOR,hashed_password=get_password_hash(senha)))
        db.commit()
    print("Supervisor criado. Você já pode entrar no sistema.")


if __name__ == '__main__':
    main()
