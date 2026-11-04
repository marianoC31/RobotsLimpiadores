import math
import statistics
import time
from modelo_almacen import AlmacenModel

def ejecutar_bateria_experimentos(
    dimensiones=(14, 14),
    valores_k=(15, 25, 40),
    num_robots=5,
    num_replicas=20,
    max_pasos=1200
):
    """
    Batería de Pruebas Experimentales Monte Carlo (Rúbrica SICT0102 - Nivel Destacado):
    Evalúa sistemáticamente la relación causa-efecto entre:
      - Variable Independiente 1: Estrategia del sistema multiagente (BASE vs OPTIMIZADA).
      - Variable Independiente 2: Cantidad/densidad de cajas en el almacén (K = 15, 25, 40).
      - Variables Dependientes: Pasos de convergencia (T), movimientos totales (M),
                                movimientos por caja (M/K) y conflictos de carreras perdidas (C).
    Utiliza réplicas pareadas con semillas pseudoaleatorias idénticas para control estricto.
    """
    m, n = dimensiones
    print("\n" + "="*85)
    print("🔬 BATERÍA DE EXPERIMENTACIÓN MULTIAGENTE - ANÁLISIS CIENTÍFICO CAUSA-EFECTO")
    print("   Subcompetencia SICT0102: Demostración del funcionamiento de los sistemas")
    print("="*85)
    print(f"  • Dimensiones del almacén (M x N): {m} x {n} celdas")
    print(f"  • Flota de robots: {num_robots} omnidireccionales")
    print(f"  • Configuraciones de cajas (K): {valores_k}")
    print(f"  • Réplicas Monte Carlo por configuración: {num_replicas} ejecuciones pareadas")
    print("="*85 + "\n")

    resultados = {}

    tiempo_total_inicio = time.time()

    for k in valores_k:
        resultados[k] = {}
        for estrategia in ['BASE', 'OPTIMIZADA']:
            lista_pasos = []
            lista_movs = []
            lista_movs_caja = []
            lista_conflictos = []
            exitos = 0

            for rep in range(num_replicas):
                semilla = 1000 + rep # Semillas idénticas para ambas estrategias (muestras pareadas)
                modelo = AlmacenModel(
                    m=m, n=n, k=k,
                    num_robots=num_robots,
                    max_pasos=max_pasos,
                    estrategia=estrategia,
                    semilla=semilla
                )

                while not modelo.simulacion_terminada:
                    modelo.step()

                met = modelo.obtener_metricas()
                if met['exito_mision']:
                    exitos += 1
                    lista_pasos.append(met['pasos_totales'])
                    lista_movs.append(met['movimientos_totales'])
                    lista_movs_caja.append(met['movimientos_por_caja'])
                    lista_conflictos.append(met['intentos_fallidos_totales'])

            tasa_exito = (exitos / num_replicas) * 100.0
            media_pasos = statistics.mean(lista_pasos) if lista_pasos else 0
            std_pasos = statistics.stdev(lista_pasos) if len(lista_pasos) > 1 else 0

            media_movs = statistics.mean(lista_movs) if lista_movs else 0
            std_movs = statistics.stdev(lista_movs) if len(lista_movs) > 1 else 0

            media_movs_caja = statistics.mean(lista_movs_caja) if lista_movs_caja else 0
            media_conf = statistics.mean(lista_conflictos) if lista_conflictos else 0

            resultados[k][estrategia] = {
                "tasa_exito": tasa_exito,
                "media_pasos": media_pasos,
                "std_pasos": std_pasos,
                "media_movs": media_movs,
                "std_movs": std_movs,
                "media_movs_caja": media_movs_caja,
                "media_conflictos": media_conf
            }

            print(f"  [K={k:2d} | {estrategia:10s}] Éxito: {tasa_exito:5.1f}% | Pasos: {media_pasos:6.2f} ± {std_pasos:4.2f} | Movs: {media_movs:6.2f} ± {std_movs:4.2f} | Conflictos: {media_conf:4.1f}")

    duracion = time.time() - tiempo_total_inicio

    # Generar tabla resumen en formato Markdown para el reporte de entrega
    tabla_md = generar_tabla_markdown(resultados, valores_k)

    print("\n" + "="*85)
    print("📈 TABLA RESUMEN DE RESULTADOS EXPERIMENTALES (FORMATO MARKDOWN)")
    print("="*85)
    print(tabla_md)
    print(f"\nDuración total de pruebas: {duracion:.2f} segundos\n")

    return resultados, tabla_md

def generar_tabla_markdown(resultados, valores_k):
    lineas = [
        "| Cantidad Cajas ($K$) | Estrategia | Tasa Éxito | Pasos Promedio ($T$) | Movimientos Flota ($M$) | Movs / Caja | Carreras Perdidas ($C$) | Mejora en Movimientos ($\Delta M$) |",
        "|:---:|:---:|:---:|:---:|:---:|:---:|:---:|:---:|"
    ]

    for k in valores_k:
        b = resultados[k]['BASE']
        o = resultados[k]['OPTIMIZADA']

        delta_movs = ((o['media_movs'] - b['media_movs']) / b['media_movs']) * 100.0 if b['media_movs'] > 0 else 0
        delta_sign = f"{delta_movs:+.1f}%"

        lineas.append(
            f"| **K = {k}** | BASE | {b['tasa_exito']:.1f}% | {b['media_pasos']:.1f} ± {b['std_pasos']:.1f} | {b['media_movs']:.1f} ± {b['std_movs']:.1f} | {b['media_movs_caja']:.2f} | {b['media_conflictos']:.1f} | Ref. (0.0%) |"
        )
        lineas.append(
            f"| **K = {k}** | **OPTIMIZADA** | {o['tasa_exito']:.1f}% | **{o['media_pasos']:.1f} ± {o['std_pasos']:.1f}** | **{o['media_movs']:.1f} ± {o['std_movs']:.1f}** | **{o['media_movs_caja']:.2f}** | **{o['media_conflictos']:.1f}** | **{delta_sign}** |"
        )

    return "\n".join(lineas)

if __name__ == "__main__":
    ejecutar_bateria_experimentos(num_replicas=20)

