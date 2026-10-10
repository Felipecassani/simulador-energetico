"""Estimativa do consumo a partir dos aparelhos da casa (para quem não tem a fatura à mão).

kWh por mês = potência (W) ÷ 1000 × horas de uso por dia × 30 dias.
Os valores típicos são ordens de grandeza de uso doméstico: a pessoa confirma a potência na
etiqueta do aparelho e ajusta as horas ao seu caso. Os que ficam sempre ligados (frigorífico,
router) já contam o tempo em que o motor/compressor está realmente a trabalhar.
"""
from dataclasses import dataclass

DIAS_MES = 30


@dataclass(frozen=True)
class Aparelho:
    nome: str
    emoji: str
    potencia_w: float      # potência típica, em W
    horas_dia: float       # horas de uso por dia (média do mês)
    comum: bool = True     # vem marcado por omissão (quase todas as casas têm)


APARELHOS = [
    Aparelho("Frigorífico", "🧊", 150, 8),
    Aparelho("Arca congeladora", "❄️", 120, 8, comum=False),
    Aparelho("Máquina de lavar roupa", "👕", 2000, 0.5),
    Aparelho("Máquina de secar roupa", "🌀", 2500, 0.4, comum=False),
    Aparelho("Máquina de lavar loiça", "🍽️", 1800, 0.5, comum=False),
    Aparelho("Forno elétrico", "🍕", 2000, 0.3),
    Aparelho("Placa elétrica ou de indução", "🍳", 2000, 0.7, comum=False),
    Aparelho("Micro-ondas", "📦", 1000, 0.2),
    Aparelho("Termoacumulador (água quente)", "🚿", 2000, 2, comum=False),
    Aparelho("Aquecedor elétrico", "🔥", 1500, 2, comum=False),
    Aparelho("Ar condicionado", "🌬️", 1200, 2, comum=False),
    Aparelho("Televisão", "📺", 100, 4),
    Aparelho("Computador", "💻", 80, 4),
    Aparelho("Router e boxes (sempre ligados)", "📶", 20, 24),
    Aparelho("Iluminação (lâmpadas LED)", "💡", 60, 5),
    Aparelho("Ferro de engomar", "👔", 2000, 0.2, comum=False),
    Aparelho("Carro elétrico (carregar em casa)", "🚗", 2300, 2, comum=False),
]


def kwh_mes(potencia_w, horas_dia):
    """kWh por mês de um aparelho. Valores negativos são tratados como zero."""
    return max(0.0, potencia_w) / 1000 * max(0.0, horas_dia) * DIAS_MES


def estimar(linhas):
    """Total por mês e o detalhe por aparelho.

    linhas: [(nome, usar, potencia_w, horas_dia)] — só contam as marcadas.
    Devolve (total_kwh_mes, [(nome, kwh_mes)] do maior para o menor).
    """
    detalhe = [(nome, kwh_mes(w, h)) for nome, usar, w, h in linhas if usar]
    detalhe.sort(key=lambda par: par[1], reverse=True)
    return sum(k for _, k in detalhe), detalhe
