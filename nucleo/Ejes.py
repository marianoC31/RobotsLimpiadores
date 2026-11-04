# ejes.py
import pygame
from nucleo.OpMat import OpMat3D


class Ejes:
    """Dibuja los ejes X (rojo), Y (verde) y Z (azul) desde el origen."""

    def __init__(self, camara, bresenham, longitud=3, rot_x=-25):
        self.camara = camara
        self.bresenham = bresenham
        self.longitud = longitud
        self.rot_x = rot_x  # misma inclinación de vista que la pirámide
        self.op_mat = OpMat3D()
        self.font = pygame.font.SysFont("consolas", 18)

        L = longitud
        self.origen = [0.0, 0.0, 0.0]
        # (punto final, color, etiqueta)
        self.ejes = [
            ([L, 0.0, 0.0], (255, 60, 60), "X"),
            ([0.0, L, 0.0], (60, 255, 60), "Y"),
            ([0.0, 0.0, L], (80, 120, 255), "Z"),
        ]

    def render(self, surface, op_mat=None, factor=1.0):
        # Sin op_mat: ejes del mundo (solo inclinación de vista).
        # Con op_mat: ejes locales, transformados igual que el objeto.
        if op_mat is None:
            self.op_mat.reset()
            self.op_mat.rotate_x(self.rot_x)
            op_mat = self.op_mat

        # factor compensa la escala del objeto para que ambos modos midan lo mismo
        puntos = [[c * factor for c in self.origen]] + [[c * factor for c in e[0]] for e in self.ejes]
        puntos_t = op_mat.transform_points(puntos)
        puntos_2d = [self.camara.proyectar(p) for p in puntos_t]

        o = puntos_2d[0]
        for i, (_, color, etiqueta) in enumerate(self.ejes):
            fin = puntos_2d[i + 1]
            self.bresenham.linea(surface, o[0], o[1], fin[0], fin[1], color)
            texto = self.font.render(etiqueta, True, color)
            surface.blit(texto, (int(fin[0]) + 6, int(fin[1]) - 8))