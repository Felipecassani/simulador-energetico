"""Início: o que o simulador faz e por onde começar.

Ordem pensada para quem chega pela primeira vez (e no telemóvel): o botão para começar e as
ferramentas logo a seguir ao cabeçalho; o preço do mercado, que não é o preço que a pessoa
paga, vem depois e explicado.
"""
import streamlit as st

from interface import componentes as ui
from interface.conteudo import EM_CONSTRUCAO, ORDEM_FERRAMENTAS
from interface.dados import omie_hoje_e_amanha
from interface.estilo import MARCA
from nucleo import mercado, roteiro

ui.cabecalho(
    MARCA,
    "Percebe a tua conta da luz e descobre como pagar menos. Começa pela tua última fatura: "
    "carregas o PDF ou uma foto, ou escreves os números, e vês quanto pagas e que ofertas te saem "
    "mais baratas.",
    kicker="Grátis · sem registo · nada fica guardado",
)

with st.container(key="cta_inicio"):
    st.page_link("paginas/fatura.py", label="Começar pela minha fatura", icon=":material/arrow_forward:")
st.caption("Não tens a fatura à mão? Entra na mesma: há números de exemplo que podes trocar pelos teus.")

st.subheader("Ferramentas")
st.caption("Escolhe o que queres fazer. Os números que escreves numa ferramenta passam sozinhos para as outras.")
ferramentas = [roteiro.passo(n) for n in ORDEM_FERRAMENTAS]
# Uma linha de 3 colunas por cada 3 ferramentas: no telemóvel mantém a ordem
for inicio in range(0, len(ferramentas), 3):
    for coluna, passo in zip(st.columns(3), ferramentas[inicio:inicio + 3]):
        with coluna:
            ui.cartao_ferramenta(passo, roteiro.disponivel(passo.numero))

st.subheader("Aprender o básico")
st.caption("Nunca olhaste com atenção para uma fatura da luz? Começa por aqui.")
with st.container(horizontal=True, key="aprender"):
    st.page_link("paginas/guia.py", label="Guia rápido: o essencial em poucos minutos", icon=":material/school:")
    st.page_link("paginas/faq.py", label="Perguntas frequentes", icon=":material/help:")
    st.page_link("paginas/recursos.py", label="O que quer dizer cada palavra", icon=":material/menu_book:")

st.subheader("O preço da eletricidade agora")
try:
    hoje, amanha = omie_hoje_e_amanha()
except mercado.SemRede:
    pass
else:
    ui.painel_mercado(hoje, amanha)
    st.caption("É o preço a que as empresas compram a eletricidade no mercado ibérico (OMIE), antes das "
               "redes, da margem e dos impostos. Não é o que pagas, mas mostra se hoje a eletricidade "
               "está cara ou barata. Só mexe logo na tua conta se o teu contrato for indexado.")
ui.periodo_atual()
st.caption("Se tens bi-horário ou tri-horário (vem escrito na fatura), isto diz-te em que período "
           "estás agora. No simples, pagas o mesmo a qualquer hora.")
st.page_link("paginas/graficos.py", label="Ver o preço hora a hora", icon=":material/bar_chart:")

st.subheader("Como funciona")
ui.grelha([
    '<div class="lc-card"><span class="lc-n">01</span><h4>Pega na tua fatura</h4>'
    '<p>Basta a última fatura da luz, em papel, PDF ou foto. Se a carregares, o simulador lê os '
    'números sozinho.</p></div>',
    '<div class="lc-card"><span class="lc-n">02</span><h4>Confirma os números</h4>'
    '<p>Compara com a fatura e corrige o que for preciso. Cada campo tem um ponto de interrogação '
    'que diz onde encontrar o valor.</p></div>',
    '<div class="lc-card"><span class="lc-n">03</span><h4>Vê e compara</h4>'
    '<p>Os resultados aparecem na hora. Muda os números para experimentar outros casos.</p></div>',
])

st.subheader("Em breve")
st.caption("Secções a caminho. Toca numa para ver o que vai ter.")
with st.container(horizontal=True, key="em_breve"):
    for secao in EM_CONSTRUCAO:
        st.page_link(f"paginas/breve/{secao.chave}.py", label=secao.titulo, icon=secao.icone)
