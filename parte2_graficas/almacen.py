"""Almacén: piso, paredes y puerta, construidos a partir de la cuadrícula del modelo.

La cuadrícula de AgentPy tiene M x N celdas y su borde es pared, así que el piso
caminable son las (M-2) x (N-2) celdas interiores.  Cada celda mide TAM_CELDA m.
"""
import math
import superficies

TAM_CELDA = 2.0
COLOR_PISO = (0.35, 0.38, 0.42)
COLOR_PARED = (0.55, 0.60, 0.66)
COLOR_PUERTA = (0.30, 0.65, 0.95)
BLANCO = (1.0, 1.0, 1.0)


class Almacen:

    def __init__(self, M, N, bresenham, altura=4.0, ancho_puerta=3.6, alto_puerta=3.2):
        self.M, self.N = M, N
        self.bresenham = bresenham
        self.hx = (M - 2) * TAM_CELDA / 2.0      # medio ancho del piso interior
        self.hz = (N - 2) * TAM_CELDA / 2.0
        self.altura = altura
        self.pw, self.ph = ancho_puerta / 2.0, alto_puerta
        self._crear_geometria()

    def centro_celda(self, x, y):
        """Celda (x, y) de la cuadrícula -> punto (x, z) del mundo."""
        return ((x - self.M / 2.0 + 0.5) * TAM_CELDA, (y - self.N / 2.0 + 0.5) * TAM_CELDA)

    def _crear_geometria(self):
        hx, hz, h, pw, ph = self.hx, self.hz, self.altura, self.pw, self.ph
        # Piso: una línea por cada borde de celda
        self.piso = []
        x = -hx
        while x <= hx + 1e-6:
            self.piso.append(([x, 0.0, -hz], [x, 0.0, hz]))
            x += TAM_CELDA
        z = -hz
        while z <= hz + 1e-6:
            self.piso.append(([-hx, 0.0, z], [hx, 0.0, z]))
            z += TAM_CELDA
        # Paredes: contorno superior y columnas de las esquinas
        esquinas = [(-hx, -hz), (hx, -hz), (hx, hz), (-hx, hz)]
        self.paredes = []
        for i, (xa, za) in enumerate(esquinas):
            xb, zb = esquinas[(i + 1) % 4]
            self.paredes.append(([xa, h, za], [xb, h, zb]))
            self.paredes.append(([xa, 0.0, za], [xa, h, za]))
        # Puerta en la pared sur (z = +hz)
        self.puerta = [([-pw, 0.0, hz], [-pw, ph, hz]), ([pw, 0.0, hz], [pw, ph, hz]),
                       ([-pw, ph, hz], [pw, ph, hz]),
                       ([-pw, 0.8, hz], [pw, 0.8, hz]), ([-pw, 1.6, hz], [pw, 1.6, hz]),
                       ([-pw, 2.4, hz], [pw, 2.4, hz])]

    def _lineas(self, camara, lineas, color):
        pts = [p for linea in lineas for p in linea]
        self.bresenham.dibujar_aristas(camara, pts, [(2 * i, 2 * i + 1) for i in range(len(lineas))], color)

    def render(self, camara):
        hx, hz, h, pw, ph = self.hx, self.hz, self.altura, self.pw, self.ph
        T = TAM_CELDA

        # ---- Aristas (Bresenham) ----
        self._lineas(camara, self.piso, COLOR_PISO)
        self._lineas(camara, self.paredes, COLOR_PARED)
        self._lineas(camara, self.puerta, COLOR_PUERTA)

        # ---- Caras con textura ----
        # Piso: una baldosa por celda (UV 0..1 cada una)
        x = -hx
        while x < hx - 1e-6:
            z = -hz
            while z < hz - 1e-6:
                superficies.agregar_quad("piso", [[x, 0, z], [x + T, 0, z], [x + T, 0, z + T], [x, 0, z + T]],
                                         superficies.UV_CARA, BLANCO)
                z += T
            x += T

        # Paredes en tramos de 2 m (v = altura / 2 para que la textura no se estire).
        # Vista desde afuera, una pared se pinta semitransparente para no tapar el almacén.
        ox, _, oz = camara.ojo
        paredes = [((-hx, -hz), (hx, -hz), (0, 1)),    # norte (normal hacia adentro: +z)
                   ((-hx, hz), (-hx, -hz), (1, 0)),    # oeste
                   ((hx, -hz), (hx, hz), (-1, 0)),     # este
                   ((hx, hz), (pw, hz), (0, -1)),      # sur, a la derecha de la puerta
                   ((-pw, hz), (-hx, hz), (0, -1))]    # sur, a la izquierda de la puerta
        for (x1, z1), (x2, z2), (nx, nz) in paredes:
            transparente = (ox - x1) * nx + (oz - z1) * nz <= 0
            pasos = max(1, round(math.hypot(x2 - x1, z2 - z1) / T))
            for i in range(pasos):
                a, b = i / pasos, (i + 1) / pasos
                xa, za = x1 + (x2 - x1) * a, z1 + (z2 - z1) * a
                xb, zb = x1 + (x2 - x1) * b, z1 + (z2 - z1) * b
                superficies.agregar_quad("pared", [[xa, 0, za], [xb, 0, zb], [xb, h, zb], [xa, h, za]],
                                         ((0, 0), (1, 0), (1, h / T), (0, h / T)), BLANCO, transparente)
        sur_transparente = oz >= hz
        superficies.agregar_quad("pared", [[pw, ph, hz], [-pw, ph, hz], [-pw, h, hz], [pw, h, hz]],
                                 ((0, 0), (pw, 0), (pw, (h - ph) / T), (0, (h - ph) / T)), BLANCO, sur_transparente)
        zp = hz - 0.02
        superficies.agregar_quad("puerta", [[pw, 0, zp], [-pw, 0, zp], [-pw, ph, zp], [pw, ph, zp]],
                                 superficies.UV_CARA, BLANCO, sur_transparente)
