"""OpMat3D unificado: una sola clase de matrices para TODO el proyecto.

Lo usan:
  - tareas/   (pirámide y robot wireframe)         -> API: M, rotate_x, transform_points
  - parte2_graficas/ (almacén 3D de la integradora) -> API: mat, rotateX, transform

Ambas APIs son la misma matriz por dentro; los nombres de la Parte 2 son alias.

Modos de composición
  post = False  ->  M = T · M   (cada transformación nueva se aplica "por fuera";
                                 se lee en el orden en que la escribes: pirámide)
  post = True   ->  M = M · T   (jerárquico: padre -> hijo, con push/pop; robots)
"""
import math


def _identidad():
    return [
        [1.0, 0.0, 0.0, 0.0],
        [0.0, 1.0, 0.0, 0.0],
        [0.0, 0.0, 1.0, 0.0],
        [0.0, 0.0, 0.0, 1.0],
    ]


class OpMat3D:

    def __init__(self, post=False):
        self.post = post
        self._pila = []
        self.reset()

    # ------------------------------------------------------------------
    # Estado y pila jerárquica
    # ------------------------------------------------------------------
    def reset(self):
        """Matriz identidad y pila vacía."""
        self.M = _identidad()
        self._pila.clear()

    def push(self):
        """Guarda una copia de la matriz actual (el "padre")."""
        self._pila.append([fila[:] for fila in self.M])

    def pop(self):
        """Regresa a la matriz del padre (identidad si la pila está vacía)."""
        self.M = self._pila.pop() if self._pila else _identidad()

    # ------------------------------------------------------------------
    # Multiplicación
    # ------------------------------------------------------------------
    @staticmethod
    def _mult_matrices(A, B):
        # Multiplicación AFÍN: todas nuestras matrices tienen la última fila
        # [0, 0, 0, 1], así que no hace falta calcularla.
        #   C(3x3) = A(3x3)·B(3x3)          -> 27 multiplicaciones
        #   c_t    = A(3x3)·b_t + a_t       ->  9 multiplicaciones
        # Total 36 en vez de 64 de la 4x4 genérica.
        C = []
        for i in range(3):
            a0, a1, a2, a3 = A[i]
            C.append([
                a0*B[0][0] + a1*B[1][0] + a2*B[2][0],
                a0*B[0][1] + a1*B[1][1] + a2*B[2][1],
                a0*B[0][2] + a1*B[1][2] + a2*B[2][2],
                a0*B[0][3] + a1*B[1][3] + a2*B[2][3] + a3,
            ])
        C.append([0.0, 0.0, 0.0, 1.0])
        return C

    def _aplicar(self, T):
        if self.post:
            self.M = self._mult_matrices(self.M, T)
        else:
            self.M = self._mult_matrices(T, self.M)

    def multiplicar(self, T):
        """Aplica una matriz ya colapsada (por ejemplo, la de matriz_T_Ry_Rx)."""
        self._aplicar(T)

    # ------------------------------------------------------------------
    # Transformaciones básicas
    # ------------------------------------------------------------------
    def translate(self, tx, ty, tz):
        # Colapsada: una traslación solo modifica la columna de traslación.
        #   post (M·T): t_nueva = R·t + t_actual   (9 mult)
        #   pre  (T·M): t_nueva = t_actual + t     (0 mult)
        M = self.M
        if self.post:
            for i in range(3):
                M[i][3] += M[i][0]*tx + M[i][1]*ty + M[i][2]*tz
        else:
            M[0][3] += tx
            M[1][3] += ty
            M[2][3] += tz

    def scale(self, sx, sy, sz):
        self._aplicar([
            [sx,  0.0, 0.0, 0.0],
            [0.0, sy,  0.0, 0.0],
            [0.0, 0.0, sz,  0.0],
            [0.0, 0.0, 0.0, 1.0],
        ])

    def rotate_x(self, deg):
        rad = math.radians(deg)
        c, s = math.cos(rad), math.sin(rad)
        self._aplicar([
            [1.0, 0.0, 0.0, 0.0],
            [0.0,   c,  -s, 0.0],
            [0.0,   s,   c, 0.0],
            [0.0, 0.0, 0.0, 1.0],
        ])

    def rotate_y(self, deg):
        rad = math.radians(deg)
        c, s = math.cos(rad), math.sin(rad)
        self._aplicar([
            [  c, 0.0,   s, 0.0],
            [0.0, 1.0, 0.0, 0.0],
            [ -s, 0.0,   c, 0.0],
            [0.0, 0.0, 0.0, 1.0],
        ])

    def rotate_z(self, deg):
        rad = math.radians(deg)
        c, s = math.cos(rad), math.sin(rad)
        self._aplicar([
            [  c,  -s, 0.0, 0.0],
            [  s,   c, 0.0, 0.0],
            [0.0, 0.0, 1.0, 0.0],
            [0.0, 0.0, 0.0, 1.0],
        ])

    def rotate_free(self, deg, a, b, c):
        """Rotación alrededor de un eje arbitrario (a, b, c) que pasa por el origen.

        Es la fórmula de Rodrigues: la versión colapsada de
        "alinear el eje con Z, rotar en Z, deshacer la alineación" (5 matrices).
        """
        norm = math.sqrt(a*a + b*b + c*c)
        if norm == 0.0:
            return
        ux, uy, uz = a / norm, b / norm, c / norm
        rad = math.radians(deg)
        ct, st = math.cos(rad), math.sin(rad)
        omc = 1.0 - ct
        self._aplicar([
            [ct + ux*ux*omc,     ux*uy*omc - uz*st,  ux*uz*omc + uy*st,  0.0],
            [uy*ux*omc + uz*st,  ct + uy*uy*omc,     uy*uz*omc - ux*st,  0.0],
            [uz*ux*omc - uy*st,  uz*uy*omc + ux*st,  ct + uz*uz*omc,     0.0],
            [0.0,                0.0,                0.0,                1.0],
        ])

    # ------------------------------------------------------------------
    # Aplicar la matriz a puntos
    # ------------------------------------------------------------------
    def transform_points(self, points):
        """Puntos [x, y, z] -> [x', y', z'] (9 mult por punto)."""
        (m00, m01, m02, m03), (m10, m11, m12, m13), (m20, m21, m22, m23) = self.M[0], self.M[1], self.M[2]
        transformed_points = []
        for p in points:
            x, y, z = p[0], p[1], p[2]
            transformed_points.append([
                m00*x + m01*y + m02*z + m03,
                m10*x + m11*y + m12*z + m13,
                m20*x + m21*y + m22*z + m23,
            ])
        return transformed_points

    def transform(self, points):
        """Versión homogénea de la Parte 2: [x, y, z, 1] -> [x', y', z', 1]."""
        return [q + [1.0] for q in self.transform_points(points)]

    def get_matrix(self):
        return [fila[:] for fila in self.M]

    def get_gl_matrix(self):
        """La matriz en 16 flotantes column-major, como la pide glLoadMatrixf."""
        return [self.M[fila][col] for col in range(4) for fila in range(4)]

    # ------------------------------------------------------------------
    # Alias con los nombres que usa la Parte 2
    # ------------------------------------------------------------------
    @property
    def mat(self):
        return self.M

    @mat.setter
    def mat(self, valor):
        self.M = valor

    @property
    def stack(self):
        return self._pila

    rotateX = rotate_x
    rotateY = rotate_y
    rotateZ = rotate_z
    rotateFree = rotate_free


# ----------------------------------------------------------------------
# Matrices colapsadas: el producto de varias transformaciones escrito
# directamente con su fórmula cerrada (cero multiplicaciones de matrices).
# ----------------------------------------------------------------------
def matriz_T_Ry(px, py, pz, theta):
    """T(px,py,pz) · Ry(theta)  (posición + orientación en el piso).

        | c    0   s   px |
        | 0    1   0   py |
        | -s   0   c   pz |
    """
    rt = math.radians(theta)
    c, s = math.cos(rt), math.sin(rt)
    return [
        [c,    0.0, s,    px],
        [0.0,  1.0, 0.0,  py],
        [-s,   0.0, c,    pz],
        [0.0,  0.0, 0.0,  1.0],
    ]


def matriz_Rx_T_Ry(alpha, px, py, pz, theta):
    """Rx(alpha) · T(px,py,pz) · Ry(theta)  (vista + posición + orientación).

    Rx·Ry da el bloque 3x3 y Rx·p da la traslación:
        | c       0    s       px            |
        | sa*s    ca   -sa*c   ca*py - sa*pz |
        | -ca*s   sa   ca*c    sa*py + ca*pz |
    """
    ra, rt = math.radians(alpha), math.radians(theta)
    ca, sa = math.cos(ra), math.sin(ra)
    c, s = math.cos(rt), math.sin(rt)
    return [
        [c,      0.0, s,      px],
        [sa*s,   ca,  -sa*c,  ca*py - sa*pz],
        [-ca*s,  sa,  ca*c,   sa*py + ca*pz],
        [0.0,    0.0, 0.0,    1.0],
    ]


def matriz_T_Ry_Rx(px, py, pz, phi, beta):
    """T(px,py,pz) · Ry(phi) · Rx(beta)  (rueda: posición + dirección + rodamiento).

    Ry·Rx:
        | c    s*sb   s*cb |
        | 0    cb     -sb  |
        | -s   c*sb   c*cb |
    """
    rp, rb = math.radians(phi), math.radians(beta)
    c, s = math.cos(rp), math.sin(rp)
    cb, sb = math.cos(rb), math.sin(rb)
    return [
        [c,    s*sb,  s*cb,  px],
        [0.0,  cb,    -sb,   py],
        [-s,   c*sb,  c*cb,  pz],
        [0.0,  0.0,   0.0,   1.0],
    ]
