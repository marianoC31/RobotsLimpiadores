"""Clase Bresenham: dibuja las aristas de los objetos 3D píxel por píxel.

Flujo de una arista:
  1. Los extremos ya transformados (OpMat3D) se proyectan con Camara3D a
     coordenadas de ventana: (x, y, profundidad).
  2. linea() aplica el algoritmo de Bresenham 2D entre los dos extremos y
     decide qué píxeles forman la línea (interpolando también la profundidad).
  3. Los píxeles se acumulan con su color y, al final del cuadro,
     dibujar_lote() los manda a la tarjeta de video en una sola llamada.
     OpenGL solo pinta esos puntos; qué píxeles forman cada línea lo decide
     esta clase.

La profundidad hace que las aristas que quedan detrás de una cara con textura
se oculten (en pantalla la profundidad varía linealmente, así que basta con
interpolarla a lo largo de la línea).
"""
import ctypes
from array import array
from OpenGL.GL import *


class Bresenham:

    SESGO_PROFUNDIDAD = 0.00005   # acerca un poco las aristas para que no "peleen" con su propia cara

    def __init__(self):
        self.color = (1.0, 1.0, 1.0)
        self._vertices = array('f')   # x, y, z de cada píxel del cuadro
        self._colores = array('f')    # r, g, b de cada píxel

    def linea(self, x0, y0, x1, y1, z0, z1):
        """Algoritmo de Bresenham entre (x0, y0) y (x1, y1), interpolando la profundidad."""
        x0, y0 = int(round(x0)), int(round(y0))
        x1, y1 = int(round(x1)), int(round(y1))
        dx, dy = abs(x1 - x0), abs(y1 - y0)
        sx = 1 if x1 > x0 else -1
        sy = 1 if y1 > y0 else -1
        err = dx - dy

        # Con glOrtho(..., -1, 1), un vértice con z = 1 - 2·profundidad queda exactamente a esa profundidad
        zv = 1.0 - 2.0 * (z0 - self.SESGO_PROFUNDIDAD)
        dz = -2.0 * (z1 - z0) / max(1, dx, dy)

        pixeles = []
        agregar = pixeles.append
        while True:
            agregar(x0)
            agregar(y0)
            agregar(zv)
            if x0 == x1 and y0 == y1:
                break
            zv += dz
            e2 = 2 * err
            if e2 > -dy:
                err -= dy
                x0 += sx
            if e2 < dx:
                err += dx
                y0 += sy
        self._vertices.extend(pixeles)
        self._colores.extend(self.color * (len(pixeles) // 3))

    def dibujar_aristas(self, camara, puntos, aristas, color):
        """Proyecta los vértices (coordenadas del mundo) y traza cada arista con linea()."""
        self.color = color
        p2d = [camara.proyectar(p) for p in puntos]
        for a, b in aristas:
            pa, pb = p2d[a], p2d[b]
            if pa is not None and pb is not None:      # se omite si un extremo queda detrás de la cámara
                self.linea(pa[0], pa[1], pb[0], pb[1], pa[2], pb[2])

    def dibujar_lote(self):
        """Manda a OpenGL, en una sola llamada, todos los píxeles acumulados en el cuadro."""
        n = len(self._vertices) // 3
        if n:
            vbuf = (ctypes.c_float * len(self._vertices)).from_buffer_copy(self._vertices)
            cbuf = (ctypes.c_float * len(self._colores)).from_buffer_copy(self._colores)
            glEnableClientState(GL_VERTEX_ARRAY)
            glEnableClientState(GL_COLOR_ARRAY)
            glVertexPointer(3, GL_FLOAT, 0, vbuf)
            glColorPointer(3, GL_FLOAT, 0, cbuf)
            glDrawArrays(GL_POINTS, 0, n)
            glDisableClientState(GL_COLOR_ARRAY)
            glDisableClientState(GL_VERTEX_ARRAY)
        self._vertices = array('f')
        self._colores = array('f')
