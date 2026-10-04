from datetime import datetime, date
from typing import Optional, List
from pydantic import BaseModel, Field, model_validator, field_validator
from app.schemas.geometria import validar_poligono
from app.schemas.base import DadosEntrada
from app.models.registro import (
    StatusRegistro, TipoAtividade, TipoImovel, TipoVisita,
    Pendencia, CategoriaDeposito, CategoriaTratamento
)


# ---------- Inspecao ----------
class InspecaoBase(DadosEntrada):
    a1: int = Field(0, ge=0)
    a2: int = Field(0, ge=0)
    b: int = Field(0, ge=0)
    c: int = Field(0, ge=0)
    d1: int = Field(0, ge=0)
    d2: int = Field(0, ge=0)
    e: int = Field(0, ge=0)
    client_id: Optional[str] = None

    @model_validator(mode="after")
    def calc_total(self):
        self.total = self.a1 + self.a2 + self.b + self.c + self.d1 + self.d2 + self.e
        return self


class InspecaoCreate(InspecaoBase):
    total: int = Field(0, ge=0)


class InspecaoResponse(InspecaoBase):
    id: int
    imovel_id: int
    total: int
    created_at: datetime



# ---------- Coleta ----------
class ColetaBase(DadosEntrada):
    numero_amostra: str = Field(..., min_length=1, max_length=50)
    tubito_inicial: int = Field(..., ge=0)
    tubito_final: int = Field(..., ge=0)
    client_id: Optional[str] = None

    @model_validator(mode="after")
    def calc_qtd(self):
        if self.tubito_final < self.tubito_inicial:
            raise ValueError("O tubito final deve ser maior ou igual ao inicial")
        self.quantidade_tubitos = max(0, self.tubito_final - self.tubito_inicial + 1)
        return self


class ColetaCreate(ColetaBase):
    quantidade_tubitos: int = Field(0, ge=0)


class ColetaResponse(ColetaBase):
    id: int
    imovel_id: int
    quantidade_tubitos: int
    created_at: datetime



# ---------- Especime ----------
class EspecimeBase(DadosEntrada):
    especie: str = Field(..., min_length=1, max_length=100)
    larvas: int = Field(0, ge=0)
    pupas: int = Field(0, ge=0)
    pupa_aedes: int = Field(0, ge=0)
    adultos: int = Field(0, ge=0)
    client_id: Optional[str] = None


class EspecimeCreate(EspecimeBase):
    pass


class EspecimeResponse(EspecimeBase):
    id: int
    imovel_id: int
    created_at: datetime



# ---------- Tratamento ----------
class TratamentoBase(DadosEntrada):
    categoria: CategoriaTratamento
    produto: Optional[str] = None
    quantidade: float = Field(0, ge=0, allow_inf_nan=False)
    depositos_tratados: int = Field(0, ge=0)
    cargas: int = Field(0, ge=0)
    client_id: Optional[str] = None


class TratamentoCreate(TratamentoBase):
    pass


class TratamentoResponse(TratamentoBase):
    id: int
    imovel_id: int
    created_at: datetime



# ---------- DepositoEliminado ----------
class DepositoEliminadoBase(DadosEntrada):
    tipo: str
    quantidade: int = Field(0, ge=0)
    client_id: Optional[str] = None


class DepositoEliminadoCreate(DepositoEliminadoBase):
    pass


class DepositoEliminadoResponse(DepositoEliminadoBase):
    id: int
    imovel_id: int
    created_at: datetime



# ---------- Foto ----------
class FotoResponse(DadosEntrada):
    id: int
    imovel_id: int
    filename: str
    descricao: Optional[str] = None
    data_hora: datetime
    created_at: datetime



# ---------- Imovel ----------
class ImovelBase(DadosEntrada):
    numero: str = Field(..., min_length=1, max_length=20)
    complemento: Optional[str] = None
    logradouro: Optional[str] = Field(None, max_length=255, description="Rua ou logradouro do imóvel")
    lado: Optional[str] = Field(None, max_length=20, description="Lado do quarteirão, conforme a ficha")
    tipo: TipoImovel = TipoImovel.RESIDENCIAL
    hora_entrada: Optional[str] = None
    tipo_visita: TipoVisita = TipoVisita.NORMAL
    pendencia: Pendencia = Pendencia.NENHUMA
    quarteirao_id: Optional[int] = None
    quarteirao_client_id: Optional[str] = Field(None, max_length=64, description="Identificador do quarteirão criado no mesmo envio offline")
    client_id: Optional[str] = None


class ImovelCreate(ImovelBase):
    inspecoes: List[InspecaoCreate] = Field(default_factory=list)
    coletas: List[ColetaCreate] = Field(default_factory=list)
    especimes: List[EspecimeCreate] = Field(default_factory=list)
    tratamentos: List[TratamentoCreate] = Field(default_factory=list)
    depositos_eliminados: List[DepositoEliminadoCreate] = Field(default_factory=list)


class ImovelUpdate(DadosEntrada):
    numero: Optional[str] = None
    complemento: Optional[str] = None
    logradouro: Optional[str] = Field(None, max_length=255)
    lado: Optional[str] = Field(None, max_length=20)
    tipo: Optional[TipoImovel] = None
    hora_entrada: Optional[str] = None
    tipo_visita: Optional[TipoVisita] = None
    pendencia: Optional[Pendencia] = None
    quarteirao_id: Optional[int] = None


class ImovelResponse(ImovelBase):
    id: int
    registro_id: int
    created_at: datetime
    updated_at: datetime
    inspecoes: List[InspecaoResponse] = Field(default_factory=list)
    coletas: List[ColetaResponse] = Field(default_factory=list)
    especimes: List[EspecimeResponse] = Field(default_factory=list)
    tratamentos: List[TratamentoResponse] = Field(default_factory=list)
    depositos_eliminados: List[DepositoEliminadoResponse] = Field(default_factory=list)
    fotos: List[FotoResponse] = Field(default_factory=list)



# ---------- Quarteirao ----------
class QuarteiraoBase(DadosEntrada):
    numero: str = Field(..., min_length=1, max_length=20)
    sequencia: Optional[int] = None
    lado: Optional[str] = None
    logradouro: Optional[str] = None
    client_id: Optional[str] = None
    geometria: Optional[dict] = None

    @field_validator('geometria')
    @classmethod
    def validar_geometria(cls, valor):
        return validar_poligono(valor)


class QuarteiraoCreate(QuarteiraoBase):
    pass


class QuarteiraoResponse(QuarteiraoBase):
    id: int
    registro_id: int
    created_at: datetime



# ---------- RegistroDiario ----------
class RegistroDiarioBase(DadosEntrada):
    codigo_serie: Optional[str] = Field("20ª Ceres", min_length=1, max_length=100)
    municipio: str = Field(..., min_length=1, max_length=100)
    codigo_area: str = Field(..., min_length=1, max_length=50)
    ciclo: str = Field(..., min_length=1, max_length=50)
    data: date
    zona: Optional[str] = None
    atividade: TipoAtividade
    concluido: bool = False
    observacoes: Optional[str] = None
    client_id: Optional[str] = None


class RegistroDiarioCreate(RegistroDiarioBase):
    model_config = {"json_schema_extra": {"examples": [{
        "municipio": "Fortaleza", "codigo_area": "Centro", "ciclo": "03",
        "data": "2026-09-15", "atividade": "LI", "observacoes": "Visitas no período da manhã"
    }]}}
    quarteiroes: List[QuarteiraoCreate] = Field(default_factory=list)
    imoveis: List[ImovelCreate] = Field(default_factory=list)


class RegistroDiarioUpdate(DadosEntrada):
    codigo_serie: Optional[str] = Field(None, min_length=1, max_length=100)
    municipio: Optional[str] = None
    codigo_area: Optional[str] = None
    ciclo: Optional[str] = None
    data: Optional[date] = None
    zona: Optional[str] = None
    atividade: Optional[TipoAtividade] = None
    concluido: Optional[bool] = None
    observacoes: Optional[str] = None
    status: Optional[StatusRegistro] = None


class RegistroDiarioResponse(RegistroDiarioBase):
    id: int
    agente_id: int
    status: StatusRegistro
    synced_at: Optional[datetime] = None
    created_at: datetime
    updated_at: datetime
    resumo_imoveis_trabalhados: int = Field(0, ge=0)
    resumo_pendencias: int = Field(0, ge=0)
    resumo_depositos_inspecionados: int = Field(0, ge=0)
    resumo_imoveis_com_especimes: int = Field(0, ge=0)
    resumo_totais_tratamento: int = Field(0, ge=0)
    resumo_exemplares: int = Field(0, ge=0)
    quarteiroes: List[QuarteiraoResponse] = Field(default_factory=list)
    imoveis: List[ImovelResponse] = Field(default_factory=list)



class RegistroDiarioListItem(DadosEntrada):
    codigo_serie: Optional[str] = None
    id: int
    municipio: str = Field(..., min_length=1, max_length=100)
    codigo_area: str = Field(..., min_length=1, max_length=50)
    ciclo: str = Field(..., min_length=1, max_length=50)
    data: date
    zona: Optional[str]
    atividade: TipoAtividade
    status: StatusRegistro
    concluido: bool
    created_at: datetime
    resumo_imoveis_trabalhados: int = Field(0, ge=0)



# ---------- Sync ----------
class SyncPayload(DadosEntrada):
    """Payload para sincronização em lote de registros offline."""
    registros: List[RegistroDiarioCreate] = Field(..., min_length=1, max_length=100)

    @model_validator(mode="after")
    def validar_identificadores(self):
        if any(not r.client_id for r in self.registros):
            raise ValueError("Cada registro offline precisa de client_id")
        return self


class SyncResultItem(DadosEntrada):
    client_id: Optional[str]
    server_id: int
    status: str  # created | updated | skipped
    message: Optional[str] = None


class SyncResponse(DadosEntrada):
    results: List[SyncResultItem]
    total_processed: int
    total_created: int
    total_skipped: int


# ---------- Stats ----------
class StatsAgente(DadosEntrada):
    agente_id: int
    agente_nome: str
    total_registros: int
    total_imoveis: int
    total_inspecoes: int
    periodo_inicio: Optional[date]
    periodo_fim: Optional[date]
