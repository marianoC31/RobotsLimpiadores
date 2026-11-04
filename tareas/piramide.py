import pygame
from nucleo.OpMat import OpMat3D
from nucleo.Bresenham import Bresenham
from nucleo.Camara import Camara
from nucleo.Ejes import Ejes


class Piramide:
    def __init__(self, screen_width, screen_height):
        self.width = screen_width
        self.height = screen_height

        # Clases auxiliares
        self.bresenham = Bresenham()
        self.camara = Camara(screen_width, screen_height)
        self.ejes = Ejes(self.camara, self.bresenham)
        self.ejes_locales = False  # False: ejes del mundo, True: giran con la pirámide

        #para agarrar la piramide de un ladinshki y que gire bien loco
        self.escala = 1.5
        #Variables de control
        self.deg = 0.0
        self.delta_deg = 2.0 #Que tan rapido gira

        self.vertices_unitarios = [
            [0.0, 0.0, 0.0], # 0: Base-inferior-izquierda
            [ 1.0, 0.0, 0.0], # 1: Base-inferior-derecha
            [ 1.0, 0.0,  1.0], # 2: Base-superior-derecha
            [0.0, 0.0,  1.0], # 3: Base-superior-izquierda
            [ 0.5,  1.0,  0.5] #Peak
        ]
        self.pivote = self.vertices_unitarios[0]

        self.aristas = [
            #base
            (0,1),(1,2),(2,3),(3,0),
            #lados
            (0,4), (1,4), (2,4), (3,4)
        ]
        self.op_mat = OpMat3D()

    def update(self):
        #gira actualizando el angulo de rotación con el paso definido
        self.deg = (self.deg + self.delta_deg) % 360

    def render(self, surface):
        px = self.pivote[0] * self.escala
        py = self.pivote[1] * self.escala
        pz = self.pivote[2] * self.escala

        self.op_mat.reset()

        self.op_mat.scale(self.escala,self.escala,self.escala)

        self.op_mat.translate(-px,-py,-pz)
        self.op_mat.rotate_z(self.deg)
        self.op_mat.translate(px,py,pz)
        self.op_mat.rotate_y(25)
        transformed_vertices = self.op_mat.transform_points(self.vertices_unitarios)

        # Ejes primero, para que la pirámide quede encima
        if self.ejes_locales:
            self.ejes.render(surface, self.op_mat, factor=1 / self.escala)
        else:
            self.ejes.render(surface)

        points_2d = [self.camara.proyectar(v) for v in transformed_vertices]

        for edge in self.aristas:
            p1 = points_2d[edge[0]]
            p2 = points_2d[edge[1]]
            self.bresenham.linea(surface, p1[0], p1[1], p2[0], p2[1], color=(0, 255, 200))

        pivote_2d = self.camara.proyectar([px,py,pz])
        pygame.draw.circle(surface, (255, 80, 80), (int(pivote_2d[0]), int(pivote_2d[1])), 5)