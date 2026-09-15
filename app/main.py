import os
from contextlib import asynccontextmanager
from fastapi import FastAPI
from fastapi.middleware.cors import CORSMiddleware
from fastapi.openapi.utils import get_openapi
from fastapi.staticfiles import StaticFiles
from fastapi.responses import FileResponse, JSONResponse
from sqlalchemy.exc import IntegrityError
from pathlib import Path

from app.core.config import settings
from app.db.session import engine, Base, SessionLocal
from app.models.user import User, UserRole
from app.core.security import get_password_hash

from app.api import auth, users, registros, fotos, relatorios, manutencao, painel, boletins
import app.services.arquivos


def seed_admin():
    """Cria usuarios iniciais se o banco estiver vazio."""
    db = SessionLocal()
    try:
        if db.query(User).count() == 0:
            supervisor = User(
                username="supervisor",
                email="supervisor@pncd.gov.br",
                full_name="Supervisor PNCD",
                hashed_password=get_password_hash("supervisor123"),
                role=UserRole.SUPERVISOR,
                municipio="Exemplo",
                is_active=True,
            )
            db.add(supervisor)
            db.flush()
            agente = User(
                username="agente",
                email="agente@pncd.gov.br",
                full_name="Agente de Campo",
                hashed_password=get_password_hash("agente123"),
                role=UserRole.AGENTE,
                municipio="Exemplo",
                supervisor_id=supervisor.id,
                is_active=True,
            )
            db.add(agente)
            db.commit()
            print("Usuarios seed criados: supervisor/supervisor123 | agente/agente123")
    finally:
        db.close()


@asynccontextmanager
async def lifespan(app: FastAPI):
    if settings.AUTO_CREATE_TABLES:
        Base.metadata.create_all(bind=engine)
    os.makedirs(settings.UPLOAD_DIR, exist_ok=True)
    if settings.SEED_DEMO:
        seed_admin()
    yield


app = FastAPI(
    title=settings.PROJECT_NAME,
    description=settings.PROJECT_DESCRIPTION,
    version=settings.VERSION,
    openapi_url=f"{settings.API_V1_STR}/openapi.json",
    docs_url="/docs",
    redoc_url="/redoc",
    lifespan=lifespan,
    swagger_ui_parameters={"displayRequestDuration": True, "docExpansion": "none"},
    responses={
        401: {"description": "Entre na conta ou renove a sessão"},
        403: {"description": "Seu perfil não tem acesso a esta operação"},
        404: {"description": "O item solicitado não foi encontrado"},
        409: {"description": "Há um conflito de dados ou o registro já foi enviado"},
        422: {"description": "Revise os campos informados"},
    },
)

app.add_middleware(
    CORSMiddleware,
    allow_origins=settings.CORS_ORIGINS,
    allow_credentials=True,
    allow_methods=["*"],
    allow_headers=["*"],
)

app.include_router(auth.router, prefix=settings.API_V1_STR)
app.include_router(users.router, prefix=settings.API_V1_STR)
app.include_router(registros.router, prefix=settings.API_V1_STR)
app.include_router(fotos.router, prefix=settings.API_V1_STR)
app.include_router(relatorios.router, prefix=settings.API_V1_STR)
app.include_router(manutencao.router, prefix=settings.API_V1_STR)
app.include_router(painel.router, prefix=settings.API_V1_STR)
app.include_router(boletins.router, prefix=settings.API_V1_STR)


@app.exception_handler(IntegrityError)
async def conflito_de_dados(request, exc):
    return JSONResponse(status_code=409, content={"detail": "Dados duplicados ou vínculo inválido. Revise os campos informados."})


@app.get("/api", tags=["Health"])
def root():
    return {
        "name": settings.PROJECT_NAME,
        "version": settings.VERSION,
        "docs": "/docs",
        "openapi": f"{settings.API_V1_STR}/openapi.json",
    }


@app.get("/health", tags=["Health"])
def health():
    return {"status": "ok"}


def custom_openapi():
    if app.openapi_schema:
        return app.openapi_schema
    openapi_schema = get_openapi(
        title=settings.PROJECT_NAME,
        version=settings.VERSION,
        description=settings.PROJECT_DESCRIPTION,
        routes=app.routes,
        tags=[{"name": nome, "description": descricao} for nome, descricao in [
            ("Autenticação", "Login, renovação, encerramento de sessão e troca de senha."),
            ("Usuários", "Supervisor administra os agentes da própria equipe."),
            ("Registros Diários", "Atividades diárias, imóveis e envio offline."),
            ("Dados das visitas", "Editar e excluir inspeções, coletas, espécimes e tratamentos."),
            ("Fotos", "Imagens protegidas por login, com validação de conteúdo."),
            ("Relatórios e Estatísticas", "Resumo da ficha e PDF. Estatísticas e PDF são restritos ao supervisor."),
            ("Painel", "Totais dentro da área de acesso da pessoa autenticada."),
            ("Boletim de Reconhecimento", "Cabeçalho por quarteirão, imóveis da visita, fechamento e impressão da ficha."),
        ]],
    )
    app.openapi_schema = openapi_schema
    return app.openapi_schema


app.openapi = custom_openapi

FRONTEND = Path(__file__).resolve().parent.parent / "frontend"
app.mount("/static", StaticFiles(directory=FRONTEND, check_dir=False), name="static")


@app.get("/", include_in_schema=False)
def frontend():
    return FileResponse(FRONTEND / "index.html")


@app.get("/sw.js", include_in_schema=False)
def service_worker():
    return FileResponse(FRONTEND / "sw.js", media_type="application/javascript", headers={"Cache-Control": "no-cache"})
