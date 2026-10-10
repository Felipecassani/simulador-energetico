"""Perguntas frequentes, agrupadas por assunto, em acordeão.

Os textos vêm de interface/conteudo.py (FAQ), lidos pela pergunta. Quando a resposta fala de uma
ferramenta («A minha fatura», «Bi-horário compensa?»...), aparece logo por baixo um botão para a abrir.
"""
import streamlit as st

from interface import componentes as ui
from interface.conteudo import FAQ
from nucleo import roteiro

# (assunto, perguntas do FAQ por esta ordem). Um teste garante que nenhuma pergunta fica de fora.
GRUPOS = [
    ("Para começar",
     ("Por onde começo?",
      "Preciso de criar conta ou de pagar?",
      "O que acontece aos dados que escrevo ou à fatura que carrego?",
      "A leitura da fatura falhou ou leu um valor errado. E agora?")),
    ("Perceber a fatura e os preços",
     ("Qual é a diferença entre kWh e kVA?",
      "Porque é que o total não é igual ao da minha fatura?",
      "Como sei se a minha fatura é de preço fixo ou indexado?",
      "De onde vêm os preços?")),
    ("Escolher o tarifário e mudar",
     ("A tarifa regulada é de preço fixo ou indexado?",
      "Quando é que o bi-horário compensa?",
      "Mudar de comercializador corta a luz?",
      "As recomendações são uma garantia de poupança?")),
]
# Ferramentas a abrir em respostas que não as citam pelo nome (as citadas «assim» entram sozinhas)
FERRAMENTAS_EXTRA = {
    "Qual é a diferença entre kWh e kVA?": (1,),
    "De onde vêm os preços?": (4,),
    "Mudar de comercializador corta a luz?": (3,),
}

respostas = dict(FAQ)
agrupadas = {q for _, perguntas in GRUPOS for q in perguntas}
# Uma pergunta nova no FAQ sem assunto aparece no fim em vez de desaparecer
soltas = tuple(q for q, _ in FAQ if q not in agrupadas)
grupos = GRUPOS + ([("Outras perguntas", soltas)] if soltas else [])

ui.cabecalho("Perguntas frequentes", "Respostas curtas às dúvidas mais comuns.", kicker="Ajuda",
             chips=(f"{len(FAQ)} perguntas", "respostas curtas"), imagem=ui.imagem_svg("ilustracao.svg"))
ui.nota("As palavras sublinhadas explicam-se ao tocar nelas (no computador, basta passar o rato por cima).",
        "Palavras sublinhadas")

indice = 0
for assunto, perguntas in grupos:
    perguntas = [q for q in perguntas if q in respostas]   # pergunta que mudou de texto: não rebenta
    if not perguntas:
        continue
    st.subheader(f":material/help: {assunto}")
    for pergunta in perguntas:
        indice += 1
        resposta = respostas[pergunta]
        with st.expander(pergunta, icon=":material/help:"):
            st.html(f'<div class="lc-faq-resposta">{ui.com_glossario(resposta)}</div>')
            ferramentas = [p for p in roteiro.PASSOS
                           if f"«{p.titulo}»" in resposta or p.numero in FERRAMENTAS_EXTRA.get(pergunta, ())]
            if ferramentas:
                with st.container(horizontal=True, key=f"botoes_faq_{indice}"):
                    for p in ferramentas:
                        st.page_link(p.pagina, label=f"Abrir «{p.titulo}»", icon=p.icone)

st.write("")
ui.nota("Não encontras a tua dúvida? Experimenta com a tua própria fatura: muitas respostas ficam "
           "mais claras com os teus números.")
with st.container(horizontal=True, key="botoes_faq_mais"):
    fatura = roteiro.passo(1)
    st.page_link(fatura.pagina, label=f"Abrir «{fatura.titulo}»", icon=fatura.icone)
