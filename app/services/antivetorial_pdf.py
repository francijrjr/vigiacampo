"""Geração da ficha diária do serviço antivetorial, no modelo do PNCD."""
from io import BytesIO

from reportlab.lib import colors
from reportlab.lib.pagesizes import A4, landscape
from reportlab.lib.units import mm
from reportlab.pdfbase.pdfmetrics import stringWidth
from reportlab.pdfgen import canvas


CINZA = colors.HexColor("#d9d9d9")
MARGEM = 12 * mm
LARGURA, ALTURA = landscape(A4)


def _texto(c, valor, x, y, largura, tamanho=5, negrito=False, limite=None):
    """Escreve texto centralizado, reduzindo-o sem deixá-lo ultrapassar a célula."""
    fonte = "Helvetica-Bold" if negrito else "Helvetica"
    valor = str(valor or "")
    maximo = largura - 1.2 * mm if limite is None else limite
    while valor and stringWidth(valor, fonte, tamanho) > maximo:
        valor = valor[:-1]
    c.setFont(fonte, tamanho)
    c.drawCentredString(x + largura / 2, y, valor)


def _caixa(c, x, y, largura, altura, rotulo="", valor="", tamanho=5, faixa=True):
    c.rect(x, y, largura, altura)
    if rotulo:
        faixa_altura = min(4 * mm, altura * .46) if faixa else 0
        if faixa_altura:
            c.setFillColor(CINZA)
            c.rect(x, y + altura - faixa_altura, largura, faixa_altura, fill=1, stroke=1)
            c.setFillColor(colors.black)
            _texto(c, rotulo, x, y + altura - faixa_altura + 1.05 * mm, largura, 4.1, True)
        else:
            _texto(c, rotulo, x, y + altura - 3.2 * mm, largura, 4.1, True)
    _texto(c, valor, x, y + 1.55 * mm, largura, tamanho)


def _faixa(c, texto, y, altura=5.5 * mm):
    c.setFillColor(CINZA)
    c.rect(MARGEM, y, LARGURA - 2 * MARGEM, altura, fill=1, stroke=1)
    c.setFillColor(colors.black)
    _texto(c, texto, MARGEM, y + 1.55 * mm, LARGURA - 2 * MARGEM, 5.5, True)


def _campo(c, x_mm, y, largura_mm, rotulo, valor, altura=8 * mm, tamanho=4.8):
    _caixa(c, MARGEM + x_mm * mm, y, largura_mm * mm, altura, rotulo, valor, tamanho)


def _soma(linhas, campo):
    return sum(int(item.get(campo) or 0) for item in linhas)


def _por_tipo(linhas, tipo):
    return sum(1 for item in linhas if str(item.get("tipo_imovel") or "").upper() == tipo)


def _cabecalho(c, registro, dados):
    y = ALTURA - 12 * mm
    c.setFont("Helvetica-Bold", 5.6)
    for indice, texto in enumerate((
        "PREFEITURA MUNICIPAL DE CHAVAL",
        "SECRETARIA MUNICIPAL DE SAÚDE",
        "PROGRAMA NACIONAL DE CONTROLE DO SERVIÇO ANTIVETORIAL",
    )):
        c.drawString(MARGEM, y - indice * 2.8 * mm, texto)
    c.setFont("Helvetica-Bold", 8.2)
    c.drawCentredString(LARGURA / 2, y - 5.6 * mm, "REGISTRO DIÁRIO DO SERVIÇO ANTIVETORIAL")

    topo = ALTURA - 30 * mm
    _campo(c, 0, topo, 52, "Município", registro.municipio)
    _campo(c, 55, topo, 70, "Código e nome da localidade", dados.get("codigo_localidade") or registro.localidade)
    _campo(c, 128, topo, 27, "Categoria / localidade", dados.get("categoria_localidade"))
    _campo(c, 158, topo, 58, "Zona", dados.get("zona") or registro.zona_bairro)
    _campo(c, 219, topo, 22, "Tipo", dados.get("tipo"))
    _campo(c, 244, topo, 18, "Concluída", dados.get("conclusao"))

    linha = topo - 10 * mm
    _campo(c, 0, linha, 42, "Data da atividade", registro.data.strftime("%d/%m/%Y"))
    _campo(c, 45, linha, 32, "Ciclo / ano", registro.ciclo)
    _campo(c, 80, linha, 182, "Atividade", dados.get("atividade") or "Pesquisa entomológica / tratamento")

    linha -= 7 * mm
    atividades = [
        "1 - L.I. / levantamento de índice", "2 - L.I.A. / levantamento de índice",
        "3 - P.E. / pesquisa especial", "4 - T. / tratamento", "5 - P.E. + tratamento",
        "6 - P.V.E. / pesquisa vetorial especial",
    ]
    largura = (LARGURA - 2 * MARGEM) / len(atividades)
    for indice, atividade in enumerate(atividades):
        _caixa(c, MARGEM + indice * largura, linha, largura, 5 * mm, "", atividade, 3.65, False)
    return linha - 2 * mm


def _pagina_pesquisa(c, registro, dados):
    y = _cabecalho(c, registro, dados)
    _faixa(c, "PESQUISA ENTOMOLÓGICA / TRATAMENTO", y)
    y -= 1 * mm
    inicio_x = MARGEM
    largura_tabela = LARGURA - 2 * MARGEM
    # Mantém somente Nº do quart. e Lado: o Seq. ao lado do quarteirão não existe no formulário.
    rotulos = [
        "Nº do\nquart.", "Lado", "Nome do logradouro", "Nº", "Tipo do\nimóvel", "Hora", "Visita",
        "Pend.", "A1", "A2", "B", "C", "D1", "D2", "E", "Total", "Foco", "Tratamento", "Observações",
    ]
    pesos = [15, 14, 94, 17, 21, 18, 20, 18, 12, 12, 12, 12, 12, 12, 12, 17, 18, 31, 44]
    fator = largura_tabela / sum(pesos)
    colunas = [peso * fator for peso in pesos]
    cab_altura = 10 * mm
    c.setFillColor(CINZA)
    c.rect(inicio_x, y - cab_altura, largura_tabela, cab_altura, fill=1, stroke=1)
    c.setFillColor(colors.black)
    x = inicio_x
    for coluna, rotulo in zip(colunas, rotulos):
        c.rect(x, y - cab_altura, coluna, cab_altura)
        partes = rotulo.split("\n")
        for indice, parte in enumerate(partes):
            _texto(c, parte, x, y - 4.2 * mm - indice * 3.3 * mm, coluna, 3.75, True)
        x += coluna

    linhas_por_ordem = {item.get("ordem"): item for item in dados.get("linhas", [])}
    altura_linha = 5.25 * mm
    for ordem in range(1, 25):
        yy = y - cab_altura - ordem * altura_linha
        item = linhas_por_ordem.get(ordem, {})
        total = sum(int(item.get(chave) or 0) for chave in ("a1", "a2", "b", "c", "d1", "d2", "e"))
        valores = [
            item.get("quarteirao"), item.get("lado"), item.get("logradouro"), item.get("numero"),
            item.get("tipo_imovel"), "", item.get("visita"), "", item.get("a1"), item.get("a2"),
            item.get("b"), item.get("c"), item.get("d1"), item.get("d2"), item.get("e"), total,
            "X" if item.get("foco") else "", item.get("tratamento"), "",
        ]
        x = inicio_x
        for coluna, valor in zip(colunas, valores):
            c.rect(x, yy, coluna, altura_linha)
            _texto(c, valor, x, yy + 1.35 * mm, coluna, 3.7)
            x += coluna

    rodape = y - cab_altura - 24 * altura_linha - 8 * mm
    _caixa(c, MARGEM, rodape, 74 * mm, 7 * mm, "Agente", dados.get("agente") or registro.agente.full_name, 4.8)
    _caixa(c, MARGEM + 77 * mm, rodape, 78 * mm, 7 * mm, "Supervisor", dados.get("supervisor"), 4.8)
    _caixa(c, MARGEM + 158 * mm, rodape, 54 * mm, 7 * mm, "Tipo de imóvel", "R: residencial  C: comércio", 3.4)
    _caixa(c, MARGEM + 215 * mm, rodape, 47 * mm, 7 * mm, "Pendência", "F: fechado  R: recusa", 3.35)
    c.setFont("Helvetica", 3.6)
    c.drawString(MARGEM, 10 * mm, "A1: depósito elevado | A2: depósito ao nível do solo | B: móvel | C: fixo | D1/D2: pneus e materiais | E: natural")


def _resumo_caixa(c, x, y, largura, altura, titulo, colunas, valores):
    _caixa(c, x, y, largura, altura, titulo, "", 4.2)
    largura_celula = largura / len(colunas)
    meio = y + altura * .42
    for indice, (coluna, valor) in enumerate(zip(colunas, valores)):
        xx = x + indice * largura_celula
        c.rect(xx, y, largura_celula, altura * .56)
        _texto(c, coluna, xx, meio, largura_celula, 3.5, True)
        _texto(c, valor, xx, y + 1.7 * mm, largura_celula, 5)


def _pagina_resumo(c, registro, dados):
    linhas = dados.get("linhas", [])
    totais = {chave: _soma(linhas, chave) for chave in ("a1", "a2", "b", "c", "d1", "d2", "e")}
    _faixa(c, "RESUMO DIÁRIO DO TRABALHO DE CAMPO", ALTURA - 16 * mm)
    y = ALTURA - 42 * mm
    _resumo_caixa(c, MARGEM, y, 68 * mm, 21 * mm, "Nº de imóveis trabalhados por tipo", ["Resid.", "Comércio", "T. bald.", "Outros", "Total"], [_por_tipo(linhas, "RESIDENCIAL"), _por_tipo(linhas, "COMERCIAL"), _por_tipo(linhas, "TERRENO BALDIO"), _por_tipo(linhas, "OUTROS"), len(linhas)])
    _resumo_caixa(c, MARGEM + 72 * mm, y, 56 * mm, 21 * mm, "Nº imóveis", ["Trat. focal", "Trat. perif.", "Inspec.", "Recup."], [sum(bool(i.get("foco")) for i in linhas), 0, len(linhas), 0])
    _resumo_caixa(c, MARGEM + 132 * mm, y, 30 * mm, 21 * mm, "Nº tubitos / amostras", ["Amostras"], [0])
    _resumo_caixa(c, MARGEM + 166 * mm, y, 35 * mm, 21 * mm, "Pendências", ["Fechados", "Recusas"], [sum(str(i.get("visita") or "").upper() == "FECHADO" for i in linhas), sum(str(i.get("visita") or "").upper() == "RECUSA" for i in linhas)])
    _resumo_caixa(c, MARGEM + 205 * mm, y, 57 * mm, 21 * mm, "Nº de depósitos inspecionados por tipo", ["A1", "A2", "B", "C", "D1", "D2", "E", "Total"], [totais["a1"], totais["a2"], totais["b"], totais["c"], totais["d1"], totais["d2"], totais["e"], sum(totais.values())])

    y -= 28 * mm
    _resumo_caixa(c, MARGEM, y, 88 * mm, 22 * mm, "Nº depósitos", ["Eliminado", "Tratados", "Lavados (T)", "Lavados (Q)", "Q. depos. trat."], [0, 0, 0, 0, 0])
    _resumo_caixa(c, MARGEM + 93 * mm, y, 30 * mm, 22 * mm, "Adulticida", ["Tipo", "Qtd. carga"], ["", ""])
    _resumo_caixa(c, MARGEM + 128 * mm, y, 30 * mm, 22 * mm, "Imóveis informados", ["Total"], [0])
    _resumo_caixa(c, MARGEM + 163 * mm, y, 99 * mm, 10 * mm, "Nº dos quarteirões trabalhados", [str(i) for i in range(1, 10)], ["" for _ in range(9)])
    _resumo_caixa(c, MARGEM + 163 * mm, y - 12 * mm, 99 * mm, 10 * mm, "Nº dos quarteirões concluídos", [str(i) for i in range(1, 10)], ["" for _ in range(9)])

    y -= 32 * mm
    _faixa(c, "RESUMO DO LABORATÓRIO", y)
    y -= 23 * mm
    _resumo_caixa(c, MARGEM, y, 130 * mm, 17 * mm, "Nº dos quarteirões com Aedes aegypti", [str(i) for i in range(1, 10)], ["" for _ in range(9)])
    _resumo_caixa(c, MARGEM + 141 * mm, y, 121 * mm, 17 * mm, "Nº e seq. dos quarteirões com Aedes albopictus", [str(i) for i in range(1, 9)], ["" for _ in range(8)])
    y -= 34 * mm
    _resumo_caixa(c, MARGEM, y, 112 * mm, 27 * mm, "Nº de depósitos com espécimes por tipo", ["A1", "A2", "B", "C", "D1", "D2", "E", "Total"], ["" for _ in range(8)])
    _resumo_caixa(c, MARGEM + 117 * mm, y, 84 * mm, 27 * mm, "Nº de imóveis com espécimes por tipo", ["A. aegypti", "A. albop.", "Outros", "Total"], ["" for _ in range(4)])
    _resumo_caixa(c, MARGEM + 206 * mm, y, 56 * mm, 27 * mm, "Nº de exemplares", ["Larvas", "Pupas", "Adultos"], ["" for _ in range(3)])

    y -= 17 * mm
    _campo(c, 0, y, 55, "Data de entrada", dados.get("data_entrada"), 8 * mm)
    _campo(c, 58, y, 55, "Data da conclusão", dados.get("data_conclusao"), 8 * mm)
    _campo(c, 116, y, 55, "Laboratório", dados.get("laboratorio"), 8 * mm)
    _campo(c, 174, y, 40, "Laboratorista", dados.get("laboratorista"), 8 * mm)
    _campo(c, 217, y, 45, "Assinatura", "", 8 * mm)
    c.setFont("Helvetica", 3.55)
    c.drawString(MARGEM, 10 * mm, "A1: armazenamento elevado | A2: ao nível do solo | B: móveis | C: fixos | D1/D2: pneus e materiais | E: naturais")
    c.drawString(MARGEM, 7 * mm, "Documento gerado pelo VigiaCampo a partir do registro diário do serviço antivetorial.")


def gerar_pdf_antivetorial(registro, dados):
    """Retorna o formulário oficial em duas páginas, pronto para download."""
    arquivo = BytesIO()
    pdf = canvas.Canvas(arquivo, pagesize=landscape(A4))
    pdf.setTitle(f"Registro Diário Antivetorial - {registro.id}")
    _pagina_pesquisa(pdf, registro, dados)
    pdf.showPage()
    _pagina_resumo(pdf, registro, dados)
    pdf.save()
    arquivo.seek(0)
    return arquivo
