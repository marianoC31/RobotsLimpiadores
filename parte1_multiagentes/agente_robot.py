from collections import deque
import random
import math

class RobotAgent:
    """
    Agente Robot Autónomo con Ruedas Omnidireccionales y Manipulador Mecánico:
    - Movilidad omnidireccional en las 4 direcciones ortogonales: Norte, Sur, Este y Oeste.
    - Sistema de percepción:
        * Sensores en las cuatro celdas adyacentes (N, S, E, O): detecta campo libre, pared,
          pila de cajas (y su altura exacta de 1 a 5) u ocupación por otro robot.
        * Sensor de presión: booleano que indica con certeza si lleva una caja en el manipulador.
    - Manipulador:
        * Recoge cajas en celdas de cuadrícula adyacentes.
        * Deposita cajas en celdas adyacentes para construir pilas de hasta 5 cajas.
    - Navegación Ortogonal Óptima:
        * Planificación de trayectorias mediante Búsqueda en Anchura (BFS) sobre el espacio
          libre de obstáculos (evita muros, cajas apiladas y colisiones con otros robots).
    - Soporte para dos estrategias comparables (para la subcompetencia SICT0102):
        * 'BASE': Reactiva individual / Greedy sin reservas (competencia por recursos).
        * 'OPTIMIZADA': Coordinada por estigmergia (reservas exclusivas de cajas/pilas) y
                        heurística de cierre rápido (prioriza alturas altas 4->3->2->1).
    """
    DIRECCIONES = {
        'N': (0, -1),
        'S': (0, 1),
        'E': (1, 0),
        'O': (-1, 0)
    }

    def __init__(self, id_robot, x, y, modelo, estrategia='OPTIMIZADA'):
        self.id_robot = id_robot
        self.x = x
        self.y = y
        self.modelo = modelo
        self.estrategia = estrategia # 'BASE' o 'OPTIMIZADA'

        # Sensor de presión (True = lleva caja sujeta, False = manipulador vacío)
        self.lleva_caja = False

        # Estado del protocolo de control del agente:
        # 'BUSCAR': rastrear y aproximarse a cajas disponibles en el almacén.
        # 'TRANSPORTAR': trasladar la caja hacia una pila en construcción (< 5 cajas).
        # 'ESPERAR': ceder el paso temporalmente ante congestión.
        self.estado = 'BUSCAR'
        self.celda_objetivo = None
        self.ultima_direccion = None

        # Métricas individuales de desempeño
        self.movimientos_realizados = 0
        self.cajas_recogidas = 0
        self.cajas_depositadas = 0
        self.conflictos_resueltos = 0
        self.intentos_fallidos = 0 # Carreras perdidas (cuando otro robot retira la caja antes)

    def sensar_vecindad(self):
        """
        Lee los sensores de las 4 celdas adyacentes (N, S, E, O).
        Retorna: {dir: {'tipo': 'LIBRE'|'PARED'|'ROBOT'|'CAJAS', 'cajas': int, 'pos': (x, y)}}
        """
        lecturas = {}
        for d, (dx, dy) in self.DIRECCIONES.items():
            nx = self.x + dx
            ny = self.y + dy
            lecturas[d] = self.modelo.obtener_info_celda(nx, ny)
        return lecturas

    def step(self):
        """
        Ciclo de Percepción-Decisión-Acción del Agente (PDA):
        1. Percibir: sensar las 4 celdas adyacentes + sensor de presión.
        2. Deliberar: evaluar estado actual y seleccionar celda objetivo cooperativa.
        3. Actuar: ejecutar acción atómica de manipulación (recoger/depositar) o desplazamiento.
        """
        sensores = self.sensar_vecindad()

        # ==========================================================
        # RAMA 1: SENSOR DE PRESIÓN INACTIVO (NO LLEVA CAJA)
        # Objetivo: Localizar y recoger una caja disponible
        # ==========================================================
        if not self.lleva_caja:
            self.estado = 'BUSCAR'

            # 1. Comprobar si hay una caja adyacente para recoger inmediatamente
            cajas_adyacentes = []
            for d, info in sensores.items():
                if info['tipo'] == 'CAJAS':
                    pos = info['pos']
                    if pos not in self.modelo.zonas_pilas:
                        cajas_adyacentes.append((d, pos))

            if cajas_adyacentes:
                _, pos_caja = cajas_adyacentes[0]
                if self.modelo.retirar_caja(pos_caja[0], pos_caja[1]):
                    self.lleva_caja = True
                    self.cajas_recogidas += 1
                    self.celda_objetivo = None
                    if self.estrategia == 'OPTIMIZADA':
                        self.modelo.liberar_reserva_caja(self.id_robot)
                    return # Acción de turno completada

            # 2. Si el objetivo previo ya no tiene cajas (otro robot se la llevó)
            if self.celda_objetivo is not None:
                ox, oy = self.celda_objetivo
                if self.modelo.cajas[oy][ox] == 0 or self.celda_objetivo in self.modelo.zonas_pilas:
                    self.intentos_fallidos += 1
                    self.celda_objetivo = None
                    if self.estrategia == 'OPTIMIZADA':
                        self.modelo.liberar_reserva_caja(self.id_robot)

            # 3. Deliberar selección de nuevo objetivo
            if self.celda_objetivo is None:
                self.celda_objetivo = self._determinar_objetivo_recoleccion()

            # 4. Navegar hacia el objetivo seleccionado
            if self.celda_objetivo:
                self._navegar_hacia(self.celda_objetivo, sensores)
            else:
                self._mover_exploracion(sensores)

        # ==========================================================
        # RAMA 2: SENSOR DE PRESIÓN ACTIVO (LLEVA CAJA)
        # Objetivo: Transportar y apilar la caja en una pila de hasta 5
        # ==========================================================
        else:
            self.estado = 'TRANSPORTAR'

            # 1. Comprobar si hay una pila con espacio (< 5 cajas) adyacente
            pilas_adyacentes = []
            for d, info in sensores.items():
                pos = info['pos']
                if pos in self.modelo.zonas_pilas and self.modelo.cajas[pos[1]][pos[0]] < 5:
                    pilas_adyacentes.append((d, pos, self.modelo.cajas[pos[1]][pos[0]]))

            if pilas_adyacentes:
                if self.estrategia == 'OPTIMIZADA':
                    pilas_adyacentes.sort(key=lambda item: item[2], reverse=True)
                _, pos_pila, _ = pilas_adyacentes[0]

                if self.modelo.agregar_caja(pos_pila[0], pos_pila[1]):
                    self.lleva_caja = False
                    self.cajas_depositadas += 1
                    self.celda_objetivo = None
                    if self.estrategia == 'OPTIMIZADA':
                        self.modelo.liberar_reserva_pila(self.id_robot)
                    return # Acción de turno completada

            # 2. Si no hay pila adyacente, buscar una pila abierta existente
            pilas_abiertas = self.modelo.obtener_pilas_abiertas()
            if pilas_abiertas:
                pila_dest = self._determinar_objetivo_apilamiento(pilas_abiertas)
                self.celda_objetivo = pila_dest
                self._navegar_hacia(pila_dest, sensores)
            else:
                # 3. Si no hay pilas abiertas, fundar una nueva pila si no se excede max_pilas
                max_pilas = math.ceil(self.modelo.k_inicial / 5)
                if len(self.modelo.zonas_pilas) < max_pilas:
                    celdas_libres = [info['pos'] for info in sensores.values() if info['tipo'] == 'LIBRE']
                    if celdas_libres:
                        pos_nueva = self._seleccionar_celda_nueva_pila(celdas_libres)
                        self.modelo.registrar_nueva_pila(pos_nueva[0], pos_nueva[1])
                        if self.modelo.agregar_caja(pos_nueva[0], pos_nueva[1]):
                            self.lleva_caja = False
                            self.cajas_depositadas += 1
                            self.celda_objetivo = None
                            return
                self._mover_exploracion(sensores)

    def _determinar_objetivo_recoleccion(self):
        """Selecciona la caja objetivo según la estrategia configurada."""
        cajas_sueltas = self.modelo.obtener_cajas_sueltas()
        if not cajas_sueltas:
            return None

        if self.estrategia == 'OPTIMIZADA':
            # Filtrar cajas que no estén reservadas por otro agente
            disponibles = [
                c for c in cajas_sueltas
                if not self.modelo.esta_caja_reservada(c, self.id_robot)
            ]
            if not disponibles:
                disponibles = cajas_sueltas

            # Ordenar por distancia Manhattan |x1 - x2| + |y1 - y2|
            disponibles.sort(key=lambda pos: abs(pos[0] - self.x) + abs(pos[1] - self.y))
            elegida = disponibles[0]
            self.modelo.reservar_caja(elegida, self.id_robot)
            return elegida
        else:
            # Estrategia BASE: Cada robot va por la más cercana sin coordinar reservas
            cajas_sueltas.sort(key=lambda pos: abs(pos[0] - self.x) + abs(pos[1] - self.y))
            return cajas_sueltas[0]

    def _determinar_objetivo_apilamiento(self, pilas_abiertas):
        """Selecciona la pila destino (< 5 cajas) según la estrategia configurada."""
        if self.estrategia == 'OPTIMIZADA':
            # Priorizar pilas con mayor altura (4, 3, 2, 1) y menor distancia Manhattan
            pilas_abiertas.sort(
                key=lambda item: (-item[1], abs(item[0][0] - self.x) + abs(item[0][1] - self.y))
            )
            elegida = pilas_abiertas[0][0]
            self.modelo.reservar_pila(elegida, self.id_robot)
            return elegida
        else:
            # Estrategia BASE: Solo distancia Manhattan sin priorizar llenado
            pilas_abiertas.sort(
                key=lambda item: (abs(item[0][0] - self.x) + abs(item[0][1] - self.y))
            )
            return pilas_abiertas[0][0]

    def _seleccionar_celda_nueva_pila(self, celdas_libres):
        """Selecciona la celda para fundar una nueva pila."""
        if self.estrategia == 'OPTIMIZADA':
            cx, cy = self.modelo.m // 2, self.modelo.n // 2
            celdas_libres.sort(key=lambda p: abs(p[0] - cx) + abs(p[1] - cy))
            return celdas_libres[0]
        else:
            random.shuffle(celdas_libres)
            return celdas_libres[0]

    def _navegar_hacia(self, destino, sensores):
        """
        Navegación robusta libre de callejones sin salida mediante BFS:
        Busca aproximarse a cualquiera de las celdas adyacentes transitables al destino.
        """
        # Celdas adyacentes al objetivo donde el robot puede realizar pick/drop
        adj_targets = set()
        for dx, dy in [(0, -1), (0, 1), (1, 0), (-1, 0)]:
            nx, ny = destino[0] + dx, destino[1] + dy
            if 0 < nx < self.modelo.m - 1 and 0 < ny < self.modelo.n - 1:
                if self.modelo.cajas[ny][nx] == 0:
                    adj_targets.add((nx, ny))

        # Si ya estamos en una celda adyacente al destino, no requiere más pasos
        if (self.x, self.y) in adj_targets:
            return

        if not adj_targets:
            self._mover_exploracion(sensores)
            return

        # Búsqueda en anchura (BFS) del camino más corto
        queue = deque([(self.x, self.y)])
        visited = {(self.x, self.y): None}
        found = None

        while queue:
            curr = queue.popleft()
            if curr in adj_targets:
                found = curr
                break

            for dx, dy in [(0, -1), (0, 1), (1, 0), (-1, 0)]:
                nx, ny = curr[0] + dx, curr[1] + dy
                if 0 < nx < self.modelo.m - 1 and 0 < ny < self.modelo.n - 1:
                    if (nx, ny) not in visited:
                        # Una celda es transitable si no tiene cajas apiladas y no está ocupada por otro robot
                        if self.modelo.cajas[ny][nx] == 0 and (
                            self.modelo.grid_robots[ny][nx] is None or (nx == self.x and ny == self.y)
                        ):
                            visited[(nx, ny)] = curr
                            queue.append((nx, ny))

        if not found:
            # Si el camino directo está congestionado por otros robots, explorar desvío
            self.conflictos_resueltos += 1
            self._mover_exploracion(sensores)
            return

        # Reconstruir el primer paso desde la posición actual hacia el objetivo
        curr = found
        while visited[curr] != (self.x, self.y) and visited[curr] is not None:
            curr = visited[curr]

        if self.modelo.mover_robot(self, curr[0], curr[1]):
            self.x, self.y = curr
            self.movimientos_realizados += 1

    def _mover_exploracion(self, sensores):
        """Desplazamiento aleatorio a una celda libre adyacente."""
        opciones = list(self.DIRECCIONES.keys())
        random.shuffle(opciones)
        for d in opciones:
            info = sensores.get(d)
            if info and info['tipo'] == 'LIBRE':
                nx, ny = info['pos']
                if self.modelo.mover_robot(self, nx, ny):
                    self.x, self.y = nx, ny
                    self.movimientos_realizados += 1
                    return
