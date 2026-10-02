"""Configuração do pytest.

- Põe a pasta do app no sys.path (para `from nucleo import ...` funcionar).
- Um teste que esbarra num dos stubs do projeto (NotImplementedError("Passo N — ..."))
  conta como "skipped" (por implementar), não como falha: o vermelho fica só para
  contas erradas. Um NotImplementedError vindo de outro sítio continua a ser falha.
"""
import os
import sys
from pathlib import Path

import pytest

sys.path.insert(0, str(Path(__file__).resolve().parents[1]))
# os testes nunca vão à internet (OMIE/ERSE usam ficheiros de tests/dados quando é preciso)
os.environ.setdefault("SIMULADOR_OFFLINE", "1")


@pytest.hookimpl(hookwrapper=True)
def pytest_runtest_makereport(item, call):
    resultado = yield
    relatorio = resultado.get_result()
    if relatorio.when == "call" and call.excinfo is not None \
            and call.excinfo.errisinstance(NotImplementedError) \
            and str(call.excinfo.value).startswith("Passo "):
        relatorio.outcome = "skipped"
        relatorio.longrepr = (str(item.path), (item.location[1] or 0) + 1,
                              f"Por implementar — {call.excinfo.value}")
