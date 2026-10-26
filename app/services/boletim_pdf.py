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


def gerar_boletim_pdf(boletim):
    arquivo = BytesIO()
    largura, altura = A4
    util = largura - 2 * MARGEM
    metade = (util - 12) / 2
    registros = []
    colunas = [metade * .60, metade * .14, metade * .08, metade * .18]
    for imovel in boletim.imoveis:
        valores = [imovel.logradouro or "", imovel.numero, imovel.lado or "", TIPOS_BOLETIM[imovel.tipo.value][0]]
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

        # Quadro do responsável, seguindo o modelo oficial.
        x, y, w = largura - MARGEM - 195, altura - 123, 195
        pdf.rect(x, y - 39, w, 39)
        pdf.setFont("Helvetica", 8)
        pdf.drawCentredString(x + w / 2, y - 10, "RESPONSÁVEL")
        pdf.line(x, y - 14, x + w, y - 14)
        for divisor in (w * .42, w * .50, w * .88):
            pdf.line(x + divisor, y - 14, x + divisor, y - 39)
        pdf.line(x, y - 26, x + w, y - 26)
        labels = [("Inspetor Geral", x + 4, y - 23), ("Inspetor", x + w * .52, y - 23), ("Chefe de Equipe", x + 4, y - 35), ("Agente", x + w * .52, y - 35)]
        for label, lx, ly in labels:
            pdf.setFont("Helvetica", 7)
            pdf.drawString(lx, ly, label)
        funcao_x = {"INSPETOR_GERAL": x + w * .46, "INSPETOR": x + w * .92, "CHEFE_EQUIPE": x + w * .46, "AGENTE": x + w * .92}[boletim.funcao_responsavel]
        funcao_y = y - 20 if boletim.funcao_responsavel in ("INSPETOR_GERAL", "INSPETOR") else y - 32
        pdf.setFont("Helvetica-Bold", 9)
        pdf.drawCentredString(funcao_x, funcao_y, "X")

    for numero, grupos in enumerate(paginas, 1):
        pdf.setStrokeColorRGB(.15, .15, .15)
        pdf.setLineWidth(.45)
        cabecalho(numero)
        campo(MARGEM, 654, 140, 19, "UF", boletim.uf)
        campo(MARGEM, 636, 245, 19, "Município", boletim.municipio)
        campo(MARGEM + 245, 636, util - 245, 19, "Sublocalidade", boletim.sublocal)
        campo(MARGEM, 610, 220, 19, "Localidade", boletim.localidade)
        campo(MARGEM + 220, 610, 150, 19, "Categoria", boletim.categoria)
        campo(largura - MARGEM - 130, 610, 130, 19, "Quart. nº", boletim.quarteirao_numero)

        for coluna, grupo in enumerate(grupos):
            x, y = MARGEM + coluna * (metade + 12), topo_tabela
            cabecalho_colunas = ["Rua ou logradouro", "Nº", "L\nA\nD\nO", "Tipo do\nimóvel"]
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

        campo(MARGEM + 10, 104, 335, 20, "Nome", boletim.responsavel)
        pdf.rect(MARGEM + 10, 84, 335, 20)
        pdf.setFont("Helvetica", 8)
        pdf.drawString(MARGEM + 15, 92, "ASSINATURA")
        campo(largura - MARGEM - 150, 91, 150, 20, "Data", boletim.data.strftime("%d/%m/%Y"))
        pdf.showPage()
    pdf.save()
    return arquivo.getvalue()
