import sys
import argparse
from simulacion_visual import ejecutar_simulacion_visual
from simulacion_consola import ejecutar_simulacion_consola
from experimentos import ejecutar_bateria_experimentos

def main():
    parser = argparse.ArgumentParser(
        description="TC2008B - Parte 1: Simulación de Sistemas Multiagentes (Almacén Autónomo)",
        formatter_class=argparse.ArgumentDefaultsHelpFormatter
    )
    parser.add_argument("--consola", action="store_true", help="Ejecutar en modo consola interactiva ASCII sin ventana gráfica")
    parser.add_argument("--experimentos", action="store_true", help="Ejecutar batería de experimentación científica Monte Carlo (SICT0102)")
    parser.add_argument("--estrategia", type=str, choices=['BASE', 'OPTIMIZADA'], default='OPTIMIZADA', help="Estrategia cooperativa de los robots")
    parser.add_argument("-m", type=int, default=14, help="Ancho del almacén en celdas")
    parser.add_argument("-n", type=int, default=14, help="Largo del almacén en celdas")
    parser.add_argument("-k", type=int, default=25, help="Cantidad de cajas iniciales a nivel de piso")
    parser.add_argument("--robots", type=int, default=5, help="Cantidad de robots en la flota")
    parser.add_argument("--pasos", type=int, default=1000, help="Límite máximo de pasos de simulación")
    parser.add_argument("--semilla", type=int, default=None, help="Semilla pseudoaleatoria para reproducibilidad")
    parser.add_argument("--replicas", type=int, default=20, help="Número de réplicas pareadas para el modo experimentos")

    args = parser.parse_args()

    if args.experimentos:
        ejecutar_bateria_experimentos(
            dimensiones=(args.m, args.n),
            valores_k=(15, 25, 40),
            num_robots=args.robots,
            num_replicas=args.replicas,
            max_pasos=args.pasos
        )
    elif args.consola:
        ejecutar_simulacion_consola(
            m=args.m,
            n=args.n,
            k=args.k,
            num_robots=args.robots,
            max_pasos=args.pasos,
            estrategia=args.estrategia,
            semilla=args.semilla,
            animado=True
        )
    else:
        try:
            ejecutar_simulacion_visual(
                m=args.m,
                n=args.n,
                k=args.k,
                num_robots=args.robots,
                max_pasos=args.pasos,
                estrategia=args.estrategia,
                semilla=args.semilla
            )
        except Exception as e:
            print(f"\n⚠️  No se pudo abrir la ventana gráfica de Pygame ({e}). Ejecutando en consola...")
            ejecutar_simulacion_consola(
                m=args.m,
                n=args.n,
                k=args.k,
                num_robots=args.robots,
                max_pasos=args.pasos,
                estrategia=args.estrategia,
                semilla=args.semilla,
                animado=True
            )

if __name__ == "__main__":
    main()
