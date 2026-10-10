"""As outras duas partes da Fatura: «Como pagar menos» e «O teu ano (várias faturas)».

Ficam fora de paginas/fatura.py para se poderem testar sem carregar ficheiros (o AppTest não envia
ficheiros): recebem o que a página já calculou num Contexto.
"""
from dataclasses import dataclass, field
from datetime import date

import pandas as pd
import streamlit as st

from interface import componentes as ui
from interface.dados import ofertas_erse
from interface.graficos import CONFIG
from interface.graficos_ano import grafico_cenarios, grafico_faturas, grafico_meses, grafico_semana, mapa_calor
from interface import perfil as pf
from nucleo import aparelhos, cenarios, historico, periodos


@dataclass
class Contexto:
    p: dict                      # perfil da pessoa
    f: object                    # resultado da fatura (energia, potência, total) ou None
    tarifa: dict                 # ERSE
    medias: object               # médias OMIE (ou None)
    com_perfil: bool
    sem_tri: bool
    lidas: list = field(default_factory=list)   # faturas lidas (até 12)


HORAS_BARATAS = f"das {periodos.VAZIO_INICIO.hour}h às {periodos.VAZIO_FIM.hour}h"


def _kva(k):
    """Potência como vem no papel: 6.9 → '6,9'."""
    return f"{float(k):g}".replace(".", ",")


def _base_de_consumo(c):
    """(kWh por mês, % vazio, % ponta, de onde vêm) com o melhor que houver: ano de faturas, E-REDES, fatura."""
    p = c.p
    ano = historico.resumo(historico.juntar(c.lidas))
    er = st.session_state.get("eredes_analise")
    usar_ano = ano is not None and ano["faturas"] >= 3
    kwh_mes = ano["kwh_mes"] if usar_ano else p["consumo_kwh"] * 30 / p["dias"]
    if er:
        pv, pp, origem_perfil = er["pct_vazio"], er["pct_ponta"], "dos teus consumos da E-REDES"
    elif c.com_perfil:
        pv, pp, origem_perfil = p["pct_vazio"], (None if c.sem_tri else p["pct_ponta"]), "da tua fatura"
    elif usar_ano and ano["pct_vazio"] is not None:
        pv, pp, origem_perfil = ano["pct_vazio"], ano["pct_ponta"], "das tuas faturas"
    else:
        pv, pp, origem_perfil = None, None, None
    origem = f"média das tuas {ano['faturas']} faturas" if usar_ano else "os números de «A tua fatura»"
    return kwh_mes, pv, pp, origem, origem_perfil


def _pico_medido():
    """Maior pico da E-REDES (kW, média de 15 min), se houver ficheiros carregados."""
    er = st.session_state.get("eredes_analise")
    return er["pico_kw"] if er else None


ANO = 365 / 30               # de "por mês (30 dias)" para "por ano": igual em todo o site

# nomes dos cenários como a pessoa os vê (os de nucleo/cenarios.py ficam iguais: os testes usam-nos)
NOMES_VISIVEIS = {"Melhor oferta em simples": "Melhor oferta (mesmo preço a toda a hora)",
                  "Melhor oferta em bi-horário": "Melhor oferta bi-horária (noite mais barata)"}


def _euros_ano(v):
    return f"{ui.euros(v)} €"


# ---------- como pagar menos
def _explicar(cen):
    """(em que consiste, contrato usado na conta) de um cenário, em palavras simples.

    Os nomes e os detalhes vêm de nucleo/cenarios.py (os testes dependem deles): aqui só se
    traduzem para a pessoa. O detalhe é "contrato · extra" nos cenários que mudam hábitos ou potência.
    """
    nome, detalhe = cen.nome, cen.detalhe
    if nome == "Tarifa regulada":
        opcao = detalhe.rsplit(", ", 1)[-1]
        return ("Mudar para a tarifa regulada, o preço fixo que a ERSE define todos os anos.",
                f"tarifa regulada, {opcao}")
    if nome.startswith("Melhor oferta"):
        return "Mudar só de contrato, para a oferta mais barata, sem mudar nada em casa.", detalhe
    if nome == "Indexado ao mercado":
        return ("Mudar para um tarifário em que o preço segue o mercado. É uma estimativa: o preço muda "
                "todos os meses e pode subir.", detalhe.split(" (", 1)[0])
    contrato, _, extra = detalhe.rpartition(" · ")
    contrato = contrato or detalhe
    if nome.startswith("Descer"):
        return ("Baixar a potência contratada. Pagas menos por dia, mas o quadro pode disparar se ligares "
                "muitos aparelhos ao mesmo tempo.", contrato)
    if nome.startswith("Pôr mais"):
        return (f"Passar 10 % do consumo para as horas baratas, {HORAS_BARATAS}: por exemplo, máquinas e "
                "água quente à noite, num tarifário bi ou tri-horário.", contrato)
    if nome.startswith("Gastar"):
        return "Gastar 10 % menos eletricidade, com as dicas de «Poupar em casa».", contrato
    if nome == "Juntar tudo":
        partes = ["gastar 10 % menos"]
        if "horas baratas" in extra or "vazio" in extra:
            partes.append("usar mais as horas baratas")
        if "kVA" in extra:
            partes.append("baixar a potência")
        texto = partes[0] if len(partes) == 1 else ", ".join(partes[:-1]) + " e " + partes[-1]
        return f"Fazer tudo ao mesmo tempo: {texto}.", contrato
    return detalhe, contrato


def _diferenca_ano(atual_mes, mensal):
    dif = (atual_mes - mensal) * ANO
    if dif > 0.005:
        return f"poupas {ui.euros(dif)} €"
    if dif < -0.005:
        return f"pagas mais {ui.euros(-dif)} €"
    return "igual a hoje"


def explorar(c):
    """Parte «Como pagar menos»: o que custaria cada mudança e o simulador «E se…»."""
    p, f, tarifa, medias = c.p, c.f, c.tarifa, c.medias
    lista_ex, _ = ofertas_erse()
    if f is None:
        st.info("Preenche primeiro os números da tua fatura na parte «A tua fatura».", icon=":material/info:")
    else:
        kwh_mes, pv, pp, origem, origem_perfil = _base_de_consumo(c)
        # o teu contrato com o MESMO consumo dos cenários (a média do ano, se houver)
        atual_mes = kwh_mes * p["preco_energia"] + p["preco_diario"] * 30
        hoje = date.today()
        lista_cen = cenarios.explorar(kwh_mes, p["kva"], pv, pp, tarifa, lista_ex, medias, hoje,
                                      pico_kw=_pico_medido())
        st.subheader("O que podes mudar e quanto custaria")
        ui.nota(f"Contas para {ui.numero(kwh_mes)} kWh por mês ({origem})"
                   + (f", com as horas a que gastas tiradas {origem_perfil}" if origem_perfil else "")
                   + ". Valores por mês, sem IVA."
                   + ("" if origem_perfil else " Como ainda não sei a que horas gastas, só comparo preços "
                                               "iguais a qualquer hora.")
                   + (" «Hoje pagas» usa o preço da tua fatura mais recente; em «O teu ano» a conta usa o que "
                      "pagaste em cada fatura, por isso a poupança pode ser um pouco diferente."
                      if origem.startswith("média") else ""))
        if lista_cen:
            melhor_c = lista_cen[0]
            poupanca = (atual_mes - melhor_c.mensal) * ANO
            consiste, contrato = _explicar(melhor_c)
            nome_melhor = NOMES_VISIVEIS.get(melhor_c.nome, melhor_c.nome)
            if melhor_c.mensal >= atual_mes - 0.005:
                # nenhuma mudança poupa: o contrato atual já é o mais barato (só muda o texto)
                st.success(f"Boa notícia: o teu contrato já é mais barato do que todas estas mudanças. "
                           f"Hoje pagas {ui.euros(atual_mes)} € por mês.", icon=":material/thumb_up:")
                ui.grelha([
                    ui.metrica("Hoje pagas", ui.euros(atual_mes), "€ por mês", destaque=True),
                    ui.metrica("A mudança menos cara", ui.euros(melhor_c.mensal), "€ por mês", destaque=False),
                ], largura_min=160)
                ui.texto(f"A mudança menos cara seria: **{nome_melhor}**. {consiste} Mesmo assim, pagarias "
                            f"mais {ui.euros(melhor_c.mensal - atual_mes)} € por mês. Conta feita com: {contrato}.")
            else:
                ui.grelha([
                    ui.metrica("Hoje pagas", ui.euros(atual_mes), "€ por mês"),
                    ui.metrica("Com a melhor mudança", ui.euros(melhor_c.mensal), "€ por mês", destaque=True),
                    ui.metrica("Poupavas por ano", ui.euros(max(0.0, poupanca)), "€"),
                ], largura_min=160)
                ui.texto(f"A mudança que mais poupa: **{nome_melhor}**. {consiste} "
                            f"Conta feita com: {contrato}.")
            ui.nota("Cada barra é uma mudança possível e mostra quanto pagarias por mês. A linha tracejada "
                       "é o que pagas hoje: as barras verdes acabam antes dela, ou seja, poupas.")
            st.plotly_chart(grafico_cenarios(lista_cen, atual_mes, nomes=NOMES_VISIVEIS), config=CONFIG,
                            width="stretch")
            linhas = []
            for cen in lista_cen:
                consiste_c, contrato_c = _explicar(cen)
                linhas.append({
                    "Mudança": NOMES_VISIVEIS.get(cen.nome, cen.nome), "Em que consiste": f"{consiste_c} Com: {contrato_c}.",
                    "O que tens de fazer": cen.esforco,
                    "Custo por mês (€)": cen.mensal, "Custo por ano (€)": cen.mensal * ANO,
                    "Diferença por ano": _diferenca_ano(atual_mes, cen.mensal),
                })
            with st.expander("Ver estes números numa tabela", icon=":material/table:"):
                st.dataframe(ui.tabela_formatada(pd.DataFrame(linhas)), hide_index=True, width="stretch")

        st.write("")
        st.subheader("E se… mudares alguns hábitos?")
        ui.nota("Arrasta as bolinhas para experimentar. Em baixo vês quanto pagarias com a oferta mais "
                   "barata para esse caso.")
        if pv is None:
            st.info("Para experimentar as horas baratas preciso de saber a que horas gastas: carrega uma fatura "
                    "bi ou tri-horária ou os ficheiros do contador (E-REDES), em «Carregar a fatura», no fim da página.",
                    icon=":material/schedule:")
        c1, c2, c3 = st.columns(3)
        with c1:
            mais_vazio = st.slider("Passar consumo para as horas baratas (%)", 0, 40, 10, key="x_vazio",
                                   disabled=pv is None,
                                   help=f"As horas de vazio, {HORAS_BARATAS}, são as mais baratas. Ex.: pôr a "
                                        "máquina da roupa ou o cilindro da água quente a trabalhar à noite. "
                                        "10 quer dizer passar 10 % do teu consumo para essas horas.")
        with c2:
            menos = st.slider("Gastar menos eletricidade (%)", 0, 30, 0, key="x_menos",
                              help="Ex.: lâmpadas LED, desligar aparelhos da tomada, máquinas só cheias. "
                                   "10 quer dizer gastar 10 % menos.")
        with c3:
            kva_x = st.selectbox("Potência contratada (kVA)", cenarios.ESCALOES,
                                 index=cenarios.ESCALOES.index(p["kva"]) if p["kva"] in cenarios.ESCALOES else 5,
                                 key="x_kva", format_func=lambda k: f"{_kva(k)} kVA",
                                 help="Uma potência mais baixa custa menos por dia, mas o quadro pode disparar "
                                      "se ligares muitos aparelhos ao mesmo tempo.")
        vazio_x = min(100.0 - (pp or 0.0), pv + mais_vazio) if pv is not None else None
        pico = _pico_medido()
        if pico is not None and pico > 0.9 * kva_x:
            st.warning(f"O teu maior consumo de uma vez foi {ui.numero(pico, 1)} kW: com {_kva(kva_x)} kVA o "
                       "quadro pode disparar.", icon=":material/bolt:")
        m = cenarios.melhor(lista_ex, kwh_mes * (1 - menos / 100), kva_x, vazio_x, pp, tarifa)
        if m:
            dif = (atual_mes - m[0]) * ANO
            ui.grelha([
                ui.metrica("Pagarias por mês", ui.euros(m[0]), "€", destaque=True),
                ui.metrica("Por ano", ui.euros(m[0] * ANO), "€"),
                ui.metrica("Poupas por ano" if dif >= 0 else "Pagas a mais por ano", ui.euros(abs(dif)), "€"),
            ], largura_min=150)
            ui.nota(f"A oferta mais barata para este caso: {m[1]}.")
        ui.nota("São estimativas sem IVA, com as ofertas de preço fixo publicadas pela ERSE e a tarifa "
                   "regulada. Antes de baixar a potência, confirma que o quadro não dispara com os teus aparelhos.")


# ---------- o teu ano (até 12 faturas e/ou E-REDES)
def o_teu_ano(c):
    """Parte «O teu ano»: até 12 faturas e os consumos da E-REDES."""
    p, tarifa = c.p, c.tarifa
    per = historico.juntar(c.lidas)
    ano = historico.resumo(per)
    pad = st.session_state.get("eredes_padroes")
    if len(per) < 2 and not pad:
        st.info(f"Carrega várias faturas de uma vez em «Carregar a fatura», no fim da página (até {historico.MAX_FATURAS}), "
                "ou os ficheiros do contador inteligente (E-REDES). Depois aparece aqui o teu ano inteiro: "
                "quanto gastas no inverno e no verão, os meses fora do normal e o contrato mais barato para o "
                "ano todo.", icon=":material/calendar_month:")
    if len(per) >= 2:
        st.subheader("As tuas faturas")
        intervalo = (f"{ano['inicio']:%d/%m/%Y} a {ano['fim']:%d/%m/%Y}" if ano["inicio"] else f"{ano['dias']} dias")
        ui.grelha([
            ui.metrica("Faturas", str(ano["faturas"]), intervalo),
            ui.metrica("Gasto por ano", ui.numero(ano["kwh_ano"]), "kWh"),
            ui.metrica("Por dia, em média", ui.numero(ano["kwh_dia"], 1), "kWh"),
            ui.metrica("Custo por ano", ui.euros(ano["custo_ano"]) if ano["custo_ano"] else "—", "€ sem IVA",
                       vazio=not ano["custo_ano"]),
        ], largura_min=150)
        st.plotly_chart(grafico_faturas(per), config=CONFIG, width="stretch")
        com_preco = any(q.preco_kwh is not None for q in per)
        ui.nota("As barras mostram quanto gastaste por dia em cada fatura (escala da esquerda)."
                   + (" A linha dourada mostra o preço de cada kWh, em cêntimos (escala da direita)."
                      if com_preco else ""))

        notas = []
        if ano["variacao_sazonal"] is not None:
            notas.append(f"No inverno gastas {ui.numero(abs(ano['variacao_sazonal']))} % "
                         + ("mais" if ano["variacao_sazonal"] >= 0 else "menos") + " por dia do que no verão: "
                         f"{ui.numero(ano['inverno_kwh_dia'], 1)} kWh por dia, contra "
                         f"{ui.numero(ano['verao_kwh_dia'], 1)} no verão.")
        mx, mn = ano["maior"], ano["menor"]
        if mx is not mn and mx.inicio:
            notas.append(f"A fatura com mais gasto começou a {mx.inicio:%d/%m/%Y}, com {ui.numero(mx.kwh_dia, 1)} "
                         f"kWh por dia; a com menos, a {mn.inicio:%d/%m/%Y}, com {ui.numero(mn.kwh_dia, 1)} kWh por dia.")
        if ano["variacao_preco"] is not None and abs(ano["variacao_preco"]) >= 1:
            notas.append(f"O preço da energia {'subiu' if ano['variacao_preco'] > 0 else 'desceu'} "
                         f"{ui.numero(abs(ano['variacao_preco']), 1)} % entre a primeira e a última fatura.")
        for q in ano["fora_do_normal"]:
            if q.inicio:
                notas.append(f"A fatura de {q.inicio:%d/%m/%Y} está bem acima da tua média, com "
                             f"{ui.numero(q.kwh_dia, 1)} kWh por dia: aquecimento, visitas ou uma leitura estimada?")
        for de, ate, n in ano["lacunas"]:
            notas.append(f"Faltam {n} dias entre {de:%d/%m/%Y} e {ate:%d/%m/%Y}: com essa fatura, as contas ficam "
                         "mais certas.")
        if len(ano["empresas"]) > 1:
            notas.append("Faturas de várias empresas: " + ", ".join(ano["empresas"]) + ".")
        if notas:
            ui.texto("\n".join(f"- {n}" for n in notas))

        lista_ano, _ = ofertas_erse()
        kwh_mes_a = ano["kwh_mes"]
        pv_a = (st.session_state.get("eredes_analise") or {}).get("pct_vazio", ano["pct_vazio"])
        pp_a = (st.session_state.get("eredes_analise") or {}).get("pct_ponta", ano["pct_ponta"])
        melhor_a = cenarios.melhor(lista_ano, kwh_mes_a, p["kva"], pv_a, pp_a, tarifa)
        if melhor_a and ano["custo_ano"]:
            custo_a = melhor_a[0] * ANO
            poupa = ano["custo_ano"] - custo_a
            st.success(f"Para o teu ano inteiro, o mais barato é **{melhor_a[1]}**: cerca de {_euros_ano(custo_a)} "
                       f"por ano. Ao ritmo das tuas faturas pagas cerca de {_euros_ano(ano['custo_ano'])}, "
                       + (f"por isso poupavas cerca de {_euros_ano(poupa)} por ano. " if poupa > 0.5 else
                          "por isso já pagas o mesmo ou menos. ")
                       + "Valores sem IVA.", icon=":material/savings:")
        tabela_per = pd.DataFrame([{
            "Início": f"{q.inicio:%d/%m/%Y}" if q.inicio else "—", "Fim": f"{q.fim:%d/%m/%Y}" if q.fim else "—",
            "Dias": q.dias, "Gasto (kWh)": q.kwh, "Por dia (kWh)": q.kwh_dia,
            "Preço de cada kWh (€)": q.preco_kwh if q.preco_kwh is not None else float("nan"),
            "Custo sem IVA (€)": q.custo if q.custo is not None else float("nan"), "Empresa": q.empresa or "—",
        } for q in per])
        with st.expander("Ver as faturas uma a uma", icon=":material/table:"):
            st.dataframe(ui.tabela_formatada(tabela_per, {"Gasto (kWh)": 0, "Por dia (kWh)": 1,
                                                          "Preço de cada kWh (€)": 4}),
                         hide_index=True, width="stretch")

    if pad:
        st.write("")
        st.subheader("Os teus consumos da E-REDES")
        preco_ref = p["preco_energia"]
        base_eur = pad["base_kwh_ano"] * preco_ref if pad["base_kwh_ano"] else None
        ui.grelha([
            ui.metrica("Meses", str(len(pad["meses"])), f"{pad['dias_completos']} dias completos"),
            ui.metrica("Dias úteis", ui.numero(pad["kwh_dia_util"] or 0, 1), "kWh por dia"),
            ui.metrica("Fins de semana", ui.numero(pad["kwh_dia_fds"] or 0, 1), "kWh por dia"),
            ui.metrica("Sempre ligado", ui.numero((pad["base_kw"] or 0) * 1000), "W, dia e noite"),
        ], largura_min=150)
        st.plotly_chart(grafico_meses(pad["meses"]), config=CONFIG, width="stretch")
        ui.nota("As barras mostram quanto gastaste em cada mês (escala da esquerda). A linha dourada mostra "
                   f"que parte foi gasta nas horas baratas, {HORAS_BARATAS} (escala da direita).")
        ui.texto("**A que horas gastas, mês a mês**")
        st.plotly_chart(mapa_calor(pad["mapa"]), config=CONFIG, width="stretch")
        ui.nota("Cada quadrado é uma hora de um mês. Quanto mais vermelho, mais gastas a essa hora. É nas "
                   "horas mais vermelhas que mudar hábitos ou de opção horária faz mais diferença.")
        e, d = st.columns([1, 1])
        with e:
            ui.texto("**Por dia da semana**")
            st.plotly_chart(grafico_semana(pad["por_dia_semana"]), config=CONFIG, width="stretch")
            ui.nota("Quanto gastas, em média, em cada dia da semana. Sábado e domingo estão a dourado.")
        with d:
            notas_er = []
            if base_eur:
                notas_er.append(f"Há cerca de **{ui.numero(pad['base_kw'] * 1000)} W sempre ligados** "
                                f"(frigorífico, router, aparelhos em espera): {ui.numero(pad['base_kwh_ano'])} kWh "
                                f"e cerca de {_euros_ano(base_eur)} por ano. Cada 10 W a menos poupa cerca de "
                                f"{_euros_ano(87.6 * preco_ref)} por ano.")
            if pad["dia_maior"]:
                dia, kwh_d = pad["dia_maior"]
                notas_er.append(f"O dia em que gastaste mais foi {dia:%d/%m/%Y}, com {ui.numero(kwh_d, 1)} kWh.")
            picos = [m for m in pad["meses"] if m["pico_kw"] > 0.9 * p["kva"]]
            if picos:
                notas_er.append("Em " + ", ".join(f"{m['mes']:%m/%Y}" for m in picos)
                                + f" chegaste perto dos {_kva(p['kva'])} kVA: não convém baixar a potência.")
            else:
                pico_max = max(m["pico_kw"] for m in pad["meses"])
                notas_er.append(f"O teu maior consumo de uma vez foi {ui.numero(pico_max, 1)} kW (medido de 15 em "
                                f"15 minutos), abaixo dos {_kva(p['kva'])} kVA contratados.")
            if pad["kwh_dia_util"] and pad["kwh_dia_fds"]:
                dif_fds = (pad["kwh_dia_fds"] / pad["kwh_dia_util"] - 1) * 100
                notas_er.append(f"Ao fim de semana gastas {ui.numero(abs(dif_fds))} % "
                                + ("mais" if dif_fds >= 0 else "menos") + " por dia do que nos dias úteis.")
            ui.texto("\n".join(f"- {n}" for n in notas_er))


# ---------- estimar pelos aparelhos (para quem não tem a fatura à mão)
def estimar_aparelhos():
    """Lista de aparelhos para marcar, com potência e horas editáveis → kWh por mês; um botão põe a
    estimativa no campo «Eletricidade gasta» (30 dias)."""
    with st.expander("Não sabes quanto gastas? Estima pelos teus aparelhos", icon=":material/electrical_services:"):
        ui.nota("Marca o que tens e ajusta a potência (vem na etiqueta do aparelho, em W) e as horas de uso "
                "por dia. Os valores já escritos são típicos de uma casa.", "Como funciona?")
        tabela = pd.DataFrame([{"Tenho": a.comum, "Aparelho": f"{a.emoji} {a.nome}",
                                "Watts": a.potencia_w, "Horas/dia": a.horas_dia}
                               for a in aparelhos.APARELHOS])
        editada = st.data_editor(
            tabela, key="f_aparelhos", hide_index=True, width="stretch", disabled=["Aparelho"],
            column_config={
                "Tenho": st.column_config.CheckboxColumn("Tenho", width="small",
                                                         help="Marca os aparelhos que tens e usas."),
                "Aparelho": st.column_config.TextColumn("Aparelho", width="medium"),
                "Watts": st.column_config.NumberColumn("Watts", min_value=0, step=50, width="small",
                                                       help="A potência, na etiqueta do aparelho: por exemplo 2000 W."),
                "Horas/dia": st.column_config.NumberColumn("Horas/dia", min_value=0.0, max_value=24.0, step=0.1,
                                                           format="%.1f", width="small",
                                                           help="Horas de uso por dia, em média. Meia hora = 0,5."),
            })
        total, detalhe = aparelhos.estimar(
            [(r["Aparelho"], bool(r["Tenho"]), float(r["Watts"] or 0), float(r["Horas/dia"] or 0))
             for _, r in editada.iterrows()])
        if not detalhe:
            st.info("Marca pelo menos um aparelho.", icon=":material/check_box:")
            return
        ui.grelha([ui.metrica("Estimativa por mês", ui.numero(total), "kWh", destaque=True)])
        ui.texto("**Os que mais gastam:** " + ", ".join(f"{nome} ({ui.numero(k)} kWh)" for nome, k in detalhe[:3]))
        if st.button(f"Usar esta estimativa: {ui.numero(total)} kWh em 30 dias", key="f_usar_aparelhos",
                     icon=":material/check:", type="primary"):
            pf.aplicar(consumo_kwh=float(round(total)), dias=30)
            st.rerun()
