"""Simulación multiagente del almacén con AgentPy.

TC2008B - Actividad Integradora (Parte 1 / Módulo de Agentes)
Modelo formal con ciclo percibir -> decidir -> actuar.

5 robots omnidireccionales organizan un almacén de M x N celdas:
recogen K cajas sueltas a nivel de piso y las apilan en grupos de máximo 5.
"""
import math
from collections import deque
import agentpy as ap

DIRECCIONES = {'N': (0, -1), 'S': (0, 1), 'E': (1, 0), 'O': (-1, 0)}
MAX_PILA = 5


class RobotAgente(ap.Agent):
    """Robot recolector y apilador con ruedas omnidireccionales y sensores locales."""

    def setup(self):
        """Inicializa las variables internas y sensores del robot."""
        self.movimientos = 0
        self.lleva_caja = False          # Sensor de presión
        self.orientacion = 'S'           # Dirección visual ('N', 'S', 'E', 'O')
        self.accion = 'esperar'          # Acción actual: 'esperar', 'mover', 'recoger', 'apilar'
        self.sensores = {}               # Lecturas de las 4 celdas vecinas

    @property
    def pos(self):
        """Posición actual del agente en la cuadrícula (x, y)."""
        return self.model.grid.positions[self]

    # ---------------- 1. PERCIBIR ----------------
    def percibir(self):
        """Lee el estado de las 4 celdas ortogonales vecinas (N, S, E, O)."""
        x, y = self.pos
        self.sensores = {
            d: self.model.info_celda(x + dx, y + dy)
            for d, (dx, dy) in DIRECCIONES.items()
        }

    # ---------------- 2. DECIDIR ----------------
    def decidir(self):
        """Determina la acción a ejecutar según el sensor de presión y la vecindad.
        
        Retorna: tupla (accion, direccion, destino)
        """
        modelo = self.model

        # CASO A: EL ROBOT NO LLEVA CAJA (Buscar y recoger)
        if not self.lleva_caja:
            # 1. Si hay una caja suelta adyacente, recogerla inmediatamente
            for d, info in self.sensores.items():
                if info['tipo'] == 'CAJAS' and info['pos'] not in modelo.pilas:
                    return ('recoger', d, info['pos'])

            # 2. Si no hay caja adyacente, dirigirse a la caja suelta no reservada más cercana
            caja_meta = modelo.reservar_caja_cercana(self)
            if caja_meta:
                paso = self.siguiente_paso_hacia(caja_meta)
                if paso:
                    return ('mover', paso, None)

            # 3. Si no hay ruta directa o está bloqueado, explorar en una celda libre
            libres = [d for d, i in self.sensores.items() if i['tipo'] == 'LIBRE']
            if libres:
                return ('mover', self.model.random.choice(libres), None)
            return ('esperar', self.orientacion, None)

        # CASO B: EL ROBOT YA LLEVA UNA CAJA (Buscar pila y depositar)
        else:
            # 1. Si hay una pila vecina con espacio (< 5 cajas), apilar en ella
            pilas_vecinas = [
                (d, i['pos'], modelo.cajas[i['pos'][0]][i['pos'][1]])
                for d, i in self.sensores.items()
                if i['pos'] in modelo.pilas and i['cajas'] < MAX_PILA and i['tipo'] == 'CAJAS'
            ]
            if pilas_vecinas:
                # Priorizar la pila más alta para cerrarla pronto en 5
                pilas_vecinas.sort(key=lambda item: item[2], reverse=True)
                d, pos_pila, _ = pilas_vecinas[0]
                return ('apilar', d, pos_pila)

            # 2. Si no está adyacente a una pila, dirigirse a la pila abierta más cercana
            abiertas = modelo.pilas_abiertas()
            if abiertas:
                x, y = self.pos
                pila_meta = min(abiertas, key=lambda p: abs(p[0] - x) + abs(p[1] - y))
                paso = self.siguiente_paso_hacia(pila_meta)
                if paso:
                    return ('mover', paso, None)

            # 3. Si no hay pilas abiertas y aún no se alcanza el máximo, fundar una en celda vecina
            if len(modelo.pilas) < modelo.max_pilas:
                libres = [
                    (d, i['pos']) for d, i in self.sensores.items()
                    if i['tipo'] == 'LIBRE'
                ]
                if libres:
                    cx, cy = modelo.M // 2, modelo.N // 2
                    d, pos_nueva = min(libres, key=lambda t: abs(t[1][0] - cx) + abs(t[1][1] - cy))
                    return ('fundar_pila', d, pos_nueva)

            # 4. En caso de congestión, moverse a una celda libre
            libres = [d for d, i in self.sensores.items() if i['tipo'] == 'LIBRE']
            if libres:
                return ('mover', self.model.random.choice(libres), None)
            return ('esperar', self.orientacion, None)

    # ---------------- 3. ACTUAR ----------------
    def actuar(self, decision):
        """Aplica sobre el entorno la acción decidida."""
        accion, direccion, destino = decision
        modelo = self.model

        if accion == 'recoger':
            modelo.retirar_caja(destino)
            modelo.liberar_reservas(self)
            self.lleva_caja = True
            self.orientacion = direccion
            self.accion = 'recoger'

        elif accion == 'apilar':
            modelo.agregar_caja(destino)
            self.lleva_caja = False
            self.orientacion = direccion
            self.accion = 'apilar'

        elif accion == 'fundar_pila':
            modelo.pilas.add(destino)
            modelo.agregar_caja(destino)
            self.lleva_caja = False
            self.orientacion = direccion
            self.accion = 'apilar'

        elif accion == 'mover':
            dx, dy = DIRECCIONES[direccion]
            x, y = self.pos
            nueva_pos = (x + dx, y + dy)
            if modelo.mover(self, nueva_pos):
                self.movimientos += 1
                self.orientacion = direccion
                self.accion = 'mover'
            else:
                self.accion = 'esperar'

        elif accion == 'esperar':
            self.accion = 'esperar'

    # ---------------- CICLO DEL AGENTE ----------------
    def step(self):
        """Ejecuta un ciclo completo: percibir -> decidir -> actuar."""
        self.percibir()
        self.actuar(self.decidir())

    # ---------------- NAVEGACIÓN ----------------
    def siguiente_paso_hacia(self, destino):
        """Busca el primer paso en el camino más corto hacia una celda vecina a destino."""
        metas = {(destino[0] + dx, destino[1] + dy) for dx, dy in DIRECCIONES.values()}
        metas = {p for p in metas if self.model.transitable(p)}
        if self.pos in metas:
            return None
        if not metas:
            return None

        inicio = self.pos
        padre = {inicio: None}
        cola = deque([inicio])
        encontrada = None

        while cola:
            actual = cola.popleft()
            if actual in metas:
                encontrada = actual
                break
            for d, (dx, dy) in DIRECCIONES.items():
                sig = (actual[0] + dx, actual[1] + dy)
                if sig not in padre and self.model.transitable(sig) and self.model.robot_en(sig) is None:
                    padre[sig] = actual
                    cola.append(sig)

        if encontrada is None:
            return None

        while padre[encontrada] != inicio:
            encontrada = padre[encontrada]

        paso = (encontrada[0] - inicio[0], encontrada[1] - inicio[1])
        return next(d for d, v in DIRECCIONES.items() if v == paso)


class AlmacenModelo(ap.Model):
    """Modelo del almacén con cuadrícula M x N, cajas y flota de robots."""

    def setup(self):
        """Inicializa el entorno, obstáculos, cajas iniciales y robots."""
        self.M = self.p.get('M', 14)
        self.N = self.p.get('N', 14)
        self.K = self.p.get('K', 20)
        self.max_pilas = math.ceil(self.K / MAX_PILA)

        # Estantes fijos (obstáculos del almacén)
        self.estantes = set()
        for x, y, largo in self.p.get('estantes', []):
            self.estantes.update((x, y + i) for i in range(largo))

        # Cuadrícula de cajas: cajas[x][y] guarda cuántas cajas hay en la celda
        self.cajas = [[0] * self.N for _ in range(self.M)]
        self.pilas = set()       # Celdas designadas para formar pilas
        self.reservas = {}      # celda_caja -> robot (evita que 2 vayan por la misma)
        self.ocupacion = {}     # celda -> robot

        # Celdas libres interiores (el borde perimetral es pared)
        libres = [
            (x, y) for x in range(1, self.M - 1) for y in range(1, self.N - 1)
            if (x, y) not in self.estantes
        ]
        self.random.shuffle(libres)

        # K cajas iniciales en posiciones aleatorias, todas a nivel de piso (altura 1)
        for x, y in libres[:self.K]:
            self.cajas[x][y] = 1

        # Cuadrícula espacial de AgentPy y flota de robots
        self.grid = ap.Grid(self, (self.M, self.N), track_empty=True)
        self.robots = ap.AgentList(self, self.p.get('robots', 5), RobotAgente)
        vacias = libres[self.K:]
        self.grid.add_agents(self.robots, positions=vacias[:len(self.robots)])

        for i, r in enumerate(self.robots):
            r.numero = i
            self.ocupacion[r.pos] = r

        self.tiempo_finalizacion = None

    def step(self):
        """Ejecuta un paso de tiempo activando a los robots en orden aleatorio."""
        for r in self.robots.shuffle():
            r.step()

    def update(self):
        """Registra métricas y evalúa si todas las cajas están en pilas de 5."""
        self.record('movimientos', sum(r.movimientos for r in self.robots))
        if self.terminado():
            self.tiempo_finalizacion = self.t
            self.stop()

    def end(self):
        """Reporta las estadísticas finales."""
        self.report('tiempo_finalizacion', self.tiempo_finalizacion)
        self.report('movimientos_totales', self.movimientos_totales())
        self.report('pilas_completas', self.pilas_completas())

    # ---------------- FUNCIONES DEL ENTORNO ----------------
    def info_celda(self, x, y):
        """Devuelve el tipo de entidad presente en la celda (x, y)."""
        if x <= 0 or y <= 0 or x >= self.M - 1 or y >= self.N - 1:
            return {'tipo': 'PARED', 'cajas': 0, 'pos': (x, y)}
        if (x, y) in self.estantes:
            return {'tipo': 'ESTANTE', 'cajas': 0, 'pos': (x, y)}
        if (x, y) in self.ocupacion:
            return {'tipo': 'ROBOT', 'cajas': self.cajas[x][y], 'pos': (x, y)}
        if self.cajas[x][y] > 0 or (x, y) in self.pilas:
            return {'tipo': 'CAJAS', 'cajas': self.cajas[x][y], 'pos': (x, y)}
        return {'tipo': 'LIBRE', 'cajas': 0, 'pos': (x, y)}

    def transitable(self, p):
        """Verifica si una celda se puede transitar (sin pared, estante ni cajas)."""
        x, y = p
        return (
            0 < x < self.M - 1 and 0 < y < self.N - 1
            and p not in self.estantes
            and self.cajas[x][y] == 0
            and p not in self.pilas
        )

    def robot_en(self, p):
        """Retorna el robot en la celda p, o None."""
        return self.ocupacion.get(p)

    def mover(self, robot, destino):
        """Mueve al robot a la celda de destino si está libre."""
        if self.transitable(destino) and destino not in self.ocupacion:
            del self.ocupacion[robot.pos]
            self.grid.move_to(robot, destino)
            self.ocupacion[destino] = robot
            return True
        return False

    def retirar_caja(self, p):
        """Resta una caja de la celda p."""
        self.cajas[p[0]][p[1]] -= 1

    def agregar_caja(self, p):
        """Añade una caja a la celda p."""
        self.cajas[p[0]][p[1]] += 1

    def cajas_sueltas(self):
        """Retorna las posiciones de cajas sueltas fuera de pilas designadas."""
        return [
            (x, y) for x in range(self.M) for y in range(self.N)
            if self.cajas[x][y] > 0 and (x, y) not in self.pilas
        ]

    def pilas_abiertas(self):
        """Retorna las pilas que aún tienen espacio (< 5 cajas)."""
        return [p for p in self.pilas if self.cajas[p[0]][p[1]] < MAX_PILA]

    def reservar_caja_cercana(self, robot):
        """Asigna la caja suelta más cercana al robot para evitar carreras duplicadas."""
        x, y = robot.pos
        libres = [c for c in self.cajas_sueltas() if self.reservas.get(c, robot) is robot]
        if not libres:
            return None
        elegida = min(libres, key=lambda c: abs(c[0] - x) + abs(c[1] - y))
        self.reservas[elegida] = robot
        return elegida

    def liberar_reservas(self, robot):
        """Libera cualquier caja reservada por el robot."""
        for c in [c for c, r in self.reservas.items() if r is robot]:
            del self.reservas[c]

    # ---------------- MÉTRICAS ----------------
    def movimientos_totales(self):
        """Suma de movimientos realizados por todos los robots."""
        return sum(r.movimientos for r in self.robots)

    def pilas_completas(self):
        """Cantidad de pilas que alcanzaron la altura máxima de 5."""
        return sum(1 for p in self.pilas if self.cajas[p[0]][p[1]] == MAX_PILA)

    def terminado(self):
        """Condición de éxito: ninguna caja suelta y todas en pilas de máx. 5."""
        if any(r.lleva_caja for r in self.robots) or self.cajas_sueltas():
            return False
        incompletas = sum(1 for p in self.pilas if 0 < self.cajas[p[0]][p[1]] < MAX_PILA)
        return incompletas <= (1 if self.K % MAX_PILA else 0)


# Parámetros estándar de la actividad
PARAMETROS = {
    'M': 14,
    'N': 14,
    'K': 20,
    'robots': 5,
    'estantes': [(4, 3, 2), (4, 9, 2), (9, 3, 2), (9, 9, 2)],
    'steps': 1500,
}


if __name__ == "__main__":
    import sys
    semilla = int(sys.argv[1]) if len(sys.argv) > 1 else 42
    modelo = AlmacenModelo({**PARAMETROS, 'seed': semilla})
    modelo.run(display=False)

    print("\n" + "=" * 60)
    print("🤖 RESULTADOS DE LA SIMULACIÓN (AgentPy)")
    print("=" * 60)
    print(f"  • Misión completada: {'SÍ' if modelo.tiempo_finalizacion else 'NO (llegó al tiempo máximo)'}")
    print(f"  • Tiempo necesario: {modelo.tiempo_finalizacion or modelo.t} pasos")
    print(f"  • Movimientos totales de la flota: {modelo.movimientos_totales()}")
    print(f"  • Pilas de 5 completas: {modelo.pilas_completas()} de {modelo.K // MAX_PILA}")
    print("-" * 60)
    for r in modelo.robots:
        print(f"    Robot {r.numero}: {r.movimientos} movimientos")
    print("=" * 60 + "\n")