"""OMIE e ERSE: leitura dos ficheiros oficiais (fixtures reais, sem rede)."""
from datetime import datetime
from pathlib import Path

import pytest

from nucleo import mercado, periodos

DADOS = Path(__file__).resolve().parent / "dados"
aprox = pytest.approx


def _omie():
    return (DADOS / "marginalpdbcpt_20260930.1").read_text()


class TestOMIE:
    def test_96_quartos_de_hora_em_hora_de_portugal(self):
        precos = mercado.ler_omie(_omie())
        assert len(precos) == 96
        # o dia 30/09 de Espanha começa às 23:00 de 29/09 em Portugal
        assert precos[0][0] == datetime(2026, 9, 29, 23, 0, tzinfo=periodos.LISBOA)
        assert precos[-1][0] == datetime(2026, 9, 30, 22, 45, tzinfo=periodos.LISBOA)
        assert precos[0][1] == aprox(135.1)

    def test_resumo(self):
        r = mercado.resumo_omie(mercado.ler_omie(_omie()))
        assert r["n"] == 96
        assert r["min"] == aprox(85.6) and r["max"] == aprox(350.0)

    def test_dia_da_mudanca_de_hora(self):
        # 25/10/2026: o dia de Espanha tem 25 h (100 quartos); o último fica às 22:45 em Portugal
        linhas = "\n".join(f"2026;10;25;{p};100;100;" for p in range(1, 101))
        precos = mercado.ler_omie("MARGINALPDBCPT;\n" + linhas + "\n*")
        assert precos[0][0].hour == 23 and precos[0][0].day == 24
        assert precos[-1][0].strftime("%d %H:%M") == "25 22:45"

    def test_ficheiro_vazio_rejeitado(self):
        with pytest.raises(ValueError):
            mercado.ler_omie("MARGINALPDBCPT;\n*")

    def test_modo_offline_nao_vai_a_rede(self, monkeypatch):
        monkeypatch.setenv("SIMULADOR_OFFLINE", "1")
        with pytest.raises(mercado.SemRede):
            mercado.obter_omie(datetime(2026, 9, 30).date())


class TestERSE:
    def test_quadro_tar_igual_a_copia_local(self):
        lido = mercado.ler_quadro_erse((DADOS / "erse_2026_pag_tar.txt").read_text())
        local = mercado.carregar_erse_local(2026)["tar"]
        assert lido["energia_eur_kwh"] == local["energia_eur_kwh"]
        assert lido["potencia_eur_dia"] == local["potencia_eur_dia"]

    def test_quadro_regulado_e_escalao_ate_2_3_kva(self):
        texto = (DADOS / "erse_2026_pag_regulada.txt").read_text()
        grande = mercado.ler_quadro_erse(texto)
        pequena = mercado.ler_quadro_erse(texto, ordem=1, exigir_6_9=False)
        local = mercado.carregar_erse_local(2026)["regulada"]
        assert grande["energia_eur_kwh"] == local["energia_eur_kwh"]
        assert grande["potencia_eur_dia"]["6.9"] == aprox(0.3659)
        assert pequena["potencia_eur_dia"] == {"1.15": 0.0893, "2.3": 0.1500}
        assert pequena["energia_eur_kwh"]["simples"]["simples"] == local["energia_simples_ate_2_3_kva"]

    def test_valores_oficiais_2026(self):
        e = mercado.carregar_erse_local(2026)
        assert e["regulada"]["energia_eur_kwh"]["bi"] == {"fora_vazio": 0.1988, "vazio": 0.1087}
        assert e["tar"]["energia_eur_kwh"]["tri"]["ponta"] == aprox(0.2452)

    def test_diferencas(self):
        a = mercado.carregar_erse_local(2026)
        b = mercado.carregar_erse_local(2026)
        assert mercado.diferencas_erse(a, b) == []
        b["regulada"]["energia_eur_kwh"]["simples"]["simples"] = 0.2
        assert mercado.diferencas_erse(a, b) == ["regulada simples/simples"]


class TestPeriodos:
    def test_horas_por_dia(self):
        assert periodos.horas_por_periodo("bi") == {"vazio": 10, "fora_vazio": 14}
        inverno = periodos.horas_por_periodo("tri", datetime(2026, 1, 15, tzinfo=periodos.LISBOA))
        verao = periodos.horas_por_periodo("tri", datetime(2026, 7, 15, tzinfo=periodos.LISBOA))
        assert inverno == verao == {"vazio": 10, "cheias": 10, "ponta": 4}

    @pytest.mark.parametrize("mes,hora,minuto,esperado", [
        (1, 9, 30, "ponta"), (1, 12, 0, "cheias"), (1, 19, 0, "ponta"), (1, 23, 0, "vazio"),
        (7, 9, 30, "cheias"), (7, 11, 0, "ponta"), (7, 20, 0, "ponta"), (7, 7, 59, "vazio"),
    ])
    def test_tri_horario(self, mes, hora, minuto, esperado):
        instante = datetime(2026, mes, 15, hora, minuto, tzinfo=periodos.LISBOA)
        assert periodos.periodo(instante, "tri") == esperado

    def test_bi_horario_fronteiras(self):
        d = lambda h, m=0: datetime(2026, 3, 10, h, m, tzinfo=periodos.LISBOA)
        assert periodos.periodo(d(7, 59), "bi") == "vazio"
        assert periodos.periodo(d(8, 0), "bi") == "fora_vazio"
        assert periodos.periodo(d(21, 59), "bi") == "fora_vazio"
        assert periodos.periodo(d(22, 0), "bi") == "vazio"


def test_melhor_janela():
    from datetime import datetime, timedelta, timezone
    inicio = datetime(2026, 10, 1, tzinfo=timezone.utc)
    precos = [(inicio + timedelta(hours=h), v) for h, v in enumerate([90, 80, 30, 20, 40, 100, 10, 95])]
    ini, fim, media = mercado.melhor_janela(precos, 2)
    assert (ini.hour, fim.hour, media) == (2, 4, 25)            # 30 + 20 é melhor do que 10 + 95
    assert mercado.melhor_janela(precos, 2, depois_de=inicio + timedelta(hours=5))[2] == 52.5
    assert mercado.melhor_janela(precos, 10) is None
