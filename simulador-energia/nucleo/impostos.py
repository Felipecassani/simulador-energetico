"""IVA, taxas e encargos da fatura de eletricidade (Portugal continental, baixa tensão normal).

Valores de 2026, conferidos linha a linha com uma fatura real (o total bate ao cêntimo):
  - Contribuição audiovisual (CAV): 2,85 € por mês, IVA 6 %
  - Taxa de exploração da DGEG: 0,07 € por mês, IVA 23 %
  - Imposto especial de consumo (IEC): 0,001 €/kWh, IVA 23 %
  - Encargo de financiamento da tarifa social: 0,0020666 €/kWh (Diretiva ERSE 12-A/2025),
    com o IVA repartido como a energia
  - IVA da energia: 6 % nos primeiros 200 kWh por 30 dias (300 para famílias numerosas) até
    6,9 kVA; o resto a 23 %
  - IVA da potência: 6 % até 3,45 kVA; acima, 23 %
CAV e DGEG são por mês faturado: um período de 31 dias paga 1 mês.
"""
IVA_NORMAL = 0.23
IVA_REDUZIDO = 0.06
CAV_MES = 2.85
DGEG_MES = 0.07
IEC_KWH = 0.001
TARIFA_SOCIAL_KWH = 0.0020666
KWH_IVA_REDUZIDO = 200            # por 30 dias
KWH_IVA_REDUZIDO_FAMILIA = 300
KVA_ENERGIA_REDUZIDA = 6.9
KVA_POTENCIA_REDUZIDA = 3.45


def meses_faturados(dias):
    return max(1, round(dias / 30.4))


def com_impostos(energia, potencia, kwh, dias, kva, familia_numerosa=False):
    """Total da fatura com taxas e IVA, a partir do custo sem IVA da energia e da potência.

    Devolve {"sem_iva", "taxas", "iva", "total"} em € para o período.
    """
    meses = meses_faturados(dias)
    limite = (KWH_IVA_REDUZIDO_FAMILIA if familia_numerosa else KWH_IVA_REDUZIDO) * dias / 30
    kwh_reduzido = min(kwh, limite) if kva <= KVA_ENERGIA_REDUZIDA else 0.0
    parte_reduzida = kwh_reduzido / kwh if kwh else 0.0

    cav, dgeg = CAV_MES * meses, DGEG_MES * meses
    iec, social = IEC_KWH * kwh, TARIFA_SOCIAL_KWH * kwh
    base_6 = (energia + social) * parte_reduzida + cav
    base_23 = (energia + social) * (1 - parte_reduzida) + dgeg + iec
    if kva <= KVA_POTENCIA_REDUZIDA:
        base_6 += potencia
    else:
        base_23 += potencia
    iva = base_6 * IVA_REDUZIDO + base_23 * IVA_NORMAL
    taxas = cav + dgeg + iec + social
    sem_iva = energia + potencia + taxas
    return {"sem_iva": sem_iva, "taxas": taxas, "iva": iva, "total": sem_iva + iva}
