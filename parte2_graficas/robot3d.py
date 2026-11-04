"""Robot 3D: representa a un agente de AgentPy (no decide nada por sí mismo).

En cada paso de la simulación, nuevo_paso(agente) lee lo que hizo el agente
(moverse, recoger, apilar o esperar).  Durante los cuadros de ese paso,
update(f) anima la transición con f de 0 a 1:
    - si cambió de dirección, primero gira en su lugar (ruedas omnidireccionales),
    - luego avanza de la celda anterior a la nueva,
    - al recoger/apilar, baja los brazos y cierra/abre las pinzas.
render(camara) dibuja la jerarquía de piezas con OpMat3D (push/pop):
aristas con la clase Bresenham y caras con textura.
"""
import math
from nucleo.OpMat import OpMat3D, matriz_T_Ry, matriz_T_Ry_Rx
import superficies

ESCALA = 0.5            # el modelo mide ~2.1 x 3.5 unidades; en el almacén cada celda mide 2 m
ALTURA_BASE = 0.26      # para que las ruedas toquen el piso
RUMBO = {'S': 0.0, 'E': 90.0, 'N': 180.0, 'O': 270.0}   # dirección de la cuadrícula -> grados en Y

COLOR_CHASIS = (0.92, 0.70, 0.08)
COLOR_RUEDA = (0.50, 0.52, 0.58)
COLOR_BRAZO = (0.95, 0.45, 0.05)
COLOR_PINZA = (0.65, 0.68, 0.72)
COLOR_CAJA = (0.82, 0.60, 0.32)
COLORES_CABINA = [(1.0, 0.25, 0.2), (0.25, 0.55, 1.0), (1.0, 0.7, 0.1), (0.2, 0.9, 0.4), (0.9, 0.3, 0.85)]

CAJA_ARISTAS = [(0, 1), (1, 2), (2, 3), (3, 0), (4, 5), (5, 6), (6, 7), (7, 4),
                (0, 4), (1, 5), (2, 6), (3, 7), (2, 7), (3, 6)]


def _caja(w, h, l):
    return [[-w, -h, -l], [w, -h, -l], [w, h, -l], [-w, h, -l],
            [-w, -h, l], [w, -h, l], [w, h, l], [-w, h, l]]


def _suave(t):
    t = max(0.0, min(1.0, t))
    return t * t * (3.0 - 2.0 * t)


class Robot3D:

    def __init__(self, agente, almacen, bresenham):
        self.agente = agente
        self.almacen = almacen
        self.bresenham = bresenham
        self.color_cabina = COLORES_CABINA[agente.numero % len(COLORES_CABINA)]
        self.op = OpMat3D(post=True)      # jerárquico: M = M·T

        x, z = almacen.centro_celda(*agente.pos)
        self.desde = self.hasta = (x, z)
        self.rumbo_desde = self.rumbo_hasta = RUMBO[agente.orientacion]
        self.accion = 'esperar'
        self.lleva_caja = self.lleva_antes = False

        # Estado animado (lo calcula update, lo usa render)
        self.pos_x, self.pos_z = x, z
        self.rot_y = self.rumbo_desde
        self.wheel_spin = 0.0
        self.steering_angle = 0.0
        self.arm_angle = -5.0
        self.claw_angle = 15.0
        self.mostrar_caja = False
        self._crear_geometria()

    # ------------------------------------------------------------------
    def nuevo_paso(self, agente):
        """Lee el resultado del paso de AgentPy y prepara su animación."""
        self.desde = (self.pos_x, self.pos_z)
        self.hasta = self.almacen.centro_celda(*agente.pos)
        self.rumbo_desde = self.rot_y
        self.rumbo_hasta = RUMBO[agente.orientacion]
        self.accion = agente.accion
        self.lleva_antes = self.lleva_caja
        self.lleva_caja = agente.lleva_caja

    def update(self, f):
        """Animación del paso actual; f va de 0 (inicio del paso) a 1 (fin)."""
        giro = (self.rumbo_hasta - self.rumbo_desde + 180.0) % 360.0 - 180.0
        # Todos con el mismo ritmo: giran en el primer 40 % del paso y avanzan en el resto.
        # Así, si un robot entra a la celda que otro está dejando, ambos se mueven a la vez.
        f_giro, f_avance = _suave(f / 0.4), _suave((f - 0.4) / 0.6)

        self.rot_y = self.rumbo_desde + giro * f_giro
        self.steering_angle = max(-30.0, min(30.0, giro * (1.0 - f_giro)))
        x_antes, z_antes = self.pos_x, self.pos_z
        self.pos_x = self.desde[0] + (self.hasta[0] - self.desde[0]) * f_avance
        self.pos_z = self.desde[1] + (self.hasta[1] - self.desde[1]) * f_avance
        avance = math.hypot(self.pos_x - x_antes, self.pos_z - z_antes)
        self.wheel_spin = (self.wheel_spin + math.degrees(avance / (0.42 * ESCALA))) % 360.0

        # Brazos y pinzas
        if self.accion in ('recoger', 'apilar'):
            bajar = math.sin(math.pi * f)                  # baja y vuelve a subir
            self.arm_angle = -5.0 + 14.0 * bajar
            cerrada = f >= 0.5 if self.accion == 'recoger' else f < 0.5
            self.claw_angle = 6.0 if cerrada else 15.0
            self.mostrar_caja = cerrada                    # la caja pasa a las pinzas a la mitad
        else:
            self.arm_angle = -2.0 if self.lleva_caja else -5.0
            self.claw_angle = 6.0 if self.lleva_caja else 15.0
            self.mostrar_caja = self.lleva_caja

    # ------------------------------------------------------------------
    def _dibujar(self, camara, pts, aristas, color):
        self.bresenham.dibujar_aristas(camara, self.op.transform_points(pts), aristas, color)

    def render(self, camara):
        op = self.op
        op.reset()
        # Posición y orientación en el piso (colapsada) y escala del modelo
        op.M = matriz_T_Ry(self.pos_x, ALTURA_BASE, self.pos_z, self.rot_y)
        op.scale(ESCALA, ESCALA, ESCALA)

        # Chasis (con textura) y sensor de presión (verde si lleva caja)
        self._dibujar(camara, self.chasis_pts, self.chasis_aristas, COLOR_CHASIS)
        superficies.agregar_caja("robot_metal", op.transform_points(self.chasis_pts), COLOR_CHASIS)
        self._dibujar(camara, self.sensor_pts, self.sensor_aristas,
                      (0.1, 1.0, 0.2) if self.lleva_caja else (0.2, 0.3, 0.2))

        # Cabina (hija del chasis), con el color de cada robot
        op.push()
        op.translate(0.0, 0.65, 0.2)
        self._dibujar(camara, self.cabina_pts, self.cabina_aristas, self.color_cabina)
        superficies.agregar_caja("robot_metal", op.transform_points(self.cabina_pts), self.color_cabina)
        op.pop()

        # Ruedas: T·Ry(dirección)·Rx(rodamiento) colapsada; solo las delanteras giran la dirección
        for (px, py, pz), delantera in (((-0.95, -0.1, -0.8), False), ((0.95, -0.1, -0.8), False),
                                         ((-0.95, -0.1, 0.8), True), ((0.95, -0.1, 0.8), True)):
            op.push()
            op.multiplicar(matriz_T_Ry_Rx(px, py, pz, self.steering_angle if delantera else 0.0,
                                          self.wheel_spin))
            self._dibujar(camara, self.rueda_pts, self.rueda_aristas, COLOR_RUEDA)
            op.pop()

        # Brazos y pinzas
        op.push()
        op.translate(0.0, -0.15, 1.25)
        op.rotate_x(self.arm_angle)
        self._dibujar(camara, self.barra_pts, self.barra_aristas, COLOR_PINZA)
        for lado, signo in ((-0.55, -1.0), (0.55, 1.0)):
            op.push()
            op.translate(lado, 0.0, 0.0)
            self._dibujar(camara, self.brazo_pts, [(0, 1)], COLOR_BRAZO)
            op.translate(0.0, 0.0, 0.45)
            op.rotate_y(signo * self.claw_angle)
            pinza = self.pinza_izq_pts if signo < 0 else self.pinza_der_pts
            self._dibujar(camara, pinza, [(0, 1), (1, 2)], COLOR_PINZA)
            op.pop()
        if self.mostrar_caja:
            op.push()
            op.translate(0.0, 0.0, 0.70)
            self._dibujar(camara, self.caja_cargo_pts, CAJA_ARISTAS, COLOR_CAJA)
            superficies.agregar_caja("caja", op.transform_points(self.caja_cargo_pts), (1.0, 1.0, 1.0))
            op.pop()
        op.pop()

    # ------------------------------------------------------------------
    def _crear_geometria(self):
        self.chasis_pts = _caja(0.8, 0.4, 1.2)
        self.chasis_aristas = CAJA_ARISTAS[:12] + [(2, 5), (3, 4)]
        self.cabina_pts = _caja(0.35, 0.25, 0.35)
        self.cabina_aristas = CAJA_ARISTAS[:12]

        # Sensor de presión: placa al frente del chasis
        self.sensor_pts = [[-0.15, -0.06, 1.22], [0.15, -0.06, 1.22], [0.15, 0.06, 1.22], [-0.15, 0.06, 1.22]]
        self.sensor_aristas = [(0, 1), (1, 2), (2, 3), (3, 0), (0, 2), (1, 3)]

        # Rueda omnidireccional: dos octágonos + rodillos a 45°
        r, w = 0.42, 0.12
        self.rueda_pts = ([[w, r * math.cos(math.radians(i * 45)), r * math.sin(math.radians(i * 45))] for i in range(8)]
                          + [[-w, r * math.cos(math.radians(i * 45)), r * math.sin(math.radians(i * 45))] for i in range(8)]
                          + [[w, 0.0, 0.0]])
        self.rueda_aristas = ([(i, (i + 1) % 8) for i in range(8)] + [(8 + i, 8 + (i + 1) % 8) for i in range(8)]
                              + [(i, 8 + i) for i in range(8)] + [(16, 0), (16, 2), (16, 4), (16, 6)]
                              + [(i, 8 + (i + 1) % 8) for i in range(8)])

        self.barra_pts = [[-0.55, 0.0, 0.0], [0.55, 0.0, 0.0], [-0.55, 0.0, 0.08], [0.55, 0.0, 0.08]]
        self.barra_aristas = [(0, 1), (2, 3), (0, 2), (1, 3)]
        self.brazo_pts = [[0.0, 0.0, 0.0], [0.0, 0.0, 0.45]]
        self.pinza_izq_pts = [[0.0, 0.0, 0.0], [0.0, 0.0, 0.35], [0.22, 0.0, 0.35]]
        self.pinza_der_pts = [[0.0, 0.0, 0.0], [0.0, 0.0, 0.35], [-0.22, 0.0, 0.35]]
        cs = 0.55     # caja transportada: 0.55 x 2 x ESCALA = 0.55 m, igual que las del piso
        self.caja_cargo_pts = _caja(cs, cs, cs)
