"""Calendário energético: datas que mexem na fatura (Portugal continental).

Regras usadas (datas fixas ou calculadas; as que dependem de decisões são "previsão"):
  - Mudança de hora: último domingo de março (adianta) e de outubro (atrasa), à 1h UTC.
    Muda também o horário de verão/inverno do tri-horário.
  - Tarifas de eletricidade da ERSE: entram a 1 de janeiro. A proposta sai por volta de 15 de
    outubro e a decisão até 15 de dezembro (previsões).
  - Tarifas de gás natural da ERSE: o "ano gás" começa a 1 de outubro.
  - 2027: novos períodos horários aplicados instalação a instalação entre 1/7 e 31/12/2027
    (comunicado da ERSE de 31/07/2026; ver nucleo/periodos.py).
"""
from dataclasses import dataclass
from datetime import date, timedelta

CATEGORIAS = ("Eletricidade", "Gás", "Hora", "Regulação")


@dataclass(frozen=True)
class Evento:
    dia: date
    titulo: str
    texto: str
    categoria: str
    previsao: bool = False


def ultimo_domingo(ano, mes):
    fim = date(ano, mes + 1, 1) - timedelta(days=1) if mes < 12 else date(ano, 12, 31)
    return fim - timedelta(days=(fim.weekday() + 1) % 7)


def eventos(desde, meses=15):
    """Eventos de `desde` até `meses` à frente, por ordem de data."""
    ate = desde + timedelta(days=round(meses * 30.5))
    lista = []
    for ano in range(desde.year, ate.year + 1):
        lista += [
            Evento(ultimo_domingo(ano, 3), "Muda a hora (verão)",
                   "Os relógios adiantam 1 hora. O tri-horário passa para o horário de verão.", "Hora"),
            Evento(ultimo_domingo(ano, 10), "Muda a hora (inverno)",
                   "Os relógios atrasam 1 hora. O tri-horário passa para o horário de inverno.", "Hora"),
            Evento(date(ano, 1, 1), "Novas tarifas de eletricidade",
                   "Entram em vigor as tarifas da ERSE para o ano (tarifa regulada e acesso às redes). "
                   "Bom momento para voltar a comparar ofertas.", "Eletricidade"),
            Evento(date(ano, 10, 15), "Proposta de tarifas da ERSE",
                   "A ERSE propõe as tarifas de eletricidade do ano seguinte.", "Regulação", previsao=True),
            Evento(date(ano, 12, 15), "Decisão das tarifas da ERSE",
                   "A ERSE publica as tarifas finais do ano seguinte.", "Regulação", previsao=True),
            Evento(date(ano, 10, 1), "Novo ano gás",
                   "Entram em vigor as tarifas de gás natural da ERSE.", "Gás"),
        ]
    lista += [
        Evento(date(2027, 7, 1), "Começam os novos horários",
               "Entre julho e dezembro de 2027, cada instalação passa para os novos períodos horários: o "
               "vazio do bi-horário começa às 22h30 e o tri-horário deixa de ter verão e inverno.",
               "Regulação"),
        Evento(date(2027, 12, 31), "Fim da mudança de horários",
               "Todas as instalações ficam com os novos períodos horários.", "Regulação"),
    ]
    return sorted((e for e in lista if desde <= e.dia <= ate), key=lambda e: e.dia)
