"""Sobre: o projeto, o autor e de onde vêm os dados."""
import base64
from html import escape
from pathlib import Path

import streamlit as st

from interface import componentes as ui
from interface.conteudo import AUTOR

def _imagem(svg):
    """O st.html retira os <svg>; como imagem (data URI) passam."""
    return "data:image/svg+xml;base64," + base64.b64encode(svg.encode()).decode()


ICONE = _imagem((Path(__file__).resolve().parents[1] / "assets" / "logo_icone.svg").read_text(encoding="utf-8"))
SIMBOLOS = {
    "codigo": '<svg xmlns="http://www.w3.org/2000/svg" viewBox="0 0 24 24" fill="none" stroke="#D9B45B" stroke-width="2" '
              'stroke-linecap="round" stroke-linejoin="round"><path d="M8 7l-5 5 5 5M16 7l5 5-5 5"/></svg>',
    "linkedin": '<svg xmlns="http://www.w3.org/2000/svg" viewBox="0 0 24 24" fill="none" stroke="#D9B45B" '
                'stroke-width="2" stroke-linecap="round"><rect x="3" y="3" width="18" height="18" rx="4"/>'
                '<path d="M8 10.5V16M12 16v-3.2a2.2 2.2 0 0 1 4.4 0V16M12 10.5V16"/>'
                '<circle cx="8" cy="7.6" r="1" fill="#D9B45B" stroke="none"/></svg>',
}

ui.cabecalho("Sobre o projeto",
             "Ferramentas gratuitas e simples para perceberes a tua fatura de eletricidade e pagares menos.",
             kicker="Sobre")

def _icone(simbolo):
    """Sem símbolo conhecido, a ligação aparece só com o nome (não rebenta a página)."""
    return f'<img src="{_imagem(SIMBOLOS[simbolo])}" alt="">' if simbolo in SIMBOLOS else ""


ligacoes = "".join(
    f'<a href="{escape(url)}" target="_blank" rel="noopener">{_icone(simbolo)}<span>{escape(nome)}</span></a>'
    for nome, url, simbolo in AUTOR["ligacoes"])
st.html(f"""
<div class="lc-card lc-autor">
  <div class="lc-autor-logo"><img src="{ICONE}" alt="Logótipo LC"></div>
  <div>
    <span class="lc-n">AUTOR</span>
    <h4>{escape(AUTOR["nome"])}</h4>
    <p>{escape(AUTOR["linha"])}</p>
    <div class="lc-social">{ligacoes}</div>
  </div>
</div>""")

ui.grelha([
    '<div class="lc-card"><span class="lc-n">MISSÃO</span><h4>Simples, gratuito e independente</h4>'
    '<p>Carregas a fatura ou escreves meia dúzia de valores e vês logo quanto podes poupar. '
    'Sem contas, sem publicidade e sem vender nada.</p></div>',
    '<div class="lc-card"><span class="lc-n">DADOS</span><h4>Fontes públicas e oficiais</h4>'
    '<p>Tarifas da <a href="https://www.erse.pt" target="_blank" rel="noopener">ERSE</a> e preços do '
    'mercado ibérico do <a href="https://www.omie.es" target="_blank" rel="noopener">OMIE</a>, '
    'atualizados todos os dias.</p></div>',
    '<div class="lc-card"><span class="lc-n">PRIVACIDADE</span><h4>Nada é guardado</h4>'
    '<p>A fatura é lida só para preencher os campos. Os valores desaparecem quando fechas a página.</p></div>',
    '<div class="lc-card"><span class="lc-n">AVISO</span><h4>Resultados indicativos</h4>'
    '<p>Valores sem IVA nem taxas. Antes de mudar de contrato, confirma sempre as condições na ficha '
    'da oferta.</p></div>',
], largura_min=260)
