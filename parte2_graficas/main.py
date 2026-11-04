"""Almacén 3D: los robots se mueven según la simulación de AgentPy (agentes/modelo.py).

Cada CUADROS_POR_PASO cuadros se ejecuta un paso del modelo; entre paso y paso,
cada Robot3D anima su transición (girar, avanzar, recoger o apilar).

Controles: arrastrar con el ratón = girar la cámara, rueda = zoom,
Espacio = pausa, R = nueva simulación, T = caras con textura sí/no, Esc = salir.
"""
import os
import sys
sys.path.insert(0, os.path.dirname(os.path.dirname(os.path.abspath(__file__))))  # raíz -> nucleo, agentes
sys.stdout.reconfigure(encoding="utf-8", errors="replace")
import OpenGL
OpenGL.ERROR_CHECKING = False   # sin esto PyOpenGL revisa errores tras cada llamada (muy lento)

import math
import pygame
from pygame.locals import DOUBLEBUF, OPENGL, QUIT, KEYDOWN, K_ESCAPE, K_SPACE, K_r, K_t, MOUSEBUTTONDOWN, MOUSEBUTTONUP, MOUSEMOTION
from OpenGL.GL import *

from agentes.modelo import AlmacenModelo, PARAMETROS, DIRECCIONES, MAX_PILA
from nucleo.OpMat import OpMat3D
from camara3d import Camara3D
from bresenham import Bresenham
import superficies
from almacen import Almacen, TAM_CELDA
from estante import Estante
from caja import dibujar_pila
from robot3d import Robot3D

ANCHO, ALTO = 1100, 750
CUADROS_POR_PASO = 8     # 30 cuadros por segundo -> ~4 pasos de simulación por segundo


class Escena:
    """Une el modelo de AgentPy con sus modelos 3D."""

    def __init__(self):
        self.modelo = AlmacenModelo(PARAMETROS)
        self.modelo.sim_setup()
        m = self.modelo
        self.bresenham = Bresenham()          # una sola instancia para todas las aristas
        self.almacen = Almacen(m.M, m.N, self.bresenham)
        self.estantes = []
        for x, y, largo in PARAMETROS['estantes']:
            cx, cz1 = self.almacen.centro_celda(x, y)
            _, cz2 = self.almacen.centro_celda(x, y + largo - 1)
            self.estantes.append(Estante(cx, (cz1 + cz2) / 2.0, self.bresenham, largo=largo * TAM_CELDA - 0.8))
        self.robots = [Robot3D(a, self.almacen, self.bresenham) for a in m.robots]
        self.op = OpMat3D(post=True)
        self.cuadro = CUADROS_POR_PASO
        self.cambios_pendientes = []      # cajas que cambian de lugar a mitad de la animación

    def avanzar(self):
        """Un cuadro: si terminó la animación del paso anterior, ejecuta otro paso de AgentPy."""
        self.cuadro += 1
        if self.cuadro >= CUADROS_POR_PASO:
            if self.modelo.running:
                self.modelo.sim_step()
                self.cuadro = 0
                self.cambios_pendientes = []
                for r3d in self.robots:
                    agente = r3d.agente          # (no usar zip: AgentPy reordena su lista en cada paso)
                    r3d.nuevo_paso(agente)
                    if agente.accion in ('recoger', 'apilar'):
                        dx, dy = DIRECCIONES[agente.orientacion]
                        x, y = agente.pos
                        # El modelo ya movió la caja; en 3D cambia cuando las pinzas la toman/sueltan
                        self.cambios_pendientes.append(((x + dx, y + dy), 1 if agente.accion == 'recoger' else -1))
            else:
                self.cuadro = CUADROS_POR_PASO
        f = self.cuadro / CUADROS_POR_PASO
        for r in self.robots:
            r.update(f)
        return f

    def render(self, camara, f):
        self.almacen.render(camara)
        for e in self.estantes:
            e.render(camara, self.op)
        m = self.modelo
        ajuste = {celda: d for celda, d in self.cambios_pendientes} if f < 0.5 else {}
        for x in range(m.M):
            for y in range(m.N):
                h = m.cajas[x][y] + ajuste.get((x, y), 0)
                if h > 0:
                    cx, cz = self.almacen.centro_celda(x, y)
                    dibujar_pila(self.bresenham, camara, self.op, cx, cz, h, completa=(h == MAX_PILA and (x, y) in m.pilas))
        for r in self.robots:
            r.render(camara)


class Panel:
    """Texto en pantalla con las métricas de la simulación."""

    def __init__(self):
        self.fuente = pygame.font.Font(None, 24)
        self.tex = glGenTextures(1)

    def render(self, lineas):
        superficie = pygame.Surface((560, 26 * len(lineas) + 12), pygame.SRCALPHA)
        superficie.fill((10, 14, 22, 210))
        for i, (texto, color) in enumerate(lineas):
            superficie.blit(self.fuente.render(texto, True, color), (10, 8 + 26 * i))
        w, h = superficie.get_size()
        glBindTexture(GL_TEXTURE_2D, self.tex)
        glTexParameteri(GL_TEXTURE_2D, GL_TEXTURE_MIN_FILTER, GL_LINEAR)
        glTexParameteri(GL_TEXTURE_2D, GL_TEXTURE_MAG_FILTER, GL_LINEAR)
        glTexImage2D(GL_TEXTURE_2D, 0, GL_RGBA, w, h, 0, GL_RGBA, GL_UNSIGNED_BYTE,
                     pygame.image.tostring(superficie, "RGBA", True))
        glEnable(GL_TEXTURE_2D)
        glEnable(GL_BLEND)
        glBlendFunc(GL_SRC_ALPHA, GL_ONE_MINUS_SRC_ALPHA)
        glColor4f(1, 1, 1, 1)
        x0, y0 = 12, ALTO - 12 - h
        glBegin(GL_QUADS)
        glTexCoord2f(0, 0); glVertex2f(x0, y0)
        glTexCoord2f(1, 0); glVertex2f(x0 + w, y0)
        glTexCoord2f(1, 1); glVertex2f(x0 + w, y0 + h)
        glTexCoord2f(0, 1); glVertex2f(x0, y0 + h)
        glEnd()
        glDisable(GL_BLEND)
        glDisable(GL_TEXTURE_2D)


def lineas_panel(modelo, pausado):
    lineas = [(f"Paso {modelo.t}   |   Movimientos: {modelo.movimientos_totales()}   |   "
               f"Pilas de 5: {modelo.pilas_completas()} / {modelo.K // MAX_PILA}", (235, 240, 250))]
    if modelo.tiempo_finalizacion:
        lineas.append((f"Terminado: todas las cajas en pilas en {modelo.tiempo_finalizacion} pasos", (110, 255, 130)))
    elif not modelo.running:
        lineas.append(("Se alcanzó el tiempo máximo", (255, 170, 80)))
    elif pausado:
        lineas.append(("En pausa", (255, 215, 0)))
    modo = "caras con textura + aristas" if superficies.activas else "solo aristas de Bresenham"
    lineas.append((f"Modo: {modo}", (160, 180, 205)))
    lineas.append(("Ratón: girar   Rueda: zoom   Espacio: pausa   R: reiniciar   T: caras", (160, 180, 205)))
    return lineas


def main():
    pygame.init()
    pygame.display.gl_set_attribute(pygame.GL_DEPTH_SIZE, 24)
    pygame.display.set_mode((ANCHO, ALTO), DOUBLEBUF | OPENGL)
    pygame.display.set_caption("Almacén 3D - robots controlados con AgentPy")
    glClearColor(0.03, 0.04, 0.06, 1.0)
    glDepthFunc(GL_LEQUAL)
    glPointSize(1.8)
    superficies.cargar_texturas()

    camara = Camara3D(ANCHO, ALTO)
    escena = Escena()
    panel = Panel()
    yaw, pitch, distancia = 30.0, 50.0, 34.0
    arrastrando, pausado = False, False
    reloj = pygame.time.Clock()

    while True:
        reloj.tick(30)
        for e in pygame.event.get():
            if e.type == QUIT or (e.type == KEYDOWN and e.key == K_ESCAPE):
                pygame.quit()
                return
            if e.type == KEYDOWN and e.key == K_SPACE:
                pausado = not pausado
            if e.type == KEYDOWN and e.key == K_r:
                escena = Escena()
            if e.type == KEYDOWN and e.key == K_t:
                superficies.activas = not superficies.activas
            if e.type == MOUSEBUTTONDOWN and e.button == 1:
                arrastrando = True
            if e.type == MOUSEBUTTONUP and e.button == 1:
                arrastrando = False
            if e.type == MOUSEBUTTONDOWN and e.button in (4, 5):
                distancia = max(8.0, min(70.0, distancia + (-2.0 if e.button == 4 else 2.0)))
            if e.type == MOUSEMOTION and arrastrando:
                yaw += e.rel[0] * 0.4
                pitch = max(10.0, min(85.0, pitch + e.rel[1] * 0.4))

        f = escena.cuadro / CUADROS_POR_PASO if pausado else escena.avanzar()

        # Cámara orbital alrededor del centro del almacén
        ry, rp = math.radians(yaw), math.radians(pitch)
        ojo = (distancia * math.cos(rp) * math.sin(ry), distancia * math.sin(rp), distancia * math.cos(rp) * math.cos(ry))
        camara.mirar(ojo, (0.0, 0.0, 0.0))

        glClear(GL_COLOR_BUFFER_BIT | GL_DEPTH_BUFFER_BIT)
        escena.render(camara, f)                 # transforma, proyecta y acumula aristas y caras

        glEnable(GL_DEPTH_TEST)
        if superficies.activas:                  # 1) caras con textura, con nuestras matrices (tecla T)
            camara.cargar_en_opengl()
            superficies.dibujar()

        glMatrixMode(GL_PROJECTION)              # 2) píxeles de Bresenham en coordenadas de ventana
        glLoadIdentity()
        glOrtho(0, ANCHO, 0, ALTO, -1, 1)
        glMatrixMode(GL_MODELVIEW)
        glLoadIdentity()
        escena.bresenham.dibujar_lote()
        glDisable(GL_DEPTH_TEST)

        panel.render(lineas_panel(escena.modelo, pausado))
        pygame.display.flip()


if __name__ == "__main__":
    main()
