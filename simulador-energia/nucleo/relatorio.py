"""Resumo da simulação em PDF (para a pessoa guardar), gerado em memória.

Só números e textos do simulador: sem nome, morada, NIF nem o ficheiro da fatura.
Fonte Helvetica (base do PDF): tem acentos e o símbolo do euro, não tem emojis.
"""
import io
from datetime import date

from reportlab.lib import colors
from reportlab.lib.enums import TA_LEFT
from reportlab.lib.pagesizes import A4
from reportlab.lib.styles import ParagraphStyle
from reportlab.lib.units import mm
from reportlab.platypus import Paragraph, SimpleDocTemplate, Spacer, Table, TableStyle

CARMIM, DOURADO, CINZA = colors.HexColor("#A8192E"), colors.HexColor("#A8842E"), colors.HexColor("#6E5A55")


def _euros(v):
    return f"{v:,.2f}".replace(",", " ").replace(".", ",") + " €"


def _estilos():
    base = dict(fontName="Helvetica", fontSize=10, leading=14, alignment=TA_LEFT)
    return {
        "titulo": ParagraphStyle("t", **{**base, "fontName": "Helvetica-Bold", "fontSize": 20,
                                         "leading": 24, "textColor": CARMIM}),
        "sub": ParagraphStyle("s", **{**base, "textColor": CINZA}),
        "h2": ParagraphStyle("h", **{**base, "fontName": "Helvetica-Bold", "fontSize": 13,
                                     "leading": 18, "textColor": CARMIM, "spaceBefore": 10}),
        "h3": ParagraphStyle("h3", **{**base, "fontName": "Helvetica-Bold"}),
        "corpo": ParagraphStyle("c", **base),
        "pequeno": ParagraphStyle("p", **{**base, "fontSize": 8, "leading": 11, "textColor": CINZA}),
    }


def _tabela(linhas, larguras):
    t = Table(linhas, colWidths=larguras)
    t.setStyle(TableStyle([
        ("FONTNAME", (0, 0), (-1, 0), "Helvetica-Bold"), ("FONTNAME", (0, 1), (-1, -1), "Helvetica"),
        ("FONTSIZE", (0, 0), (-1, -1), 9), ("TEXTCOLOR", (0, 0), (-1, 0), colors.white),
        ("BACKGROUND", (0, 0), (-1, 0), CARMIM),
        ("ROWBACKGROUNDS", (0, 1), (-1, -1), [colors.white, colors.HexColor("#F7EFEA")]),
        ("VALIGN", (0, 0), (-1, -1), "TOP"), ("TOPPADDING", (0, 0), (-1, -1), 4),
        ("BOTTOMPADDING", (0, 0), (-1, -1), 4)]))
    return t


def gerar(tarifario, resultado, regulada, recomendacoes, top, data_ofertas=None):
    """PDF (bytes).

    tarifario: {empresa, tipo, opcao, kva, consumo_kwh, dias, preco_energia, preco_diario}
    resultado: {energia, potencia, total[, total_com_iva]} no período
    regulada:  {opcao, total} no período
    recomendacoes: [Recomendacao]; top: [(nome_empresa, nome_oferta, opcao, €/mês)]
    """
    e = _estilos()
    largura = A4[0] - 40 * mm
    h = [Paragraph("Simulador Energético", e["titulo"]),
         Paragraph(f"Resumo da simulação · {date.today():%d/%m/%Y} · valores sem IVA nem taxas, "
                   "salvo indicação", e["sub"]), Spacer(1, 8)]

    t = tarifario
    h.append(Paragraph("O meu tarifário", e["h2"]))
    h.append(_tabela([["Empresa", "Tipo", "Opção", "Potência", "Consumo"],
                      [t["empresa"], t["tipo"], t["opcao"], f"{t['kva']:g} kVA".replace(".", ","),
                       f"{t['consumo_kwh']:g} kWh em {t['dias']} dias".replace(".", ",")]],
                     [largura * x for x in (0.24, 0.2, 0.16, 0.14, 0.26)]))
    h.append(Spacer(1, 4))
    h.append(Paragraph(f"Energia {t['preco_energia']:.4f} €/kWh · potência {t['preco_diario']:.4f} €/dia"
                       .replace(".", ","), e["corpo"]))

    r = resultado
    h.append(Paragraph("Resultado deste período", e["h2"]))
    linhas = [["Energia", "Potência", "Total sem IVA"] + (["Total com IVA"] if "total_com_iva" in r else []),
              [_euros(r["energia"]), _euros(r["potencia"]), _euros(r["total"])]
              + ([_euros(r["total_com_iva"])] if "total_com_iva" in r else [])]
    h.append(_tabela(linhas, [largura / len(linhas[0])] * len(linhas[0])))
    dif = r["total"] - regulada["total"]
    h.append(Spacer(1, 4))
    h.append(Paragraph(f"Na tarifa regulada da ERSE ({regulada['opcao']}) seriam {_euros(regulada['total'])}"
                       + (f": pagarias menos {_euros(dif)}." if dif > 0.005 else
                          f": o teu preço está {_euros(-dif)} abaixo." if dif < -0.005 else "."),
                       e["corpo"]))

    if top:
        h.append(Paragraph("As ofertas mais baratas para ti", e["h2"]))
        h.append(_tabela([["", "Empresa", "Oferta", "Opção", "€/mês"]]
                         + [[f"{i}.º", a, b, c, _euros(v)] for i, (a, b, c, v) in enumerate(top, 1)],
                         [largura * x for x in (0.07, 0.22, 0.43, 0.12, 0.16)]))
        if data_ofertas:
            h.append(Paragraph(f"Ofertas de preço fixo publicadas pela ERSE (dados de {data_ofertas:%d/%m/%Y}). "
                               "Confirma sempre as condições na ficha da oferta.", e["pequeno"]))

    if recomendacoes:
        h.append(Paragraph("Recomendações", e["h2"]))
        for rec in recomendacoes:
            valor = f" — poupa cerca de {_euros(rec.poupanca_mensal)} por mês" if rec.poupanca_mensal else ""
            h.append(Paragraph(f"{rec.titulo}{valor}", e["h3"]))
            h.append(Paragraph(rec.texto, e["corpo"]))
            h.append(Spacer(1, 4))

    h.append(Spacer(1, 10))
    h.append(Paragraph("Resultados indicativos, calculados com a tua fatura e com dados públicos da ERSE "
                       "e do OMIE. Feito por Luiz Cassani.", e["pequeno"]))
    saida = io.BytesIO()
    SimpleDocTemplate(saida, pagesize=A4, leftMargin=20 * mm, rightMargin=20 * mm, topMargin=18 * mm,
                      bottomMargin=18 * mm, title="Simulador Energético — resumo",
                      author="Simulador Energético").build(h)
    return saida.getvalue()
