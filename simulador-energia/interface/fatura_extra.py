"""Separadores novos da Fatura: "Explorar possibilidades" e "O teu ano".

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
from nucleo import cenarios, historico


@dataclass
class Contexto:
    p: dict                      # perfil da pessoa
    f: object                    # resultado da fatura (energia, potência, total) ou None
    tarifa: dict                 # ERSE
    medias: object               # médias OMIE (ou None)
    com_perfil: bool
    sem_tri: bool
    lidas: list = field(default_factory=list)   # faturas lidas (até 12)


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
    origem = f"média das tuas {ano['faturas']} faturas" if usar_ano else "a fatura em cima"
    return kwh_mes, pv, pp, origem, origem_perfil


def _pico_medido():
    """Maior pico da E-REDES (kW, média de 15 min), se houver ficheiros carregados."""
    er = st.session_state.get("eredes_analise")
    return er["pico_kw"] if er else None


ANO = 365 / 30               # de "por mês (30 dias)" para "por ano": igual em todo o site


def _euros_ano(v):
    return f"{ui.euros(v)} €"


# ---------- explorar possibilidades
def explorar(c):
    """Separador \"Explorar possibilidades\": cenários e o simulador \"e se\"."""
    p, f, tarifa, medias = c.p, c.f, c.tarifa, c.medias
    lista_ex, _ = ofertas_erse()
    if f is None:
        st.info("Preenche primeiro os teus dados no separador \"Esta fatura\".", icon=":material/info:")
    else:
        kwh_mes, pv, pp, origem, origem_perfil = _base_de_consumo(c)
        # o teu contrato com o MESMO consumo dos cenários (a média do ano, se houver)
        atual_mes = kwh_mes * p["preco_energia"] + p["preco_diario"] * 30
        hoje = date.today()
        lista_cen = cenarios.explorar(kwh_mes, p["kva"], pv, pp, tarifa, lista_ex, medias, hoje,
                                      pico_kw=_pico_medido())
        st.subheader("O que podes mudar e quanto custaria")
        st.caption(f"Para {ui.numero(kwh_mes)} kWh por mês ({origem})"
                   + (f", com a repartição {origem_perfil}" if origem_perfil else
                      ", sem repartição por horas: só se compara a opção simples")
                   + ". Valores sem IVA nem taxas.")
        if lista_cen:
            melhor_c = lista_cen[0]
            poupanca = (atual_mes - melhor_c.mensal) * ANO
            ui.grelha([
                ui.metrica("O teu contrato", ui.euros(atual_mes), "€/mês"),
                ui.metrica("A melhor possibilidade", ui.euros(melhor_c.mensal), "€/mês", destaque=True),
                ui.metrica("Poupança possível", ui.euros(max(0.0, poupanca)), "€/ano"),
            ], largura_min=160)
            st.caption(f"A melhor: **{melhor_c.nome}** · {melhor_c.detalhe}.")
            st.plotly_chart(grafico_cenarios(lista_cen, atual_mes), config=CONFIG, width="stretch")
            tabela_cen = pd.DataFrame([{
                "Possibilidade": c.nome, "O que é": c.detalhe, "Esforço": c.esforco,
                "€/mês": c.mensal, "€/ano": c.mensal * ANO, "Poupas por ano (€)": (atual_mes - c.mensal) * ANO,
            } for c in lista_cen])
            st.dataframe(ui.tabela_formatada(tabela_cen), hide_index=True, width="stretch")

        st.write("")
        st.subheader("E se…")
        st.caption("Mexe nos valores e vê o contrato mais barato para esse cenário.")
        c1, c2, c3 = st.columns(3)
        with c1:
            mais_vazio = st.slider("Consumo que passas para o vazio (pontos %)", 0, 40, 10, key="x_vazio",
                                   disabled=pv is None,
                                   help="Ex.: pôr a máquina da roupa e a água quente a trabalhar à noite.")
        with c2:
            menos = st.slider("Gastar menos (%)", 0, 30, 0, key="x_menos",
                              help="Ex.: LED, standby desligado, máquinas cheias.")
        with c3:
            kva_x = st.selectbox("Potência", cenarios.ESCALOES, index=cenarios.ESCALOES.index(p["kva"])
                                 if p["kva"] in cenarios.ESCALOES else 5, key="x_kva",
                                 format_func=lambda k: f"{ui.numero(k, 2)} kVA")
        vazio_x = min(100.0 - (pp or 0.0), pv + mais_vazio) if pv is not None else None
        pico = _pico_medido()
        if pico is not None and pico > 0.9 * kva_x:
            st.warning(f"O teu maior pico medido foi {ui.numero(pico, 1)} kW: com {ui.numero(kva_x, 2)} kVA o "
                       "quadro pode disparar.", icon=":material/bolt:")
        m = cenarios.melhor(lista_ex, kwh_mes * (1 - menos / 100), kva_x, vazio_x, pp, tarifa)
        if pv is None:
            st.caption("Para mexer no vazio é preciso saber quando consomes: carrega uma fatura bi ou tri-horária "
                       "ou os ficheiros da E-REDES.")
        if m:
            dif = (atual_mes - m[0]) * ANO
            ui.grelha([
                ui.metrica("Custaria", ui.euros(m[0]), "€/mês", destaque=True),
                ui.metrica("Por ano", ui.euros(m[0] * ANO), "€"),
                ui.metrica("Poupas" if dif >= 0 else "Pagas a mais", ui.euros(abs(dif)), "€/ano"),
            ], largura_min=150)
            st.caption(f"Com: {m[1]}.")
        st.caption("Estimativas: ofertas de preço fixo da ERSE e tarifa regulada; o indexado depende do mercado. "
                   "Antes de mudar de potência, confirma que o quadro não dispara com os teus aparelhos.")


# ---------- o teu ano (até 12 faturas e/ou E-REDES)
def o_teu_ano(c):
    """Separador \"O teu ano\": até 12 faturas e os consumos da E-REDES."""
    p, tarifa = c.p, c.tarifa
    per = historico.juntar(c.lidas)
    ano = historico.resumo(per)
    pad = st.session_state.get("eredes_padroes")
    if len(per) < 2 and not pad:
        st.info(f"Carrega várias faturas no topo da página (até {historico.MAX_FATURAS}, todas de uma vez) e/ou "
                "os ficheiros da E-REDES de até um ano: aqui aparecem a evolução do consumo e do preço, o "
                "inverno contra o verão, os meses fora do normal e o contrato mais barato para o ano inteiro.",
                icon=":material/calendar_month:")
    if len(per) >= 2:
        st.subheader("As tuas faturas")
        intervalo = (f"{ano['inicio']:%d/%m/%Y} a {ano['fim']:%d/%m/%Y}" if ano["inicio"] else f"{ano['dias']} dias")
        ui.grelha([
            ui.metrica("Faturas", str(ano["faturas"]), intervalo),
            ui.metrica("Consumo por ano", ui.numero(ano["kwh_ano"]), "kWh"),
            ui.metrica("Por dia, em média", ui.numero(ano["kwh_dia"], 1), "kWh"),
            ui.metrica("Custo por ano", ui.euros(ano["custo_ano"]) if ano["custo_ano"] else "—", "€ sem IVA",
                       vazio=not ano["custo_ano"]),
        ], largura_min=150)
        st.plotly_chart(grafico_faturas(per), config=CONFIG, width="stretch")

        notas = []
        if ano["variacao_sazonal"] is not None:
            notas.append(f"No inverno gastas {ui.numero(abs(ano['variacao_sazonal']))} % "
                         + ("mais" if ano["variacao_sazonal"] >= 0 else "menos") + " por dia do que no verão "
                         f"({ui.numero(ano['inverno_kwh_dia'], 1)} contra {ui.numero(ano['verao_kwh_dia'], 1)} kWh/dia).")
        mx, mn = ano["maior"], ano["menor"]
        if mx is not mn and mx.inicio:
            notas.append(f"O período de maior consumo começou a {mx.inicio:%d/%m/%Y} ({ui.numero(mx.kwh_dia, 1)} kWh/dia); "
                         f"o de menor, a {mn.inicio:%d/%m/%Y} ({ui.numero(mn.kwh_dia, 1)} kWh/dia).")
        if ano["variacao_preco"] is not None and abs(ano["variacao_preco"]) >= 1:
            notas.append(f"O preço da energia {'subiu' if ano['variacao_preco'] > 0 else 'desceu'} "
                         f"{ui.numero(abs(ano['variacao_preco']), 1)} % entre a primeira e a última fatura.")
        for q in ano["fora_do_normal"]:
            if q.inicio:
                notas.append(f"A fatura de {q.inicio:%d/%m/%Y} está bem acima da tua média "
                             f"({ui.numero(q.kwh_dia, 1)} kWh/dia): aquecimento, visitas ou uma leitura estimada?")
        for de, ate, n in ano["lacunas"]:
            notas.append(f"Faltam {n} dias entre {de:%d/%m/%Y} e {ate:%d/%m/%Y}: com essa fatura a análise fica mais certa.")
        if len(ano["empresas"]) > 1:
            notas.append("Faturas de várias empresas: " + ", ".join(ano["empresas"]) + ".")
        if notas:
            st.markdown("\n".join(f"- {n}" for n in notas))

        lista_ano, _ = ofertas_erse()
        kwh_mes_a = ano["kwh_mes"]
        pv_a = (st.session_state.get("eredes_analise") or {}).get("pct_vazio", ano["pct_vazio"])
        pp_a = (st.session_state.get("eredes_analise") or {}).get("pct_ponta", ano["pct_ponta"])
        melhor_a = cenarios.melhor(lista_ano, kwh_mes_a, p["kva"], pv_a, pp_a, tarifa)
        if melhor_a and ano["custo_ano"]:
            custo_a = melhor_a[0] * ANO
            st.success(f"Para o teu ano inteiro ({ui.numero(ano['kwh_ano'])} kWh), o mais barato é **{melhor_a[1]}**: "
                       f"cerca de {_euros_ano(custo_a)} por ano, contra cerca de {_euros_ano(ano['custo_ano'])} ao ritmo das tuas "
                       f"faturas, sem IVA "
                       f"(poupança de {_euros_ano(max(0.0, ano['custo_ano'] - custo_a))}).", icon=":material/savings:")
        tabela_per = pd.DataFrame([{
            "Início": f"{q.inicio:%d/%m/%Y}" if q.inicio else "—", "Fim": f"{q.fim:%d/%m/%Y}" if q.fim else "—",
            "Dias": q.dias, "kWh": q.kwh, "kWh/dia": q.kwh_dia,
            "€/kWh": q.preco_kwh if q.preco_kwh is not None else float("nan"),
            "Custo (€)": q.custo if q.custo is not None else float("nan"), "Empresa": q.empresa or "—",
        } for q in per])
        with st.expander("Ver as faturas uma a uma"):
            st.dataframe(ui.tabela_formatada(tabela_per, {"kWh": 0, "kWh/dia": 1, "€/kWh": 4}),
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
            ui.metrica("Sempre ligado", ui.numero((pad["base_kw"] or 0) * 1000), "W de base"),
        ], largura_min=150)
        st.plotly_chart(grafico_meses(pad["meses"]), config=CONFIG, width="stretch")
        st.markdown("**A que horas gastas, mês a mês**")
        st.plotly_chart(mapa_calor(pad["mapa"]), config=CONFIG, width="stretch")
        st.caption("Cada quadrado é o consumo médio, por dia, nessa hora e nesse mês. As faixas mais escuras "
                   "mostram onde está o teu consumo: é aí que mudar hábitos ou de opção horária faz diferença.")
        e, d = st.columns([1, 1])
        with e:
            st.markdown("**Por dia da semana**")
            st.plotly_chart(grafico_semana(pad["por_dia_semana"]), config=CONFIG, width="stretch")
        with d:
            notas_er = []
            if base_eur:
                notas_er.append(f"Há cerca de **{ui.numero(pad['base_kw'] * 1000)} W sempre ligados** "
                                f"(frigorífico, routers, standby): {ui.numero(pad['base_kwh_ano'])} kWh e "
                                f"~{_euros_ano(base_eur)} por ano. Cada 10 W a menos poupa ~{_euros_ano(87.6 * preco_ref)}/ano.")
            if pad["dia_maior"]:
                dia, kwh_d = pad["dia_maior"]
                notas_er.append(f"O dia de maior consumo foi {dia:%d/%m/%Y}, com {ui.numero(kwh_d, 1)} kWh.")
            picos = [m for m in pad["meses"] if m["pico_kw"] > 0.9 * p["kva"]]
            if picos:
                notas_er.append("Em " + ", ".join(f"{m['mes']:%m/%Y}" for m in picos)
                                + f" chegaste perto dos {ui.numero(p['kva'], 2)} kVA: não convém descer de potência.")
            else:
                pico_max = max(m["pico_kw"] for m in pad["meses"])
                notas_er.append(f"O teu maior pico foi {ui.numero(pico_max, 1)} kW (média de 15 min), abaixo dos "
                                f"{ui.numero(p['kva'], 2)} kVA contratados.")
            if pad["kwh_dia_util"] and pad["kwh_dia_fds"]:
                dif_fds = (pad["kwh_dia_fds"] / pad["kwh_dia_util"] - 1) * 100
                notas_er.append(f"Ao fim de semana gastas {ui.numero(abs(dif_fds))} % "
                                + ("mais" if dif_fds >= 0 else "menos") + " por dia do que nos dias úteis.")
            st.markdown("\n".join(f"- {n}" for n in notas_er))
