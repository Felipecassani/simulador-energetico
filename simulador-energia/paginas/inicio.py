"""Início: o que o simulador faz e por onde começar."""
import streamlit as st

from interface import componentes as ui
from interface.conteudo import EM_CONSTRUCAO
from interface.dados import omie_hoje_e_amanha
from nucleo import mercado
from interface.estilo import MARCA
from nucleo import roteiro

ui.cabecalho(
    MARCA,
    "Descobre quanto vais pagar de eletricidade, quanto poupas com uma medida de "
    "eficiência e que tarifário te sai mais barato. Só precisas dos dados da tua fatura.",
    kicker="Simulador de eletricidade",
)

st.write("")
st.subheader("Agora")
try:
    hoje, amanha = omie_hoje_e_amanha()
except mercado.SemRede:
    pass
else:
    ui.painel_mercado(hoje, amanha)
ui.periodo_atual()

st.write("")
st.subheader("Ferramentas")
# Uma linha de 3 colunas por cada 3 ferramentas: no telemóvel mantém a ordem
for inicio in range(0, len(roteiro.PASSOS), 3):
    for coluna, passo in zip(st.columns(3), roteiro.PASSOS[inicio:inicio + 3]):
        with coluna:
            ui.cartao_ferramenta(passo, roteiro.disponivel(passo.numero))

st.write("")
st.subheader("Em construção")
st.caption("Mais ferramentas a caminho.")
for inicio in range(0, len(EM_CONSTRUCAO), 4):
    for coluna, secao in zip(st.columns(4), EM_CONSTRUCAO[inicio:inicio + 4]):
        with coluna:
            ui.cartao_em_construcao(secao)

st.write("")
st.subheader("Como funciona")
ui.grelha([
    '<div class="lc-card"><span class="lc-n">01</span><h4>Pega na tua fatura</h4>'
    '<p>Precisas do consumo em kWh, do preço da energia, do preço diário da potência e dos dias do período.</p></div>',
    '<div class="lc-card"><span class="lc-n">02</span><h4>Introduz os valores</h4>'
    '<p>Escolhe uma ferramenta e preenche os campos. O (?) de cada campo explica o valor pedido.</p></div>',
    '<div class="lc-card"><span class="lc-n">03</span><h4>Vê e compara</h4>'
    '<p>Os resultados aparecem na hora. Muda os valores para experimentar outros cenários.</p></div>',
])
