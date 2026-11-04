from OpenGL.GL import *
from OpenGL.GLU import *
from robot_limpiador import bresenham_2d

class Almacen:
    """
    Modelo 3D del Almacén de dimensiones M x N espacios:
    - Piso: Rejilla de celdas con líneas de seguridad amarillas que delimitan los pasillos.
    - Paredes: Muros perimetrales Norte, Oeste, Este y Sur con zócalos.
    - Puerta: Portón seccional industrial en la pared Sur con franjas de advertencia.
    - Renderizado exclusivamente mediante proyección 3D->2D y algoritmo bresenham_2d.
    - Iluminación matemática calculada en Python.
    """
    def __init__(self, m=20.0, n=20.0, altura=4.0):
        self.m = float(m)
        self.n = float(n)
        self.altura = float(altura)

        self.ancho_puerta = 3.6
        self.alto_puerta = 3.2

        self._crear_geometria()

    def _crear_geometria(self):
        hx = self.m / 2.0
        hz = self.n / 2.0
        h = self.altura

        # 1. PISO: Cuadrícula de Celdas (Espacios M x N)
        self.piso_lineas = []
        # Líneas a lo largo de X (paralelas a X)
        paso_z = 2.0
        z = -hz
        while z <= hz + 1e-4:
            self.piso_lineas.append(([-hx, 0.0, z], [hx, 0.0, z]))
            z += paso_z

        # Líneas a lo largo de Z (paralelas a Z)
        paso_x = 2.0
        x = -hx
        while x <= hx + 1e-4:
            self.piso_lineas.append(([x, 0.0, -hz], [x, 0.0, hz]))
            x += paso_x

        # 2. DEMARCACIONES DE SEGURIDAD EN PASILLOS (Líneas amarillas)
        self.demarcaciones = [
            # Pasillo Oeste (X = -5.8)
            ([-5.8, 0.01, -hz + 1.5], [-5.8, 0.01, hz - 1.5]),
            # Pasillo Central Carril Izquierdo (X = -2.6)
            ([-2.6, 0.01, -hz + 1.5], [-2.6, 0.01, hz - 1.5]),
            # Pasillo Central Carril Derecho (X = +2.6)
            ([ 2.6, 0.01, -hz + 1.5], [ 2.6, 0.01, hz - 1.5]),
            # Pasillo Este (X = +5.8)
            ([ 5.8, 0.01, -hz + 1.5], [ 5.8, 0.01, hz - 1.5]),
            # Pasillos transversales Norte y Sur
            ([-hx + 1.5, 0.01, -6.8], [hx - 1.5, 0.01, -6.8]),
            ([-hx + 1.5, 0.01,  6.8], [hx - 1.5, 0.01,  6.8]),
            # Recuadro de bahía de carga frente a la puerta
            ([-self.ancho_puerta/2.0 - 0.4, 0.01, hz - 2.5], [ self.ancho_puerta/2.0 + 0.4, 0.01, hz - 2.5]),
            ([-self.ancho_puerta/2.0 - 0.4, 0.01, hz],       [-self.ancho_puerta/2.0 - 0.4, 0.01, hz - 2.5]),
            ([ self.ancho_puerta/2.0 + 0.4, 0.01, hz],       [ self.ancho_puerta/2.0 + 0.4, 0.01, hz - 2.5])
        ]

        # 3. PAREDES PERIMETRALES
        self.pared_lineas = [
            # Base del almacén
            ([-hx, 0.0, -hz], [ hx, 0.0, -hz]),
            ([ hx, 0.0, -hz], [ hx, 0.0,  hz]),
            ([-hx, 0.0,  hz], [-hx, 0.0, -hz]),
            # Techo / Corona de muros
            ([-hx, h, -hz], [ hx, h, -hz]),
            ([ hx, h, -hz], [ hx, h,  hz]),
            ([ hx, h,  hz], [-hx, h,  hz]),
            ([-hx, h,  hz], [-hx, h, -hz]),
            # Columnas en las 4 esquinas
            ([-hx, 0.0, -hz], [-hx, h, -hz]),
            ([ hx, 0.0, -hz], [ hx, h, -hz]),
            ([ hx, 0.0,  hz], [ hx, h,  hz]),
            ([-hx, 0.0,  hz], [-hx, h,  hz]),
            # Zócalo perimetral (a 0.5m de altura)
            ([-hx, 0.5, -hz], [ hx, 0.5, -hz]),
            ([ hx, 0.5, -hz], [ hx, 0.5,  hz]),
            ([-hx, 0.5,  hz], [-hx, 0.5, -hz]),
            # Pared Sur dividida
            ([-hx, 0.0, hz], [-self.ancho_puerta/2.0, 0.0, hz]),
            ([ self.ancho_puerta/2.0, 0.0, hz], [hx, 0.0, hz]),
            ([-hx, 0.5, hz], [-self.ancho_puerta/2.0, 0.5, hz]),
            ([ self.ancho_puerta/2.0, 0.5, hz], [hx, 0.5, hz])
        ]

        # 4. PUERTA SECCIONAL EN PARED SUR
        pw = self.ancho_puerta / 2.0
        ph = self.alto_puerta
        self.puerta_lineas = [
            # Marco de la puerta
            ([-pw, 0.0, hz], [-pw, ph, hz]),
            ([ pw, 0.0, hz], [ pw, ph, hz]),
            ([-pw, ph, hz],  [ pw, ph, hz]),
            # Dintel superior hacia el techo
            ([-pw, ph, hz], [-pw, h, hz]),
            ([ pw, ph, hz], [ pw, h, hz]),
            # Paneles seccionales horizontales
            ([-pw, 0.8, hz], [pw, 0.8, hz]),
            ([-pw, 1.6, hz], [pw, 1.6, hz]),
            ([-pw, 2.4, hz], [pw, 2.4, hz]),
            # Manija / cerradura
            ([pw - 0.4, 1.2, hz], [pw - 0.2, 1.2, hz])
        ]

    def render(self, mv, proj, vp, iluminacion, robots):
        """Dibuja todo el almacén proyectado a 2D y rasterizado con Bresenham."""
        # 1. PISO (Rejilla de celdas en gris tenue)
        col_piso = (0.35, 0.38, 0.42)
        for p1, p2 in self.piso_lineas:
            mid = ((p1[0]+p2[0])*0.5, (p1[1]+p2[1])*0.5, (p1[2]+p2[2])*0.5)
            c = iluminacion.calcular_color(col_piso, mid, (0.0, 1.0, 0.0), robots)
            glColor3f(*c)
            wx1, wy1, _ = gluProject(*p1, mv, proj, vp)
            wx2, wy2, _ = gluProject(*p2, mv, proj, vp)
            bresenham_2d(wx1, wy1, wx2, wy2)

        # 2. DEMARCACIONES AMARILLAS DE PASILLOS
        col_amarillo = (0.92, 0.75, 0.10)
        for p1, p2 in self.demarcaciones:
            mid = ((p1[0]+p2[0])*0.5, (p1[1]+p2[1])*0.5, (p1[2]+p2[2])*0.5)
            c = iluminacion.calcular_color(col_amarillo, mid, (0.0, 1.0, 0.0), robots)
            glColor3f(*c)
            wx1, wy1, _ = gluProject(*p1, mv, proj, vp)
            wx2, wy2, _ = gluProject(*p2, mv, proj, vp)
            bresenham_2d(wx1, wy1, wx2, wy2)

        # 3. PAREDES PERIMETRALES (Líneas de muros y zócalo)
        col_pared = (0.55, 0.60, 0.66)
        for p1, p2 in self.pared_lineas:
            mid = ((p1[0]+p2[0])*0.5, (p1[1]+p2[1])*0.5, (p1[2]+p2[2])*0.5)
            c = iluminacion.calcular_color(col_pared, mid, (0.0, 0.5, 0.5), robots)
            glColor3f(*c)
            wx1, wy1, _ = gluProject(*p1, mv, proj, vp)
            wx2, wy2, _ = gluProject(*p2, mv, proj, vp)
            bresenham_2d(wx1, wy1, wx2, wy2)

        # 4. PUERTA SECCIONAL (Metálica azul / seguridad)
        col_puerta = (0.30, 0.65, 0.95)
        for p1, p2 in self.puerta_lineas:
            mid = ((p1[0]+p2[0])*0.5, (p1[1]+p2[1])*0.5, (p1[2]+p2[2])*0.5)
            c = iluminacion.calcular_color(col_puerta, mid, (0.0, 0.0, -1.0), robots)
            glColor3f(*c)
            wx1, wy1, _ = gluProject(*p1, mv, proj, vp)
            wx2, wy2, _ = gluProject(*p2, mv, proj, vp)
            bresenham_2d(wx1, wy1, wx2, wy2)
