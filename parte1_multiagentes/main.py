"""TC2008B - Actividad Integradora: Parte 1 (Sistemas Multiagentes)

Ejecución de la simulación multiagente con AgentPy:
5 robots omnidireccionales organizan un almacén de M x N celdas:
recogen K cajas a nivel de piso y las apilan en grupos de máximo 5.

Uso:
    python main.py [semilla]
    (O desde la raíz: python run.py parte1)
"""
import os
import sys

# Permitir importar agentes desde la raíz del proyecto
RAIZ = os.path.dirname(os.path.dirname(os.path.abspath(__file__)))
if RAIZ not in sys.path:
    sys.path.insert(0, RAIZ)

from agentes.modelo import AlmacenModelo, PARAMETROS, MAX_PILA


def ejecutar_simulacion(semilla=42, verbose=True):
    """Ejecuta una corrida de la simulación e imprime las métricas de la actividad."""
    params = {**PARAMETROS, 'seed': semilla}
    modelo = AlmacenModelo(params)

    if verbose:
        print("\n" + "=" * 65)
        print("🤖 TC2008B - PARTE 1: SISTEMAS MULTIAGENTES (AgentPy)")
        print("=" * 65)
        print(f"  • Dimensiones del almacén : {params['M']} x {params['N']} celdas")
        print(f"  • Cajas iniciales (K)     : {params['K']} a nivel de piso (sin pilas)")
        print(f"  • Flota de robots         : {params['robots']} omnidireccionales")
        print(f"  • Límite por pila         : {MAX_PILA} cajas máximo")
        print(f"  • Semilla aleatoria       : {semilla}")
        print("=" * 65)

    # Ejecutar simulación
    modelo.run(display=False)

    exito = modelo.tiempo_finalizacion is not None
    tiempo = modelo.tiempo_finalizacion or modelo.t
    movs_totales = modelo.movimientos_totales()
    pilas_llenas = modelo.pilas_completas()
    pilas_esperadas = modelo.K // MAX_PILA

    if verbose:
        print("\n" + "=" * 65)
        print("📊 RESULTADOS FINALES DE LA SIMULACIÓN")
        print("=" * 65)
        print(f"  • Misión completada       : {'✅ SÍ' if exito else '❌ NO (alcanzó tiempo máximo)'}")
        print(f"  • Tiempo necesario (pasos): {tiempo} pasos")
        print(f"  • Movimientos totales     : {movs_totales} movimientos")
        print(f"  • Movimientos promedio/caja: {round(movs_totales / modelo.K, 2)}")
        print(f"  • Pilas de 5 completadas  : {pilas_llenas} de {pilas_esperadas}")
        print("-" * 65)
        print("  Desglose individual por robot:")
        for r in modelo.robots:
            print(f"    • Robot {r.numero}: {r.movimientos} movimientos")
        print("=" * 65 + "\n")

    return {
        'exito': exito,
        'tiempo': tiempo,
        'movimientos': movs_totales,
        'pilas_completas': pilas_llenas,
    }


if __name__ == "__main__":
    semilla = int(sys.argv[1]) if len(sys.argv) > 1 else 42
    ejecutar_simulacion(semilla=semilla)

