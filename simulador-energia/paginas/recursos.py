"""Glossário e ligações: o que quer dizer cada palavra, as datas que mexem no preço e os sites oficiais.

O glossário é o primeiro separador: é para lá que levam as ligações "O que quer dizer cada palavra"
do Início, do rodapé e das ferramentas.
"""
import unicodedata
from datetime import date
from html import escape

import streamlit as st

from interface import componentes as ui
from interface.conteudo import GLOSSARIO, LIGACOES
from nucleo import calendario, roteiro

MESES = ["jan", "fev", "mar", "abr", "mai", "jun", "jul", "ago", "set", "out", "nov", "dez"]
FATURA, OFERTAS = roteiro.passo(1), roteiro.passo(3)


def _simples(texto):
    """Minúsculas e sem acentos, para «potencia» encontrar «potência»."""
    return "".join(c for c in unicodedata.normalize("NFD", texto.lower()) if unicodedata.category(c) != "Mn")


ui.cabecalho("Glossário e ligações",
             "O que quer dizer cada palavra da fatura da luz, as datas em que o preço pode mudar e os "
             "sites oficiais onde podes confirmar tudo.",
             kicker="Ajuda")
glossario, cal, ligacoes = st.tabs(["O que quer dizer cada palavra", "Datas que mexem no preço",
                                    "Sites oficiais"])

with glossario:
    st.caption("Viste uma palavra estranha na fatura? Escreve-a aqui, ou escolhe um tema para veres só "
               "as palavras desse tema.")
    procura = st.text_input("Procurar uma palavra", key="r_procura", placeholder="ex.: vazio, kVA, IVA")
    procurado = _simples((procura or "").strip())
    categorias = sorted({c for c, _ in GLOSSARIO.values()})
    escolha = st.pills("Mostrar só as palavras sobre", categorias, selection_mode="multi", key="r_categorias")
    blocos = []
    for termo, (categoria, definicao) in sorted(GLOSSARIO.items(), key=lambda x: x[0].lower()):
        if procurado and procurado not in _simples(termo + " " + definicao):
            continue
        if escolha and categoria not in escolha:
            continue
        blocos.append(f'<div class="lc-card"><span class="lc-n">{escape(categoria)}</span>'
                      f'<h4>{escape(termo)}</h4><p>{escape(definicao)}</p></div>')
    if blocos:
        if procurado or escolha:
            st.caption(f"Encontrei {len(blocos)} de {len(GLOSSARIO)} palavras.")
        ui.grelha(blocos, largura_min=260)
    else:
        st.info("Não encontrei essa palavra. Experimenta escrever só uma parte dela, ou apaga o que "
                "escreveste e tira os temas escolhidos para veres todas.", icon=":material/search_off:")
    st.write("")
    st.caption("Já percebes as palavras? Vê-as na tua própria fatura: carregas o PDF ou uma foto e o "
               "simulador mostra-te para onde vai o dinheiro.")
    with st.container(horizontal=True, key="botoes_glossario"):
        st.page_link(FATURA.pagina, label=f"Abrir «{FATURA.titulo}»", icon=FATURA.icone)

with cal:
    st.caption("Dias em que o preço da luz ou os horários podem mudar: tarifas novas, mudança da hora e "
               "decisões do regulador. São bons momentos para voltares a comparar ofertas. As datas com "
               "«previsão» ainda dependem da ERSE, o regulador, e podem mudar.")
    categorias_cal = st.pills("Mostrar só as datas sobre", list(calendario.CATEGORIAS), selection_mode="multi",
                              format_func=lambda c: {"Hora": "Mudança da hora"}.get(c, c), key="r_cal_cat")
    blocos = []
    for e in calendario.eventos(date.today()):
        if categorias_cal and e.categoria not in categorias_cal:
            continue
        aviso = " · previsão" if e.previsao else ""
        blocos.append(f"""
        <div class="lc-card lc-evento">
          <div class="lc-evento-data"><div class="lc-evento-dia">{e.dia.day}</div>
            <div class="lc-evento-mes">{MESES[e.dia.month - 1]} {e.dia.year}</div></div>
          <div><span class="lc-n">{escape(e.categoria)}{aviso}</span>
            <h4>{escape(e.titulo)}</h4><p>{escape(e.texto)}</p></div>
        </div>""")
    ui.grelha(blocos or ['<div class="lc-card"><p>Não há datas deste tipo nos próximos meses.</p></div>'],
              largura_min=340)
    with st.container(horizontal=True, key="botoes_calendario"):
        st.page_link(OFERTAS.pagina, label=f"Abrir «{OFERTAS.titulo}»", icon=OFERTAS.icone)

with ligacoes:
    st.caption("Sites gratuitos das entidades oficiais. Abrem noutra janela: o simulador continua aberto "
               "aqui, com os teus números.")
    ui.grelha([f'<div class="lc-card"><h4><a href="{escape(url)}" target="_blank" rel="noopener">'
               f'{escape(nome)} <span aria-hidden="true">↗</span></a></h4><p>{escape(texto)}</p></div>'
               for nome, url, texto in LIGACOES],
              largura_min=260)
