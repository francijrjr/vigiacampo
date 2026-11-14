"""Schemas de entrada e resposta do módulo de Reconhecimento Geográfico."""
from datetime import datetime
from typing import Optional
from pydantic import BaseModel, Field, field_validator, model_validator
from app.schemas.base import DadosEntrada
from app.schemas.geometria import validar_poligono


class TerritorioBase(DadosEntrada):
    municipio: str = Field(..., min_length=1, max_length=100)
    distrito: Optional[str] = Field("20ª CRES", max_length=100)
    codigo_localidade: Optional[str] = Field(None, max_length=50)
    localidade: str = Field(..., min_length=1, max_length=150)
    categoria: str = Field("Urbana", min_length=1, max_length=50)
    zona: Optional[str] = Field(None, max_length=50)
    quarteirao_numero: str = Field(..., min_length=1, max_length=20)
    lados: int = Field(4, ge=0, le=50)
    logradouros: Optional[str] = Field(None, max_length=500)
    residenciais: int = Field(0, ge=0)
    comerciais: int = Field(0, ge=0)
    terrenos_baldios: int = Field(0, ge=0)
    pontos_estrategicos: int = Field(0, ge=0)
    outros: int = Field(0, ge=0)
    geometria: Optional[dict] = None
    observacoes: Optional[str] = Field(None, max_length=5000)

    @field_validator("geometria")
    @classmethod
    def checar_geometria(cls, valor):
        return validar_poligono(valor)

    @model_validator(mode="after")
    def calcular_total(self):
        self.total_imoveis = (
            self.residenciais
            + self.comerciais
            + self.terrenos_baldios
            + self.pontos_estrategicos
            + self.outros
        )
        return self


class TerritorioCreate(TerritorioBase):
    total_imoveis: int = Field(0, ge=0)


class TerritorioResponse(TerritorioBase):
    id: int
    criado_por_id: int
    total_imoveis: int
    created_at: datetime
    updated_at: datetime


class ResumoTerritorio(BaseModel):
    total_localidades: int
    total_quarteiroes: int
    total_mapeados: int
    total_imoveis: int
