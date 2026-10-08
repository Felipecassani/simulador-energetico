"""Textos do site: Guia, Perguntas frequentes, secções em construção e o autor.

Escrito para qualquer pessoa (tu, português de Portugal), sem fórmulas.
Os horários vêm de nucleo/periodos para não haver dois sítios a dizer coisas diferentes.
"""
from dataclasses import dataclass

from nucleo import periodos

AUTOR = {
    "nome": "Luiz Cassani",
    "linha": "Programação, eletrónica e automação da casa.",
    "ligacoes": [
        ("GitHub", "https://github.com/Felipecassani", "codigo"),
        ("LinkedIn", "https://www.linkedin.com/in/luizfelipecassani/", "linkedin"),
    ],
}

VAZIO = periodos.texto_vazio_curto()

GUIA = [
    ("Por onde começar",
     "Pega na tua última fatura da luz e abre «A minha fatura». Em poucos minutos vês quanto pagas, "
     "para onde vai o dinheiro e se há ofertas mais baratas. Depois, se quiseres, vê as dicas de "
     "«Poupar em casa» e se o bi-horário compensa para ti."),
    ("O que pagas numa fatura",
     "A fatura tem duas partes principais. A energia é o que consomes, em kWh, a um preço por kWh. "
     "A potência é um valor fixo por dia, que depende da potência contratada. Por cima vêm as taxas "
     "e impostos: IVA, contribuição audiovisual, taxa da DGEG e imposto especial de consumo. "
     "Este simulador compara os valores sem IVA nem taxas: as taxas são iguais em todas as ofertas "
     "e o IVA acompanha o preço, por isso quase nunca muda qual é a oferta mais barata."),
    ("Potência contratada",
     "É a potência máxima que podes usar ao mesmo tempo, em kVA. Numa casa vai de 1,15 a 20,7 kVA; "
     "os valores mais comuns são 3,45, 4,6 e 6,9 kVA. Quanto maior, mais pagas por dia, mesmo sem consumir. Se o quadro nunca "
     "dispara, talvez possas descer um escalão; se ligas muitas vezes forno, placa e máquinas ao "
     "mesmo tempo, mantém a que tens."),
    ("Opções horárias",
     f"No simples, o preço é igual a qualquer hora. No bi-horário, as horas de vazio ({VAZIO}) são "
     "mais baratas e as restantes mais caras. No tri-horário há vazio, cheias e ponta, e a ponta "
     "(a mais cara) muda entre o inverno e o verão. Compensa mudar quando grande parte do consumo "
     "é feita no vazio. Em «Bi-horário compensa?» fazes a conta com o teu consumo."),
    ("Preço fixo ou indexado",
     "Com preço fixo, o kWh custa sempre o mesmo durante o contrato. Com preço indexado, acompanha o "
     "mercado (OMIE), como a gasolina na bomba: há semanas mais barato e outras mais caro. Ao preço do "
     "mercado, a empresa soma as perdas na rede, a sua margem e as tarifas de acesso às redes. "
     "O indexado costuma compensar quando o mercado está baixo; em troca, arriscas pagar mais se o "
     "mercado subir."),
    ("Tarifa regulada",
     "É o preço fixo definido pela ERSE, a entidade reguladora, normalmente uma vez por ano. Podes "
     "aderir a ela através de um comercializador de último recurso. Serve de referência: "
     "se pagas mais do que a regulada, vale a pena comparar ofertas. Em «A minha fatura» vês "
     "sempre esta comparação."),
    ("Campanhas e descontos",
     "Muitas ofertas têm descontos temporários. A fatura costuma mostrar o preço sem desconto: "
     "confirma até quando dura a campanha e volta a comparar nessa altura."),
    ("Mudar de comercializador",
     "Mudar é gratuito, não corta a luz e não muda o contador. Antes de mudar, vê se o contrato "
     "atual tem fidelização. O simulador oficial da ERSE compara as ofertas de todas as empresas."),
    ("Poupar sem mudar de contrato",
     "Desliga os aparelhos em standby, usa iluminação LED, põe as máquinas a trabalhar cheias e em "
     "programas eco, e seca a roupa ao ar sempre que der. Em «Poupar em casa» vês as dicas "
     "que mais contam para o teu consumo."),
]

FAQ = [
    ("Por onde começo?",
     "Pega na tua última fatura da luz e abre «A minha fatura», no menu Ferramentas, em cima. No "
     "telemóvel, o menu abre no botão «Menu», ao lado do logótipo. Carregas o PDF ou uma foto, ou "
     "escreves os números, e vês logo quanto pagas e que ofertas te saem mais baratas."),
    ("Qual é a diferença entre kWh e kVA?",
     "O kWh é quanto gastas, como os litros de água que passam pelo contador num mês. O kVA é a "
     "largura do cano: quantos aparelhos podes ter ligados ao mesmo tempo. Pagas os kWh que gastas e "
     "a potência todos os dias, mesmo sem gastar."),
    ("Preciso de criar conta ou de pagar?",
     "Não. O simulador é gratuito e não tem contas."),
    ("O que acontece aos dados que escrevo ou à fatura que carrego?",
     "A fatura é lida só para preencher os campos e não é guardada. Os valores passam entre as "
     "ferramentas enquanto estás no site e desaparecem quando fechas ou recarregas a página."),
    ("A leitura da fatura falhou ou leu um valor errado. E agora?",
     "Corrige ou preenche os campos à mão: o resultado atualiza na hora. Faturas em foto leem-se "
     "melhor com boa luz e a folha direita."),
    ("De onde vêm os preços?",
     "Da tua fatura, da tarifa regulada publicada pela ERSE e do mercado ibérico (OMIE). "
     "Os preços do mercado para o dia seguinte saem por volta do meio-dia (hora de Portugal continental)."),
    ("Porque é que o total não é igual ao da minha fatura?",
     "Porque, para comparar empresas, o simulador mostra os valores sem IVA nem taxas, que são iguais "
     "em todas as ofertas. Em «A minha fatura», liga «Incluir IVA e taxas» para veres o total como "
     "vem na fatura. Arredondamentos e acertos de leituras também podem dar pequenas diferenças."),
    ("A tarifa regulada é de preço fixo ou indexado?",
     "De preço fixo: a ERSE define os preços para o ano inteiro."),
    ("Como sei se a minha fatura é de preço fixo ou indexado?",
     "Uma fatura indexada fala do mercado (OMIE), de perdas e de uma margem ou custo de gestão, e o "
     "preço por kWh muda de mês para mês. Ao carregar a fatura, o simulador tenta perceber sozinho; "
     "podes sempre mudar em «A minha fatura»."),
    ("Quando é que o bi-horário compensa?",
     f"Quando uma boa parte do consumo cai no vazio ({VAZIO}). Se já estás em bi ou tri-horário, a "
     "fatura mostra essa repartição; no simples, com contador inteligente, vês os consumos no Balcão "
     "Digital da E-REDES. Depois indica-a em «Bi-horário compensa?»."),
    ("Mudar de comercializador corta a luz?",
     "Não. A rede, o contador e a qualidade do serviço são os mesmos; muda só quem te fatura. "
     "Vê apenas se o contrato atual tem fidelização."),
    ("As recomendações são uma garantia de poupança?",
     "Não. São estimativas com os teus dados e os preços oficiais. Confirma sempre as condições na "
     "ficha da oferta antes de decidir."),
]


@dataclass(frozen=True)
class EmConstrucao:
    chave: str
    titulo: str
    icone: str
    emoji: str
    descricao: str
    planos: tuple


EM_CONSTRUCAO = [
    EmConstrucao("gas", "Gás natural", ":material/local_fire_department:", "🔥",
                 "Simular a fatura do gás e comparar a tarifa regulada com as ofertas do mercado.",
                 ("Consumo em kWh ou em metros cúbicos", "Escalões de consumo",
                  "Comparação com a tarifa regulada")),
    EmConstrucao("gas-eletricidade", "Gás + eletricidade", ":material/join_inner:", "🔗",
                 "Juntar as duas faturas e ver se um pacote dual compensa.",
                 ("As duas faturas lado a lado", "Custo total por mês e por ano")),
    EmConstrucao("fotovoltaico", "Fotovoltaico", ":material/solar_power:", "☀️",
                 "Quantos painéis fazem sentido para o teu consumo, quanto poupas e quando recuperas "
                 "o investimento.",
                 ("Produção estimada para a tua zona", "Autoconsumo e excedente",
                  "Tempo de retorno do investimento")),
    EmConstrucao("regulamentacao", "Regulamentação", ":material/gavel:", "⚖️",
                 "As regras do setor explicadas de forma simples.",
                 ("Tarifas de acesso às redes", "Tarifa social", "Perdas na rede")),
    EmConstrucao("europa", "Europa", ":material/public:", "🇪🇺",
                 "Comparar os preços da eletricidade em Portugal com os outros países europeus.",
                 ("Preços por país", "Evolução ao longo do ano")),
    EmConstrucao("mercado", "Mercado", ":material/candlestick_chart:", "📈",
                 "Histórico do mercado ibérico e as horas mais baratas de cada dia.",
                 ("Histórico do OMIE", "Melhor janela horária do dia", "Preços futuros")),
    EmConstrucao("producao", "Produção", ":material/factory:", "🏭",
                 "De onde vem a eletricidade de cada dia.",
                 ("Renováveis, gás e importação", "Balanço diário")),
]


def em_construcao(chave):
    return next(e for e in EM_CONSTRUCAO if e.chave == chave)


# termo → (categoria, definição curta). Os termos aparecem sublinhados no Guia e nas Perguntas
# frequentes e explicam-se ao passar o rato (ou ao tocar, no telemóvel).
GLOSSARIO = {
    "kWh": ("Unidades", "Quilowatt-hora: a energia que gastas. Um aparelho de 1000 W ligado 1 hora gasta 1 kWh."),
    "kVA": ("Unidades", "A unidade da potência contratada: diz quantos aparelhos podes ligar ao mesmo tempo. Com 3,45 kVA, o forno e a máquina de lavar juntos podem fazer disparar o quadro."),
    "potência contratada": ("Fatura", "A potência máxima que podes usar ao mesmo tempo. Pagas um valor por dia, mesmo sem consumir."),
    "CPE": ("Fatura", "Código de Ponto de Entrega: o número que identifica a tua instalação na rede. Pede-se ao mudar de comercializador."),
    "leitura estimada": ("Fatura", "Quando ninguém leu o contador, a fatura usa uma estimativa; a diferença é acertada mais tarde."),
    "contribuição audiovisual": ("Fatura", "Taxa de 2,85 € por mês que financia o serviço público de rádio e televisão."),
    "tarifa social": ("Fatura", "Desconto para famílias com baixos rendimentos ou que recebem certas prestações sociais."),
    "IVA": ("Fatura", "Imposto sobre o valor acrescentado: 6 % numa parte da energia e da potência, 23 % no resto."),
    "OMIE": ("Mercado", "O mercado ibérico onde as empresas compram a eletricidade de Portugal e Espanha, com um preço para cada quarto de hora. Não é o preço que pagas: a isso juntam-se as redes, a margem e os impostos."),
    "indexado": ("Mercado", "Tarifário em que o preço da energia acompanha o mercado (OMIE), em vez de ser fixo."),
    "perdas": ("Mercado", "A energia que se perde no caminho até tua casa. Nos indexados é cobrada como uma percentagem sobre o preço do mercado."),
    "margem": ("Mercado", "O que o comercializador soma ao preço do mercado para cobrir os seus custos e o lucro."),
    "ERSE": ("Regulação", "Entidade Reguladora dos Serviços Energéticos, o árbitro do setor: define a tarifa regulada e o preço das redes."),
    "tarifas de acesso às redes": ("Regulação", "A parte do preço que paga o uso das redes e outros custos do sistema. É igual em todos os comercializadores."),
    "tarifa regulada": ("Regulação", "O preço fixo definido pela ERSE. Serve de referência para comparar ofertas."),
    "comercializador de último recurso": ("Regulação", "A empresa que vende a tarifa regulada (no continente, a SU Eletricidade)."),
    "comercializador": ("Regulação", "A empresa que te vende a eletricidade e emite a fatura."),
    "fidelização": ("Regulação", "Período mínimo do contrato. Sair antes pode ter custos; vê sempre na ficha da oferta."),
    "E-REDES": ("Regulação", "A empresa que gere a rede e os contadores. Não é quem te vende a luz e não muda quando mudas de comercializador."),
    "contador inteligente": ("Fatura", "Contador que envia sozinho os consumos à E-REDES, de 15 em 15 minutos. Ninguém precisa de vir ler."),
    "imposto especial de consumo": ("Fatura", "Imposto pequeno, de cêntimos por cada kWh, que vem em todas as faturas."),
    "escalão": ("Fatura", "Cada um dos valores possíveis da potência contratada, como 3,45, 4,6 ou 6,9 kVA."),
    "DGEG": ("Fatura", "Direção-Geral de Energia e Geologia. Cobra uma pequena taxa mensal que vem em todas as faturas."),
    "vazio": ("Horários", "O período mais barato do bi e do tri-horário (no ciclo diário, das 22h às 8h)."),
    "ponta": ("Horários", "O período mais caro do tri-horário: 4 horas por dia, que mudam entre o inverno e o verão."),
    "cheias": ("Horários", "No tri-horário, as horas de preço intermédio: nem as mais baratas (vazio) nem as mais caras (ponta)."),
    "fora de vazio": ("Horários", "No bi-horário, as horas do dia (das 8h às 22h), mais caras do que o vazio."),
    "bi-horário": ("Horários", "Opção com dois preços: vazio (mais barato) e fora de vazio."),
    "tri-horário": ("Horários", "Opção com três preços: vazio, cheias e ponta."),
}

LIGACOES = [
    ("Simulador de preços da ERSE", "https://simuladorprecos.erse.pt/", "Compara as ofertas de todas as empresas."),
    ("ERSE — tarifas e preços", "https://www.erse.pt/atividade/regulacao/tarifas-e-precos-eletricidade/", "As tarifas oficiais de cada ano."),
    ("OMIE — resultados do mercado", "https://www.omie.es/pt/market-results", "Os preços do mercado ibérico, dia a dia."),
    ("Balcão Digital da E-REDES", "https://balcaodigital.e-redes.pt/", "Os teus consumos de 15 em 15 minutos (com contador inteligente)."),
    ("Tarifa social", "https://www.dgeg.gov.pt/pt/areas-transversais/tarifa-social-de-energia/", "Quem tem direito e como se pede."),
]


# Ordem das ferramentas no menu, na Início e no "Próximo passo": o percurso de quem aprende
# (perceber a fatura → poupar → horários → escolher o tarifário → o mercado hora a hora).
# A numeração de nucleo/roteiro.py fica igual (é a do guia PDF).
ORDEM_FERRAMENTAS = (1, 2, 5, 3, 4)

# O que a pessoa ficou a saber em cada ferramenta (aparece no fim, com a ligação para a seguinte)
APRENDESTE = {
    1: "A tua fatura tem duas partes: a energia, que depende de quanto gastas (em kWh), e a potência "
       "contratada, que pagas todos os dias, mesmo sem gastar. Viste também se pagarias menos na "
       "tarifa regulada ou noutra empresa.",
    2: "Os aparelhos que aquecem (água, casa e roupa) são os que mais pesam na fatura. Cada kWh que "
       "deixas de gastar poupa o preço da energia; a parte da potência fica igual.",
    5: f"No bi e no tri-horário, as horas de vazio ({VAZIO}) são mais baratas e as outras mais caras. "
       "Só compensa mudar se uma boa parte do teu consumo cair no vazio.",
    3: "O mesmo consumo custa valores diferentes conforme a empresa e o tipo de preço, fixo ou "
       "indexado. A tarifa regulada serve de referência: se pagas mais do que ela, vale a pena "
       "comparar. Mudar de empresa é gratuito e não corta a luz.",
    4: "O preço do mercado muda ao longo do dia e costuma ser mais baixo a meio do dia e de "
       "madrugada. Só pagas o preço de cada hora se o teu tarifário for indexado.",
}

# Palavras explicadas no topo de cada ferramenta (todas existem no GLOSSARIO)
TERMOS = {
    1: ["kWh", "potência contratada", "kVA", "IVA", "tarifa regulada", "ERSE", "indexado"],
    2: ["kWh", "vazio", "bi-horário"],
    3: ["tarifa regulada", "ERSE", "indexado", "OMIE", "fidelização", "comercializador"],
    4: ["OMIE", "indexado", "vazio", "kWh"],
    5: ["vazio", "fora de vazio", "cheias", "ponta", "bi-horário", "tri-horário", "indexado"],
}
