"""PDF do registro diário no modelo oficial de Boletim de Reconhecimento."""
from types import SimpleNamespace

from app.services.boletim import TIPOS_BOLETIM
from app.services.boletim_pdf import gerar_boletim_pdf


def gerar_pdf(registro):
    """Converte o registro diário em um boletim oficial para o download geral.

    O botão *Baixar PDF* do registro pode reunir mais de um quarteirão. Por isso
    o número identifica todos os quarteirões presentes, enquanto as linhas trazem
    todos os imóveis cadastrados no dia.
    """
    imoveis = []
    totais = {"residencial": 0, "comercial": 0, "terreno_baldio": 0, "ponto_estrategico": 0, "outros": 0}
    for imovel in registro.imoveis:
        quarteirao = imovel.quarteirao
        imoveis.append(SimpleNamespace(
            logradouro=imovel.logradouro or (quarteirao.logradouro if quarteirao else ""),
            numero=imovel.numero,
            lado=imovel.lado or (quarteirao.lado if quarteirao else ""),
            tipo=imovel.tipo,
        ))
        campo = TIPOS_BOLETIM[imovel.tipo.value][2]
        totais[campo] += 1

    numeros = ", ".join(dict.fromkeys(q.numero for q in registro.quarteiroes)) or "—"
    fechamento = SimpleNamespace(**totais, total=len(imoveis))
    boletim = SimpleNamespace(
        uf="CE",
        distrito=registro.codigo_serie or "",
        municipio=registro.municipio,
        subdistrito=registro.codigo_area or "",
        sublocal=registro.zona or "",
        localidade=registro.zona or registro.municipio,
        categoria="Urbana",
        quarteirao_numero=numeros,
        responsavel=registro.agente.full_name,
        funcao_responsavel="AGENTE",
        data=registro.data,
        imoveis=imoveis,
        fechamento=fechamento,
    )
    return gerar_boletim_pdf(boletim)
