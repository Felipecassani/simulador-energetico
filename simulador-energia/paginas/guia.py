"""Guia rápido: o essencial para perceber a fatura e escolher melhor, pelos mesmos 3 passos do simulador.

Os textos vêm de interface/conteudo.py (GUIA), lidos pelo título. Depois de cada passo há uma
ligação para a ferramenta onde se experimenta o que se acabou de ler.
"""
from html import escape

import streamlit as st

from interface import componentes as ui
from interface.conteudo import GUIA
from nucleo import roteiro

# (passo, o que se aprende nele, temas do GUIA por esta ordem, ferramentas onde se experimenta).
# Um teste (tests/test_app.py) garante que todos os temas do GUIA estão aqui, cada um uma só vez.
GRUPOS = [
    ("1 · Percebe a tua fatura",
     "Para onde vai o teu dinheiro: a energia que gastas e o valor fixo que pagas todos os dias.",
     ("Por onde começar", "O que pagas numa fatura", "Potência contratada", "Tarifa regulada"),
     (1,)),
    ("2 · Descobre onde poupar",
     "Gastar menos e aproveitar as horas mais baratas, sem precisares de mudar de empresa.",
     ("Poupar sem mudar de contrato", "Opções horárias"),
     (2, 5)),
    ("3 · Escolhe o tarifário certo",
     "Comparar preços e empresas antes de decidir, e mudar sem medo.",
     ("Preço fixo ou indexado", "Campanhas e descontos", "Mudar de comercializador"),
     (3, 4)),
]

textos = dict(GUIA)
agrupados = {t for _, _, temas, _ in GRUPOS for t in temas}
# Se um dia entrar um tema novo no GUIA sem passo, aparece no fim em vez de desaparecer
soltos = tuple(t for t, _ in GUIA if t not in agrupados)
grupos = GRUPOS + ([("Mais temas", "", soltos, ())] if soltos else [])

ui.cabecalho("Guia rápido",
             "O essencial para perceberes a tua fatura da luz e pagares menos. Está dividido em 3 passos: "
             "lê um passo e experimenta logo a seguir, na ferramenta indicada.",
             kicker="Ajuda")
ui.nota("As palavras sublinhadas explicam-se ao tocar nelas (no computador, basta passar o rato por cima).")
with st.container(horizontal=True, key="botoes_guia_glossario"):
    st.page_link("paginas/recursos.py", label="Ver todas as palavras no glossário", icon=":material/menu_book:")

numero = 0
for i, (titulo, resumo, temas, ferramentas) in enumerate(grupos, 1):
    cartoes = []
    for tema in temas:
        if tema not in textos:          # tema que mudou de nome no GUIA: não rebenta a página
            continue
        numero += 1
        cartoes.append(f'<div class="lc-card lc-aberto"><span class="lc-n">{numero:02d}</span>'
                       f'<h4>{escape(tema)}</h4><p>{ui.com_glossario(textos[tema])}</p></div>')
    if not cartoes:
        continue
    st.subheader(f":material/menu_book: {titulo}")
    if resumo:
        ui.nota(resumo)
    ui.grelha(cartoes, largura_min=320)
    if ferramentas:
        with st.container(horizontal=True, key=f"botoes_guia_{i}"):
            for n in ferramentas:
                passo = roteiro.passo(n)
                st.page_link(passo.pagina, label=f"Experimenta: «{passo.titulo}»", icon=passo.icone)
