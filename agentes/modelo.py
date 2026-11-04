"""Simulación multiagente del almacén con AgentPy (módulo externo a la gráfica).

El almacén es una cuadrícula de M x N celdas (el borde es pared). Hay K cajas
sueltas en el piso, algunos estantes (celdas bloqueadas) y 5 robots.

Cada robot:
  - Percibe solo sus 4 celdas vecinas: LIBRE, PARED, ESTANTE, CAJAS (y cuántas) o ROBOT.
  - Tiene un sensor de presión: sabe si lleva una caja.
  - Puede moverse a una celda vecina libre, recoger una caja de una celda vecina,
    o dejarla en una pila vecina (máximo 5 cajas por pila).

Estrategia cooperativa:
  - Cada robot RESERVA la caja que va a buscar; los demás eligen otra.
  - Al cargar una caja, la lleva a la pila abierta más alta (para cerrar pilas
    de 5 cuanto antes). Si no hay pilas abiertas, funda una cerca del centro.
  - Para llegar usa BFS (camino más corto) y recalcula en cada paso, porque los
    demás robots se mueven.

Uso sin gráficos (imprime las métricas que pide la actividad):
    python run.py agentes
"""
import math
from collections import deque

import agentpy as ap

DIRECCIONES = {'N': (0, -1), 'S': (0, 1), 'E': (1, 0), 'O': (-1, 0)}
MAX_PILA = 5


class RobotAgente(ap.Agent):

    def setup(self):
        self.lleva_caja = False     # sensor de presión
        self.objetivo = None        # celda de la caja o pila a la que va
        self.movimientos = 0
        self.orientacion = 'S'      # hacia dónde mira (lo usa la gráfica)
        self.accion = 'esperar'     # 'mover' | 'recoger' | 'apilar' | 'esperar'

    @property
    def pos(self):
        return self.model.grid.positions[self]

    # ---------------- Percepción ----------------
    def sensar(self):
        x, y = self.pos
        return {d: self.model.info_celda(x + dx, y + dy) for d, (dx, dy) in DIRECCIONES.items()}

    # ---------------- Ciclo percepción -> decisión -> acción ----------------
    def step(self):
        self.accion = 'esperar'
        sensores = self.sensar()
        modelo = self.model

        if not self.lleva_caja:
            # 1. ¿Hay una caja suelta al lado? -> la recojo
            for d, info in sensores.items():
                if info['tipo'] == 'CAJAS' and info['pos'] not in modelo.pilas:
                    modelo.retirar_caja(info['pos'])
                    self.lleva_caja = True
                    self.objetivo = None
                    modelo.liberar_reservas(self)
                    self.orientacion, self.accion = d, 'recoger'
                    return
            # 2. ¿Mi objetivo sigue existiendo?
            if self.objetivo is not None:
                ox, oy = self.objetivo
                if modelo.cajas[ox][oy] == 0 or self.objetivo in modelo.pilas:
                    self.objetivo = None
                    modelo.liberar_reservas(self)
            # 3. Elegir la caja suelta más cercana que nadie haya reservado
            if self.objetivo is None:
                self.objetivo = modelo.reservar_caja_cercana(self)
            # 4. Ir hacia ella
            if self.objetivo is not None:
                self.navegar_hacia(self.objetivo, sensores)
            else:
                self.explorar(sensores)
        else:
            # 1. ¿Hay una pila con espacio al lado? -> dejo la caja en la más alta
            vecinas = [(modelo.cajas[i['pos'][0]][i['pos'][1]], d, i['pos'])
                       for d, i in sensores.items()
                       if i['pos'] in modelo.pilas and i['cajas'] < MAX_PILA and i['tipo'] == 'CAJAS']
            if vecinas:
                _, d, pos = max(vecinas)
                modelo.agregar_caja(pos)
                self.lleva_caja = False
                self.objetivo = None
                self.orientacion, self.accion = d, 'apilar'
                return
            # 2. Ir a la pila abierta más alta (y más cercana)
            abiertas = modelo.pilas_abiertas()
            if abiertas:
                x, y = self.pos
                self.objetivo = min(abiertas, key=lambda p: (-modelo.cajas[p[0]][p[1]],
                                                            abs(p[0] - x) + abs(p[1] - y)))
                self.navegar_hacia(self.objetivo, sensores)
                return
            # 3. No hay pilas abiertas: fundar una en una celda libre vecina (la más central)
            if len(modelo.pilas) < modelo.max_pilas:
                libres = [(d, i['pos']) for d, i in sensores.items() if i['tipo'] == 'LIBRE']
                if libres:
                    cx, cy = modelo.M // 2, modelo.N // 2
                    d, pos = min(libres, key=lambda t: abs(t[1][0] - cx) + abs(t[1][1] - cy))
                    modelo.pilas.add(pos)
                    modelo.agregar_caja(pos)
                    self.lleva_caja = False
                    self.objetivo = None
                    self.orientacion, self.accion = d, 'apilar'
                    return
            self.explorar(sensores)

    # ---------------- Movimiento ----------------
    def mover(self, d):
        x, y = self.pos
        dx, dy = DIRECCIONES[d]
        if self.model.mover(self, (x + dx, y + dy)):
            self.movimientos += 1
            self.orientacion, self.accion = d, 'mover'
            return True
        return False

    def navegar_hacia(self, destino, sensores):
        """BFS hasta cualquier celda libre vecina al destino; da solo el primer paso."""
        modelo = self.model
        metas = {(destino[0] + dx, destino[1] + dy) for dx, dy in DIRECCIONES.values()}
        metas = {p for p in metas if modelo.transitable(p)}
        if self.pos in metas:
            return
        if not metas:
            self.explorar(sensores)
            return
        inicio = self.pos
        padre = {inicio: None}
        cola = deque([inicio])
        encontrada = None
        while cola:
            actual = cola.popleft()
            if actual in metas:
                encontrada = actual
                break
            for dx, dy in DIRECCIONES.values():
                sig = (actual[0] + dx, actual[1] + dy)
                if sig not in padre and modelo.transitable(sig) and modelo.robot_en(sig) is None:
                    padre[sig] = actual
                    cola.append(sig)
        if encontrada is None:
            self.explorar(sensores)     # camino bloqueado por otros robots: desvío
            return
        while padre[encontrada] != inicio:
            encontrada = padre[encontrada]
        paso = (encontrada[0] - inicio[0], encontrada[1] - inicio[1])
        self.mover(next(d for d, v in DIRECCIONES.items() if v == paso))

    def explorar(self, sensores):
        opciones = [d for d, i in sensores.items() if i['tipo'] == 'LIBRE']
        self.model.random.shuffle(opciones)
        for d in opciones:
            if self.mover(d):
                return


class AlmacenModelo(ap.Model):
    """Parámetros (self.p): M, N, K, robots, estantes, steps (tiempo máximo), seed."""

    def setup(self):
        self.M, self.N = self.p.get('M', 14), self.p.get('N', 14)
        self.K = self.p.get('K', 20)
        self.max_pilas = math.ceil(self.K / MAX_PILA)
        self.estantes = set()
        for x, y, largo in self.p.get('estantes', []):
            self.estantes.update((x, y + i) for i in range(largo))

        self.cajas = [[0] * self.N for _ in range(self.M)]   # cajas[x][y] = altura de la pila
        self.pilas = set()                                  # celdas designadas como pila
        self.reservas = {}                                  # celda de caja -> robot
        self.ocupacion = {}                                 # celda -> robot

        libres = [(x, y) for x in range(1, self.M - 1) for y in range(1, self.N - 1)
                  if (x, y) not in self.estantes]
        self.random.shuffle(libres)
        for x, y in libres[:self.K]:
            self.cajas[x][y] = 1                            # todas a nivel de piso, sin pilas

        self.grid = ap.Grid(self, (self.M, self.N), track_empty=True)
        self.robots = ap.AgentList(self, self.p.get('robots', 5), RobotAgente)
        vacias = [p for p in libres[self.K:]]
        self.grid.add_agents(self.robots, positions=vacias[:len(self.robots)])
        for i, r in enumerate(self.robots):
            r.numero = i                                    # 0..4 (AgentPy usa otros ids internos)
        for r in self.robots:
            self.ocupacion[r.pos] = r

        self.tiempo_finalizacion = None

    def step(self):
        for r in self.robots.shuffle():      # orden aleatorio cada paso
            r.step()

    def update(self):
        self.record('movimientos', sum(r.movimientos for r in self.robots))
        if self.terminado():
            self.tiempo_finalizacion = self.t
            self.stop()

    def end(self):
        self.report('tiempo_finalizacion', self.tiempo_finalizacion)
        self.report('movimientos_totales', self.movimientos_totales())
        self.report('pilas_completas', self.pilas_completas())

    # ---------------- Mundo ----------------
    def info_celda(self, x, y):
        if x <= 0 or y <= 0 or x >= self.M - 1 or y >= self.N - 1:
            return {'tipo': 'PARED', 'cajas': 0, 'pos': (x, y)}
        if (x, y) in self.estantes:
            return {'tipo': 'ESTANTE', 'cajas': 0, 'pos': (x, y)}
        if (x, y) in self.ocupacion:
            return {'tipo': 'ROBOT', 'cajas': self.cajas[x][y], 'pos': (x, y)}
        if self.cajas[x][y] > 0:
            return {'tipo': 'CAJAS', 'cajas': self.cajas[x][y], 'pos': (x, y)}
        if (x, y) in self.pilas:      # pila designada que se quedó vacía: sigue siendo pila
            return {'tipo': 'CAJAS', 'cajas': 0, 'pos': (x, y)}
        return {'tipo': 'LIBRE', 'cajas': 0, 'pos': (x, y)}

    def transitable(self, p):
        x, y = p
        return (0 < x < self.M - 1 and 0 < y < self.N - 1 and p not in self.estantes
                and self.cajas[x][y] == 0 and p not in self.pilas)

    def robot_en(self, p):
        return self.ocupacion.get(p)

    def mover(self, robot, destino):
        if self.transitable(destino) and destino not in self.ocupacion:
            del self.ocupacion[robot.pos]
            self.grid.move_to(robot, destino)
            self.ocupacion[destino] = robot
            return True
        return False

    def retirar_caja(self, p):
        self.cajas[p[0]][p[1]] -= 1

    def agregar_caja(self, p):
        self.cajas[p[0]][p[1]] += 1

    def cajas_sueltas(self):
        return [(x, y) for x in range(self.M) for y in range(self.N)
                if self.cajas[x][y] > 0 and (x, y) not in self.pilas]

    def pilas_abiertas(self):
        return [p for p in self.pilas if self.cajas[p[0]][p[1]] < MAX_PILA]

    def reservar_caja_cercana(self, robot):
        x, y = robot.pos
        libres = [c for c in self.cajas_sueltas() if self.reservas.get(c, robot) is robot]
        if not libres:
            return None
        elegida = min(libres, key=lambda c: abs(c[0] - x) + abs(c[1] - y))
        self.reservas[elegida] = robot
        return elegida

    def liberar_reservas(self, robot):
        for c in [c for c, r in self.reservas.items() if r is robot]:
            del self.reservas[c]

    # ---------------- Métricas ----------------
    def movimientos_totales(self):
        return sum(r.movimientos for r in self.robots)

    def pilas_completas(self):
        return sum(1 for p in self.pilas if self.cajas[p[0]][p[1]] == MAX_PILA)

    def terminado(self):
        """Todas las cajas en pilas de máximo 5 (solo una pila puede quedar incompleta)."""
        if any(r.lleva_caja for r in self.robots) or self.cajas_sueltas():
            return False
        incompletas = sum(1 for p in self.pilas if 0 < self.cajas[p[0]][p[1]] < MAX_PILA)
        return incompletas <= (1 if self.K % MAX_PILA else 0)


# Configuración usada por la gráfica y por la ejecución en consola
PARAMETROS = {
    'M': 14, 'N': 14,          # celdas (el borde es pared)
    'K': 20,                   # cajas iniciales
    'robots': 5,
    'estantes': [(4, 3, 2), (4, 9, 2), (9, 3, 2), (9, 9, 2)],   # (x, y, largo en celdas)
    'steps': 1500,             # tiempo máximo de ejecución
}


if __name__ == "__main__":
    import sys
    semilla = int(sys.argv[1]) if len(sys.argv) > 1 else None
    modelo = AlmacenModelo({**PARAMETROS, 'seed': semilla})
    modelo.run(display=False)
    print(f"Terminó: {'sí' if modelo.tiempo_finalizacion else 'no (llegó al tiempo máximo)'}")
    print(f"Pasos hasta que todas las cajas quedaron en pilas: {modelo.tiempo_finalizacion or modelo.t}")
    print(f"Movimientos de todos los robots: {modelo.movimientos_totales()}")
    print(f"Pilas de 5 completas: {modelo.pilas_completas()} de {modelo.K // MAX_PILA}")
    for r in modelo.robots:
        print(f"  Robot {r.numero}: {r.movimientos} movimientos")
