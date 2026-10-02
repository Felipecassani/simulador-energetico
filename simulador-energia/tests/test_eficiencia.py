"""Dicas de eficiência: aparecem as certas para cada casa."""
from nucleo import eficiencia as ef


def _ids(**kw):
    return [d.id for d in ef.dicas_para(ef.Perfil(**kw))]


def test_dicas_gerais_aparecem_sempre():
    ids = _ids(consumo_mensal_kwh=100, pessoas=2)
    assert {"standby", "led", "maquinas_eco", "frio"} <= set(ids)
    assert "termo_vazio" not in ids and "carro" not in ids


def test_dicas_conforme_os_equipamentos():
    ids = _ids(consumo_mensal_kwh=300, pessoas=2, termoacumulador=True, carro_eletrico=True)
    assert {"termo_vazio", "carro", "opcao_horaria"} <= set(ids)


def test_bi_horario_so_e_sugerido_a_quem_esta_em_simples():
    ids = _ids(consumo_mensal_kwh=300, pessoas=2, termoacumulador=True, opcao="bi")
    assert "opcao_horaria" not in ids


def test_ordenadas_por_impacto():
    ordem = {"alto": 0, "medio": 1, "baixo": 2}
    impactos = [ordem[d.impacto] for d in ef.dicas_para(ef.Perfil(
        consumo_mensal_kwh=500, pessoas=1, termoacumulador=True, aquecimento_eletrico=True))]
    assert impactos == sorted(impactos)


def test_nivel_consumo_devolve_um_nivel_valido():
    for kwh in (0, 50, 150, 400, 2000):
        assert ef.nivel_consumo(ef.Perfil(consumo_mensal_kwh=kwh, pessoas=2)) in ef.NIVEIS
