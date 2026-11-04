"""Lanzador único del proyecto.

Uso:
    python run.py parte2              Almacén 3D: los robots siguen la simulación de AgentPy
    python run.py agentes [semilla]   Solo la simulación de AgentPy, sin gráficos (imprime métricas)
    python run.py parte1 [opciones]   Versión 2D anterior de tu compañero (sin AgentPy)
"""
import os
import runpy
import sys

RAIZ = os.path.dirname(os.path.abspath(__file__))

# Los programas imprimen emojis; sin esto fallan en Windows si la salida se redirige
sys.stdout.reconfigure(encoding="utf-8", errors="replace")

PROGRAMAS = {
    "parte2":   ("parte2_graficas", "main.py"),
    "agentes":  ("agentes", "modelo.py"),
    "parte1":   ("parte1_multiagentes", "main.py"),
}

if __name__ == "__main__":
    if len(sys.argv) < 2 or sys.argv[1] not in PROGRAMAS:
        print(__doc__)
        sys.exit(1)

    carpeta, archivo = PROGRAMAS[sys.argv[1]]
    ruta = os.path.join(RAIZ, carpeta, archivo)

    # Igual que si corrieras "python <carpeta>/<archivo> [opciones]"
    sys.path[:0] = [os.path.join(RAIZ, carpeta), RAIZ]
    sys.argv = [ruta] + sys.argv[2:]
    runpy.run_path(ruta, run_name="__main__")
