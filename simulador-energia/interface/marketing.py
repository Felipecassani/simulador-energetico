"""Pequenas ajudas para o site ser usado e partilhado: partilhar o resultado, cartão em imagem,
avisos de datas, «Ajudou-te?» e a visita guiada.
Regra: só mostro números calculados pelo site; nada de testemunhos ou contadores inventados.
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


def cartao_png(poupanca_ano, atual_mes=None, melhor_mes=None):
    """Imagem 1080×1080 para partilhar: logótipo, a poupança, «de X € para Y € por mês» e um código
    QR que abre o site (quem vê a imagem consegue chegar lá). Sem empresa nem kWh: é público."""
    from pathlib import Path

    import reportlab
    import segno
    from PIL import Image, ImageDraw, ImageFont
    lado = 1080
    img = Image.new("RGB", (lado, lado), "#6E0E1C")
    d = ImageDraw.Draw(img)
    for y in range(lado):                                   # degradê carmim → vinho
        t = y / lado
        d.line([(0, y), (lado, y)], fill=(int(200 - 90 * t), int(40 - 26 * t), int(60 - 32 * t)))
    d.rounded_rectangle([50, 50, lado - 50, lado - 50], radius=56, outline="#D9B45B", width=6)

    # a letra de origem do Pillow não tem «É», «á» nem «€»; a Vera vem com o reportlab (já usado no PDF)
    pasta = Path(reportlab.__file__).parent / "fonts"

    def fonte(tam, negrito=False):
        try:
            return ImageFont.truetype(str(pasta / ("VeraBd.ttf" if negrito else "Vera.ttf")), tam)
        except OSError:
            return ImageFont.load_default(size=tam)

    def centrado(texto, y, tam, cor, negrito=False, x0=0, x1=lado):
        f = fonte(tam, negrito)
        d.text((x0 + (x1 - x0 - d.textlength(texto, font=f)) / 2, y), texto, font=f, fill=cor)

    # topo: logótipo + nome
    logo = Image.open(Path(__file__).resolve().parents[1] / "assets" / "icone.png").convert("RGBA").resize((96, 96))
    mascara = Image.new("L", (96, 96), 0)                    # cantos redondos (o PNG tem cantos claros)
    ImageDraw.Draw(mascara).rounded_rectangle([0, 0, 95, 95], radius=24, fill=255)
    logo.putalpha(mascara)
    nome = fonte(40, True)
    largura = 96 + 22 + d.textlength("Simulador Energético", font=nome)
    x = (lado - largura) / 2
    img.paste(logo, (int(x), 110), logo)
    d.text((x + 118, 136), "Simulador Energético", font=nome, fill="#FFE9B8")

    if poupanca_ano >= 1:
        centrado("Posso poupar cerca de", 270, 56, "#FFF7F2")
        centrado(f"{numero(poupanca_ano)} €", 345, 170, "#FFE9B8", negrito=True)
        centrado("por ano na conta da luz", 545, 56, "#FFF7F2")
        if atual_mes and melhor_mes:
            texto = f"de {numero(atual_mes)} € para {numero(melhor_mes)} € por mês"
            f = fonte(40, True)
            w = d.textlength(texto, font=f)
            d.rounded_rectangle([(lado - w) / 2 - 30, 630, (lado + w) / 2 + 30, 700], radius=35, fill="#FFF7F2")
            d.text(((lado - w) / 2, 643), texto, font=f, fill="#8C1424")
    else:
        centrado("Fiz as contas à", 320, 66, "#FFF7F2")
        centrado("minha conta da luz", 410, 66, "#FFF7F2")

    # fundo: código QR que abre o site + o convite
    qr = segno.make(URL_SITE, error="m")
    tamanho = 250
    buffer = io.BytesIO()
    qr.save(buffer, kind="png", scale=10, border=2, dark="#2A0A10", light="#FFFFFF")
    codigo = Image.open(io.BytesIO(buffer.getvalue())).convert("RGB").resize((tamanho, tamanho), Image.NEAREST)
    x_qr, y_qr = 140, 738
    d.rounded_rectangle([x_qr - 14, y_qr - 14, x_qr + tamanho + 14, y_qr + tamanho + 14], radius=24, fill="#FFFFFF")
    img.paste(codigo, (x_qr, y_qr))
    x_txt = x_qr + tamanho + 60
    d.text((x_txt, y_qr + 40), "Faz a tua conta", font=fonte(50, True), fill="#FFE9B8")
    d.text((x_txt, y_qr + 112), "Aponta a câmara", font=fonte(36), fill="#FFF7F2")
    d.text((x_txt, y_qr + 160), "para o código", font=fonte(36), fill="#FFF7F2")
    d.text((x_txt, y_qr + 218), "Grátis e sem registo", font=fonte(30), fill="#FFE9B8")
    saida = io.BytesIO()
    img.save(saida, format="PNG")
    return saida.getvalue()


def partilhar(poupanca_ano, chave, atual_mes=None, melhor_mes=None):
    """Botões para partilhar no WhatsApp e guardar o cartão em imagem."""
    with st.container(horizontal=True, key=f"partilhar_{chave}"):
        st.link_button("Partilhar no WhatsApp", f"https://wa.me/?text={quote(texto_partilha(poupanca_ano))}",
                       icon=":material/share:")
        st.download_button("Guardar imagem para partilhar", cartao_png(poupanca_ano, atual_mes, melhor_mes),
                           file_name="poupanca-luz.png", mime="image/png", icon=":material/image:",
                           key=f"cartao_{chave}")


# ---------- calculadora relâmpago (Início)
def relampago(lista_ofertas, tarifa):
    """Um campo (quanto pagaste) → «podes poupar cerca de X € por ano»."""
    from nucleo import relampago as calc
    with st.container(key="relampago"):
        from interface.componentes import icone
        st.html(f'<div class="lc-relampago-titulo">{icone("bolt")} Quanto pagaste na última fatura da luz?</div>')
        total = st.number_input("Total da última fatura, com IVA (€)", min_value=0.0, max_value=2000.0,
                                value=None, step=1.0, placeholder="por exemplo 65", key="relampago_total",
                                label_visibility="collapsed",
                                help="O total a pagar, com IVA, de uma fatura de cerca de um mês.")
        with st.expander("Afinar a conta (opcional): quantos kWh gastaste?", icon=":material/tune:"):
            kwh = st.number_input("Eletricidade gasta nessa fatura (kWh)", min_value=0.0, max_value=10000.0,
                                  value=None, step=10.0, placeholder="por exemplo 258", key="relampago_kwh",
                                  help="Está junto às leituras do contador, por exemplo «Consumo: 258 kWh». "
                                       "Com este número a conta fica muito mais certa.")
        if not total:
            return
        r = calc.poupanca(total, lista_ofertas, tarifa, kwh_real=kwh)
        if r is None:
            st.info("Não consegui fazer a conta agora. Experimenta «A minha fatura».", icon=":material/info:")
            return
        tipo = ("com o teu consumo" if r["exata"] else "estimativa por baixo")
        if r["poupanca_ano"] >= 1:
            st.html(f'<div class="lc-relampago-res">Podes poupar cerca de <b>{numero(r["poupanca_ano"])} €</b> '
                    f'por ano <span class="lc-relampago-tipo">{tipo}</span></div>')
        else:
            st.html('<div class="lc-relampago-res">Boa notícia: já pagas perto do mais barato.</div>')
        from interface.componentes import nota
        if r["exata"]:
            nota(f"Com {numero(r['kwh_mes'])} kWh num mês (6,9 kVA, tarifa simples), a oferta de preço fixo mais "
                 f"barata ({r['oferta'].comercializador}) custaria cerca de {euros(r['melhor_mes'])} € por mês, "
                 f"com IVA e taxas, contra os {euros(total)} € que pagaste. Para a conta completa, com a tua "
                 "potência e o teu horário, usa «A minha fatura».", "Como fiz esta conta?")
        else:
            nota(f"Não sei quanto gastaste, por isso calculei o consumo com os preços da tarifa regulada: "
                 f"{euros(total)} € dão cerca de {numero(r['kwh_mes'])} kWh por mês (6,9 kVA, tarifa simples). "
                 f"Com esse consumo, a oferta de preço fixo mais barata ({r['oferta'].comercializador}) custaria "
                 f"cerca de {euros(r['melhor_mes'])} € por mês, com IVA. Se pagas mais caro do que a regulada, "
                 "a poupança real é maior do que esta: escreve os kWh em «Afinar a conta» para a saberes.",
                 "Como fiz esta conta?")
        st.page_link("paginas/fatura.py", label="Ver a conta exata com a minha fatura",
                     icon=":material/arrow_forward:")
        partilhar(r["poupanca_ano"], "inicio", total, r["melhor_mes"])


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
    from interface.componentes import icone
    st.html(f'<div class="lc-sazonal"><span class="lc-sazonal-data">{icone("event")} {escape(quando)}</span>'
            f'<b>{escape(e.titulo)}</b><span>{escape(e.texto)}</span></div>')


# ---------- «Ajudou-te?»
def ajudou(pagina):
    """👍/👎 no fim de cada ferramenta. A resposta fica no registo do servidor (sem dados pessoais)."""
    voto = st.feedback("thumbs", key=f"ajudou_{pagina}")
    if voto is not None:
        print(f"[ajudou] pagina={pagina} voto={'sim' if voto == 1 else 'nao'}", file=sys.stderr, flush=True)
        st.html('<p class="lc-micro">Obrigado! A tua resposta ajuda a melhorar o simulador.</p>')


# ---------- visita guiada (até a pessoa carregar em «Percebi»; o browser lembra-se)
_LEMBRAR = """<script>
(function () {{
  const chave = "lc-visita-vista";
  try {{
    {gravar}
    if (localStorage.getItem(chave)) document.querySelectorAll(".st-key-visita").forEach(e => e.style.display = "none");
  }} catch (e) {{}}
}})();
</script>"""


def visita_guiada():
    """Três passos curtos. «Percebi» fecha-a nesta sessão e o browser guarda a marca «já vi»
    (localStorage, sem dados pessoais), para não voltar a aparecer nas visitas seguintes."""
    vista = st.session_state.get("visita_vista")
    if not vista:
        with st.container(key="visita"):
            st.html('<div class="lc-visita">'
                    '<div><span>1</span><b>Escreve os números</b><small>da tua fatura, ou usa os de exemplo</small></div>'
                    '<div><span>2</span><b>Vê quanto pagas</b><small>e para onde vai o dinheiro</small></div>'
                    '<div><span>3</span><b>Descobre a mais barata</b><small>entre as ofertas oficiais</small></div>'
                    '</div>')
            if st.button("Percebi", key="visita_ok", icon=":material/check:"):
                st.session_state["visita_vista"] = True
                st.rerun()
    gravar = 'localStorage.setItem(chave, "1");' if vista else ""
    st.html(_LEMBRAR.format(gravar=gravar), unsafe_allow_javascript=True)
