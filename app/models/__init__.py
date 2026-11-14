from app.models.user import User, UserRole
from app.models.boletim import BoletimReconhecimento
from app.models.territorio import CadastroTerritorial
from app.models.registro import (
    RegistroDiario,
    Quarteirao,
    Imovel,
    Inspecao,
    Coleta,
    Especime,
    Tratamento,
    DepositoEliminado,
    Foto,
    StatusRegistro,
    TipoAtividade,
)

__all__ = [
    "User",
    "UserRole",
    "CadastroTerritorial",
    "RegistroDiario",
    "Quarteirao",
    "Imovel",
    "Inspecao",
    "Coleta",
    "Especime",
    "Tratamento",
    "DepositoEliminado",
    "Foto",
    "StatusRegistro",
    "TipoAtividade",
]
