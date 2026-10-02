from datetime import date

from nucleo import calendario


def test_mudancas_de_hora():
    assert calendario.ultimo_domingo(2026, 10) == date(2026, 10, 25)
    assert calendario.ultimo_domingo(2027, 3) == date(2027, 3, 28)
    assert calendario.ultimo_domingo(2026, 12) == date(2026, 12, 27)


def test_eventos_ordenados_e_dentro_do_intervalo():
    lista = calendario.eventos(date(2026, 10, 1), meses=15)
    dias = [e.dia for e in lista]
    assert dias == sorted(dias) and dias[0] >= date(2026, 10, 1)
    titulos = [e.titulo for e in lista]
    assert "Muda a hora (inverno)" in titulos and "Novas tarifas de eletricidade" in titulos
    assert any(e.previsao for e in lista)
