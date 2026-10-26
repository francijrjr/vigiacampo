"""Ficha A4 do Boletim de Reconhecimento no padrão da Vigilância Ambiental."""
from io import BytesIO
from pathlib import Path
from xml.sax.saxutils import escape

from reportlab.lib.pagesizes import A4
from reportlab.lib.styles import ParagraphStyle
from reportlab.lib.utils import ImageReader
from reportlab.pdfgen import canvas
from reportlab.platypus import Paragraph

from app.services.boletim import TIPOS_BOLETIM


FUNCOES = {"INSPETOR_GERAL": "Inspetor Geral", "INSPETOR": "Inspetor", "CHEFE_EQUIPE": "Chefe de Equipe", "AGENTE": "Agente"}
ESTILO = ParagraphStyle("celula", fontName="Helvetica", fontSize=7.2, leading=8.7, splitLongWords=True)
MARGEM = 42


def _paragrafo(valor, largura):
    texto = Paragraph(escape(str(valor if valor is not None else "")), ESTILO)
    _, altura = texto.wrap(largura, 1000)
    return texto, altura


def _logo_crato():
    """Encontra a marca tanto no repositório quanto na imagem de produção."""
    candidatos = (
        Path(__file__).resolve().parents[1] / "assets" / "logoCrato.png",
        Path(__file__).resolve().parents[2] / "frontend" / "assets" / "logoCrato.png",
    )
    return next((caminho for caminho in candidatos if caminho.exists()), None)


def _numero_lado(valor):
    """Garante que PDFs antigos não voltem a imprimir direção em vez de número."""
    chave = str(valor or "").strip().lower()
    return {"direito": "1", "direita": "1", "esquerdo": "2", "esquerda": "2"}.get(chave, valor or "")


def gerar_boletim_pdf(boletim):
    arquivo = BytesIO()
    largura, altura = A4
    util = largura - 2 * MARGEM
    metade = (util - 12) / 2
    registros = []
    colunas = [metade * .60, metade * .14, metade * .08, metade * .18]
    for imovel in boletim.imoveis:
        valores = [imovel.logradouro or "", imovel.numero, _numero_lado(imovel.lado), TIPOS_BOLETIM[imovel.tipo.value][0]]
        altura_linha = max(13, max(_paragrafo(valor, coluna - 6)[1] + 4 for valor, coluna in zip(valores, colunas)))
        registros.append((valores, altura_linha))

    # Cada folha possui duas listas, como a ficha oficial de reconhecimento.
    topo_tabela, fundo_tabela = 581, 189
    capacidade = topo_tabela - fundo_tabela - 33
    paginas, indice = [], 0
    while indice < len(registros) or not paginas:
        grupos = []
        for _ in range(2):
            grupo, usado = [], 0
            while indice < len(registros) and usado + registros[indice][1] <= capacidade:
                valores, altura_linha = registros[indice]
                grupo.append((valores, altura_linha))
                usado += altura_linha
                indice += 1
            while usado + 13 <= capacidade:
                grupo.append((["", "", "", ""], 13))
                usado += 13
            grupos.append(grupo)
        paginas.append(grupos)

    pdf = canvas.Canvas(arquivo, pagesize=A4)
    pdf.setTitle(f"Boletim de Reconhecimento - Quarteirão {boletim.quarteirao_numero}")
    pdf.setAuthor("Prefeitura do Crato")

    def texto(valor, x, y, caixa_largura):
        paragrafo, h = _paragrafo(valor, caixa_largura)
        paragrafo.drawOn(pdf, x, y - h)

    def campo(x, y, w, h, rotulo, valor="", fonte=7):
        pdf.rect(x, y - h, w, h)
        pdf.setFont("Helvetica", fonte)
        pdf.drawString(x + 5, y - 9, rotulo.upper())
        paragrafo, _ = _paragrafo(valor, w - 10)
        paragrafo.drawOn(pdf, x + 5, y - h + 3)

    def campo_linha(x, y, w, rotulo, valor, largura_rotulo):
        """Campo do cabeçalho oficial: rótulo à esquerda e valor manuscrito ao lado."""
        altura_campo = 17
        pdf.rect(x, y - altura_campo, w, altura_campo)
        pdf.line(x + largura_rotulo, y, x + largura_rotulo, y - altura_campo)
        pdf.setFont("Helvetica", 6.7)
        pdf.drawCentredString(x + largura_rotulo / 2, y - 11, rotulo.upper())
        paragrafo, h = _paragrafo(valor, w - largura_rotulo - 7)
        paragrafo.drawOn(pdf, x + largura_rotulo + 4, y - altura_campo + max(2, (altura_campo - h) / 2))

    def cabecalho(numero):
        logo = _logo_crato()
        if logo:
            imagem = ImageReader(str(logo))
            iw, ih = imagem.getSize()
            escala = min(116 / iw, 56 / ih)
            pdf.drawImage(imagem, MARGEM, altura - 73, iw * escala, ih * escala, mask="auto")
        pdf.setFont("Helvetica-Bold", 10.8)
        pdf.drawString(MARGEM + 123, altura - 34, "SECRETARIA ESTADUAL DE SAÚDE")
        pdf.drawString(MARGEM + 123, altura - 51, "CENTRO ESTADUAL DE VIGILÂNCIA EM SAÚDE")
        pdf.drawString(MARGEM + 123, altura - 68, "DIVISÃO DE VIGILÂNCIA AMBIENTAL EM SAÚDE")
        pdf.setFont("Helvetica-Bold", 14.5)
        pdf.drawCentredString(largura / 2, altura - 109, "BOLETIM DE RECONHECIMENTO")
        pdf.setFont("Helvetica", 6.2)
        pdf.drawRightString(largura - MARGEM, altura - 113, f"Folha {numero} de {len(paginas)}")

        # Quadro do responsável com quatro células equivalentes e seleção legível.
        x, y, w = largura - MARGEM - 210, altura - 123, 210
        altura_titulo, altura_opcao = 14, 16
        pdf.rect(x, y - altura_titulo - 2 * altura_opcao, w, altura_titulo + 2 * altura_opcao)
        pdf.setFont("Helvetica-Bold", 8)
        pdf.drawCentredString(x + w / 2, y - 10, "RESPONSÁVEL")
        pdf.line(x, y - altura_titulo, x + w, y - altura_titulo)
        pdf.line(x, y - altura_titulo - altura_opcao, x + w, y - altura_titulo - altura_opcao)
        pdf.line(x + w / 2, y - altura_titulo, x + w / 2, y - altura_titulo - 2 * altura_opcao)
        metade, caixa = w / 2, 17
        opcoes = [
            ("INSPETOR_GERAL", "Inspetor Geral", 0, 0),
            ("INSPETOR", "Inspetor", 1, 0),
            ("CHEFE_EQUIPE", "Chefe de Equipe", 0, 1),
            ("AGENTE", "Agente", 1, 1),
        ]
        for codigo, nome, coluna, linha in opcoes:
            inicio_x = x + coluna * metade
            inicio_y = y - altura_titulo - linha * altura_opcao
            pdf.rect(inicio_x + metade - caixa, inicio_y - altura_opcao, caixa, altura_opcao)
            pdf.setFont("Helvetica", 7)
            pdf.drawString(inicio_x + 6, inicio_y - 10, nome)
            if boletim.funcao_responsavel == codigo:
                pdf.setFont("Helvetica-Bold", 10)
                pdf.drawCentredString(inicio_x + metade - caixa / 2, inicio_y - 11, "X")

    for numero, grupos in enumerate(paginas, 1):
        pdf.setStrokeColorRGB(.15, .15, .15)
        pdf.setLineWidth(.45)
        cabecalho(numero)
        # Bloco de identificação equilibrado em duas colunas, dentro das margens da folha.
        esquerda, largura_coluna = MARGEM, 245
        direita = esquerda + largura_coluna + 21
        campo_linha(esquerda, 654, largura_coluna, "UF", boletim.uf, 43)
        campo_linha(esquerda, 637, largura_coluna, "Distrito", getattr(boletim, "distrito", ""), 62)
        campo_linha(esquerda, 620, largura_coluna, "Município", boletim.municipio, 66)
        campo_linha(esquerda, 603, largura_coluna, "Localidade", boletim.localidade, 72)
        campo_linha(direita, 637, largura_coluna, "Subdistr.", getattr(boletim, "subdistrito", ""), 66)
        campo_linha(direita, 620, largura_coluna, "Sublocal", boletim.sublocal, 66)
        campo_linha(direita, 603, 105, "Categoria", boletim.categoria, 62)
        campo_linha(direita + 105, 603, largura_coluna - 105, "Quart. nº", boletim.quarteirao_numero, 65)

        for coluna, grupo in enumerate(grupos):
            x, y = MARGEM + coluna * (metade + 12), topo_tabela
            cabecalho_colunas = ["Rua ou logradouro", "Nº", "Nº do\nlado", "Tipo do\nimóvel"]
            alturas = [33] + [h for _, h in grupo]
            for valores, h in [(cabecalho_colunas, alturas[0]), *grupo]:
                pos = x
                for valor, coluna_largura in zip(valores, colunas):
                    pdf.rect(pos, y - h, coluna_largura, h)
                    if valores is cabecalho_colunas:
                        pdf.setFont("Helvetica", 7 if "\n" not in valor else 6.5)
                        partes = valor.split("\n")
                        for idx, parte in enumerate(partes):
                            pdf.drawCentredString(pos + coluna_largura / 2, y - h / 2 + (len(partes) / 2 - idx - .5) * 8, parte)
                    else:
                        texto(valor, pos + 3, y - 3, coluna_largura - 6)
                    pos += coluna_largura
                y -= h

        pdf.rect(MARGEM, 165, util, 15)
        pdf.setFont("Helvetica", 10)
        pdf.drawCentredString(largura / 2, 170, "FECHAMENTO")
        pares = [
            ("RESIDENCIAL", "R", boletim.fechamento.residencial, "PONTO ESTRATÉGICO", "PE", boletim.fechamento.ponto_estrategico),
            ("COMERCIAL", "C", boletim.fechamento.comercial, "OUTROS", "O", boletim.fechamento.outros),
            ("TERRENO BALDIO", "TB", boletim.fechamento.terreno_baldio, "TOTAL GERAL", "", boletim.fechamento.total),
        ]
        y = 165
        for linha in pares:
            for lado in range(2):
                label, sigla, total = linha[lado * 3: lado * 3 + 3]
                x = MARGEM + lado * util / 2
                pdf.rect(x, y - 15, util / 2, 15)
                pdf.setFont("Helvetica", 8)
                pdf.drawCentredString(x + util * .22, y - 10, label)
                pdf.drawCentredString(x + util * .36, y - 10, sigla)
                pdf.setFont("Helvetica-Bold", 8)
                pdf.drawRightString(x + util / 2 - 8, y - 10, str(total))
            y -= 15

        # Rodapé amplo: nome legível, campo reservado para assinatura e data separada.
        assinatura_x, assinatura_largura = MARGEM + 10, 335
        pdf.rect(assinatura_x, 92, assinatura_largura, 18)
        pdf.setFont("Helvetica-Bold", 7.5)
        pdf.drawString(assinatura_x + 7, 99, "NOME DO RESPONSÁVEL")
        pdf.setFont("Helvetica", 8.5)
        pdf.drawString(assinatura_x + 105, 99, str(boletim.responsavel or ""))
        pdf.rect(assinatura_x, 55, assinatura_largura, 37)
        pdf.setFont("Helvetica-Bold", 8)
        pdf.drawString(assinatura_x + 7, 82, "ASSINATURA")
        pdf.setLineWidth(.7)
        pdf.line(assinatura_x + 12, 64, assinatura_x + assinatura_largura - 12, 64)
        pdf.setLineWidth(.45)
        data_x, data_largura = largura - MARGEM - 150, 150
        pdf.rect(data_x, 67, data_largura, 25)
        pdf.setFont("Helvetica-Bold", 8)
        pdf.drawString(data_x + 8, 82, "DATA")
        pdf.setFont("Helvetica", 9)
        pdf.drawString(data_x + 8, 72, boletim.data.strftime("%d/%m/%Y"))
        pdf.showPage()
    pdf.save()
    return arquivo.getvalue()
