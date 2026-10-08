"""Recomendações a partir da fatura, das tarifas da ERSE e do mercado OMIE.

Tudo em € por mês (30 dias), sem IVA nem taxas, para comparar faturas de
períodos diferentes. Nada de nomes de comercializadores: para comparar ofertas
concretas, a recomendação aponta para o simulador oficial da ERSE.
"""
from dataclasses import dataclass

from nucleo import calculos, periodos, tarifas

SIMULADOR_ERSE = "https://simulador.precos.erse.pt/"
LIMIAR = 0.50            # € por mês: abaixo disto não vale a pena recomendar mudar
ESCALOES = tarifas.ESCALOES_KVA


@dataclass(frozen=True)
class Recomendacao:
    id: str
    titulo: str
    texto: str
    poupanca_mensal: object = None      # € / mês; positivo = poupa; None = informativa
    ligacao: str = ""


def _mes(valor, dias):
    return valor * 30 / dias if dias else 0.0


def _euros(v):
    return f"{v:,.2f}".replace(",", " ").replace(".", ",")


def _preco(v):
    return f"{v:.4f}".replace(".", ",")


def _kva(v):
    return f"{v:g}".replace(".", ",")


def recomendar(fatura, erse, medias_omie=None):
    """Lista de recomendações, das que mais poupam para as informativas.

    fatura: consumo_kwh, preco_energia, preco_diario, dias, kva, opcao e, se a fatura
    os tiver, pct_vazio/pct_ponta (perfil real do contador), precos_base
    {"energia", "potencia_dia"}, desconto_pct e, num indexado, modalidade="indexado"
    com perdas_pct e margem_kwh do contrato.

    Num indexado, a fatura mostra o mercado desse mês. Com o OMIE recente, a comparação
    com o preço fixo usa o custo com o mercado de agora e as condições do contrato.
    """
    consumo, dias, kva = fatura["consumo_kwh"], fatura["dias"], float(fatura["kva"])
    if not dias or consumo <= 0:
        return []
    atual = calculos.fatura_simplificada(consumo, fatura["preco_energia"],
                                         fatura["preco_diario"], dias)["total"]
    atual_m = _mes(atual, dias)
    recs = []

    tem_perfil = fatura.get("pct_vazio") is not None
    sem_ponta = tem_perfil and fatura.get("pct_ponta") is None   # fatura bi-horária: ponta desconhecida
    pct_vazio = fatura.get("pct_vazio") or 0.0
    pct_ponta = fatura.get("pct_ponta") or 0.0

    def entra(linha):
        """Opções que se podem comparar com o que a fatura diz do perfil."""
        if not tem_perfil:
            return linha["opcao"] == "simples"
        return not (sem_ponta and linha["opcao"] == "tri")

    reguladas = [l for l in tarifas.comparar_opcoes(consumo, pct_vazio, pct_ponta, dias, kva, erse)
                 if entra(l)]
    texto_perfil = (f"O teu contador mostra {round(pct_vazio)} % do consumo em vazio "
                    f"({periodos.texto_vazio_curto()})"
                    + (f" e {round(pct_ponta)} % em ponta" if not sem_ponta and pct_ponta > 0 else ""))
    melhor_reg = reguladas[0]
    melhor_reg_m = _mes(melhor_reg["total"], dias)
    nome_reg = periodos.NOMES[melhor_reg["opcao"]].lower()
    opcao_atual = fatura.get("opcao", "simples") if tem_perfil else "simples"

    # indexado: o mesmo contrato com o mercado de agora (energia do OMIE recente + potência do contrato)
    indexado = fatura.get("modalidade") == "indexado"
    linhas_idx, agora = [], ""
    ref_m = atual_m
    if indexado and medias_omie is not None:
        perdas, margem = fatura.get("perdas_pct") or 0.0, fatura.get("margem_kwh") or 0.0
        linhas_idx = [l for l in tarifas.comparar_opcoes(
                          consumo, pct_vazio, pct_ponta, dias, kva, erse, medias_omie=medias_omie,
                          perdas_pct=perdas, margem_eur_kwh=margem)
                      if l["modalidade"] == "indexado" and entra(l)]
        linha = next((l for l in linhas_idx if l["opcao"] == opcao_atual), linhas_idx[0])
        ref_m = _mes(linha["energia"] + fatura["preco_diario"] * dias, dias)
        agora = (f"Com estes números pagas cerca de {_euros(atual_m)} € por mês (sem IVA nem taxas); "
                 f"com o mercado dos últimos dias e as condições do teu contrato pagarias "
                 f"{_euros(ref_m)} €. ")
        faltam = [n for n, v in (("as perdas", perdas), ("a margem", margem)) if not v]
        if faltam:
            agora += (f"Esta conta não mostra {' nem '.join(faltam)} do contrato, porque não "
                      + ("as indicaste (ficaram a 0)" if len(faltam) > 1 or faltam == ["as perdas"]
                         else "a indicaste (ficou a 0)")
                      + ", por isso este é o valor mais baixo possível; o real será um pouco maior. ")

    # 1. a tarifa regulada face ao contrato atual (num indexado: face ao mercado de agora)
    diferenca = ref_m - melhor_reg_m
    pot_reg = tarifas.preco_potencia(erse, kva)
    if agora:
        if diferenca > LIMIAR:
            recs.append(Recomendacao(
                "regulada", "Com os preços desta semana, o preço fixo da tarifa regulada sai mais barato",
                f"{agora}Na tarifa regulada da ERSE (preço fixo) em {nome_reg} pagarias "
                f"{_euros(melhor_reg_m)} €, sem depender do mercado.", diferenca))
        elif diferenca < -LIMIAR:
            recs.append(Recomendacao(
                "regulada", "Com os preços desta semana, o teu indexado fica abaixo do preço fixo",
                f"{agora}Na tarifa regulada da ERSE (preço fixo) seriam {_euros(melhor_reg_m)} €. "
                "Com o mercado atual, o indexado compensa; o preço fixo só protege se o mercado subir.",
                None))
        else:
            recs.append(Recomendacao(
                "regulada", "Estás praticamente igual à tarifa regulada",
                f"{agora}A melhor opção da tarifa regulada da ERSE (preço fixo, {nome_reg}) "
                f"custaria {_euros(melhor_reg_m)} €. Hoje não há poupança em mudar.", None))
    elif diferenca > LIMIAR:
        recs.append(Recomendacao(
            "regulada", "A tarifa regulada sai mais barata",
            f"Com o teu consumo, a tarifa regulada da ERSE (preço fixo) em {nome_reg} custaria cerca de "
            f"{_euros(melhor_reg_m)} € por mês, contra {_euros(atual_m)} € agora.", diferenca))
    elif diferenca < -LIMIAR:
        recs.append(Recomendacao(
            "regulada", "O teu preço está abaixo da tarifa regulada",
            f"Pagas cerca de {_euros(atual_m)} € por mês; na tarifa regulada da ERSE (preço fixo) seriam "
            f"{_euros(melhor_reg_m)} €. Com estes preços, mudar para a regulada não compensa.",
            None))
    else:
        recs.append(Recomendacao(
            "regulada", "Estás praticamente igual à tarifa regulada",
            f"Pagas cerca de {_euros(atual_m)} € por mês; a melhor opção da tarifa regulada da "
            f"ERSE (preço fixo, {nome_reg}) custaria {_euros(melhor_reg_m)} €. Hoje não há poupança "
            "em mudar.",
            None))

    # 2. potência cara face à regulada
    if fatura["preco_diario"] > pot_reg * 1.15:
        excesso = (fatura["preco_diario"] - pot_reg) * 30
        energia_reg = tarifas.precos_fixos(erse, kva)["simples"]["simples"]
        compensa = (f" Em compensação, a tua energia ({_preco(fatura['preco_energia'])} € por kWh) é mais "
                    f"barata do que a regulada ({_preco(energia_reg)} € por kWh)."
                    if fatura["preco_energia"] < energia_reg else "")
        # informativa: a poupança real depende do preço da energia de cada oferta
        recs.append(Recomendacao(
            "potencia_cara", "A tua potência está cara",
            f"Pagas {_preco(fatura['preco_diario'])} € por dia pela potência de {_kva(kva)} kVA; na "
            f"tarifa regulada são {_preco(pot_reg)} € por dia, cerca de {_euros(excesso)} € por mês a "
            f"menos.{compensa} Ao comparar ofertas, olha para os dois preços.", None))

    # 3. opção horária (só com o perfil real da fatura)
    if tem_perfil and linhas_idx:
        # indexado: as outras opções com o mesmo mercado, perdas e margem do contrato
        melhor_idx = linhas_idx[0]
        linha_atual = next((l for l in linhas_idx if l["opcao"] == opcao_atual), melhor_idx)
        ganho = _mes(linha_atual["total"] - melhor_idx["total"], dias)
        if melhor_idx["opcao"] != opcao_atual and ganho > LIMIAR:
            nome_idx = periodos.NOMES[melhor_idx["opcao"]].lower()
            recs.append(Recomendacao(
                "opcao", f"No indexado, o teu perfil favorece o {nome_idx}",
                f"{texto_perfil}. Com o mercado dos últimos dias e as condições do teu contrato, o {nome_idx} sairia "
                f"{_euros(ganho)} € por mês mais barato do que o "
                f"{periodos.NOMES[opcao_atual].lower()}. Se a tua empresa tiver "
                f"{nome_idx} indexado, pede o preço e compara.", None))
    elif tem_perfil:
        simples_reg = next(l for l in reguladas if l["opcao"] == "simples")
        ganho = _mes(simples_reg["total"] - melhor_reg["total"], dias)
        atual_opcao = fatura.get("opcao", "simples")
        if melhor_reg["opcao"] != atual_opcao and ganho > LIMIAR:
            # informativa: compara duas opções da regulada, não o teu contrato (cujo tri não se conhece)
            recs.append(Recomendacao(
                "opcao", f"O teu perfil favorece o {nome_reg}",
                f"{texto_perfil}. Na tarifa regulada, o {nome_reg} sai {_euros(ganho)} € por mês mais barato do que o "
                f"simples. Se a tua empresa tiver {nome_reg}, pede o preço e compara.",
                None))
    else:
        recs.append(Recomendacao(
            "perfil", "Descobre se o bi ou tri-horário compensa",
            "Se já estás em bi ou tri-horário, a fatura mostra quanto gastas em cada período. No simples, "
            "com contador inteligente, encontras esses dados no Balcão Digital da E-REDES: carrega-os no "
            "quadro «Consumos do contador inteligente (E-REDES)», no topo de «A minha fatura», ou "
            "experimenta em «Bi-horário compensa?».",
            None))

    # 4. indexado com o mercado recente (limite mínimo: sem perdas nem margem), para contratos fixos
    if medias_omie is not None and not indexado:
        indexadas = [l for l in tarifas.comparar_opcoes(consumo, pct_vazio, pct_ponta, dias, kva,
                                                        erse, medias_omie=medias_omie)
                     if l["modalidade"] == "indexado" and entra(l)]
        melhor_idx_m = _mes(indexadas[0]["total"], dias)
        if melhor_idx_m < atual_m - LIMIAR:
            recs.append(Recomendacao(
                "indexado", "Um tarifário indexado pode compensar",
                f"Com os preços do mercado da eletricidade dos últimos dias, um indexado custaria a partir de "
                f"{_euros(melhor_idx_m)} € por mês, contra {_euros(atual_m)} € agora. As ofertas "
                "reais somam as perdas na rede e uma margem, por isso a poupança real será menor; "
                "e o preço acompanha o mercado, que pode subir.", None))
        else:
            recs.append(Recomendacao(
                "indexado", "Com o mercado atual, o indexado não compensa",
                f"Mesmo sem perdas nem margem, um indexado custaria cerca de {_euros(melhor_idx_m)} € "
                f"por mês com os preços do mercado dos últimos dias, contra {_euros(atual_m)} € agora.",
                None))

    # 4b. indexado: o preço muda ao longo do dia
    if indexado:
        recs.append(Recomendacao(
            "horas_baratas", "Aproveita as horas baratas do mercado",
            "Se o teu indexado cobra cada hora (ou cada 15 minutos) ao preço do mercado, põe as máquinas e o "
            "cilindro da água quente a trabalhar nas horas mais baratas, muitas vezes a meio do dia e de "
            "madrugada. A ferramenta «Preço hora a hora» mostra o mercado de hoje e, a partir do meio-dia, o de "
            "amanhã. Se o contrato usa a média do mês, mudar de hora não altera o preço.",
            None))

    # 5. campanha ou desconto temporário
    base = fatura.get("precos_base") or {}
    if base.get("energia") and base.get("potencia_dia"):
        sem = _mes(consumo * base["energia"] + base["potencia_dia"] * dias, dias)
        desconto = fatura.get("desconto_pct")
        rotulo = f"de {round(desconto)} % " if desconto else ""
        depois = (f" Nessa altura, a tarifa regulada ({_euros(melhor_reg_m)} €) poupava cerca de "
                  f"{_euros(sem - melhor_reg_m)} € por mês." if sem - melhor_reg_m > LIMIAR else
                  f" A tarifa regulada ficaria em {_euros(melhor_reg_m)} €.")
        recs.append(Recomendacao(
            "campanha", "Atenção ao fim da campanha",
            f"O teu preço inclui um desconto temporário{(' ' + rotulo.strip()) if rotulo else ''}. Sem ele pagarias cerca de "
            f"{_euros(sem)} € por mês ({_euros(sem - atual_m)} € a mais).{depois} Confirma até "
            "quando dura o desconto e volta a comparar nessa altura.", None))

    # 6. descer um escalão de potência (poupança na parte regulada)
    abaixo = [e for e in ESCALOES if e < kva]
    if abaixo:
        menor = abaixo[-1]
        poupa = (pot_reg - tarifas.preco_potencia(erse, menor)) * 30
        recs.append(Recomendacao(
            "descer_potencia", f"Precisas mesmo de {_kva(kva)} kVA?",
            f"Se raramente ligas vários aparelhos fortes ao mesmo tempo, descer para {_kva(menor)} kVA poupa cerca de "
            f"{_euros(poupa)} € por mês na tarifa regulada. Só compensa se não ligares muitos "
            "aparelhos ao mesmo tempo; se a luz for abaixo muitas vezes, volta a subir.",
            None))

    # 7. comparar comercializadores (sempre)
    recs.append(Recomendacao(
        "comercializador", "Compara as ofertas de todas as empresas",
        "O simulador da ERSE compara as ofertas de todas as empresas com os teus dados. Mudar "
        "de empresa é gratuito e não corta a luz; vê só se o teu contrato tem um prazo mínimo (fidelização).",
        None, SIMULADOR_ERSE))

    return sorted(recs, key=lambda r: (r.poupanca_mensal is None, -(r.poupanca_mensal or 0)))
