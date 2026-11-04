import random
import math
from OpenGL.GL import *
from OpenGL.GLU import *
from robot_limpiador import bresenham_2d

class Caja:
    """
    Modelo 3D de Caja de almacén con geometría wireframe:
    - 8 vértices cúbicos, 12 aristas perimetrales y líneas diagonales de cinta de empaque.
    - Soporta nivel de apilamiento (nivel=0 en piso, hasta nivel=4 para pilas de 5 cajas).
    - Transformada con OpMat3D, proyectada con gluProject y rasterizada con bresenham_2d.
    - Iluminada matemáticamente en Python.
    """
    def __init__(self, pos_x, pos_z, tamano=0.65, rot_y=0.0, nivel=0):
        self.pos_x = float(pos_x)
        self.pos_z = float(pos_z)
        self.tamano = float(tamano)
        self.rot_y = float(rot_y)
        self.nivel = int(nivel)
        
        # Altura vertical según el nivel de la pila
        self.pos_y = (self.nivel + 0.5) * self.tamano

        self._crear_geometria()

    def _crear_geometria(self):
        s = self.tamano / 2.0
        self.pts = [
            [-s, -s, -s, 1.0], [ s, -s, -s, 1.0], [ s,  s, -s, 1.0], [-s,  s, -s, 1.0],
            [-s, -s,  s, 1.0], [ s, -s,  s, 1.0], [ s,  s,  s, 1.0], [-s,  s,  s, 1.0]
        ]
        self.edges = [
            (0,1), (1,2), (2,3), (3,0), # Cara trasera
            (4,5), (5,6), (6,7), (7,4), # Cara frontal
            (0,4), (1,5), (2,6), (3,7), # Uniones laterales
            # Cinta de empaque superior
            (2,7), (3,6)
        ]

    def render(self, mv, proj, vp, op, iluminacion, robots):
        """Transforma, proyecta y dibuja la caja arista por arista con Bresenham."""
        op.push()
        op.translate(self.pos_x, self.pos_y, self.pos_z)
        if self.rot_y != 0.0:
            op.rotateY(self.rot_y)

        t_pts = op.transform(self.pts)
        pts_2d = []
        for p in t_pts:
            wx, wy, _ = gluProject(p[0], p[1], p[2], mv, proj, vp)
            pts_2d.append((wx, wy))

        col_base = (0.82, 0.60, 0.32) # Color cartón corrugado

        for e in self.edges:
            p1_3d = t_pts[e[0]]
            p2_3d = t_pts[e[1]]
            mid = (
                (p1_3d[0] + p2_3d[0]) * 0.5,
                (p1_3d[1] + p2_3d[1]) * 0.5,
                (p1_3d[2] + p2_3d[2]) * 0.5
            )
            c = iluminacion.calcular_color(col_base, mid, (0.0, 1.0, 0.0), robots)
            glColor3f(*c)

            p1 = pts_2d[e[0]]
            p2 = pts_2d[e[1]]
            bresenham_2d(p1[0], p1[1], p2[0], p2[1])

        op.pop()

def generar_cajas_aleatorias(k=18, almacen_m=20.0, almacen_n=20.0, estantes=None, margen_pared=1.8):
    """
    Genera K cajas iniciales en posiciones aleatorias a nivel de piso (sin pilas).
    Garantiza que no colisionen con los estantes ni con las paredes.
    """
    cajas = []
    lim_x = (almacen_m / 2.0) - margen_pared
    lim_z = (almacen_n / 2.0) - margen_pared
    
    intentos = 0
    max_intentos = 2500

    while len(cajas) < k and intentos < max_intentos:
        intentos += 1
        rx = random.uniform(-lim_x, lim_x)
        rz = random.uniform(-lim_z, lim_z)

        # 1. Evitar estar dentro de un estante
        en_estante = False
        if estantes:
            for e in estantes:
                min_x, max_x, min_z, max_z = e.get_bounds(margen=0.45)
                if min_x <= rx <= max_x and min_z <= rz <= max_z:
                    en_estante = True
                    break
        if en_estante:
            continue

        # 2. Evitar solapamiento con otra caja
        solapada = False
        for c in cajas:
            if math.hypot(rx - c.pos_x, rz - c.pos_z) < 0.95:
                solapada = True
                break

        if not solapada:
            rot = random.uniform(0.0, 360.0)
            cajas.append(Caja(pos_x=rx, pos_z=rz, tamano=0.65, rot_y=rot, nivel=0))

    return cajas

def generar_pilas_cajas(k=18, almacen_m=20.0, almacen_n=20.0, estantes=None):
    """
    Agrupa K cajas en pilas de hasta 5 cajas en zonas de consolidación del almacén.
    """
    cajas = []
    posiciones_pilas = [
        (-2.2, -4.5), ( 2.2, -4.5),
        (-2.2,  4.5), ( 2.2,  4.5),
        (-2.2,  0.0), ( 2.2,  0.0)
    ]
    
    cajas_restantes = k
    idx_pila = 0

    while cajas_restantes > 0 and idx_pila < len(posiciones_pilas):
        altura_pila = min(5, cajas_restantes)
        base_x, base_z = posiciones_pilas[idx_pila]
        rot_base = (idx_pila * 35.0) % 360.0

        for nivel in range(altura_pila):
            rot = rot_base + (nivel * 4.0)
            cajas.append(Caja(pos_x=base_x, pos_z=base_z, tamano=0.65, rot_y=rot, nivel=nivel))

        cajas_restantes -= altura_pila
        idx_pila += 1

    return cajas
