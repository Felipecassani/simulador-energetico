"""Componentes visuais reutilizáveis. Usam as classes .lc-* de estilo.py.

O site é para qualquer pessoa: aqui não entra nada técnico (fórmulas,
estados de desenvolvimento, comandos). Isso vive no guia PDF (docs/).
"""
from html import escape

import streamlit as st

from interface.estilo import MARCA
from interface import conteudo
from nucleo import roteiro


# ---------- formatos ----------

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

def cabecalho(titulo, subtitulo, kicker="", chips=()):
    chips_html = "".join(f'<span class="lc-chip">{escape(c)}</span>' for c in chips)
    st.html(f"""
    <section class="lc-hero">
      <div class="lc-kicker">{escape(kicker)}</div>
      <h1>{escape(titulo)}</h1>
      <p>{escape(subtitulo)}</p>
      <div class="lc-chips">{chips_html}</div>
    </section>""")


def badge(disponivel):
    if disponivel:
        return '<span class="lc-badge lc-ok">Disponível</span>'
    return '<span class="lc-badge lc-todo">Em breve</span>'


def cabecalho_ferramenta(passo, disponivel=True):
    selo = "" if disponivel else badge(False)
    st.html(f"""
    <div class="lc-step-head">
      <div class="lc-step-num">{passo.emoji}</div>
      <div class="lc-step-text">
        <div class="lc-step-title"><h2>{escape(passo.titulo)}</h2>{selo}</div>
        <p>{escape(passo.descricao)}</p>
      </div>
    </div>""")


def metrica(rotulo, valor, unidade="", destaque=False, vazio=False):
    classes = "lc-metric" + (" lc-destaque" if destaque else "") + (" lc-vazio" if vazio else "")
    return (f'<div class="{classes}"><div class="lc-label">{escape(rotulo)}</div>'
            f'<div class="lc-value">{escape(str(valor))}<span class="lc-unit">{escape(unidade)}</span></div></div>')


def grelha(blocos_html, largura_min=200):
    """Mostra vários blocos HTML lado a lado (quebram em linhas no telemóvel)."""
    estilo = f"grid-template-columns:repeat(auto-fit,minmax({largura_min}px,1fr))"
    st.html(f'<div class="lc-grid" style="{estilo}">{"".join(blocos_html)}</div>')


def cartao_ferramenta(passo, disponivel):
    """Cartão da página Início: ícone, nome e o que faz. O cartão inteiro é clicável
    (a ligação estica-se por cima dele, CSS .st-key-cartao_*)."""
    with st.container(border=True, key=f"cartao_{passo.numero}"):
        st.html(f"""
        <div class="lc-card-flat">
          <div class="lc-topo">
            <span class="lc-emoji">{passo.emoji}</span>{badge(disponivel)}
          </div>
          <h4>{escape(passo.titulo)}</h4>
          <p>{escape(passo.descricao)}</p>
        </div>""")
        st.page_link(passo.pagina, label="Abrir" if disponivel else "Ver",
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
            <span class="lc-emoji">{secao.emoji}</span><span class="lc-badge lc-todo">Em construção</span>
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


def podio_ofertas(linhas, atual, unidade="por mês", empresa_atual=None):
    """Pódio das ofertas mais baratas.

    linhas: [(oferta, valor)] já na unidade a mostrar (€/mês ou € no 1.º ano);
    atual: o valor da fatura na mesma unidade, para a comparação.
    """
    from nucleo import periodos
    medalhas = ["🥇", "🥈", "🥉", "4.º", "5.º"]
    blocos = []
    for i, (o, valor) in enumerate(linhas):
        dif = atual - valor
        if dif > 0.005:
            comparacao = f'<span class="lc-pos">−{euros(dif)} € {unidade}</span> face à tua fatura'
        elif dif < -0.005:
            comparacao = f'<span class="lc-neg">+{euros(-dif)} € {unidade}</span> face à tua fatura'
        else:
            comparacao = "igual à tua fatura"
        etiquetas = [periodos.NOMES[o.opcao]]
        etiquetas.append("com fidelização" if o.fidelizacao else "sem fidelização")
        if empresa_atual and o.comercializador == empresa_atual:
            etiquetas.append("a tua empresa")
        chips = "".join(f'<span class="lc-chip">{escape(e)}</span>' for e in etiquetas)
        extra = ('<p class="lc-podio-nota">Tem benefícios à parte (saldo ou devoluções) que não '
                 'entram nesta conta.</p>' if o.reembolsos else "")
        ligacao = (f'<a href="{escape(o.ligacao)}" target="_blank" rel="noopener">Ver a oferta ↗</a>'
                   if o.ligacao.startswith("http") else "")
        blocos.append(f"""
        <div class="lc-card lc-podio{' lc-podio-1' if i == 0 else ''}">
          <div class="lc-podio-medalha">{medalhas[i]}</div>
          <h4>{escape(o.comercializador)}</h4>
          <p class="lc-podio-oferta">{escape(o.nome)}</p>
          <div class="lc-podio-valor">{euros(valor)} €<small>{unidade}</small></div>
          <p>{comparacao}</p>
          <div class="lc-chips">{chips}</div>
          {extra}{ligacao}
        </div>""")
    grelha(blocos, largura_min=240)


def cartao_meu_tarifario(p, total_mes=None):
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
    mes = (f'<div class="lc-meu-valor">{euros(total_mes)} €<small>por mês, sem IVA</small></div>'
           if total_mes is not None else "")
    st.html(f"""
    <div class="lc-card lc-meu">
      <div class="lc-meu-topo"><span class="lc-n">🧾 O MEU TARIFÁRIO</span>
        <span class="lc-meu-fonte">da tua fatura · para mudar, volta à Fatura</span></div>
      <div class="lc-meu-corpo">
        <div><h4>{escape(empresa)}</h4><div class="lc-chips">{chips_html}</div></div>
        <div class="lc-meu-precos">
          <span>Energia <b>{preco(p['preco_energia'])} €/kWh</b></span>
          <span>Potência <b>{preco(p['preco_diario'])} €/dia</b></span>
          <span>Consumo <b>{numero(p['consumo_kwh'])} kWh em {p['dias']} dias</b></span>
        </div>
        {mes}
      </div>
    </div>""")


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
                f'<h4>{escape(periodos.NOMES[atual])}</h4>'
                f'<p>{"até às " + format(ate, "%Hh%M") if ate else ""}</p></div>')
        grelha(blocos, largura_min=170)
    _mostrar()


def painel_mercado(hoje, amanha):
    """Mini-painel do OMIE: média de hoje e de amanhã, com a tendência."""
    from nucleo import mercado
    r_hoje = mercado.resumo_omie(hoje)
    blocos = [metrica("Mercado hoje", numero(r_hoje["media"] / 10, 2), "c€/kWh")]
    if amanha:
        r_am = mercado.resumo_omie(amanha)
        dif = (r_am["media"] - r_hoje["media"]) / 10
        seta = "▲" if dif > 0.05 else "▼" if dif < -0.05 else "▬"
        blocos.append(metrica(f"Amanhã {seta}", numero(r_am["media"] / 10, 2), "c€/kWh"))
    else:
        blocos.append(metrica("Amanhã", "—", "sai por volta do meio-dia", vazio=True))
    blocos.append(metrica("Mais barato hoje", numero(r_hoje["min"] / 10, 2), "c€/kWh"))
    blocos.append(metrica("Mais caro hoje", numero(r_hoje["max"] / 10, 2), "c€/kWh"))
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


def cartao_recomendacao(rec):
    """Cartão de uma recomendação, com a poupança mensal à esquerda (se houver)."""
    if rec.poupanca_mensal is not None:
        valor = (f'<div class="lc-rec-valor">{euros(rec.poupanca_mensal)} €'
                 f'<small>por mês</small></div>')
    else:
        valor = '<div class="lc-rec-valor lc-rec-info">i<small>informação</small></div>'
    ligacao = (f' <a href="{escape(rec.ligacao)}" target="_blank" rel="noopener">Abrir o simulador '
               f'da ERSE ↗</a>' if rec.ligacao else "")
    return (f'<div class="lc-card lc-rec">{valor}<div><h4>{escape(rec.titulo)}</h4>'
            f'<p>{escape(rec.texto)}{ligacao}</p></div></div>')


def aviso_fatura(p):
    """Nas outras ferramentas: o cartão "O meu tarifário" (só depois de carregar uma fatura)."""
    if not p.get("da_fatura"):
        return
    try:
        total = (p["consumo_kwh"] * p["preco_energia"] + p["preco_diario"] * p["dias"]) * 30 / p["dias"]
    except (TypeError, ZeroDivisionError):
        total = None
    cartao_meu_tarifario(p, total)


def rodape():
    st.html(f"""
    <footer class="lc-footer">
      <span><b>{escape(MARCA)}</b> · feito por {escape(conteudo.AUTOR["nome"])} · resultados indicativos</span>
      <span>Preços da tua fatura ou oficiais (ERSE, OMIE) · sem IVA nem taxas · nada é guardado</span>
    </footer>""")
