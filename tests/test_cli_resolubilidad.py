"""Parser y despacho del modo solo verificación."""

import pytest
import subprocess
import sys
from pathlib import Path

from src.controller1.cli import parse_args
from src.main import main
from src.models.resolubilidad import ResultadoResolubilidad


@pytest.mark.parametrize("args", [
    ["--verificar", "a", "--replay", "x"],
    ["--verificar", "a", "--cargar", "x"],
    ["--verificar", "a", "--bench"],
    ["--verificar", "a", "--cripta", "b"],
    ["--forzar", "--replay", "x"],
])
def test_rechaza_combinaciones_incompatibles(args):
    with pytest.raises(SystemExit):
        parse_args(args)


@pytest.mark.parametrize(("estado", "codigo"), [
    ("resoluble", 0), ("no_resoluble", 1), ("incompleta", 2)])
def test_verificar_imprime_resultado_y_codigo(monkeypatch, capsys, estado, codigo):
    resultado = ResultadoResolubilidad("c", "v", estado, "motivo")
    class SesionFalsa:
        def preparar_inicio(self, _, contar_lista=True):
            return resultado
    monkeypatch.setattr("src.main._nueva_sesion", lambda *a, **k: SesionFalsa())
    assert main(["--verificar", "c"]) == codigo
    assert "Cripta: c" in capsys.readouterr().out


@pytest.mark.parametrize(("cripta", "codigo", "literal"), [
    ("resoluble", 0, "Resultado: RESOLUBLE"),
    ("ciclo", 1, "Resultado: NO RESOLUBLE"),
    ("incompleta", 2, "Resultado: VERIFICACIÓN INCOMPLETA"),
])
def test_subprocess_offline_no_inicia_estado_ni_necesita_catalogo(cripta, codigo, literal):
    raiz = Path(__file__).resolve().parent.parent
    fixture = raiz / "tests" / "fixtures" / "resolubilidad"
    proceso = subprocess.run([sys.executable, "-m", "src.main", "--offline",
        str(fixture), "--verificar", cripta, "--vista", "--jugar"],
        cwd=raiz, capture_output=True, text=True, timeout=20)
    assert proceso.returncode == codigo, proceso.stdout + proceso.stderr
    assert literal in proceso.stdout
