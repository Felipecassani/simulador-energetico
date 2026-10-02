"""Simulador Energético — ponto de entrada.

Executar (a partir desta pasta):  python -m streamlit run app.py
No PyCharm: botão ▶ "Simulador (Streamlit)".

Organização:
  nucleo/     cálculos puros (sem Streamlit) + roteiro com a validação de cada ferramenta
  interface/  paleta, CSS e componentes visuais
  paginas/    uma página por ferramenta, mais a Início
  tests/      pytest — o que ainda não foi feito aparece como "skipped"
  docs/       guia PDF só para o programador (fórmulas, boas práticas, ambiente)

O site é para qualquer pessoa: nada técnico aparece nas páginas.
"""
from pathlib import Path

import streamlit as st

from interface.acesso import exigir_senha
from interface.componentes import rodape
from interface.conteudo import EM_CONSTRUCAO
from interface.estilo import MARCA, aplicar_estilo
from interface.tema import seletor_tema
from nucleo.roteiro import PASSOS

ASSETS = Path(__file__).resolve().parent / "assets"

st.set_page_config(page_title=MARCA, page_icon=str(ASSETS / "icone.png"), layout="wide")
st.logo(str(ASSETS / "logo.svg"), icon_image=str(ASSETS / "logo_icone.svg"), size="large")
aplicar_estilo()
exigir_senha()          # só para quem vem pelo link público (em localhost não pede)

inicio = st.Page("paginas/inicio.py", title="Início", icon=":material/bolt:", default=True)
paginas = {
    "": [inicio],
    "Eletricidade": [st.Page(p.pagina, title=p.titulo, icon=p.icone) for p in PASSOS],
    "Em construção": [st.Page(f"paginas/breve/{e.chave}.py", title=e.titulo, icon=e.icone,
                              url_path=e.chave) for e in EM_CONSTRUCAO],
    "Ajuda": [st.Page("paginas/guia.py", title="Guia", icon=":material/school:"),
              st.Page("paginas/faq.py", title="Perguntas frequentes", icon=":material/help:",
                      url_path="faq"),
              st.Page("paginas/recursos.py", title="Recursos", icon=":material/menu_book:"),
              st.Page("paginas/sobre.py", title="Sobre", icon=":material/person:")],
}

pagina = st.navigation(paginas, position="top")
seletor_tema([f"/{p.url_path}" for grupo in paginas.values() for p in grupo])
pagina.run()
rodape()
