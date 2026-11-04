import time
import os
from modelo_almacen import AlmacenModel

def render_ascii(modelo):
    """Genera una representación en texto del almacén."""
    lineas = []
    lineas.append("+" + "---+" * modelo.m)
    for y in range(modelo.n):
        fila = "|"
        for x in range(modelo.m):
            if x == 0 or x == modelo.m - 1 or y == 0 or y == modelo.n - 1:
                fila += "###|"
            elif modelo.grid_robots[y][x] is not None:
                r = modelo.grid_robots[y][x]
                if r.lleva_caja:
                    fila += f"R{r.id_robot}*|" # Con caja
                else:
                    fila += f"R{r.id_robot} |" # Sin caja
            elif modelo.cajas[y][x] > 0:
                c = modelo.cajas[y][x]
                if c == 5:
                    fila += f"[{c}]|" # Pila completa de 5
                else:
                    fila += f" {c} |"
            else:
                fila += "   |"
        lineas.append(fila)
        lineas.append("+" + "---+" * modelo.m)
    return "\n".join(lineas)

def ejecutar_simulacion_consola(m=14, n=14, k=25, num_robots=5, max_pasos=800, estrategia='OPTIMIZADA', semilla=None, pausa=0.04, animado=True):
    """
    Ejecuta la simulación multiagente en consola e imprime las métricas exigidas por el reto.
    """
    print("\n" + "="*75)
    print("🤖 TC2008B - PARTE 1: SISTEMAS MULTIAGENTES (SIMULACIÓN EN CONSOLA)")
    print("="*75)
    print(f"  • Estrategia: {estrategia}")
    print(f"  • Dimensiones: {m}x{n} celdas")
    print(f"  • Cajas iniciales: {k} a nivel de piso (sin pilas)")
    print(f"  • Robots: {num_robots} omnidireccionales con sensores de 4 celdas y presión")
    print(f"  • Meta: Organizar todas las cajas en pilas de 5 cajas")
    print("="*75 + "\n")

    modelo = AlmacenModel(
        m=m, n=n, k=k,
        num_robots=num_robots,
        max_pasos=max_pasos,
        estrategia=estrategia,
        semilla=semilla
    )

    tiempo_inicio = time.time()

    while not modelo.simulacion_terminada:
        modelo.step()
        
        if animado and modelo.paso_actual % 2 == 0:
            os.system('clear' if os.name == 'posix' else 'cls')
            print(f"--- PASO {modelo.paso_actual} / {max_pasos} | Estrategia: {estrategia} ---")
            print(render_ascii(modelo))
            m_actual = modelo.obtener_metricas()
            print(f"Pilas de 5: {m_actual['pilas_5_completadas']}/{m_actual['pilas_5_esperadas']} | Movimientos: {m_actual['movimientos_totales']} | Cajas en transporte: {m_actual['cajas_en_transporte']}")
            time.sleep(pausa)

    tiempo_real = time.time() - tiempo_inicio
    metricas = modelo.obtener_metricas()

    print("\n" + "="*75)
    print("📊 RESULTADOS FINALES DE LA SIMULACIÓN (RECOPILACIÓN DE INFORMACIÓN)")
    print("="*75)
    print(f"  • Estrategia evaluada: {metricas['estrategia']}")
    print(f"  • Éxito de la tarea: {'✅ SÍ (Todas en pilas ordenadas de 5)' if metricas['exito_mision'] else '⚠️ LÍMITE DE PASOS ALCANZADO'}")
    print(f"  • Tiempo necesario (pasos/steps): {metricas['pasos_totales']} pasos")
    print(f"  • Tiempo de cómputo real: {tiempo_real:.2f} segundos")
    print(f"  • Total de movimientos realizados por la flota: {metricas['movimientos_totales']}")
    print(f"  • Movimientos promedio por caja: {metricas['movimientos_por_caja']}")
    print(f"  • Pilas de 5 cajas completadas: {metricas['pilas_5_completadas']} / {metricas['pilas_5_esperadas']}")
    print(f"  • Cajas en pilas completas: {metricas['cajas_en_pilas_5']}")
    print(f"  • Cajas en pilas incompletas: {metricas['cajas_en_proceso']}")
    print(f"  • Cajas sueltas restantes en piso: {metricas['cajas_sueltas']}")
    print(f"  • Cajas en transporte al finalizar: {metricas['cajas_en_transporte']}")
    print("\n--- Desglose Individual por Robot ---")
    for r_info in metricas['detalle_robots']:
        print(f"  Robot {r_info['id']}: {r_info['movimientos']:3d} movimientos | {r_info['recogidas']:2d} recogidas | {r_info['depositadas']:2d} depositadas | {r_info['conflictos']:2d} conflictos resueltos")
    print("="*75 + "\n")

    return metricas

if __name__ == "__main__":
    ejecutar_simulacion_consola(m=14, n=14, k=25, num_robots=5, animado=True)
