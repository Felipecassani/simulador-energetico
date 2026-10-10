"""Simulador Energético: é aqui que o site arranca.

Para correr:  python -m streamlit run app.py

Como está organizado:
  nucleo/     as contas (Python simples, sem Streamlit, para se poderem testar)
  interface/  cores, estilo e as peças visuais repetidas
  paginas/    uma página por ferramenta, mais o Início e a Ajuda
  tests/      testes com pytest

Este ficheiro monta o menu, aplica o tema e mostra a página escolhida.
"""
import sys
from pathlib import Path

import streamlit as st

# Depois de uma atualização (git pull no Streamlit Cloud), o Streamlit volta a correr as páginas
# mas pode manter em memória versões antigas de interface/ e nucleo/: código novo com módulos
# velhos dava KeyError/ImportError a quem estivesse a abrir o site. Se algum ficheiro mudou desde a
# última execução, estes módulos voltam a ser carregados. (Fica no sys porque sobrevive às execuções.)
_PASTA = Path(__file__).resolve().parent
_assinatura = tuple(sorted((f"{pasta}/{p.name}", p.stat().st_mtime_ns) for pasta in ("interface", "nucleo")
                           for p in (_PASTA / pasta).glob("*.py") if not p.name.startswith("._")))
if getattr(sys, "_simulador_assinatura", _assinatura) != _assinatura:
    for _nome in [m for m in sys.modules if m.split(".")[0] in ("interface", "nucleo")]:
        del sys.modules[_nome]
sys._simulador_assinatura = _assinatura

from interface.acesso import exigir_senha  # noqa: E402  (depois da verificação acima)
from interface import animacoes
from interface.componentes import proximo_passo, rodape
from interface.conteudo import EM_CONSTRUCAO, ORDEM_FERRAMENTAS
from interface.estilo import MARCA, aplicar_estilo
from interface.tema import seletor_tema
from nucleo.roteiro import passo

ASSETS = Path(__file__).resolve().parent / "assets"

st.set_page_config(page_title=MARCA, page_icon=str(ASSETS / "icone.png"), layout="wide")
# no topo aparece o logótipo completo, com o nome «Simulador Energético»
st.logo(str(ASSETS / "logo.svg"), icon_image=str(ASSETS / "logo.svg"), size="large")
aplicar_estilo()
exigir_senha()          # só para quem vem pelo link público (em localhost não pede)

inicio = st.Page("paginas/inicio.py", title="Início", icon=":material/bolt:", default=True)
# Menu com três entradas: Início, Ferramentas (pela ordem do percurso) e Ajuda. As secções em
# construção continuam a ter endereço (a Início liga para elas), mas saem do menu: competiam
# com as ferramentas que já funcionam.
paginas = {
    "": [inicio],
    "Ferramentas": [st.Page(passo(n).pagina, title=passo(n).titulo, icon=passo(n).icone)
                    for n in ORDEM_FERRAMENTAS],
    "Em construção": [st.Page(f"paginas/breve/{e.chave}.py", title=e.titulo, icon=e.icone,
                              url_path=e.chave, visibility="hidden") for e in EM_CONSTRUCAO],
    "Ajuda": [st.Page("paginas/guia.py", title="Guia rápido", icon=":material/school:"),
              st.Page("paginas/faq.py", title="Perguntas frequentes", icon=":material/help:",
                      url_path="faq"),
              st.Page("paginas/recursos.py", title="Glossário e ligações", icon=":material/menu_book:"),
              st.Page("paginas/sobre.py", title="Sobre o projeto", icon=":material/person:")],
}

pagina = st.navigation(paginas, position="top")
seletor_tema([f"/{p.url_path}" for grupo in paginas.values() for p in grupo])
pagina.run()
proximo_passo(pagina.url_path)
rodape()
animacoes.ativar()          # números que contam e cartões que entram ao descer a página
