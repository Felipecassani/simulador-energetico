"""Ferramenta 2 — Eficiência: dicas para a casa de cada pessoa e poupança estimada."""
from html import escape

import streamlit as st

from interface import componentes as ui
from interface import perfil as pf
from nucleo import calculos, eficiencia, roteiro

passo = roteiro.passo(2)
ui.cabecalho_ferramenta(passo, roteiro.disponivel(2))
ui.aviso_fatura(pf.perfil())

NIVEL_TEXTO = {"baixo": "baixo", "medio": "médio", "alto": "alto"}
IMPACTO = {"alto": ("lc-erro", "Impacto alto"), "medio": ("lc-rever", "Impacto médio"),
           "baixo": ("lc-ok", "Impacto baixo")}

esquerda, direita = st.columns([1, 1.6], gap="large")

with esquerda:
    st.subheader("A tua casa")
    consumo = pf.campo(st.number_input, "Consumo no período (kWh)", "consumo_kwh", "e_consumo",
                       min_value=0.0, step=10.0,
                       help="O consumo da tua fatura (vem da ferramenta Fatura, se já a preencheste).")
    dias = pf.campo(st.number_input, "Dias do período", "dias", "e_dias", min_value=1, step=1,
                    help="Os dias da fatura: servem para levar o consumo a um mês.")
    pessoas = pf.campo(st.number_input, "Pessoas em casa", "pessoas", "e_pessoas",
                       min_value=1, max_value=12, step=1,
                       help="Quantas pessoas vivem em casa: serve para comparar o consumo.")
    st.caption("O que tens em casa")
    equipamentos = {
        "termoacumulador": "Termoacumulador (água quente elétrica)",
        "aquecimento_eletrico": "Aquecedores elétricos",
        "ar_condicionado": "Ar condicionado",
        "maquina_secar": "Máquina de secar roupa",
        "placa_eletrica": "Placa elétrica / indução",
        "carro_eletrico": "Carro elétrico",
    }
    # guardados no perfil: não se perdem ao mudar de página
    extras = {chave: pf.campo(st.checkbox, rotulo, f"eq_{chave}", f"e_{chave}", padrao=False)
              for chave, rotulo in equipamentos.items()}

p = pf.perfil()
consumo_mensal = consumo * 30 / dias          # a fatura pode ter 28, 31 ou 60 dias
perfil_casa = eficiencia.Perfil(consumo_mensal_kwh=consumo_mensal, pessoas=int(pessoas),
                                opcao=p.get("opcao", "simples"),
                                indexado=p.get("modalidade") == "indexado", **extras)
nivel = eficiencia.nivel_consumo(perfil_casa)
dicas = eficiencia.dicas_para(perfil_casa)

with direita:
    st.subheader("Dicas para ti")
    por_pessoa = consumo_mensal / max(int(pessoas), 1)
    st.caption(f"{ui.numero(por_pessoa)} kWh por pessoa por mês · consumo "
               f"{NIVEL_TEXTO[nivel]} para o tamanho da casa. As dicas estão ordenadas "
               "pelo impacto provável.")
    blocos = []
    for d in dicas:
        classe, rotulo = IMPACTO[d.impacto]
        blocos.append(
            f'<div class="lc-card"><div class="lc-topo"><span class="lc-n">{escape(d.categoria.upper())}</span>'
            f'<span class="lc-badge {classe}">{rotulo}</span></div>'
            f'<h4>{escape(d.titulo)}</h4><p>{escape(d.texto)}</p></div>')
    ui.grelha(blocos, largura_min=240)

st.write("")
st.subheader("Quanto poupas?")
st.caption("Escolhe quanto achas que consegues reduzir com as dicas que vais aplicar. "
           "A poupança usa os teus preços (da ferramenta Fatura).")
c1, c2, c3 = st.columns(3)
with c1:
    reducao = pf.campo(st.slider, "Redução do consumo (%)", "reducao_pct", "e_reducao",
                       padrao=10, min_value=0, max_value=50,
                       help="Quanto achas que consegues reduzir com as dicas que vais aplicar.")
with c2:
    custo_medida = pf.campo(st.number_input, "Custo das medidas (€)", "custo_medidas",
                            "e_custo", padrao=0.0, min_value=0.0, step=10.0,
                            help="Opcional: quanto gastas (ex.: lâmpadas, bomba de calor), "
                                 "para calcular em quanto tempo se paga.")
with c3:
    st.caption(f"Preço da energia: {ui.preco(p['preco_energia'])} €/kWh · "
               f"potência: {ui.preco(p['preco_diario'])} €/dia · valores levados a um mês")

r = calculos.cenario_eficiencia(consumo, p["preco_energia"], p["preco_diario"], dias, reducao)
payback = calculos.payback_anos(custo_medida, r["poupanca_anual"]) if custo_medida else None
metricas = [
    ui.metrica("Consumo depois", ui.numero(r["consumo_depois"] * 30 / dias), "kWh/mês"),
    ui.metrica("kWh evitados", ui.numero(r["kwh_evitados"] * 30 / dias), "kWh/mês"),
    ui.metrica("Poupança por mês", ui.euros(r["poupanca_mensal"]), "€"),
    ui.metrica("Poupança por ano", ui.euros(r["poupanca_anual"]), "€", destaque=True),
]
if payback is not None:
    metricas.append(ui.metrica("Paga-se em", ui.numero(payback, 1), "anos"))
ui.grelha(metricas, largura_min=160)
