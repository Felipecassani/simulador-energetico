"""Ficheiro da E-REDES (FICTÍCIO, gerado aqui): dois dias de outubro, 15 em 15 minutos.

Consumo constante de 0,1 kWh por quarto de hora (= 0,4 kW), exceto das 19h00 às 19h15 do
1.º dia, com 1 kWh (pico de 4 kW). Total: 2 × 96 × 0,1 + 0,9 = 20,1 kWh.
Vazio (22h–8h) = 10 h por dia = 40 quartos × 0,1 × 2 dias = 8 kWh → 39,8 %.
"""
import io
from datetime import datetime, timedelta, timezone

import pytest
from openpyxl import Workbook

from nucleo import eredes

aprox = pytest.approx


def _xlsx(em_kw=True, hora_no_fim=True):
    livro = Workbook()
    folha = livro.active
    folha.append(["CPE", "PT0000000000000000XX"])          # linhas antes do cabeçalho
    folha.append([])
    folha.append(["Data", "Hora", "Consumo registado (kW)" if em_kw else "Consumo (kWh)"])
    inicio = datetime(2026, 10, 1)
    for q in range(2 * 96):
        t = inicio + timedelta(minutes=15 * q)
        kwh = 1.0 if (q == 19 * 4) else 0.1
        marca = t + timedelta(minutes=15) if hora_no_fim else t
        dia = t.strftime("%Y/%m/%d")
        hora = "24:00" if hora_no_fim and marca.hour == 0 and marca.minute == 0 else marca.strftime("%H:%M")
        folha.append([dia, hora, kwh * 4 if em_kw else kwh])
    saida = io.BytesIO()
    livro.save(saida)
    return saida.getvalue()


@pytest.mark.parametrize("em_kw,hora_no_fim", [(True, True), (False, False)])
def test_le_e_analisa(em_kw, hora_no_fim):
    registos = eredes.ler("consumos.xlsx", _xlsx(em_kw, hora_no_fim))
    assert len(registos) == 192 and registos[0][0].hour == 0 and registos[0][0].minute == 0
    a = eredes.analisar(registos)
    assert a["total_kwh"] == aprox(20.1)
    assert a["dias"] == 2 and a["pico_kw"] == aprox(4.0)
    assert a["pct_vazio"] == aprox(100 * 8 / 20.1)


def test_csv_com_virgula_decimal():
    texto = "Data;Hora;Consumo (kWh)\n01/10/2026;00:00;0,25\n01/10/2026;00:15;0,5\n"
    registos = eredes.ler("c.csv", texto.encode())
    assert [k for _, k in registos] == [0.25, 0.5]


def test_preco_ponderado_pelo_consumo():
    registos = eredes.ler("c.csv", b"Data;Hora;Consumo (kWh)\n01/10/2026;00:00;1\n01/10/2026;00:15;3\n")
    t0 = registos[0][0].astimezone(timezone.utc)
    precos = [(t0, 100.0), (t0 + timedelta(minutes=15), 20.0)]
    r = eredes.preco_ponderado(registos, precos)
    assert r["ponderado"] == aprox((100 + 60) / 4) and r["simples"] == aprox(60)


def test_ficheiro_sem_colunas_da_erro_claro():
    with pytest.raises(ValueError, match="colunas"):
        eredes.ler("x.csv", b"a;b\n1;2\n")


def test_varios_ficheiros_juntam_sem_repetidos():
    from interface import carregar_eredes

    class F:
        def __init__(self, nome, dados):
            self.name, self._d = nome, dados

        def getvalue(self):
            return self._d

    a = F("a.csv", b"Data;Hora;Consumo (kWh)\n01/10/2026;00:00;1\n01/10/2026;00:15;2\n")
    # a começa às 00:00 (hora = início); b às 00:15 é lido como fim → 00:00 e 00:15: junta sem repetir
    b = F("b.csv", b"Data;Hora;Consumo (kWh)\n01/10/2026;00:15;2\n01/10/2026;00:30;3\n")
    mau = F("x.csv", b"isto;nao\n1;2\n")
    registos, falhados = carregar_eredes._juntar([a, b, mau])
    assert [k for _, k in registos] == [2, 3] and falhados == ["x.csv"]



def _como_a_eredes():
    """Estrutura igual à do ficheiro real (valores fictícios): fim do intervalo, 00:00 do dia seguinte."""
    livro = Workbook()
    folha = livro.active
    folha.title = "Dados de Energia"
    for linha in (["Dados Globais"], [""], ["CPE", "PT0000000000000000XX"], ["Funções", "Consumo registado"],
                  ["", "Estado"], ["Mês/Ano", "setembro 2026"], ["Intervalo:", "15 min"], [""]):
        folha.append(linha)
    folha.append(["Data", "Hora", "Consumo registado (kW)", "Estado"])
    inicio = datetime(2026, 9, 1)
    for q in range(1, 2 * 96 + 1):                  # fins de intervalo: 00:15 … 00:00 de 3/9
        fim = inicio + timedelta(minutes=15 * q)
        folha.append([fim.strftime("%Y/%m/%d"), fim.strftime("%H:%M"), "0,4", "Estimado" if q == 5 else "Real"])
    saida = io.BytesIO()
    livro.save(saida)
    return saida.getvalue()


def test_formato_real_da_eredes():
    registos = eredes.ler("Consumos_x.xlsx", _como_a_eredes())
    assert len(registos) == 192
    assert (registos[0][0].day, registos[0][0].hour, registos[0][0].minute) == (1, 0, 0)
    assert (registos[-1][0].day, registos[-1][0].hour, registos[-1][0].minute) == (2, 23, 45)
    assert eredes.ler.estimados == 1
    a = eredes.analisar(registos)
    assert a["total_kwh"] == aprox(192 * 0.1) and a["dias"] == 2
    assert a["pct_vazio"] == aprox(100 * 80 / 192)          # 22h–8h = 40 quartos por dia
