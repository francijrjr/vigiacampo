"""Relatório legível, com quebra automática de páginas e texto escapado."""
from io import BytesIO
from xml.sax.saxutils import escape
from reportlab.lib import colors
from reportlab.lib.styles import getSampleStyleSheet
from reportlab.lib.units import cm
from reportlab.platypus import SimpleDocTemplate, Paragraph, Spacer, Table, TableStyle


def gerar_pdf(registro):
    arquivo = BytesIO()
    estilos = getSampleStyleSheet()
    def texto(valor):
        return Paragraph(escape(str(valor or "—")), estilos["BodyText"])
    partes = [Paragraph("PNCD | Registro de atividades", estilos["Title"]),
              texto(f"{registro.municipio} • {registro.data.strftime('%d/%m/%Y')}"),
              Spacer(1, .5*cm), texto(f"Agente: {registro.agente.full_name}"),
              texto(f"Área: {registro.codigo_area} | Ciclo: {registro.ciclo} | Zona: {registro.zona or '—'}"),
              texto(f"Atividade: {registro.atividade.value} | Situação: " + {"DRAFT":"Rascunho", "PENDING_SYNC":"Aguardando envio", "SYNCED":"Enviado"}[registro.status.value]),
              Spacer(1, .5*cm), Paragraph("Resumo do dia", estilos["Heading2"])]
    for label, field in [("Imóveis registrados", "imoveis_trabalhados"), ("Pendências", "pendencias"),
                         ("Depósitos inspecionados", "depositos_inspecionados"),
                         ("Imóveis com espécimes", "imoveis_com_especimes"),
                         ("Tratamentos", "totais_tratamento"), ("Exemplares", "exemplares")]:
        partes.append(texto(f"{label}: {getattr(registro, 'resumo_' + field)}"))
    partes += [Spacer(1, .4*cm), Paragraph("Imóveis visitados", estilos["Heading2"])]
    linhas = [[texto(v) for v in ["Número", "Logradouro", "Tipo", "Pendência"]]]
    for imovel in registro.imoveis:
        linhas.append([texto(imovel.numero), texto(imovel.quarteirao.logradouro if imovel.quarteirao else "—"),
                       texto(imovel.tipo.value.capitalize()), texto({"NENHUMA":"Sem pendência", "FECHADO":"Fechado", "RECUSA":"Recusa", "OUTRA":"Outra"}[imovel.pendencia.value])])
    tabela = Table(linhas, colWidths=[2*cm, 6*cm, 4*cm, 4*cm], repeatRows=1)
    tabela.setStyle(TableStyle([("BACKGROUND",(0,0),(-1,0),colors.HexColor("#dcece7")),
                               ("VALIGN",(0,0),(-1,-1),"TOP"), ("BOTTOMPADDING",(0,0),(-1,-1),9),
                               ("LINEBELOW",(0,0),(-1,-1),.4,colors.HexColor("#cccccc"))]))
    partes += [tabela, Spacer(1,.4*cm), Paragraph("Observações", estilos["Heading2"]),
               texto(registro.observacoes), Spacer(1,.5*cm),
               texto("Relatório de atividades. Não substitui o formulário oficial. Fotos não incluídas.")]
    SimpleDocTemplate(arquivo, rightMargin=1.8*cm, leftMargin=1.8*cm).build(partes)
    return arquivo.getvalue()
