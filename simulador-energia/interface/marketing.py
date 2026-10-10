"""Marketing honesto: partilhar o resultado, cartão em imagem, avisos sazonais, «Ajudou-te?» e a
visita guiada. Tudo com números calculados pelo site; nada de testemunhos, contadores ou urgência
inventados.
"""
import io
import sys
from datetime import date, timedelta
from html import escape
from urllib.parse import quote

import streamlit as st

from interface.componentes import euros, numero

URL_SITE = "https://simulador-energetico-8ufymt75zojdygw4tfgxjm.streamlit.app"


# ---------- partilhar o resultado
def texto_partilha(poupanca_ano):
    if poupanca_ano >= 1:
        return (f"Descobri que posso poupar cerca de {numero(poupanca_ano)} € por ano na conta da luz. "
                f"Experimenta, é grátis e sem registo: {URL_SITE}")
    return f"Fiz as contas à minha conta da luz. Experimenta, é grátis e sem registo: {URL_SITE}"


def cartao_png(poupanca_ano):
    """Imagem 1080×1080 com a poupança, para guardar ou publicar (cores do site)."""
    from PIL import Image, ImageDraw, ImageFont
    lado = 1080
    img = Image.new("RGB", (lado, lado), "#6E0E1C")
    d = ImageDraw.Draw(img)
    for y in range(lado):                                   # degradê carmim → vinho
        t = y / lado
        d.line([(0, y), (lado, y)], fill=(int(200 - 90 * t), int(40 - 26 * t), int(60 - 32 * t)))
    d.rounded_rectangle([60, 60, lado - 60, lado - 60], radius=60, outline="#D9B45B", width=6)

    def fonte(tam):
        return ImageFont.load_default(size=tam)

    def centrado(texto, y, tam, cor):
        f = fonte(tam)
        largura = d.textlength(texto, font=f)
        d.text(((lado - largura) / 2, y), texto, font=f, fill=cor)

    centrado("SIMULADOR ENERGÉTICO", 150, 44, "#FFE9B8")
    if poupanca_ano >= 1:
        centrado("Posso poupar cerca de", 330, 64, "#FFF7F2")
        centrado(f"{numero(poupanca_ano)} €", 440, 200, "#FFE9B8")
        centrado("por ano na conta da luz", 700, 64, "#FFF7F2")
    else:
        centrado("Fiz as contas à", 380, 72, "#FFF7F2")
        centrado("minha conta da luz", 480, 72, "#FFF7F2")
    centrado("Faz a tua conta: grátis e sem registo", 880, 40, "#FFE9B8")
    saida = io.BytesIO()
    img.save(saida, format="PNG")
    return saida.getvalue()


def partilhar(poupanca_ano, chave):
    """Botões para partilhar no WhatsApp e guardar o cartão em imagem."""
    with st.container(horizontal=True, key=f"partilhar_{chave}"):
        st.link_button("Partilhar no WhatsApp", f"https://wa.me/?text={quote(texto_partilha(poupanca_ano))}",
                       icon=":material/share:")
        st.download_button("Guardar imagem para partilhar", cartao_png(poupanca_ano),
                           file_name="poupanca-luz.png", mime="image/png", icon=":material/image:",
                           key=f"cartao_{chave}")


# ---------- calculadora relâmpago (Início)
def relampago(lista_ofertas, tarifa):
    """Um campo (quanto pagaste) → «podes poupar cerca de X € por ano»."""
    from nucleo import relampago as calc
    with st.container(key="relampago"):
        st.html('<div class="lc-relampago-titulo">⚡ Quanto pagaste na última fatura da luz?</div>')
        total = st.number_input("Total da última fatura, com IVA (€)", min_value=0.0, max_value=2000.0,
                                value=None, step=1.0, placeholder="por exemplo 65", key="relampago_total",
                                label_visibility="collapsed",
                                help="O total a pagar, com IVA, de uma fatura de cerca de um mês.")
        if not total:
            return
        r = calc.poupanca(total, lista_ofertas, tarifa)
        if r is None:
            st.info("Não consegui fazer a conta agora. Experimenta «A minha fatura».", icon=":material/info:")
            return
        if r["poupanca_ano"] >= 1:
            st.html(f'<div class="lc-relampago-res">Podes poupar cerca de <b>{numero(r["poupanca_ano"])} €</b> '
                    f'por ano</div>')
        else:
            st.html('<div class="lc-relampago-res">Boa notícia: já pagas perto do mais barato.</div>')
        from interface.componentes import nota
        nota(f"Estimativa: com os preços da tarifa regulada, {euros(total)} € dão cerca de "
             f"{numero(r['kwh_mes'])} kWh por mês (6,9 kVA, tarifa simples). Com esse consumo, a oferta "
             f"de preço fixo mais barata ({r['oferta'].comercializador}) custaria cerca de "
             f"{euros(r['melhor_mes'])} € por mês, com IVA. Para a tua conta exata, usa «A minha fatura».",
             "Como fiz esta conta?")
        st.page_link("paginas/fatura.py", label="Ver a conta exata com a minha fatura",
                     icon=":material/arrow_forward:")
        partilhar(r["poupanca_ano"], "inicio")


# ---------- avisos sazonais (do calendário de datas que mexem no preço)
def aviso_sazonal(hoje=None):
    """Aviso de uma data próxima (até 21 dias à frente ou 7 para trás), com o que fazer."""
    from nucleo import calendario
    hoje = hoje or date.today()
    perto = [e for e in calendario.eventos(hoje - timedelta(days=7), meses=1)
             if hoje - timedelta(days=7) <= e.dia <= hoje + timedelta(days=21) and not e.previsao]
    if not perto:
        return
    e = perto[0]
    quando = ("hoje" if e.dia == hoje else f"a {e.dia:%d/%m}")
    st.html(f'<div class="lc-sazonal"><span class="lc-sazonal-data">📅 {escape(quando)}</span>'
            f'<b>{escape(e.titulo)}</b><span>{escape(e.texto)}</span></div>')


# ---------- «Ajudou-te?»
def ajudou(pagina):
    """👍/👎 no fim de cada ferramenta. A resposta fica no registo do servidor (sem dados pessoais)."""
    voto = st.feedback("thumbs", key=f"ajudou_{pagina}")
    if voto is not None:
        print(f"[ajudou] pagina={pagina} voto={'sim' if voto == 1 else 'nao'}", file=sys.stderr, flush=True)
        st.html('<p class="lc-micro">Obrigado! A tua resposta ajuda a melhorar o simulador.</p>')


# ---------- visita guiada (primeira visita à Fatura nesta sessão)
def visita_guiada():
    """Três passos curtos, uma vez por sessão; «Percebi» fecha."""
    if st.session_state.get("visita_vista"):
        return
    with st.container(key="visita"):
        st.html('<div class="lc-visita">'
                '<div><span>1</span><b>Escreve os números</b><small>da tua fatura, ou usa os de exemplo</small></div>'
                '<div><span>2</span><b>Vê quanto pagas</b><small>e para onde vai o dinheiro</small></div>'
                '<div><span>3</span><b>Descobre a mais barata</b><small>entre as ofertas oficiais</small></div>'
                '</div>')
        if st.button("Percebi", key="visita_ok", icon=":material/check:"):
            st.session_state["visita_vista"] = True
            st.rerun()
