from app.schemas.boletim import BoletimDados, BoletimResponse, FechamentoBoletim
from app.schemas.registro import ImovelResponse
from app.models.registro import StatusRegistro
from app.models.user import UserRole

TIPOS_BOLETIM = {
    'RESIDENCIAL': ('R', 'Residencial', 'residencial'),
    'COMERCIAL': ('C', 'Comercial', 'comercial'),
    'TERRENO': ('TB', 'Terreno Baldio', 'terreno_baldio'),
    'PONTO_ESTRATEGICO': ('PE', 'Ponto Estratégico', 'ponto_estrategico'),
    'OUTRO': ('O', 'Outros', 'outros'),
}


def montar_boletim(boletim, usuario):
    q=boletim.quarteirao
    registro=q.registro
    imoveis=[]
    totais=FechamentoBoletim()
    for im in sorted(q.imoveis,key=lambda item:item.id):
        dados=ImovelResponse.model_validate(im)
        # Imóveis antigos podem ter a rua e o lado apenas no quarteirão.
        dados.logradouro=dados.logradouro or q.logradouro
        dados.lado=dados.lado or q.lado
        imoveis.append(dados)
        campo=TIPOS_BOLETIM[im.tipo.value][2]
        setattr(totais,campo,getattr(totais,campo)+1)
        totais.total+=1
    cabecalho={campo:getattr(boletim,campo) for campo in BoletimDados.model_fields if campo!='quarteirao_numero'}
    return BoletimResponse(id=boletim.id,registro_id=registro.id,quarteirao_id=q.id,
        quarteirao_numero=q.numero,created_at=boletim.created_at,updated_at=boletim.updated_at,
        editavel=registro.status!=StatusRegistro.SYNCED or usuario.role==UserRole.SUPERVISOR,
        imoveis=imoveis,fechamento=totais,**cabecalho)
