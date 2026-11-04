"""Estante: ocupa celdas bloqueadas del modelo de AgentPy (los robots lo rodean)."""
import superficies

COLOR_POSTES = (0.25, 0.55, 0.90)
COLOR_VIGAS = (0.95, 0.45, 0.08)
COLOR_CAJA = (0.82, 0.60, 0.32)
ARISTAS_CAJA = [(0, 1), (1, 2), (2, 3), (3, 0), (4, 5), (5, 6), (6, 7), (7, 4), (0, 4), (1, 5), (2, 6), (3, 7)]


class Estante:

    def __init__(self, x, z, bresenham, ancho=1.6, largo=3.2, alto=2.8):
        self.x, self.z = x, z
        self.bresenham = bresenham
        hx, hz, h = ancho / 2.0, largo / 2.0, alto
        self.niveles = (0.2, 1.4, h)
        self.hx, self.hz = hx, hz
        # Postes, vigas en 3 niveles y refuerzos en X (coordenadas locales)
        self.postes = [([sx * hx, 0.0, sz * hz], [sx * hx, h, sz * hz]) for sx in (-1, 1) for sz in (-1, 1)]
        self.vigas = []
        for y in self.niveles:
            self.vigas += [([-hx, y, hz], [hx, y, hz]), ([-hx, y, -hz], [hx, y, -hz]),
                           ([-hx, y, -hz], [-hx, y, hz]), ([hx, y, -hz], [hx, y, hz])]
        for sx in (-1, 1):
            self.vigas += [([sx * hx, 0.2, -hz], [sx * hx, 1.4, hz]), ([sx * hx, 0.2, hz], [sx * hx, 1.4, -hz])]
        # Dos cajas guardadas arriba
        c = 0.28
        self.cajas = [[[-c, h, cz - c], [c, h, cz - c], [c, h + 2 * c, cz - c], [-c, h + 2 * c, cz - c],
                       [-c, h, cz + c], [c, h, cz + c], [c, h + 2 * c, cz + c], [-c, h + 2 * c, cz + c]]
                      for cz in (-0.8, 0.8)]

    def render(self, camara, op):
        op.push()
        op.translate(self.x, 0.0, self.z)
        for lineas, color in ((self.postes, COLOR_POSTES), (self.vigas, COLOR_VIGAS)):
            pts = op.transform_points([p for linea in lineas for p in linea])
            self.bresenham.dibujar_aristas(camara, pts, [(2 * i, 2 * i + 1) for i in range(len(lineas))], color)
        # Repisas con textura (UV: la imagen se repite 2 veces a lo largo)
        hx, hz = self.hx, self.hz
        for y in self.niveles:
            repisa = op.transform_points([[-hx, y, -hz], [hx, y, -hz], [hx, y, hz], [-hx, y, hz]])
            superficies.agregar_quad("estante", repisa, ((0, 0), (1, 0), (1, 2), (0, 2)), COLOR_VIGAS)
        for caja in self.cajas:
            pts = op.transform_points(caja)
            self.bresenham.dibujar_aristas(camara, pts, ARISTAS_CAJA, COLOR_CAJA)
            superficies.agregar_caja("caja", pts, (1.0, 1.0, 1.0))
        op.pop()
