# robot.py  -- Robot limpiador (wireframe) usando OpMat3D, Camara y Bresenham
import math
import pygame
from nucleo.OpMat import OpMat3D, matriz_Rx_T_Ry, matriz_T_Ry_Rx
from nucleo.Bresenham import Bresenham
from nucleo.Camara import Camara
from nucleo.Ejes import Ejes

ARISTAS_CAJA = [
    (0, 1), (1, 2), (2, 3), (3, 0),
    (4, 5), (5, 6), (6, 7), (7, 4),
    (0, 4), (1, 5), (2, 6), (3, 7),
]


def caja(x0, x1, y0, y1, z0, z1):
    """Vértices de una caja alineada a los ejes (primero cara z0, luego z1)."""
    return [
        [x0, y0, z0], [x1, y0, z0], [x1, y1, z0], [x0, y1, z0],
        [x0, y0, z1], [x1, y0, z1], [x1, y1, z1], [x0, y1, z1],
    ]


class Robot:
    def __init__(self, screen_width, screen_height):
        self.bresenham = Bresenham()
        # Cámara más lejos y con más foco: la escena mide ~6 x 8 unidades
        self.camara = Camara(screen_width, screen_height, d=800, z_offset=12.0)
        self.ejes = Ejes(self.camara, self.bresenham, longitud=3.0)

        self.op = OpMat3D()
        self.op.post = True  # modo jerárquico: transformaciones de padre a hijo

        # Variables de cinemática y movimiento
        self.pos_x = 1.5
        self.pos_z = -2.5
        self.rot_y = 0.0           # orientación general (eje Y)
        self.steering_angle = 0.0  # dirección de ruedas delanteras (eje Y)
        self.wheel_spin = 0.0      # rodamiento continuo (eje X)

        # Brazos y pinzas
        self.anim_time = 0.0
        self.arm_angle = -5.0
        self.claw_angle = 15.0

        # Parámetros de desplazamiento
        self.track_s = 0.0
        self.speed = 0.06
        self.wheel_radius = 0.42

        self._crear_geometrias_locales()

    # ------------------------------------------------------------------
    def _crear_geometrias_locales(self):
        # 1. Chasis
        w, h, l = 0.8, 0.4, 1.2
        self.chasis_pts = caja(-w, w, -h, h, -l, l)
        self.chasis_edges = ARISTAS_CAJA

        # 2. Cabina superior
        cw, ch, cl = 0.4, 0.35, 0.4
        self.cabina_pts = caja(-cw, cw, -ch, ch, -cl, cl)
        self.cabina_edges = ARISTAS_CAJA

        # 3. Rueda: dos octágonos (caras) + buje central con rayos
        r, ww = 0.42, 0.12
        self.wheel_pts = []
        for i in range(8):  # cara exterior (+ww)
            a = math.radians(i * 45)
            self.wheel_pts.append([ww, r * math.cos(a), r * math.sin(a)])
        for i in range(8):  # cara interior (-ww)
            a = math.radians(i * 45)
            self.wheel_pts.append([-ww, r * math.cos(a), r * math.sin(a)])
        self.wheel_pts.append([ww, 0.0, 0.0])   # 16: centro exterior
        self.wheel_pts.append([-ww, 0.0, 0.0])  # 17: centro interior

        self.wheel_edges = []
        for i in range(8):
            j = (i + 1) % 8
            self.wheel_edges += [
                (i, j),            # aro exterior
                (8 + i, 8 + j),    # aro interior
                (i, 8 + i),        # banda de rodadura
                (16, i),           # rayos exteriores
                (17, 8 + i),       # rayos interiores
            ]

        # 4. Soporte frontal
        self.soporte_frontal_pts = [
            [-0.65, -0.15, 0.0], [0.65, -0.15, 0.0],
            [0.65, 0.15, 0.0], [-0.65, 0.15, 0.0],
            [-0.55, -0.15, 0.1], [-0.55, 0.15, 0.1],
            [0.55, -0.15, 0.1], [0.55, 0.15, 0.1],
        ]
        self.soporte_frontal_edges = [
            (0, 1), (1, 2), (2, 3), (3, 0),
            (0, 4), (3, 5), (4, 5),
            (1, 6), (2, 7), (6, 7),
        ]

        # 5. Barra transversal entre brazos
        self.barra_transversal_pts = [[-0.55, 0.0, 0.45], [0.55, 0.0, 0.45]]
        self.barra_transversal_edges = [(0, 1)]

        # 6. Brazo lateral (viga con refuerzos diagonales)
        bw, bh, bl = 0.06, 0.08, 0.85
        self.brazo_pts = caja(-bw, bw, -bh, bh, 0.0, bl)
        self.brazo_edges = ARISTAS_CAJA + [(0, 7), (1, 6)]

        # 7. Pinzas: la izquierda se define, la derecha es su espejo en X
        self.pinza_izq_pts = [
            [0.0, 0.07, 0.0], [0.0, 0.07, 0.35], [0.32, 0.07, 0.60],
            [0.16, 0.07, 0.35], [0.24, 0.07, 0.48],
            [0.0, -0.07, 0.0], [0.0, -0.07, 0.35], [0.32, -0.07, 0.60],
            [0.16, -0.07, 0.35], [0.24, -0.07, 0.48],
        ]
        self.pinza_der_pts = [[-x, y, z] for x, y, z in self.pinza_izq_pts]
        self.pinza_edges = [
            (0, 1), (1, 2), (1, 3), (3, 4), (4, 2),
            (5, 6), (6, 7), (6, 8), (8, 9), (9, 7),
            (0, 5), (1, 6), (2, 7), (3, 8), (4, 9),
        ]

    # ------------------------------------------------------------------
    def update(self):
        keys = pygame.key.get_pressed()
        manual = False

        # d_spin = (distancia / radio) * (180 / pi)
        spin_factor = (1.0 / self.wheel_radius) * (180.0 / math.pi)

        if keys[pygame.K_UP] or keys[pygame.K_w]:
            manual = True
            rad = math.radians(self.rot_y)
            self.pos_x += self.speed * math.sin(rad)
            self.pos_z += self.speed * math.cos(rad)
            self.wheel_spin += self.speed * spin_factor
        elif keys[pygame.K_DOWN] or keys[pygame.K_s]:
            manual = True
            rad = math.radians(self.rot_y)
            self.pos_x -= self.speed * math.sin(rad)
            self.pos_z -= self.speed * math.cos(rad)
            self.wheel_spin -= self.speed * spin_factor

        if keys[pygame.K_LEFT] or keys[pygame.K_a]:
            manual = True
            self.steering_angle = max(-30.0, self.steering_angle - 3.0)
            if keys[pygame.K_UP] or keys[pygame.K_w]:
                self.rot_y -= 2.0
            elif keys[pygame.K_DOWN] or keys[pygame.K_s]:
                self.rot_y += 2.0
        elif keys[pygame.K_RIGHT] or keys[pygame.K_d]:
            manual = True
            self.steering_angle = min(30.0, self.steering_angle + 3.0)
            if keys[pygame.K_UP] or keys[pygame.K_w]:
                self.rot_y += 2.0
            elif keys[pygame.K_DOWN] or keys[pygame.K_s]:
                self.rot_y -= 2.0
        elif manual:
            self.steering_angle *= 0.8

        # Recorrido automático si no se toca el teclado
        if not manual:
            L = 5.0
            R = 1.5
            half_circ = math.pi * R
            P = 2.0 * L + 2.0 * half_circ

            self.track_s = (self.track_s + self.speed) % P
            s = self.track_s

            if s < L:
                self.pos_x = R
                self.pos_z = -2.5 + (s / L) * L
                self.rot_y = 0.0
                target_steer = 0.0
            elif s < L + half_circ:
                phi = (s - L) / R
                self.pos_x = R * math.cos(phi)
                self.pos_z = 2.5 + R * math.sin(phi)
                self.rot_y = -math.degrees(phi)
                target_steer = -28.0
            elif s < 2.0 * L + half_circ:
                t = (s - (L + half_circ)) / L
                self.pos_x = -R
                self.pos_z = 2.5 - t * L
                self.rot_y = 180.0
                target_steer = 0.0
            else:
                phi = (s - (2.0 * L + half_circ)) / R
                self.pos_x = -R * math.cos(phi)
                self.pos_z = -2.5 - R * math.sin(phi)
                self.rot_y = 180.0 - math.degrees(phi)
                target_steer = -28.0

            self.steering_angle += (target_steer - self.steering_angle) * 0.15
            self.wheel_spin += self.speed * spin_factor

        self.wheel_spin %= 360.0

        # Animación de brazos y pinzas
        self.anim_time += 0.08
        self.claw_angle = 15.0 + 15.0 * math.sin(self.anim_time * 2.2)
        self.arm_angle = -5.0 + 7.0 * math.sin(self.anim_time * 1.1)

    # ------------------------------------------------------------------
    def _dibujar(self, surface, pts, edges, color=(255, 255, 255)):
        """Transforma con la matriz actual, proyecta con la cámara y traza con Bresenham."""
        pts_3d = self.op.transform_points(pts)
        pts_2d = [self.camara.proyectar(p) for p in pts_3d]
        for a, b in edges:
            p1, p2 = pts_2d[a], pts_2d[b]
            self.bresenham.linea(surface, p1[0], p1[1], p2[0], p2[1], color)

    def render(self, surface):
        self.ejes.render(surface)

        op = self.op

        # Vista (inclinación de cámara) -> posición y orientación global del robot.
        # Equivale a reset(); rotate_x(-25); translate(...); rotate_y(...),
        # pero con la matriz ya colapsada en una sola fórmula.
        op.M = matriz_Rx_T_Ry(-25, self.pos_x, 0.5, self.pos_z, self.rot_y)

        # Chasis
        self._dibujar(surface, self.chasis_pts, self.chasis_edges)

        # Cabina (hija del chasis)
        op.push()
        op.translate(0.0, 0.75, 0.3)
        self._dibujar(surface, self.cabina_pts, self.cabina_edges)
        op.pop()

        # Ruedas: T·Ry(dirección)·Rx(rodamiento) en una sola matriz.
        # Las traseras no giran la dirección (phi = 0).
        ruedas = [
            ((-0.95, -0.1, -0.8), 0.0),
            ((0.95, -0.1, -0.8), 0.0),
            ((-0.95, -0.1, 0.8), self.steering_angle),
            ((0.95, -0.1, 0.8), self.steering_angle),
        ]
        for pos, phi in ruedas:
            op.push()
            op.multiplicar(matriz_T_Ry_Rx(*pos, phi, self.wheel_spin))
            self._dibujar(surface, self.wheel_pts, self.wheel_edges)
            op.pop()

        # Soporte frontal
        op.push()
        op.translate(0.0, -0.15, 1.2)
        self._dibujar(surface, self.soporte_frontal_pts, self.soporte_frontal_edges)
        op.pop()

        # Sistema de brazos
        op.push()
        op.translate(0.0, -0.15, 1.25)
        op.rotate_x(self.arm_angle)

        self._dibujar(surface, self.barra_transversal_pts, self.barra_transversal_edges)

        # Brazo izquierdo + garra
        op.push()
        op.translate(-0.55, 0.0, 0.0)
        self._dibujar(surface, self.brazo_pts, self.brazo_edges)
        op.push()
        op.translate(0.0, 0.0, 0.85)
        op.rotate_y(-self.claw_angle)
        self._dibujar(surface, self.pinza_izq_pts, self.pinza_edges)
        op.pop()
        op.pop()

        # Brazo derecho + garra
        op.push()
        op.translate(0.55, 0.0, 0.0)
        self._dibujar(surface, self.brazo_pts, self.brazo_edges)
        op.push()
        op.translate(0.0, 0.0, 0.85)
        op.rotate_y(self.claw_angle)
        self._dibujar(surface, self.pinza_der_pts, self.pinza_edges)
        op.pop()
        op.pop()

        op.pop()  # fin sistema de brazos