"""Guia: o essencial para perceber a fatura e escolher melhor."""
from html import escape

import streamlit as st

from interface import componentes as ui
from interface.conteudo import GUIA

ui.cabecalho("Guia", "O essencial para perceberes a tua fatura de eletricidade e escolheres melhor.",
             kicker="Aprender")
ui.grelha([f'<div class="lc-card lc-aberto"><span class="lc-n">{i:02d}</span><h4>{escape(titulo)}</h4>'
           f'<p>{ui.com_glossario(texto)}</p></div>' for i, (titulo, texto) in enumerate(GUIA, 1)],
          largura_min=320)
st.caption("Os termos sublinhados explicam-se ao passar o rato (ou ao tocar). O glossário completo "
           "está em Recursos.")
