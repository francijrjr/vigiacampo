"""Protege as dependências MVC e a entrega dos módulos no navegador."""
import ast
import mimetypes
import re
from pathlib import Path
from types import SimpleNamespace


RAIZ = Path(__file__).resolve().parents[1]
FRONTEND = RAIZ / "frontend"


def test_imports_e_cache_incluem_todos_os_modulos():
    worker = (FRONTEND / "sw.js").read_text(encoding="utf-8")
    assets = ast.literal_eval(re.search(r"const ASSETS = (\[.*?\]);", worker, re.S)[1])
    for arquivo in FRONTEND.rglob("*.js"):
        if arquivo.name == "sw.js":
            continue
        assert "/static/" + arquivo.relative_to(FRONTEND).as_posix() in assets
        texto = arquivo.read_text(encoding="utf-8")
        for caminho in re.findall(r'(?:from\s+|import\s+)["\']([^"\']+)["\']', texto):
            assert (arquivo.parent / caminho).resolve().is_file(), (arquivo, caminho)


def test_views_nao_dependem_de_modelos_ou_controllers():
    for arquivo in (FRONTEND / "views").glob("*.js"):
        texto = arquivo.read_text(encoding="utf-8")
        assert "../models/" not in texto, arquivo
        assert "../controllers/" not in texto, arquivo
        assert not re.search(r"\b(fetch|localStorage|sessionStorage)\b", texto), arquivo


def test_publicacao_preserva_subpastas_do_frontend(tmp_path):
    # Executa somente a função de envio com S3 falso, sem carregar credenciais AWS.
    codigo = ast.parse((RAIZ / "deploy/aws.py").read_text(encoding="utf-8"))
    enviar = next(no for no in codigo.body if isinstance(no, ast.FunctionDef) and no.name == "enviar_front")
    enviados = []
    contexto = {
        "RAIZ": tmp_path,
        "estado": {"bucket_front": "teste"},
        "mimetypes": mimetypes,
        "cliente": lambda nome: SimpleNamespace(upload_file=lambda *args, **kwargs: enviados.append((args, kwargs))),
    }
    for caminho in ["index.html", "sw.js", "controllers/aplicacao.js", "views/registros.js"]:
        arquivo = tmp_path / "frontend" / caminho
        arquivo.parent.mkdir(parents=True, exist_ok=True)
        arquivo.write_text("teste", encoding="utf-8")
    exec(compile(ast.Module(body=[enviar], type_ignores=[]), "envio_frontend", "exec"), contexto)
    contexto["enviar_front"]()
    assert {args[2] for args, _ in enviados} == {
        "index.html", "sw.js", "static/controllers/aplicacao.js", "static/views/registros.js",
    }
    for args, opcoes in enviados:
        if args[2].endswith(".js"):
            assert opcoes["ExtraArgs"]["ContentType"] == "application/javascript; charset=utf-8"
