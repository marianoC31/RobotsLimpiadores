"""Cajas: cada celda del modelo con altura h > 0 se dibuja como una pila de h cajas."""
import superficies

TAM_CAJA = 0.55
COLOR_CAJA = (0.82, 0.60, 0.32)
COLOR_PILA_COMPLETA = (0.30, 0.85, 0.40)    # aristas verdes cuando la pila llega a 5
ARISTAS = [(0, 1), (1, 2), (2, 3), (3, 0), (4, 5), (5, 6), (6, 7), (7, 4),
           (0, 4), (1, 5), (2, 6), (3, 7), (2, 7), (3, 6)]   # + cinta de empaque arriba

s = TAM_CAJA / 2.0
CUBO = [[-s, -s, -s], [s, -s, -s], [s, s, -s], [-s, s, -s],
        [-s, -s, s], [s, -s, s], [s, s, s], [-s, s, s]]


def dibujar_pila(bresenham, camara, op, x, z, altura, completa=False):
    color = COLOR_PILA_COMPLETA if completa else COLOR_CAJA
    for nivel in range(altura):
        op.push()
        op.translate(x, (nivel + 0.5) * TAM_CAJA, z)
        pts = op.transform_points(CUBO)
        bresenham.dibujar_aristas(camara, pts, ARISTAS, color)
        superficies.agregar_caja("caja", pts, (1.0, 1.0, 1.0))
        op.pop()
