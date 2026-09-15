from sqlalchemy.orm import Session
from app.models.registro import RegistroDiario, Imovel, Inspecao, Especime, Tratamento, Pendencia


def recalcular_resumos(db: Session, registro: RegistroDiario) -> None:
    """Calcula automaticamente os resumos do verso da ficha (RF24)."""
    imoveis = db.query(Imovel).filter(Imovel.registro_id == registro.id).all()

    registro.resumo_imoveis_trabalhados = len(imoveis)
    registro.resumo_pendencias = sum(
        1 for i in imoveis if i.pendencia != Pendencia.NENHUMA
    )

    total_depositos = 0
    imoveis_com_especimes = 0
    total_exemplares = 0
    total_tratamentos = 0

    for imovel in imoveis:
        for insp in imovel.inspecoes:
            total_depositos += insp.total or (
                insp.a1 + insp.a2 + insp.b + insp.c + insp.d1 + insp.d2 + insp.e
            )
        if imovel.especimes:
            imoveis_com_especimes += 1
            for esp in imovel.especimes:
                total_exemplares += (esp.larvas or 0) + (esp.pupas or 0) + (esp.pupa_aedes or 0) + (esp.adultos or 0)
        total_tratamentos += len(imovel.tratamentos)

    registro.resumo_depositos_inspecionados = total_depositos
    registro.resumo_imoveis_com_especimes = imoveis_com_especimes
    registro.resumo_exemplares = total_exemplares
    registro.resumo_totais_tratamento = total_tratamentos

    db.add(registro)
    db.flush()
