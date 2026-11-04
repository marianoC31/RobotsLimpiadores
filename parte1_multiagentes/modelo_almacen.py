import random
import math
from agente_robot import RobotAgent

class AlmacenModel:
    """
    Modelo Computacional del Entorno del Almacén (Parte 1):
    - Cuadrícula espacial discreta M x N delimitada por muros perimetrales.
    - Manejo de K cajas iniciales en nivel de piso (altura 1, sin pilas).
    - Flota de 5 robots con sensores de 4 celdas, actuadores y sensor de presión.
    - Cumplimiento de regla de apilamiento: máximo 5 cajas por pila.
    - Soporte de semillas pseudoaleatorias para reproducibilidad científica (SICT0102).
    - Registro de telemetría por paso y métricas acumuladas de desempeño.
    """
    def __init__(self, m=14, n=14, k=25, num_robots=5, max_pasos=1000, estrategia='OPTIMIZADA', semilla=None):
        self.m = m
        self.n = n
        self.k_inicial = k
        self.num_robots = num_robots
        self.max_pasos = max_pasos
        self.estrategia = estrategia
        self.semilla = semilla
        self.max_pilas = math.ceil(k / 5)

        if semilla is not None:
            random.seed(semilla)

        # Matriz de celdas: cantidad de cajas apiladas (0 a 5)
        self.cajas = [[0 for _ in range(m)] for _ in range(n)]

        # Matriz de ocupación de agentes robots (RobotAgent o None)
        self.grid_robots = [[None for _ in range(m)] for _ in range(n)]

        # Registro de pilas activas: {(x, y): altura_actual (1..5)}
        self.zonas_pilas = {}

        # Mecanismo de reservas estigmérgicas para la estrategia coordinada (evita redundancia)
        self.reservas_cajas = {} # {pos_caja: id_robot}
        self.reservas_pilas = {} # {pos_pila: id_robot}

        # Control de simulación y métricas temporales
        self.paso_actual = 0
        self.simulacion_terminada = False
        self.tiempo_finalizacion = None
        self.exito_mision = False

        # Historial de series de tiempo para análisis causa-efecto
        self.historial_pasos = []

        # 1. Distribuir K cajas iniciales en posiciones aleatorias a nivel de piso (altura 1)
        self._inicializar_cajas()

        # 2. Inicializar los 5 robots en posiciones aleatorias vacías
        self.robots = []
        self._inicializar_robots()

    def _inicializar_cajas(self):
        """Ubica K cajas en celdas aleatorias vacías con altura 1 (nivel de piso, sin pilas)."""
        posiciones_validas = [
            (x, y) for x in range(1, self.m - 1)
                   for y in range(1, self.n - 1)
        ]
        random.shuffle(posiciones_validas)

        num_cajas = min(self.k_inicial, len(posiciones_validas))
        for i in range(num_cajas):
            x, y = posiciones_validas[i]
            self.cajas[y][x] = 1 # Nivel de piso estricto

    def _inicializar_robots(self):
        """Ubica los 5 robots en celdas aleatorias vacías (sin cajas y sin otros robots)."""
        posiciones_libres = [
            (x, y) for x in range(1, self.m - 1)
                   for y in range(1, self.n - 1)
                   if self.cajas[y][x] == 0
        ]
        random.shuffle(posiciones_libres)

        for i in range(self.num_robots):
            x, y = posiciones_libres[i]
            r = RobotAgent(id_robot=i, x=x, y=y, modelo=self, estrategia=self.estrategia)
            self.robots.append(r)
            self.grid_robots[y][x] = r

    def obtener_info_celda(self, x, y):
        """
        Retorna la percepción sensorial de la celda (x, y):
        - 'PARED': Fuera de la cuadrícula o en muros perimetrales.
        - 'ROBOT': Celda ocupada por otro agente robot.
        - 'CAJAS': Celda con cajas (cajas: 1..5).
        - 'LIBRE': Celda transitable vacía.
        """
        if x <= 0 or x >= self.m - 1 or y <= 0 or y >= self.n - 1:
            return {'tipo': 'PARED', 'cajas': 0, 'pos': (x, y)}

        if self.grid_robots[y][x] is not None:
            return {'tipo': 'ROBOT', 'cajas': self.cajas[y][x], 'pos': (x, y)}

        num_c = self.cajas[y][x]
        if num_c > 0:
            return {'tipo': 'CAJAS', 'cajas': num_c, 'pos': (x, y)}

        return {'tipo': 'LIBRE', 'cajas': 0, 'pos': (x, y)}

    def retirar_caja(self, x, y):
        """Retira 1 caja de la celda mediante el manipulador del robot."""
        if self.cajas[y][x] > 0:
            self.cajas[y][x] -= 1
            if (x, y) in self.zonas_pilas:
                self.zonas_pilas[(x, y)] = self.cajas[y][x]
                if self.cajas[y][x] == 0:
                    del self.zonas_pilas[(x, y)]
            return True
        return False

    def agregar_caja(self, x, y):
        """Apila 1 caja en la celda hasta el límite máximo de 5 cajas."""
        if self.cajas[y][x] < 5:
            self.cajas[y][x] += 1
            self.zonas_pilas[(x, y)] = self.cajas[y][x]
            return True
        return False

    def registrar_nueva_pila(self, x, y):
        """Designa una celda como zona de construcción de pila."""
        self.zonas_pilas[(x, y)] = self.cajas[y][x]

    def mover_robot(self, robot, nx, ny):
        """Actualiza la posición del robot en la matriz si la celda destino está libre."""
        if 0 < nx < self.m - 1 and 0 < ny < self.n - 1:
            if self.grid_robots[ny][nx] is None and self.cajas[ny][nx] == 0:
                self.grid_robots[robot.y][robot.x] = None
                self.grid_robots[ny][nx] = robot
                return True
        return False

    # --- Mecanismos de Reserva Estigmérgica (Estrategia Optimizada) ---
    def esta_caja_reservada(self, pos, id_robot):
        reserva = self.reservas_cajas.get(pos)
        return reserva is not None and reserva != id_robot

    def reservar_caja(self, pos, id_robot):
        self.reservas_cajas[pos] = id_robot

    def liberar_reserva_caja(self, id_robot):
        for pos, r_id in list(self.reservas_cajas.items()):
            if r_id == id_robot:
                del self.reservas_cajas[pos]

    def reservar_pila(self, pos, id_robot):
        self.reservas_pilas[pos] = id_robot

    def liberar_reserva_pila(self, id_robot):
        for pos, r_id in list(self.reservas_pilas.items()):
            if r_id == id_robot:
                del self.reservas_pilas[pos]

    def obtener_cajas_sueltas(self):
        """Retorna celdas con cajas que no forman parte de las pilas en consolidación."""
        sueltas = []
        for y in range(1, self.n - 1):
            for x in range(1, self.m - 1):
                if self.cajas[y][x] > 0 and (x, y) not in self.zonas_pilas:
                    sueltas.append((x, y))
        return sueltas

    def obtener_pilas_abiertas(self):
        """Retorna celdas que son pilas en construcción con espacio disponible (1 <= altura < 5)."""
        abiertas = []
        for pos, alt in list(self.zonas_pilas.items()):
            altura_real = self.cajas[pos[1]][pos[0]]
            if 0 < altura_real < 5:
                abiertas.append((pos, altura_real))
        return abiertas

    def todas_en_pilas_ordenadas(self):
        """
        Verifica la condición de éxito total del reto:
        - Todas las cajas están en pilas ordenadas de 5 cajas (máx. 1 pila con residuo si K % 5 != 0).
        - Ningún robot tiene caja en su manipulador (sensor de presión en False).
        - No hay cajas sueltas dispersas fuera de las zonas de pila.
        """
        for r in self.robots:
            if r.lleva_caja:
                return False

        cajas_fuera = sum(
            self.cajas[y][x]
            for y in range(1, self.n - 1)
            for x in range(1, self.m - 1)
            if (x, y) not in self.zonas_pilas
        )
        if cajas_fuera > 0:
            return False

        residuo = self.k_inicial % 5
        max_incompletas = 1 if residuo > 0 else 0
        incompletas = sum(1 for pos in self.zonas_pilas if 0 < self.cajas[pos[1]][pos[0]] < 5)

        return incompletas <= max_incompletas

    def step(self):
        """Avanza 1 paso de tiempo en la simulación multiagente."""
        if self.simulacion_terminada:
            return

        self.paso_actual += 1

        # Activación aleatoria de agentes en cada paso para evitar sesgo de orden
        agentes = list(self.robots)
        random.shuffle(agentes)
        for r in agentes:
            r.step()

        # Registro de serie temporal
        movs = sum(r.movimientos_realizados for r in self.robots)
        pilas_5 = sum(1 for y in range(self.n) for x in range(self.m) if self.cajas[y][x] == 5)
        self.historial_pasos.append({
            "paso": self.paso_actual,
            "movimientos": movs,
            "pilas_5": pilas_5
        })

        # Comprobar fin de simulación
        if self.todas_en_pilas_ordenadas():
            self.simulacion_terminada = True
            self.tiempo_finalizacion = self.paso_actual
            self.exito_mision = True
        elif self.paso_actual >= self.max_pasos:
            self.simulacion_terminada = True
            self.tiempo_finalizacion = self.paso_actual
            self.exito_mision = False

    def obtener_metricas(self):
        """Compila el informe cuantitativo exigido en la especificación."""
        movimientos_totales = sum(r.movimientos_realizados for r in self.robots)
        intentos_fallidos_totales = sum(r.intentos_fallidos for r in self.robots)
        conflictos_totales = sum(r.conflictos_resueltos for r in self.robots)
        cajas_en_pilas_5 = 0
        cajas_en_proceso = 0
        cajas_sueltas = 0
        pilas_5 = 0

        for y in range(1, self.n - 1):
            for x in range(1, self.m - 1):
                c = self.cajas[y][x]
                if (x, y) in self.zonas_pilas:
                    if c == 5:
                        cajas_en_pilas_5 += 5
                        pilas_5 += 1
                    elif c > 0:
                        cajas_en_proceso += c
                else:
                    cajas_sueltas += c

        cajas_en_transporte = sum(1 for r in self.robots if r.lleva_caja)

        return {
            "estrategia": self.estrategia,
            "dimensiones": (self.m, self.n),
            "k_inicial": self.k_inicial,
            "num_robots": self.num_robots,
            "pasos_totales": self.paso_actual,
            "tiempo_finalizacion": self.tiempo_finalizacion,
            "exito_mision": self.exito_mision,
            "movimientos_totales": movimientos_totales,
            "movimientos_por_caja": round(movimientos_totales / max(1, self.k_inicial), 2),
            "pilas_5_completadas": pilas_5,
            "pilas_5_esperadas": self.k_inicial // 5,
            "cajas_en_pilas_5": cajas_en_pilas_5,
            "cajas_en_proceso": cajas_en_proceso,
            "cajas_sueltas": cajas_sueltas,
            "cajas_en_transporte": cajas_en_transporte,
            "intentos_fallidos_totales": intentos_fallidos_totales,
            "conflictos_totales": conflictos_totales,
            "detalle_robots": [
                {
                    "id": r.id_robot,
                    "movimientos": r.movimientos_realizados,
                    "recogidas": r.cajas_recogidas,
                    "depositadas": r.cajas_depositadas,
                    "conflictos": r.conflictos_resueltos,
                    "intentos_fallidos": r.intentos_fallidos
                }
                for r in self.robots
            ]
        }
