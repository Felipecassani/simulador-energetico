"""Início: o que o simulador faz e por onde começar.

Pouco texto à vista: ícones e cores guiam; as explicações ficam nas notas «ⓘ Saber mais» e nas
palavras sublinhadas (balão ao passar o rato ou tocar). O botão para começar e as ferramentas vêm
logo a seguir ao cabeçalho; o preço do mercado, que não é o que a pessoa paga, vem depois.
"""
from html import escape

import streamlit as st

from interface import componentes as ui
from interface.conteudo import CONTA_EM_1_MINUTO, EM_CONSTRUCAO, ORDEM_FERRAMENTAS
from interface.dados import omie_hoje_e_amanha, ofertas_erse
from nucleo import mercado, ofertas, roteiro

ui.cabecalho(
    "Descobre como pagar menos",
    "",
    kicker="Grátis · sem registo",
    imagem=ui.imagem_svg("ilustracao.svg"),
)

with st.container(key="cta_inicio"):
    st.page_link("paginas/fatura.py", label="Começar aqui", icon=":material/arrow_forward:")
st.html('<p class="lc-micro">Sem fatura à mão? Entra na mesma: há números de exemplo.</p>')

# ---------- prova: números reais, calculados com as ofertas oficiais (nunca escritos à mão)
lista_ofertas, data_ofertas = ofertas_erse()
mercado_casa = ofertas.resumo_mercado(lista_ofertas) if lista_ofertas else None
if mercado_casa:
    with st.container(key="prova"):
        st.html('<div class="lc-prova">' + "".join([
            '<div class="lc-grid" style="--lc-min:95px;--lc-cols:3">',
            ui.metrica("Ofertas comparadas", str(mercado_casa["ofertas"]), "preço fixo"),
            ui.metrica("Empresas", str(mercado_casa["empresas"]), "de eletricidade"),
            ui.metrica("Diferença até", ui.numero(mercado_casa["diferenca_ano"]), "€ por ano", destaque=True),
            "</div></div>"]))
    ui.nota(f"Para uma casa típica ({ui.numero(mercado_casa['kwh_mes'])} kWh por mês, "
            f"{ui.numero(mercado_casa['kva'], 2)} kVA), a oferta de preço fixo mais cara custa até "
            f"{ui.euros(mercado_casa['diferenca_ano'])} € por ano a mais do que a mais barata, sem IVA. "
            f"Contas feitas com as ofertas publicadas pela ERSE a {data_ofertas:%d/%m/%Y}.", "De onde vêm estes números?")
st.html('<div class="lc-selos">'
        '<span class="lc-selo"><b>✓</b> Dados oficiais da ERSE</span>'
        '<span class="lc-selo"><b>✓</b> Preços do mercado OMIE</span>'
        '<span class="lc-selo"><b>✓</b> Sem publicidade</span>'
        '<span class="lc-selo"><b>✓</b> Código aberto</span></div>')

st.subheader(":material/apps: Ferramentas")
ui.nota("Escolhe o que queres fazer. Os números que escreves numa ferramenta passam sozinhos para as outras.")
ferramentas = [roteiro.passo(n) for n in ORDEM_FERRAMENTAS]
# A primeira (por onde se começa) a toda a largura; as outras 4 numa grelha regular, com a mesma
# altura: 4 lado a lado no computador, 2 × 2 no tablet, uma por linha no telemóvel (CSS .st-key-grelha_ferramentas)
ui.cartao_ferramenta(ferramentas[0], roteiro.disponivel(ferramentas[0].numero), destaque=True)
with st.container(key="grelha_ferramentas"):
    for passo in ferramentas[1:]:
        ui.cartao_ferramenta(passo, roteiro.disponivel(passo.numero))

st.subheader(":material/lightbulb: A conta da luz em 1 minuto")
ui.grelha([f'<div class="lc-card lc-parte lc-aberto"><div class="lc-emoji" aria-hidden="true">{emoji}</div>'
           f'<span class="lc-n">{escape(rotulo.upper())}</span><h4>{escape(titulo)}</h4>'
           f'<p>{ui.com_glossario(texto)}</p></div>'
           for emoji, titulo, rotulo, texto in CONTA_EM_1_MINUTO], largura_min=240)

st.subheader(":material/school: Aprender o básico")
with st.container(horizontal=True, key="aprender"):
    st.page_link("paginas/guia.py", label="Guia rápido", icon=":material/school:")
    st.page_link("paginas/faq.py", label="Perguntas frequentes", icon=":material/help:")
    st.page_link("paginas/recursos.py", label="O que quer dizer cada palavra", icon=":material/menu_book:")

st.subheader(":material/bolt: O preço da eletricidade agora")
try:
    hoje, amanha = omie_hoje_e_amanha()
except mercado.SemRede:
    pass
else:
    ui.painel_mercado(hoje, amanha)
    ui.nota("É o preço a que as empresas compram a eletricidade no mercado ibérico (OMIE), antes das redes, "
            "da margem e dos impostos. Não é o que pagas, mas mostra se hoje a eletricidade está cara ou "
            "barata. Só mexe logo na tua conta se o teu contrato for indexado.", "O que é este preço?")
ui.periodo_atual()
ui.nota("Se tens bi-horário ou tri-horário (vem escrito na fatura), isto diz-te em que período estás agora. "
        "No simples, pagas o mesmo a qualquer hora.", "Para que serve?")
st.page_link("paginas/graficos.py", label="Ver o preço hora a hora", icon=":material/bar_chart:")

st.subheader(":material/checklist: Como funciona")
ui.grelha([
    '<div class="lc-card lc-passo"><div class="lc-emoji" aria-hidden="true">🧾</div><span class="lc-n">01</span>'
    '<h4>Pega na fatura</h4><p>Em papel, PDF ou foto.</p></div>',
    '<div class="lc-card lc-passo"><div class="lc-emoji" aria-hidden="true">✍️</div><span class="lc-n">02</span>'
    '<h4>Confirma os números</h4><p>O (?) de cada campo diz onde os encontrar.</p></div>',
    '<div class="lc-card lc-passo"><div class="lc-emoji" aria-hidden="true">💶</div><span class="lc-n">03</span>'
    '<h4>Vê quanto poupas</h4><p>Os resultados aparecem na hora.</p></div>',
])

st.subheader(":material/construction: Em breve")
with st.container(horizontal=True, key="em_breve"):
    for secao in EM_CONSTRUCAO:
        st.page_link(f"paginas/breve/{secao.chave}.py", label=secao.titulo, icon=secao.icone)

# ---------- chamada final, para quem leu até ao fim
st.write("")
with st.container(key="cta_final"):
    st.html("<h2>Pronto para pagar menos?</h2><p>Leva poucos minutos. Grátis e sem registo.</p>")
    st.page_link("paginas/fatura.py", label="Começar aqui", icon=":material/arrow_forward:")
