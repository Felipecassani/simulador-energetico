"""Ferramenta 5 — Opções horárias: simples, bi ou tri-horário, em fixo e indexado."""
from datetime import datetime
from html import escape

import pandas as pd
import streamlit as st

from interface import componentes as ui
from interface import carregar_eredes
from interface import perfil as pf
from interface.dados import erse, medias_omie
from interface.graficos import CONFIG, grafico_opcoes
from nucleo import periodos, roteiro, tarifas

passo = roteiro.passo(5)
ui.cabecalho_ferramenta(passo, roteiro.disponivel(5))
ui.aviso_fatura(pf.perfil())
ui.periodo_atual()
tarifa = erse()

# ---------- consumos reais da E-REDES (contador inteligente)
carregar_eredes.secao("b")

entradas, resultado = st.columns([1, 1.5], gap="large")

with entradas:
    st.subheader("O teu consumo")
    consumo = pf.campo(st.number_input, "Consumo no período (kWh)", "consumo_kwh", "b_consumo",
                       min_value=0.0, step=10.0, help="A energia gasta no período, em kWh (vem da Fatura, se já a preencheste).")
    dias = pf.campo(st.number_input, "Dias do período", "dias", "b_dias", min_value=1, step=1,
                    help="Número de dias do período da fatura.")
    kva = pf.campo(st.selectbox, "Potência contratada", "kva", "b_kva",
                   options=pf.ESCALOES_KVA, format_func=lambda k: f"{ui.numero(k, 2)} kVA",
                   help="Está nos dados do contrato. Define o preço da potência na tarifa regulada.")
    vazio = pf.campo(st.slider, f"Consumo em vazio ({periodos.texto_vazio_curto()})", "pct_vazio", "b_vazio",
                     min_value=0.0, max_value=100.0, step=1.0, format="%.0f %%",
                     help="Quanto do teu consumo acontece à noite. Se tens bi ou tri-horário, "
                          "está na fatura. Se não, estima: água quente, máquinas e carro a "
                          "carregar à noite aumentam este valor.")
    limite = float(100 - vazio)          # vazio + ponta nunca passam de 100 %
    if pf.perfil()["pct_ponta"] > limite:
        pf.atualizar(pct_ponta=limite)
    if st.session_state.get(pf.chave("b_ponta"), 0) > limite:
        st.session_state[pf.chave("b_ponta")] = limite
    if limite > 0:
        ponta = pf.campo(st.slider, "Consumo nas horas de ponta", "pct_ponta", "b_ponta",
                         min_value=0.0, max_value=limite, step=1.0, format="%.0f %%",
                         help="Só conta no tri-horário: 4 horas por dia ao fim da manhã e ao "
                              "fim da tarde (horários em baixo).")
    else:
        ponta = 0.0
    medias, info = medias_omie(7)
    if medias is not None:
        with st.expander("Tarifa indexada: perdas e margem", icon=":material/tune:"):
            perdas = pf.campo(st.number_input, "Perdas (%)", "perdas_pct", "b_perdas", padrao=0.0,
                              min_value=0.0, max_value=50.0, step=0.5,
                              help="Do teu contrato indexado. A ERSE não publica um valor único.")
            margem = pf.campo(st.number_input, "Margem (€/kWh)", "margem_kwh", "b_margem",
                              padrao=0.0, min_value=0.0, step=0.001, format="%.4f",
                              help="Valor fixo que o comercializador soma ao preço do mercado.")
    else:
        perdas = margem = 0.0

linhas = tarifas.comparar_opcoes(consumo, vazio, ponta, dias, kva, tarifa,
                                 medias_omie=medias, perdas_pct=perdas, margem_eur_kwh=margem)
st.session_state["opcoes_linhas"] = linhas

with resultado:
    st.subheader("Quanto pagarias")
    melhor = linhas[0]
    ui.grelha([
        ui.metrica("Mais barato", f"{periodos.NOMES[melhor['opcao']]} {melhor['modalidade']}", ""),
        ui.metrica("Custo", ui.euros(melhor["total"]), "€", destaque=True),
        ui.metrica("Poupas face ao simples fixo", ui.euros(melhor["poupanca_vs_simples_fixo"]), "€"),
    ], largura_min=170)
    tabela = pd.DataFrame([{
        "Opção": periodos.NOMES[l["opcao"]], "Modalidade": l["modalidade"].capitalize(),
        "Energia (€)": l["energia"], "Potência (€)": l["potencia"], "Total (€)": l["total"],
        "Face ao simples fixo (€)": l["poupanca_vs_simples_fixo"],
    } for l in linhas])
    st.dataframe(ui.tabela_formatada(tabela), hide_index=True, width="stretch")
    st.plotly_chart(grafico_opcoes(linhas, altura=300), config=CONFIG, width="stretch")
    nota_indexado = (f" Indexado: mercado OMIE dos últimos {info['dias']} dias em cada período, "
                     "com as tarifas de acesso da ERSE e as perdas e margem que indicares."
                     if medias is not None
                     else " Sem ligação ao OMIE: só aparecem as opções fixas.")
    st.caption(f"Fixo: tarifa regulada ERSE {tarifa['ano']} para {ui.numero(kva, 2)} kVA. "
               "A potência é igual em todas as opções." + nota_indexado
               + " Valores sem IVA nem taxas.")

# ---------- horários
st.write("")
st.subheader("Quando é vazio, cheias e ponta")
estacao = periodos.epoca(datetime.now(periodos.LISBOA))


blocos = [
    f'<div class="lc-card"><span class="lc-n">BI-HORÁRIO · TODO O ANO</span><h4>Vazio</h4>'
    f'<p>{periodos.texto_intervalos("bi", "vazio")}</p><h4>Fora de vazio</h4>'
    f'<p>{periodos.texto_intervalos("bi", "fora_vazio")}</p></div>',
]
for nome_epoca, rotulo in (("inverno", "INVERNO"), ("verao", "VERÃO")):
    atual = " · agora" if nome_epoca == estacao else ""
    blocos.append(
        f'<div class="lc-card"><span class="lc-n">TRI-HORÁRIO · {rotulo}{escape(atual.upper())}</span>'
        f'<h4>Ponta</h4><p>{periodos.texto_intervalos("tri", "ponta", nome_epoca)}</p>'
        f'<h4>Cheias</h4><p>{periodos.texto_intervalos("tri", "cheias", nome_epoca)}</p>'
        f'<h4>Vazio</h4><p>{periodos.texto_intervalos("tri", "vazio", nome_epoca)}</p></div>')
ui.grelha(blocos, largura_min=220)
st.caption("Ciclo diário da ERSE para clientes domésticos (BTN), em hora legal portuguesa.")
