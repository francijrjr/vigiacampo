"""Ficha A4 do boletim: duas colunas de imóveis e fechamento automático."""
from io import BytesIO
from xml.sax.saxutils import escape
from reportlab.pdfgen import canvas
from reportlab.lib.pagesizes import A4
from reportlab.lib.styles import ParagraphStyle
from reportlab.platypus import Paragraph
from app.services.boletim import TIPOS_BOLETIM

FUNCOES={'INSPETOR_GERAL':'Inspetor geral','INSPETOR':'Inspetor','CHEFE_EQUIPE':'Chefe de equipe','AGENTE':'Agente'}
ESTILO=ParagraphStyle('celula',fontName='Helvetica',fontSize=8,leading=10,splitLongWords=True)


def paragrafo(valor, largura):
    texto=Paragraph(escape(str(valor if valor is not None else '')),ESTILO)
    _,altura=texto.wrap(largura,1000)
    return texto,altura


def gerar_boletim_pdf(boletim):
    arquivo=BytesIO()
    largura,altura=A4
    margem=30
    util=largura-2*margem
    metade=(util-14)/2
    linhas_cabecalho=[
        [('UF',boletim.uf),('Distrito',boletim.distrito)],
        [('Município',boletim.municipio),('Subdist.',boletim.subdistrito)],
        [('Localidade',boletim.localidade),('Sublocal',boletim.sublocal)],
        [('Categoria',boletim.categoria),('Quart. nº',boletim.quarteirao_numero)],
        [('Responsável',boletim.responsavel),('Função do responsável',FUNCOES[boletim.funcao_responsavel])],
    ]
    alturas_cabecalho=[max(30,max(paragrafo(v,metade-12)[1]+17 for _,v in row)) for row in linhas_cabecalho]
    topo_tabela=altura-92-sum(alturas_cabecalho)-12
    fundo_tabela=182
    capacidade=topo_tabela-fundo_tabela-27
    colunas=[metade*.58,metade*.18,metade*.10,metade*.14]
    registros=[]
    for im in boletim.imoveis:
        valores=[im.logradouro or '',im.numero,im.lado or '',TIPOS_BOLETIM[im.tipo.value][0]]
        h=max(17,max(paragrafo(v,w-8)[1]+6 for v,w in zip(valores,colunas)))
        registros.append((valores,h))
    paginas=[]
    indice=0
    while indice<len(registros) or not paginas:
        grupos=[]
        for _ in range(2):
            grupo=[]
            usado=0
            while indice<len(registros) and usado+registros[indice][1]<=capacidade:
                valores,h=registros[indice]
                grupo.append((valores,h));usado+=h;indice+=1
            if not grupo and indice<len(registros) and registros[indice][1]>capacidade:
                raise ValueError('Um endereço excede o espaço disponível na ficha')
            while usado+17<=capacidade:
                grupo.append((['','','',''],17));usado+=17
            grupos.append(grupo)
        paginas.append(grupos)
    pdf=canvas.Canvas(arquivo,pagesize=A4)
    pdf.setTitle(f'Boletim de Reconhecimento - Quarteirão {boletim.quarteirao_numero}')
    pdf.setAuthor('VigiaCampo')

    def texto(valor,x,y,w):
        p,h=paragrafo(valor,w)
        p.drawOn(pdf,x,y-h)

    for numero,grupos in enumerate(paginas,1):
        pdf.setStrokeColorRGB(.25,.25,.25);pdf.setLineWidth(.5)
        pdf.setFont('Helvetica',10)
        pdf.drawCentredString(largura/2,altura-35,'Programa de Controle da Febre Amarela e Dengue - PCFAD')
        pdf.setFont('Helvetica-Bold',16)
        pdf.drawCentredString(largura/2,altura-60,'Boletim de Reconhecimento')
        pdf.setFont('Helvetica',8)
        pdf.drawRightString(largura-margem,altura-78,f'Folha {numero} de {len(paginas)}')
        y=altura-92
        for campos,h in zip(linhas_cabecalho,alturas_cabecalho):
            for coluna,(label,valor) in enumerate(campos):
                x=margem+coluna*(metade+14)
                pdf.rect(x,y-h,metade,h)
                pdf.setFont('Helvetica-Bold',7)
                pdf.drawString(x+6,y-10,label.upper())
                texto(valor,x+6,y-14,metade-12)
            y-=h
        for coluna,grupo in enumerate(grupos):
            x=margem+coluna*(metade+14)
            y=topo_tabela
            for valores,h in [(['Rua ou logradouro','Número','Lado','Tipo do imóvel'],27),*grupo]:
                pos=x
                for valor,w in zip(valores,colunas):
                    pdf.rect(pos,y-h,w,h)
                    texto(valor,pos+4,y-4,w-8)
                    pos+=w
                y-=h
        pdf.setFont('Helvetica-Bold',9)
        pdf.drawCentredString(largura/2,163,'Fechamento geral do boletim')
        pares=[('Residencial','R',boletim.fechamento.residencial,'Ponto Estratégico','PE',boletim.fechamento.ponto_estrategico),
               ('Comercial','C',boletim.fechamento.comercial,'Outros','O',boletim.fechamento.outros),
               ('Terreno Baldio','TB',boletim.fechamento.terreno_baldio,'Total geral','',boletim.fechamento.total)]
        y=154
        for row in pares:
            for lado in range(2):
                label,sigla,total=row[lado*3:lado*3+3]
                x=margem+lado*util/2
                pdf.rect(x,y-20,util/2,20)
                pdf.setFont('Helvetica',8);pdf.drawString(x+7,y-13,label)
                pdf.drawString(x+util/2-64,y-13,sigla)
                pdf.setFont('Helvetica-Bold',9);pdf.drawRightString(x+util/2-9,y-13,str(total))
            y-=20
        pdf.setFont('Helvetica-Bold',8);pdf.drawString(margem,79,'NOME:')
        texto(boletim.responsavel,margem+36,85,util-36)
        pdf.line(margem+65,40,largura-margem-120,40)
        pdf.setFont('Helvetica',8);pdf.drawString(margem,42,'ASSINATURA:')
        pdf.drawRightString(largura-margem,42,'DATA: '+boletim.data.strftime('%d/%m/%Y'))
        pdf.setFont('Helvetica',6.5);pdf.drawString(margem,20,'VigiaCampo | Boletim de reconhecimento | Fechamento calculado a partir dos imóveis cadastrados.')
        pdf.showPage()
    pdf.save()
    return arquivo.getvalue()
