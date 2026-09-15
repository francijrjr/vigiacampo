from datetime import date, datetime
from typing import Literal
from pydantic import Field, field_validator
from app.schemas.base import DadosEntrada
from app.schemas.registro import ImovelResponse

FuncaoResponsavel = Literal['INSPETOR_GERAL', 'INSPETOR', 'CHEFE_EQUIPE', 'AGENTE']


class BoletimDados(DadosEntrada):
    uf: str = Field(..., min_length=2, max_length=2, description="Sigla do estado, por exemplo CE")
    distrito: str = Field(..., min_length=1, max_length=100)
    municipio: str = Field(..., min_length=1, max_length=100)
    localidade: str = Field(..., min_length=1, max_length=150)
    responsavel: str = Field(..., min_length=2, max_length=150, description="Nome do responsável pelo boletim")
    funcao_responsavel: FuncaoResponsavel = 'AGENTE'
    subdistrito: str | None = Field(None, max_length=100)
    sublocal: str | None = Field(None, max_length=150)
    categoria: str = Field(..., min_length=1, max_length=50, description="Categoria da localidade, por exemplo Urbana ou Rural")
    quarteirao_numero: str = Field(..., min_length=1, max_length=20, description="Quart. nº da ficha")
    data: date

    @field_validator('uf')
    @classmethod
    def validar_uf(cls, valor):
        valor=valor.upper()
        if valor not in 'AC AL AP AM BA CE DF ES GO MA MT MS MG PA PB PR PE PI RJ RN RS RO RR SC SP SE TO'.split():
            raise ValueError('Selecione uma UF válida')
        return valor


class BoletimCreate(BoletimDados):
    quarteirao_id: int | None = Field(None, gt=0, description="Use para vincular um quarteirão já cadastrado neste registro")


class FechamentoBoletim(DadosEntrada):
    residencial: int = 0
    comercial: int = 0
    terreno_baldio: int = 0
    ponto_estrategico: int = 0
    outros: int = 0
    total: int = 0


class BoletimResponse(BoletimDados):
    id: int
    registro_id: int
    quarteirao_id: int
    editavel: bool
    created_at: datetime
    updated_at: datetime
    imoveis: list[ImovelResponse]
    fechamento: FechamentoBoletim
