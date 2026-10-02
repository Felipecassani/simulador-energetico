"""Os dados da pessoa, partilhados entre ferramentas durante a visita.

Ficam só na sessão do browser (st.session_state): nada é gravado em disco.
Sem fatura, os valores iniciais são os da tarifa regulada da ERSE para 6,9 kVA.
Quando uma fatura é carregada, `carregar_fatura()` põe os valores dela no perfil e
sobe a revisão: todos os campos de todas as páginas nascem de novo com esses valores.
"""
import streamlit as st

from interface.dados import erse

PADRAO = {
    "consumo_kwh": 300.0,
    "dias": 30,
    "kva": 6.9,
    "opcao": "simples",
    "modalidade": "fixo",          # fixo · indexado
    "pct_vazio": 40.0,
    "pct_ponta": 15.0,
    "pessoas": 2,
    "perdas_pct": 0.0,             # só no indexado (vem da fatura ou do contrato)
    "margem_kwh": 0.0,
    "perfil_da_fatura": False,     # True quando a repartição vazio/ponta veio do contador
    "da_fatura": False,            # True depois de carregar uma fatura
}

ESCALOES_KVA = [1.15, 2.3, 3.45, 4.6, 5.75, 6.9, 10.35, 13.8, 17.25, 20.7]


def _precos_regulados(kva):
    """Preços da tarifa regulada (simples) para a potência: o ponto de partida sem fatura."""
    from nucleo import tarifas
    tarifa = erse()
    return {"preco_energia": tarifas.precos_fixos(tarifa, kva)["simples"]["simples"],
            "preco_diario": tarifas.preco_potencia(tarifa, kva)}, f"tarifa regulada ERSE {tarifa['ano']}"


def perfil():
    """Dicionário do perfil desta sessão (criado com os valores iniciais).

    Um preço em falta (ex.: uma fatura de onde não se conseguiu ler o preço) é preenchido com o
    da tarifa regulada e marcado em "precos_em_falta", para a página pedir que o confirmem.
    """
    if "perfil" not in st.session_state:
        base = dict(PADRAO)
        precos, fonte = _precos_regulados(base["kva"])
        base.update(precos, fonte=fonte)
        st.session_state["perfil"] = base
    p = st.session_state["perfil"]
    faltam = [k for k in ("preco_energia", "preco_diario") if p.get(k) is None]
    if faltam:
        precos, _ = _precos_regulados(p.get("kva") or PADRAO["kva"])
        p.update({k: precos[k] for k in faltam})
        ja = set(p.get("precos_em_falta", [])) | set(faltam)
        p["precos_em_falta"] = [k for k in ("preco_energia", "preco_diario") if k in ja]
    for k, v in PADRAO.items():                 # nenhum valor obrigatório fica vazio
        if p.get(k) is None:
            p[k] = v
    return p


def revisao():
    return st.session_state.setdefault("perfil_rev", 0)


def atualizar(**valores):
    perfil().update(valores)


def carregar_fatura(valores):
    """Põe os valores de uma fatura no perfil e renova todos os campos do site."""
    base = dict(PADRAO)                        # nada de valores de uma fatura anterior
    base.update({k: v for k, v in perfil().items() if k in ("pessoas",) or k.startswith(
        ("oferta_", "eq_", "reducao", "custo"))})   # o que a fatura não diz fica como estava
    base.update(valores)
    base.pop("precos_em_falta", None)
    for chave in ("preco_energia", "preco_diario"):   # sem preço na fatura → o da tarifa regulada
        if base.get(chave) is None:
            base[chave] = None                         # perfil() preenche e avisa
    analise = st.session_state.get("eredes_analise")
    if analise:                                # a repartição real da E-REDES vale mais do que a da fatura
        base.update(pct_vazio=round(analise["pct_vazio"], 1), pct_ponta=round(analise["pct_ponta"], 1),
                    perfil_da_fatura=True, ponta_na_fatura=True)
    base["da_fatura"] = True
    base["fonte"] = "a tua fatura"
    st.session_state["perfil"] = base
    st.session_state["perfil_rev"] = revisao() + 1


def aplicar(**valores):
    """Muda valores do perfil e renova os campos (para refletir uma mudança feita por código)."""
    perfil().update(valores)
    st.session_state["perfil_rev"] = revisao() + 1


def chave(key):
    """Key do widget com a revisão atual (mudar de revisão recria o campo no browser)."""
    return f"{key}__{revisao()}"


def campo(widget, rotulo, chave_perfil, key, padrao=None, **opcoes):
    """Desenha um campo ligado ao perfil: começa com o valor do perfil e grava-o de volta.

    O valor fica no perfil (e não só no campo), por isso passa entre páginas.
    `padrao` é o valor inicial de chaves que não estão em PADRAO.
    """
    p = perfil()
    p.setdefault(chave_perfil, padrao)
    k = chave(key)
    if k not in st.session_state:
        st.session_state[k] = p[chave_perfil]
    valor = widget(rotulo, key=k, **opcoes)
    p[chave_perfil] = valor
    return valor
