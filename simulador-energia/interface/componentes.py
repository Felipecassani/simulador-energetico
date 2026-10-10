"""Componentes visuais reutilizáveis. Usam as classes .lc-* de estilo.py.

O site é para qualquer pessoa: aqui não entra nada técnico (fórmulas,
estados de desenvolvimento, comandos). Isso vive no guia PDF (docs/).
"""
import re
from html import escape

import streamlit as st

from interface.estilo import MARCA
from interface import conteudo
from nucleo import roteiro


# ---------- formatos ----------

def nome_ficheiro(nome):
    """Nome de ficheiro para mostrar em texto markdown: sem formatação nem ligações (vem do browser)."""
    limpo = re.sub(r"[`*_\[\]()#<>!|~\\]", " ", str(nome))[:80].strip()
    return f"«{limpo}»"


def euros(valor):
    """90.5 → '90,50' (formato português, sem o símbolo)."""
    return f"{valor:,.2f}".replace(",", " ").replace(".", ",")


def numero(valor, casas=0):
    return f"{valor:,.{casas}f}".replace(",", " ").replace(".", ",")


def preco(valor):
    """Preço unitário (€/kWh, €/dia) com 4 casas: 0.3659 → '0,3659'."""
    return numero(valor, 4)


def tabela_formatada(df, casas=None):
    """Cópia da tabela com os números em texto português (vírgula decimal).

    casas: {coluna: n.º de casas}; colunas com "€" no nome usam 2 por omissão.
    """
    casas = casas or {}
    saida = df.copy()
    for coluna in saida.columns:
        n = casas.get(coluna, 2 if "€" in coluna else None)
        if n is not None:
            saida[coluna] = [numero(v, n) for v in saida[coluna]]
    return saida


# ---------- blocos ----------

def imagem_svg(nome):
    """Imagem SVG de assets/ como data URI (o st.html retira os <svg>; como <img> passam)."""
    import base64
    from pathlib import Path
    svg = (Path(__file__).resolve().parents[1] / "assets" / nome).read_text(encoding="utf-8")
    return "data:image/svg+xml;base64," + base64.b64encode(svg.encode()).decode()


def cabecalho(titulo, subtitulo, kicker="", chips=(), imagem=None):
    """Cabeçalho grande (hero). imagem: data URI de uma ilustração, à direita (some no telemóvel)."""
    chips_html = "".join(f'<span class="lc-chip">{escape(c)}</span>' for c in chips)
    figura = f'<img class="lc-hero-img" src="{imagem}" alt="" aria-hidden="true">' if imagem else ""
    st.html(f"""
    <section class="lc-hero{' lc-hero-com-img' if imagem else ''}">
      <div class="lc-hero-txt">
        <div class="lc-kicker">{escape(kicker)}</div>
        <h1>{escape(titulo)}</h1>
        {f"<p>{escape(subtitulo)}</p>" if subtitulo else ""}
        <div class="lc-chips">{chips_html}</div>
      </div>
      {figura}
    </section>""")


def badge(disponivel):
    if disponivel:
        return '<span class="lc-badge lc-ok">Disponível</span>'
    return '<span class="lc-badge lc-todo">Em breve</span>'


def cabecalho_ferramenta(passo, disponivel=True):
    selo = "" if disponivel else badge(False)
    st.html(f"""
    <div class="lc-step-head lc-cor-{passo.numero}">
      <div class="lc-step-num" aria-hidden="true">{passo.emoji}</div>
      <div class="lc-step-text">
        <div class="lc-step-title"><h2>{escape(passo.titulo)}</h2>{selo}</div>
        <p>{com_glossario(passo.descricao)}</p>
        {_destaques_html(passo.numero)}
      </div>
    </div>""")


def _destaques_html(numero):
    """Números reais que mostram o valor da ferramenta (interface/destaques.py)."""
    from interface import destaques
    itens = destaques.da_ferramenta(numero)
    if not itens:
        return ""
    return ('<div class="lc-destaques">' + "".join(
        f'<span class="lc-destaque"><b>{escape(v)}</b> {escape(r)}</span>' for v, r in itens) + "</div>")


def para_onde_vai(energia, potencia, impostos_e_taxas):
    """Barra "para onde vai o teu dinheiro": energia, potência e impostos, com € e % escritos
    (não só pela cor), para quem vê uma fatura pela primeira vez."""
    partes = [("Eletricidade que gastaste", energia, "lc-seg-energia"),
              ("Potência (parte fixa)", potencia, "lc-seg-potencia"),
              ("IVA e taxas", impostos_e_taxas, "lc-seg-impostos")]
    total = sum(v for _, v, _ in partes)
    if total <= 0:
        return
    barra = "".join(f'<span class="{c}" style="width:{100 * v / total:.1f}%"></span>' for _, v, c in partes)
    legenda = "".join(f'<li><span class="lc-ponto {c}" aria-hidden="true"></span>{escape(n)}: '
                      f'<b>{euros(v)} €</b> ({numero(100 * v / total)} %)</li>' for n, v, c in partes)
    st.html(f'<div class="lc-dinheiro"><div class="lc-n">PARA ONDE VAI O TEU DINHEIRO · TOTAL COM IVA '
            f'{euros(total)} €</div><div class="lc-barra" aria-hidden="true">{barra}</div>'
            f'<ul>{legenda}</ul></div>')


def metrica(rotulo, valor, unidade="", destaque=False, vazio=False):
    """Cartão de um número. Unidades compridas ("cêntimos por kWh") vão para a linha de baixo e
    valores em texto ("ainda não saiu") ficam mais pequenos: cartões lado a lado ficam iguais."""
    classes = "lc-metric" + (" lc-destaque" if destaque else "") + (" lc-vazio" if vazio else "")
    texto = any(c.isalpha() for c in str(valor)) and str(valor) != "—"
    classes += " lc-metric-texto" if texto else ""
    unidade_cls = "lc-unit lc-unit-linha" if len(unidade) > 6 else "lc-unit"
    return (f'<div class="{classes}"><div class="lc-label">{escape(rotulo)}</div>'
            f'<div class="lc-value">{escape(str(valor))}<span class="{unidade_cls}">{escape(unidade)}</span></div></div>')


def grelha(blocos_html, largura_min=200, max_colunas=4):
    """Mostra vários blocos HTML lado a lado, em linhas equilibradas e sem buracos.

    Escolhe o n.º de colunas que reparte os blocos por igual (5 → 3 + 2, 6 → 3 + 3, 7 → 4 + 3) e os da
    última linha esticam para a encher; no telemóvel, cada bloco nunca fica mais estreito do que
    largura_min (nem mais largo do que o ecrã). Os blocos da mesma linha ficam com a mesma altura.
    """
    import math
    n = max(1, len(blocos_html))
    colunas = math.ceil(n / math.ceil(n / max_colunas))
    estilo = f"--lc-min:{largura_min}px;--lc-cols:{colunas}"
    st.html(f'<div class="lc-grid" style="{estilo}">{"".join(blocos_html)}</div>')


def cartao_ferramenta(passo, disponivel, destaque=False):
    """Cartão da página Início: ícone, nome, o que faz e um botão com o que se vai fazer.
    O cartão inteiro é clicável (a ligação estica-se por cima dele, CSS .st-key-cartao_*).
    destaque: o cartão da ferramenta por onde se começa, a toda a largura."""
    selo = ('<span class="lc-badge lc-ok">Começa aqui</span>' if disponivel and destaque
            else "" if disponivel else badge(False))
    with st.container(border=True, key=f"cartao_{passo.numero}{'_destaque' if destaque else ''}"):
        if destaque:          # ícone, título e selo na mesma linha; a descrição por baixo
            st.html(f"""
            <div class="lc-card-flat">
              <div class="lc-topo"><span class="lc-emoji" aria-hidden="true">{passo.emoji}</span>
                <h4>{escape(passo.titulo)}</h4>{selo}</div>
              <p>{escape(passo.descricao)}</p>
            </div>""")
        else:
            st.html(f"""
            <div class="lc-card-flat">
              <div class="lc-topo">
                <span class="lc-emoji" aria-hidden="true">{passo.emoji}</span>{selo}
              </div>
              <h4>{escape(passo.titulo)}</h4>
              <p>{escape(passo.descricao)}</p>
            </div>""")
        st.page_link(passo.pagina, label=conteudo.ACAO.get(passo.numero, "Abrir") if disponivel else "Ver",
                     icon=":material/arrow_forward:")


def pagina_em_breve(numero):
    """Página de uma ferramenta que ainda está a ser preparada."""
    passo = roteiro.passo(numero)
    cabecalho_ferramenta(passo, disponivel=False)
    outras = any(roteiro.disponivel(p.numero) for p in roteiro.PASSOS if p.numero != numero)
    extra = ("<p>As ferramentas já disponíveis estão na página inicial.</p>" if outras else "")
    st.html(f"""
    <div class="lc-card lc-breve">
      <div class="lc-emoji">🚧</div>
      <h4>Esta ferramenta ainda não está disponível</h4>
      {extra}
    </div>""")
    st.page_link("paginas/inicio.py", label="Voltar ao início", icon=":material/arrow_back:")


def cartao_em_construcao(secao):
    """Cartão (clicável, mais apagado) de uma secção ainda em construção."""
    with st.container(border=True, key=f"cartao_breve_{secao.chave.replace('-', '_')}"):
        st.html(f"""
        <div class="lc-card-flat lc-construcao">
          <div class="lc-topo">
            <span class="lc-emoji" aria-hidden="true">{secao.emoji}</span><span class="lc-badge lc-todo">Em construção</span>
          </div>
          <h4>{escape(secao.titulo)}</h4>
          <p>{escape(secao.descricao)}</p>
        </div>""")
        st.page_link(f"paginas/breve/{secao.chave}.py", label="Ver", icon=":material/arrow_forward:")


def pagina_em_construcao(chave):
    """Página de uma secção em construção: o que vai ter e o caminho de volta."""
    secao = conteudo.em_construcao(chave)
    cabecalho(secao.titulo, secao.descricao, kicker="Em construção")
    planos = "".join(f"<li>{escape(p)}</li>" for p in secao.planos)
    st.html(f"""
    <div class="lc-card lc-breve">
      <div class="lc-emoji">🚧</div>
      <h4>Esta secção está a ser construída</h4>
      <p>O que vai ter:</p>
      <ul class="lc-lista">{planos}</ul>
    </div>""")
    st.page_link("paginas/inicio.py", label="Voltar ao início", icon=":material/arrow_back:")


def podio_ofertas(linhas, atual, unidade="por mês", empresa_atual=None, com_fatura=True):
    """Pódio das ofertas mais baratas.

    linhas: [(oferta, valor)] já na unidade a mostrar (€/mês ou € no 1.º ano);
    atual: o valor da fatura na mesma unidade, para a comparação.
    """
    from nucleo import periodos
    medalhas = ["🥇", "🥈", "🥉", "4.º", "5.º"]
    # sem fatura, a comparação é com os números de exemplo/preenchidos, não com "o que pagas hoje"
    face = "em relação a hoje" if com_fatura else "em relação aos números preenchidos"
    lugares = ["Mais barata", "2.ª mais barata", "3.ª mais barata", "4.ª mais barata", "5.ª mais barata"]
    blocos = []
    for i, (o, valor) in enumerate(linhas):
        dif = atual - valor
        if dif > 0.005:
            comparacao = f'<span class="lc-pos">Poupas {euros(dif)} € {unidade}</span> {face}'
        elif dif < -0.005:
            comparacao = f'<span class="lc-neg">Pagas mais {euros(-dif)} € {unidade}</span> {face}'
        else:
            comparacao = f"Pagas o mesmo {face}"
        etiquetas = [periodos.NOMES[o.opcao]]
        etiquetas.append("com fidelização" if o.fidelizacao else "sem fidelização")
        if empresa_atual and o.comercializador == empresa_atual:
            etiquetas.append("a tua empresa")
        chips = "".join(f'<span class="lc-chip">{escape(e)}</span>' for e in etiquetas)
        extra = ('<p class="lc-podio-nota">Tem benefícios à parte (saldo ou devoluções) que não '
                 'entram nesta conta.</p>' if o.reembolsos else "")
        ligacao = (f'<a href="{escape(o.ligacao)}" target="_blank" rel="noopener">Ver a oferta no site da '
                   f'empresa <span aria-hidden="true">↗</span></a>' if o.ligacao.startswith("http") else "")
        blocos.append(f"""
        <div class="lc-card lc-podio{' lc-podio-1' if i == 0 else ''}">
          <div class="lc-podio-medalha"><span aria-hidden="true">{medalhas[i]}</span>
            <span class="lc-podio-lugar">{lugares[i]}</span></div>
          <h4>{escape(o.comercializador)}</h4>
          <p class="lc-podio-oferta">{escape(o.nome)}</p>
          <div class="lc-podio-valor">{euros(valor)} €<small>{unidade}</small></div>
          <p>{comparacao}</p>
          <div class="lc-chips">{chips}</div>
          {extra}{ligacao}
        </div>""")
    grelha(blocos, largura_min=240)


def cartao_meu_tarifario(p, total_mes=None, na_fatura=False):
    """O contrato da pessoa, sempre à vista: empresa, tipo de preço, opção, potência e preços."""
    from nucleo import periodos
    empresa = p.get("comercializador") or "O teu contrato"
    tipo = "Indexado ao mercado" if p.get("modalidade") == "indexado" else "Preço fixo"
    desconto = p.get("desconto_pct")
    chips = [tipo, periodos.NOMES.get(p.get("opcao", "simples"), "Simples"),
             f"{numero(p['kva'], 2)} kVA"]
    if desconto:
        chips.append(f"campanha de {round(desconto)} %")
    chips_html = "".join(f'<span class="lc-chip">{escape(c)}</span>' for c in chips)
    fonte = ("lido da tua fatura · para corrigir, muda os números no passo 2, mais acima" if na_fatura
             else "lido da tua fatura · para corrigir, volta a «A minha fatura»")
    mes = (f'<div class="lc-meu-valor">{euros(total_mes)} €<small>por mês, sem IVA nem taxas</small></div>'
           if total_mes is not None else "")
    st.html(f"""
    <div class="lc-card lc-meu">
      <div class="lc-meu-topo"><span class="lc-n"><span aria-hidden="true">🧾</span> O MEU TARIFÁRIO</span>
        <span class="lc-meu-fonte">{fonte}</span></div>
      <div class="lc-meu-corpo">
        <div><h4>{escape(empresa)}</h4><div class="lc-chips">{chips_html}</div></div>
        <div class="lc-meu-precos">
          <span>Energia <b>{preco(p['preco_energia'])} € por kWh</b></span>
          <span>Potência <b>{preco(p['preco_diario'])} € por dia</b></span>
          <span>Consumo <b>{numero(p['consumo_kwh'])} kWh em {p['dias']} dias</b></span>
        </div>
        {mes}
      </div>
    </div>""")


DICA_PERIODO = {"vazio": "mais barato", "fora_vazio": "preço normal", "cheias": "preço intermédio",
                "ponta": "mais caro"}


def periodo_atual():
    """'Agora' nas opções horárias: o período de cada opção e até quando dura (atualiza a cada minuto)."""
    from datetime import datetime

    from nucleo import periodos

    @st.fragment(run_every="60s")
    def _mostrar():
        agora = datetime.now(periodos.LISBOA)
        blocos = [f'<div class="lc-card lc-agora"><span class="lc-n">AGORA</span>'
                  f'<div class="lc-agora-hora">{agora:%H:%M}</div>'
                  f'<p>{"Horário de verão" if periodos.epoca(agora) == "verao" else "Horário de inverno"}</p></div>']
        for opcao in ("bi", "tri"):
            atual = periodos.periodo(agora, opcao)
            ate = periodos.proxima_mudanca(agora, opcao)
            classe = "lc-agora-barato" if atual == "vazio" else "lc-agora-caro" if atual == "ponta" else ""
            blocos.append(
                f'<div class="lc-card lc-agora {classe}"><span class="lc-n">{escape(periodos.NOMES[opcao].upper())}</span>'
                f'<h4>{escape(periodos.NOMES[atual])} · {DICA_PERIODO.get(atual, "")}</h4>'
                f'<p>{"até às " + format(ate, "%Hh%M") if ate else ""}</p></div>')
        grelha(blocos, largura_min=150)
    _mostrar()


def painel_mercado(hoje, amanha):
    """Mini-painel do OMIE: média de hoje e de amanhã, com a tendência."""
    from nucleo import mercado
    r_hoje = mercado.resumo_omie(hoje)
    unidade = "cêntimos por kWh"
    blocos = [metrica("Preço médio hoje", numero(r_hoje["media"] / 10, 2), unidade)]
    if amanha:
        r_am = mercado.resumo_omie(amanha)
        dif = (r_am["media"] - r_hoje["media"]) / 10
        tendencia = "sobe" if dif > 0.05 else "desce" if dif < -0.05 else "fica igual"
        blocos.append(metrica(f"Amanhã {tendencia}", numero(r_am["media"] / 10, 2), unidade))
    else:
        blocos.append(metrica("Amanhã", "ainda não saiu", "sai por volta do meio-dia"))
    blocos.append(metrica("Hora mais barata hoje", numero(r_hoje["min"] / 10, 2), unidade))
    blocos.append(metrica("Hora mais cara hoje", numero(r_hoje["max"] / 10, 2), unidade))
    grelha(blocos, largura_min=150)


def com_glossario(texto):
    """HTML do texto com os termos do glossário sublinhados (balão ao passar o rato ou tocar).

    Cada termo só é marcado na primeira vez; os mais compridos primeiro ("tarifa regulada"
    antes de "tarifa"). O texto é escapado antes, por isso não entra HTML de fora.
    """
    import re as _re
    html = escape(texto)
    usados = []
    for termo in sorted(conteudo.GLOSSARIO, key=len, reverse=True):
        padrao = _re.compile(r"(?<![\w-])(" + _re.escape(escape(termo)) + r")(?![\w-])", _re.I)
        m = next((m for m in padrao.finditer(html)
                  if not any(a <= m.start() < b for a, b in usados)), None)
        if not m:
            continue
        definicao = escape(conteudo.GLOSSARIO[termo][1], quote=True)
        span = (f'<span class="lc-termo" tabindex="0" data-def="{definicao}">{m.group(1)}</span>')
        html = html[:m.start()] + span + html[m.end():]
        # posições depois desta mudaram: guarda o intervalo novo e ajusta os anteriores
        delta = len(span) - (m.end() - m.start())
        usados = [(a + delta, b + delta) if a > m.start() else (a, b) for a, b in usados]
        usados.append((m.start(), m.start() + len(span)))
    return html


def texto(md):
    """Como st.markdown (negrito com **, linhas começadas por "- " em lista), mas com as palavras
    técnicas do glossário sublinhadas e explicadas num balão ao passar o rato ou tocar."""
    html = com_glossario(str(md))
    html = re.sub(r"\*\*(.+?)\*\*", r"<b>\1</b>", html, flags=re.S)
    linhas, saida, lista = html.split("\n"), [], []
    for linha in linhas + [""]:
        if linha.startswith("- "):
            lista.append(f"<li>{linha[2:]}</li>")
            continue
        if lista:
            saida.append(f"<ul>{''.join(lista)}</ul>"); lista = []
        if linha.strip():
            saida.append(f"<p>{linha}</p>")
    st.html(f'<div class="lc-texto">{"".join(saida)}</div>')


def nota(md, rotulo="Saber mais"):
    """Explicação secundária escondida num "ⓘ": aparece ao passar o rato ou ao tocar (menos texto à vista)."""
    limpo = re.sub(r"\*\*(.+?)\*\*", r"\1", str(md))
    st.html(f'<span class="lc-nota" tabindex="0" role="note" aria-label="{escape(limpo, quote=True)}" '
            f'data-def="{escape(limpo, quote=True)}"><span aria-hidden="true">ⓘ</span> {escape(rotulo)}</span>')


def cartao_recomendacao(rec):
    """Cartão de uma recomendação, com a poupança mensal à esquerda (se houver)."""
    if rec.poupanca_mensal is not None:
        valor = (f'<div class="lc-rec-valor">{euros(rec.poupanca_mensal)} €'
                 f'<small>poupas por mês</small></div>')
    else:
        valor = '<div class="lc-rec-valor lc-rec-info">Dica</div>'
    ligacao = (f' <a href="{escape(rec.ligacao)}" target="_blank" rel="noopener">Abrir o simulador '
               f'da ERSE <span aria-hidden="true">↗</span> (abre noutra janela)</a>' if rec.ligacao else "")
    return (f'<div class="lc-card lc-rec">{valor}<div><h4>{escape(rec.titulo)}</h4>'
            f'<p>{escape(rec.texto)}{ligacao}</p></div></div>')


def aviso_fatura(p):
    """Nas outras ferramentas: o cartão "O meu tarifário" ou, sem fatura, o aviso de que os números
    já preenchidos são um exemplo (há quem pense que são os seus)."""
    from interface.perfil import PADRAO
    exemplo = all(p.get(k) == PADRAO[k] for k in ("consumo_kwh", "dias", "kva"))
    if not p.get("da_fatura") and exemplo:
        nota("Os números já preenchidos são um **exemplo**: uma casa que gasta "
                f"{numero(p['consumo_kwh'])} kWh em {p['dias']} dias, com os preços da tarifa regulada. "
                "Troca-os pelos da tua fatura, ou carrega-a em «A minha fatura» e eles passam para aqui sozinhos.", "Números de exemplo")
        st.page_link("paginas/fatura.py", label="Carregar a minha fatura", icon=":material/receipt_long:")
        return
    try:
        total = (p["consumo_kwh"] * p["preco_energia"] + p["preco_diario"] * p["dias"]) * 30 / p["dias"]
    except (TypeError, ZeroDivisionError):
        total = None
    cartao_meu_tarifario(p, total)


def proximo_passo(url_path):
    """Fim de cada ferramenta: o que a pessoa ficou a saber e o caminho para a seguinte."""
    from pathlib import Path
    numeros = {Path(p.pagina).stem: p.numero for p in roteiro.PASSOS}
    numero_atual = numeros.get(url_path)
    if url_path in ("guia", "faq", "recursos", "sobre"):
        cta_final()
        return
    if numero_atual is None or numero_atual not in conteudo.ORDEM_FERRAMENTAS:
        return
    ordem = list(conteudo.ORDEM_FERRAMENTAS)
    i = ordem.index(numero_atual)
    st.write("")
    with st.container(key="cta_final"):
        st.html(f'<span class="lc-cta-kicker">O QUE FICASTE A SABER</span>'
                f'<p class="lc-cta-txt">{escape(conteudo.APRENDESTE[numero_atual])}</p>')
        with st.container(horizontal=True, key="proximo_ligacoes"):
            if i + 1 < len(ordem):
                seguinte = roteiro.passo(ordem[i + 1])
                st.page_link(seguinte.pagina, label=f"Próximo passo: {seguinte.titulo}",
                             icon=":material/arrow_forward:")
            st.page_link("paginas/inicio.py", label="Ver todas as ferramentas", icon=":material/apps:")


def cta_final(titulo="Pronto para pagar menos?", texto="Leva poucos minutos. Grátis e sem registo."):
    """Faixa carmim no fim da página com o botão para começar (Início e páginas de ajuda)."""
    st.write("")
    with st.container(key="cta_final"):
        st.html(f"<h2>{escape(titulo)}</h2><p>{escape(texto)}</p>")
        st.page_link("paginas/fatura.py", label="Começar aqui", icon=":material/arrow_forward:")


def rodape():
    with st.container(horizontal=True, key="rodape_ajuda"):
        st.page_link("paginas/guia.py", label="Guia rápido", icon=":material/school:")
        st.page_link("paginas/faq.py", label="Perguntas frequentes", icon=":material/help:")
        st.page_link("paginas/recursos.py", label="O que quer dizer cada palavra", icon=":material/menu_book:")
    st.html(f"""
    <footer class="lc-footer">
      <span><b>{escape(MARCA)}</b> · feito por {escape(conteudo.AUTOR["nome"])} · resultados indicativos</span>
      <span>Preços da tua fatura ou oficiais (ERSE, OMIE)</span>
    </footer>""")
