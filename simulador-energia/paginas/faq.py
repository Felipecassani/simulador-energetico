"""Perguntas frequentes (em acordeão)."""
import streamlit as st

from interface import componentes as ui
from interface.conteudo import FAQ

ui.cabecalho("Perguntas frequentes", "Respostas curtas às dúvidas mais comuns.", kicker="Ajuda")
for pergunta, resposta in FAQ:
    with st.expander(pergunta):
        st.html(f'<div class="lc-faq-resposta">{ui.com_glossario(resposta)}</div>')
st.write("")
st.page_link("paginas/guia.py", label="Ler o guia completo", icon=":material/school:")
