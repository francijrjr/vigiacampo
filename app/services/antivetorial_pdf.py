"""PDF em duas páginas da ficha diária antivetorial."""
from io import BytesIO
from reportlab.lib import colors
from reportlab.lib.pagesizes import A4
from reportlab.lib.units import mm
from reportlab.pdfbase.pdfmetrics import stringWidth
from reportlab.pdfgen import canvas

LILAS=colors.HexColor("#d7d5f7")

def texto(c,v,x,y,w,s=5,b=False):
    f="Helvetica-Bold" if b else "Helvetica"; v=str(v or "")
    while v and stringWidth(v,f,s)>w-1*mm:v=v[:-1]
    c.setFont(f,s);c.drawCentredString(x+w/2,y,v)
def caixa(c,x,y,w,h,label="",v="",s=5):
    c.rect(x,y,w,h)
    if label:
        c.setFillColor(LILAS);c.rect(x,y+h-4*mm,w,4*mm,fill=1,stroke=1);c.setFillColor(colors.black);texto(c,label,x,y+h-2.8*mm,w,4.5,True)
    texto(c,v,x,y+1.4*mm,w,s)
def titulo(c,v,y):
    c.setFillColor(LILAS);c.rect(12*mm,y,186*mm,6*mm,fill=1,stroke=1);c.setFillColor(colors.black);texto(c,v,12*mm,y+1.8*mm,186*mm,6.5,True)
def gerar_pdf_antivetorial(registro,dados):
    out=BytesIO();c=canvas.Canvas(out,pagesize=A4);w,h=A4;c.setTitle(f"Registro Diário Antivetorial - {registro.id}")
    c.setFont("Helvetica-Bold",6)
    for i,v in enumerate(["PREFEITURA MUNICIPAL DE CHAVAL","SECRETARIA MUNICIPAL DE SAÚDE","PROGRAMA NACIONAL DE CONTROLE DO SERVIÇO ANTIVETORIAL"]):c.drawString(12*mm,h-(10+i*3)*mm,v)
    c.setFont("Helvetica-Bold",8);c.drawCentredString(w/2,h-19*mm,"REGISTRO DIÁRIO DO SERVIÇO ANTIVETORIAL")
    y=h-31*mm
    campos=[(12,55,"Município",registro.municipio),(67,52,"Código e nome da localidade",dados.get("codigo_localidade")),(119,33,"Categoria / localidade",dados.get("categoria_localidade")),(152,20,"Zona",dados.get("zona")),(172,26,"Conclusão",dados.get("conclusao"))]
    for x,larg,r,v in campos:caixa(c,x*mm,y,larg*mm,9*mm,r,v)
    y-=11*mm
    for x,larg,r,v in [(12,37,"Data da atividade",registro.data.strftime("%d/%m/%Y")),(49,32,"Ciclo / ano",registro.ciclo),(81,117,"Atividade",dados.get("atividade") or "Pesquisa entomológica / tratamento")]:caixa(c,x*mm,y,larg*mm,8*mm,r,v)
    y-=8*mm;titulo(c,"PESQUISA ENTOMOLÓGICA / TRATAMENTO",y);top=y-2*mm
    x=12*mm; pesos=[7,41,7,8,8,7,7,7,7,7,7,7,8,8,13,12];cols=[p*mm*(186/sum(pesos)) for p in pesos]
    labels=["Nº","Logradouro","Nº","Tipo","Visita","A1","A2","B","C","D1","D2","E","Total","Foco","Tratamento","Obs."]
    c.setFillColor(LILAS);c.rect(x,top-7*mm,186*mm,7*mm,fill=1,stroke=1);c.setFillColor(colors.black);xx=x
    for col,label in zip(cols,labels):c.rect(xx,top-7*mm,col,7*mm);texto(c,label,xx,top-4.7*mm,col,4.2,True);xx+=col
    # A ficha impressa reserva espaço para a anotação manuscrita de 20 imóveis.
    linhas={v.get("ordem"):v for v in dados.get("linhas",[])};altura=4.2*mm
    for ordem in range(1,21):
        yy=top-7*mm-ordem*altura;v=linhas.get(ordem,{});xx=x;total=sum(v.get(k,0) for k in ("a1","a2","b","c","d1","d2","e"))
        valores=[ordem,v.get("logradouro"),v.get("numero"),v.get("tipo_imovel"),v.get("visita"),v.get("a1"),v.get("a2"),v.get("b"),v.get("c"),v.get("d1"),v.get("d2"),v.get("e"),total,"X" if v.get("foco") else "",v.get("tratamento"),""]
        for col,valor in zip(cols,valores):c.rect(xx,yy,col,altura);texto(c,valor,xx,yy+.45*mm,col,4);xx+=col
    y=top-7*mm-20*altura-10*mm
    for x,larg,r,v in [(12,60,"Agente",dados.get("agente") or registro.agente.full_name),(77,60,"Supervisor",dados.get("supervisor")),(142,56,"Observações",dados.get("observacoes"))]:caixa(c,x*mm,y,larg*mm,8*mm,r,v,4.5)
    c.showPage();titulo(c,"RESUMO DIÁRIO DO TRABALHO DE CAMPO",h-18*mm);y=h-42*mm
    totais={k:sum(i.get(k,0) for i in dados.get("linhas",[])) for k in ("a1","a2","b","c","d1","d2","e")}
    caixas=[("Nº de imóveis trabalhados",len(dados.get("linhas",[]))),("Imóveis com foco",sum(i.get("foco",False) for i in dados.get("linhas",[]))),("Pendências",sum(i.get("visita") in ("FECHADO","RECUSA") for i in dados.get("linhas",[]))),("Nº de depósitos inspecionados",sum(totais.values()))]
    for n,(r,v) in enumerate(caixas):caixa(c,(12+(n%2)*94)*mm,(y-(n//2)*22*mm),88*mm,17*mm,r,v,11)
    y-=52*mm;titulo(c,"RESUMO DO LABORATÓRIO",y);y-=22*mm
    caixa(c,12*mm,y,92*mm,16*mm,"Depósitos inspecionados por tipo","  ".join(f"{k.upper()}: {v}" for k,v in totais.items()),6);caixa(c,106*mm,y,92*mm,16*mm,"Dados do laboratório",dados.get("laboratorio"),7)
    y-=29*mm
    for x,larg,r,v in [(12,58,"Data de entrada",dados.get("data_entrada")),(70,58,"Data da conclusão",dados.get("data_conclusao")),(128,70,"Laboratorista",dados.get("laboratorista"))]:caixa(c,x*mm,y,larg*mm,12*mm,r,v)
    c.setFont("Helvetica",4.8);c.drawString(12*mm,16*mm,"A1/A2 - armazenamento de água | B - recipientes | C - depósitos fixos | D1/D2 - pneus e materiais | E - naturais")
    c.drawString(12*mm,13*mm,"Documento gerado pelo VigiaCampo.");c.save();out.seek(0);return out
