"""Ferramenta 2 — Poupar em casa: dicas para a casa de cada pessoa e poupança estimada.

Para qualquer pessoa: quatro passos numerados (fatura → aparelhos → dicas → poupança),
frases curtas e nenhum valor sem explicar de onde vem.
"""
from html import escape

import streamlit as st

from interface import componentes as ui
from interface import perfil as pf
from nucleo import calculos, eficiencia, roteiro

passo = roteiro.passo(2)
ui.cabecalho_ferramenta(passo, roteiro.disponivel(2))
p = pf.perfil()
ui.aviso_fatura(p)

ui.nota("**Como usar esta página**\n\n"
            + ("1. Confirma os números da tua fatura.\n" if p.get("da_fatura")
               else "1. Escreve os números da tua fatura.\n") +
            "2. Marca os aparelhos que tens em casa.\n"
            "3. Lê as dicas: as que poupam mais aparecem primeiro.\n"
            "4. No fim, vê quanto podes poupar.", "Como usar esta página")

NIVEL_TEXTO = {"baixo": "baixo", "medio": "médio", "alto": "alto"}
# A dica que mais poupa fica a verde (o vermelho lembra erro) e a que menos poupa a cinzento
IMPACTO = {"alto": ("lc-ok", "Poupança grande"), "medio": ("lc-rever", "Poupança média"),
           "baixo": ("lc-todo", "Poupança pequena")}
# Nomes do dia a dia para as categorias das dicas (as de nucleo/ ficam iguais)
CATEGORIA = {"Climatização": "Aquecer e arrefecer", "Mobilidade": "Carro",
             "Diagnóstico": "Descobrir o que gasta", "Tarifa": "O teu contrato", "Iluminação": "Luz"}
# Dicas que mandam para outra ferramenta: a ligação aparece logo por baixo do cartão
LIGACOES = {"opcao_horaria": 5, "horas_baratas": 4}
# chave do perfil → (rótulo, ajuda)
EQUIPAMENTOS = {
    "termoacumulador": ("Termoacumulador ou cilindro (aquece a água do banho com eletricidade)",
                        "Se a água quente vem do gás, de esquentador ou caldeira, não marques."),
    "aquecimento_eletrico": ("Aquecedores elétricos (a óleo, ventiladores, convectores)",
                             "Os que ligas à tomada no inverno."),
    "ar_condicionado": ("Ar condicionado", "Para arrefecer no verão ou aquecer no inverno."),
    "maquina_secar": ("Máquina de secar roupa", None),
    "placa_eletrica": ("Placa de cozinhar elétrica ou de indução", "Se cozinhas a gás, não marques."),
    "carro_eletrico": ("Carro elétrico que carregas em casa", None),
}

esquerda, direita = st.columns([1, 1.6], gap="large")

with esquerda:
    st.subheader(":material/edit_note: 1. Os números da tua fatura")
    consumo = pf.campo(st.number_input, "Consumo da fatura (kWh)", "consumo_kwh", "e_consumo",
                       min_value=0.0, step=10.0, format="%.0f",
                       help="Na fatura, procura o consumo do período, por exemplo «Consumo: 258 kWh». "
                            "Não escrevas as leituras do contador, que são números grandes como "
                            "12 345: o consumo é a diferença entre as duas leituras. O kWh é a "
                            "unidade da eletricidade que gastas. Se já preencheste «A minha fatura», "
                            "este número vem de lá.")
    dias = pf.campo(st.number_input, "Dias da fatura", "dias", "e_dias", min_value=1, step=1,
                    help="Conta os dias entre as duas datas da fatura. Exemplo: de 1 a 31 de março "
                         "são 31 dias. Costuma aparecer perto de «Período de faturação». Serve para "
                         "fazer as contas a um mês.")
    if p.get("da_fatura"):
        ui.nota("Estes números vieram da tua fatura. Só mexe se estiverem errados.")
    else:
        ui.nota("Os dois números estão na fatura: o consumo em kWh e as datas «de … a …».")
    pessoas = pf.campo(st.number_input, "Pessoas que vivem na casa", "pessoas", "e_pessoas",
                       min_value=1, max_value=12, step=1,
                       help="Conta contigo. Serve para ver se gastas pouco ou muito para o tamanho "
                            "da família.")

    st.subheader(":material/home: 2. O que tens em casa")
    ui.nota("Marca só o que é elétrico e usas. Podes marcar vários ou nenhum. "
               "As dicas mudam conforme o que marcares.")
    # guardados no perfil: não se perdem ao mudar de página
    extras = {chave: pf.campo(st.checkbox, rotulo, f"eq_{chave}", f"e_{chave}", padrao=False, help=ajuda)
              for chave, (rotulo, ajuda) in EQUIPAMENTOS.items()}

consumo_mensal = consumo * 30 / dias          # a fatura pode ter 28, 31 ou 60 dias
perfil_casa = eficiencia.Perfil(consumo_mensal_kwh=consumo_mensal, pessoas=int(pessoas),
                                opcao=p.get("opcao", "simples"),
                                indexado=p.get("modalidade") == "indexado", **extras)
nivel = eficiencia.nivel_consumo(perfil_casa)
dicas = eficiencia.dicas_para(perfil_casa)


def _cartao(d):
    classe, rotulo = IMPACTO[d.impacto]
    # lc-aberto: o balão das palavras explicadas não fica cortado pelo cartão
    return (f'<div class="lc-card lc-aberto"><div class="lc-topo">'
            f'<span class="lc-n">{escape(CATEGORIA.get(d.categoria, d.categoria))}</span>'
            f'<span class="lc-badge {classe}">{rotulo}</span></div>'
            f'<h4>{escape(d.titulo)}</h4><p>{ui.com_glossario(d.texto)}</p></div>')


def _mostrar(lista):
    ui.grelha([_cartao(d) for d in lista], largura_min=240)
    for d in lista:
        if d.id in LIGACOES:
            destino = roteiro.passo(LIGACOES[d.id])
            st.page_link(destino.pagina, label=f"Abrir «{destino.titulo}»", icon=destino.icone)


with direita:
    st.subheader(":material/tips_and_updates: 3. Dicas para gastar menos")
    por_pessoa = consumo_mensal / max(int(pessoas), 1)
    n = int(pessoas)
    inicio = "Com estes números" if p.get("da_fatura") else "Com os números de exemplo"
    ui.texto(f"{inicio}, gastam-se cerca de **{ui.numero(por_pessoa)} kWh por pessoa, "
                f"num mês**. Para {n} {'pessoa' if n == 1 else 'pessoas'}, é um consumo "
                f"**{NIVEL_TEXTO[nivel]}**.")
    if not p.get("da_fatura"):
        ui.nota("Troca o exemplo pelos números da tua fatura para veres as dicas certas "
                   "para a tua casa.")
    ui.nota("As dicas que poupam mais aparecem primeiro.")
    ui.texto("**Começa por estas:**")
    _mostrar(dicas[:3])
    if len(dicas) > 3:
        resto = len(dicas) - 3
        with st.expander(f"Ver mais {resto} {'dica' if resto == 1 else 'dicas'}",
                         icon=":material/lightbulb:"):
            _mostrar(dicas[3:])

st.write("")
st.subheader(":material/savings: 4. Quanto podes poupar")
if p.get("da_fatura"):
    ui.nota("As contas usam os preços da tua fatura.")
else:
    ui.nota("Ainda sem fatura: as contas usam os preços oficiais de referência, "
               "os da tarifa regulada.")
coluna_slider, _ = st.columns([1, 1.6], gap="large")
with coluna_slider:
    reducao = pf.campo(st.slider, "Quanto achas que consegues gastar a menos?", "reducao_pct",
                       "e_reducao", padrao=10, min_value=0, max_value=50, format="%d %%",
                       help="10 % quer dizer gastar menos 1 kWh em cada 10. "
                            "Se não sabes, deixa nos 10 %.")

r = calculos.cenario_eficiencia(consumo, p["preco_energia"], p["preco_diario"], dias, reducao)
ui.nota("É uma estimativa, sem IVA nem taxas. Na fatura, a poupança é um pouco maior, "
        "porque o IVA também desce.", "É uma estimativa")
ui.grelha([
    ui.metrica("Poupas por ano", ui.euros(r["poupanca_anual"]), "€", destaque=True),
    ui.metrica("Poupas por mês", ui.euros(r["poupanca_mensal"]), "€"),
    ui.metrica("Gastas a menos", ui.numero(r["kwh_evitados"] * 30 / dias), "kWh por mês"),
    ui.metrica("Passas a gastar", ui.numero(r["consumo_depois"] * 30 / dias), "kWh por mês"),
], largura_min=180)
if reducao:
    ui.texto(f"Se gastares **{reducao} % menos**, pagas cerca de "
                f"**{ui.euros(r['poupanca_mensal'])} € a menos por mês**, ou "
                f"**{ui.euros(r['poupanca_anual'])} € por ano**.")
else:
    st.info("Escolhe acima quanto achas que consegues gastar a menos.", icon=":material/touch_app:")
em_media = p.get("opcao", "simples") != "simples" or p.get("modalidade") == "indexado"
ui.nota(f"Nestas contas, cada kWh custa{', em média,' if em_media else ''} "
           f"{ui.preco(p['preco_energia'])} €. A parte fixa da fatura, "
           "a potência, não muda, por isso não entra na poupança. Todos os valores são para um mês "
           "de 30 dias.")


def _tempo(anos):
    """2.5 → '2 anos e 6 meses' (só para mostrar; o cálculo fica em nucleo)."""
    meses_total = round(anos * 12)
    if meses_total < 1:
        return "menos de 1 mês"
    a, m = divmod(meses_total, 12)
    partes = ([f"{ui.numero(a)} {'ano' if a == 1 else 'anos'}"] if a else []) + \
             ([f"{m} {'mês' if m == 1 else 'meses'}"] if m else [])
    return " e ".join(partes)


with st.expander("Vais comprar alguma coisa? Vê em quanto tempo se paga", icon=":material/savings:"):
    c1, c2 = st.columns(2, gap="large")
    with c1:
        custo_medida = pf.campo(st.number_input, "Quanto custa o que vais comprar (€)", "custo_medidas",
                                "e_custo", padrao=0.0, min_value=0.0, step=10.0,
                                help="Por exemplo, lâmpadas LED, uma extensão com interruptor ou um "
                                     "aparelho novo. Mostramos em quanto tempo esse dinheiro volta "
                                     "com a poupança. Se não vais comprar nada, deixa 0.")
    payback = calculos.payback_anos(custo_medida, r["poupanca_anual"]) if custo_medida else None
    with c2:
        if payback is not None:
            ui.grelha([ui.metrica("O dinheiro volta em", _tempo(payback), destaque=True)],
                      largura_min=200)
            ui.nota(f"Gastas {ui.euros(custo_medida)} € e poupas {ui.euros(r['poupanca_anual'])} € "
                       "por ano.")
        elif custo_medida:
            ui.nota("Sem poupança, o dinheiro gasto não volta. Escolhe acima quanto achas que "
                       "consegues gastar a menos.")
        else:
            ui.nota("Escreve quanto custa e vês aqui em quanto tempo o dinheiro volta.")
