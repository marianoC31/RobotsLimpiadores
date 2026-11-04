"""Cámara 3D propia: vista (lookAt) + perspectiva, calculadas a mano.

Proyectar un punto del mundo a la pantalla:

    clip = P · V · [x, y, z, 1]          (V = vista, P = perspectiva)
    ndc  = clip / clip.w                  (división de perspectiva)
    pantalla_x = (ndc.x + 1) / 2 · ancho
    pantalla_y = (ndc.y + 1) / 2 · alto   (origen abajo a la izquierda)
    profundidad = (ndc.z + 1) / 2         (0 = cerca, 1 = lejos)

P·V se multiplica UNA vez por cuadro (matriz colapsada) y luego cada punto
cuesta solo 4 productos punto.  Las mismas matrices se le pasan a OpenGL para
pintar las caras con textura, así que todo usa la misma cámara.
"""
import math
from OpenGL.GL import glMatrixMode, glLoadMatrixf, GL_PROJECTION, GL_MODELVIEW


def _mult(A, B):
    """Multiplicación 4x4 general (la perspectiva no es afín, no sirve el atajo de OpMat)."""
    return [[sum(A[i][k] * B[k][j] for k in range(4)) for j in range(4)] for i in range(4)]


def _normalizar(v):
    n = math.sqrt(v[0] * v[0] + v[1] * v[1] + v[2] * v[2]) or 1.0
    return (v[0] / n, v[1] / n, v[2] / n)


def _cruz(a, b):
    return (a[1] * b[2] - a[2] * b[1], a[2] * b[0] - a[0] * b[2], a[0] * b[1] - a[1] * b[0])


def _punto(a, b):
    return a[0] * b[0] + a[1] * b[1] + a[2] * b[2]


class Camara3D:

    def __init__(self, ancho, alto, fovy=50.0, cerca=1.0, lejos=200.0):
        self.ancho, self.alto = ancho, alto
        self.cerca = cerca
        f = 1.0 / math.tan(math.radians(fovy) / 2.0)
        a = ancho / alto
        self.P = [
            [f / a, 0.0, 0.0, 0.0],
            [0.0, f, 0.0, 0.0],
            [0.0, 0.0, (lejos + cerca) / (cerca - lejos), 2.0 * lejos * cerca / (cerca - lejos)],
            [0.0, 0.0, -1.0, 0.0],
        ]
        self.mirar((0.0, 20.0, 30.0), (0.0, 0.0, 0.0))

    def mirar(self, ojo, objetivo, arriba=(0.0, 1.0, 0.0)):
        """Matriz de vista: la cámara en 'ojo' mirando hacia 'objetivo'."""
        self.ojo = ojo
        f = _normalizar((objetivo[0] - ojo[0], objetivo[1] - ojo[1], objetivo[2] - ojo[2]))  # adelante
        s = _normalizar(_cruz(f, arriba))                                                    # derecha
        u = _cruz(s, f)                                                                      # arriba real
        self.V = [
            [s[0], s[1], s[2], -_punto(s, ojo)],
            [u[0], u[1], u[2], -_punto(u, ojo)],
            [-f[0], -f[1], -f[2], _punto(f, ojo)],
            [0.0, 0.0, 0.0, 1.0],
        ]
        self.PV = _mult(self.P, self.V)    # colapsada: una sola matriz para todo el cuadro

    def proyectar(self, p):
        """Punto del mundo -> (x, y, profundidad) en la ventana, o None si queda detrás de la cámara."""
        (a0, a1, a2, a3), (b0, b1, b2, b3), (c0, c1, c2, c3), (d0, d1, d2, d3) = self.PV
        x, y, z = p[0], p[1], p[2]
        w = d0 * x + d1 * y + d2 * z + d3
        if w < self.cerca:
            return None
        return (((a0 * x + a1 * y + a2 * z + a3) / w + 1.0) * 0.5 * self.ancho,
                ((b0 * x + b1 * y + b2 * z + b3) / w + 1.0) * 0.5 * self.alto,
                ((c0 * x + c1 * y + c2 * z + c3) / w + 1.0) * 0.5)

    def cargar_en_opengl(self):
        """Le pasa a OpenGL NUESTRAS matrices (column-major) para pintar las texturas."""
        glMatrixMode(GL_PROJECTION)
        glLoadMatrixf([self.P[f][c] for c in range(4) for f in range(4)])
        glMatrixMode(GL_MODELVIEW)
        glLoadMatrixf([self.V[f][c] for c in range(4) for f in range(4)])
