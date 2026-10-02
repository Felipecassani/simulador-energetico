"""Recursos: glossário, calendário energético e ligações oficiais."""
from datetime import date
from html import escape

import streamlit as st

from interface import componentes as ui
from interface.conteudo import GLOSSARIO, LIGACOES
from nucleo import calendario

MESES = ["jan", "fev", "mar", "abr", "mai", "jun", "jul", "ago", "set", "out", "nov", "dez"]

ui.cabecalho("Recursos", "Glossário dos termos da fatura, as datas que mexem no preço e as ligações oficiais.",
             kicker="Ajuda")
glossario, cal, ligacoes = st.tabs(["Glossário", "Calendário", "Ligações oficiais"])

with glossario:
    procura = st.text_input("Procurar um termo", key="r_procura", placeholder="ex.: vazio, OMIE, kVA")
    categorias = sorted({c for c, _ in GLOSSARIO.values()})
    escolha = st.pills("Categoria", categorias, selection_mode="multi", key="r_categorias",
                       label_visibility="collapsed")
    blocos = []
    for termo, (categoria, definicao) in sorted(GLOSSARIO.items(), key=lambda x: x[0].lower()):
        if procura and procura.lower() not in (termo + " " + definicao).lower():
            continue
        if escolha and categoria not in escolha:
            continue
        blocos.append(f'<div class="lc-card"><span class="lc-n">{escape(categoria.upper())}</span>'
                      f'<h4>{escape(termo)}</h4><p>{escape(definicao)}</p></div>')
    if blocos:
        ui.grelha(blocos, largura_min=260)
    else:
        st.info("Nenhum termo encontrado.")

with cal:
    categorias_cal = st.pills("Mostrar", list(calendario.CATEGORIAS), selection_mode="multi",
                              key="r_cal_cat", label_visibility="collapsed")
    blocos = []
    for e in calendario.eventos(date.today()):
        if categorias_cal and e.categoria not in categorias_cal:
            continue
        aviso = " · previsão" if e.previsao else ""
        blocos.append(f"""
        <div class="lc-card lc-evento">
          <div class="lc-evento-data"><div class="lc-evento-dia">{e.dia.day}</div>
            <div class="lc-evento-mes">{MESES[e.dia.month - 1]} {e.dia.year}</div></div>
          <div><span class="lc-n">{escape(e.categoria.upper())}{aviso}</span>
            <h4>{escape(e.titulo)}</h4><p>{escape(e.texto)}</p></div>
        </div>""")
    ui.grelha(blocos or ['<div class="lc-card"><p>Sem datas nesta categoria.</p></div>'], largura_min=340)
    st.caption("As datas marcadas como previsão dependem de decisões da ERSE e podem mudar.")

with ligacoes:
    ui.grelha([f'<div class="lc-card"><h4><a href="{escape(url)}" target="_blank" rel="noopener">'
               f'{escape(nome)} ↗</a></h4><p>{escape(texto)}</p></div>' for nome, url, texto in LIGACOES],
              largura_min=260)
