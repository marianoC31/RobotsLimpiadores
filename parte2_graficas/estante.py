from OpenGL.GL import *
from OpenGL.GLU import *
from robot_limpiador import bresenham_2d

class Estante:
    """
    Modelo 3D de Estante industrial:
    - Postes esquineros verticales, vigas horizontales de carga a varios niveles.
    - Cruces de arriostramiento lateral y cajas almacenadas en la parte superior.
    - Transformado con OpMat3D, proyectado con gluProject y dibujado con bresenham_2d.
    - Iluminado matemáticamente en Python.
    """
    def __init__(self, pos_x, pos_z, ancho=1.6, alto=2.8, largo=3.2):
        self.pos_x = float(pos_x)
        self.pos_z = float(pos_z)
        self.ancho = float(ancho)
        self.alto = float(alto)
        self.largo = float(largo)

        self._crear_geometria()

    def get_bounds(self, margen=0.35):
        """Retorna la caja AABB para evitar empalmes con cajas en piso."""
        hx = self.ancho / 2.0 + margen
        hz = self.largo / 2.0 + margen
        return (self.pos_x - hx, self.pos_x + hx, self.pos_z - hz, self.pos_z + hz)

    def _crear_geometria(self):
        hx = self.ancho / 2.0
        hz = self.largo / 2.0
        h = self.alto

        # 1. Postes verticales (4 columnas)
        self.columnas = [
            ([-hx, 0.0, -hz], [-hx, h, -hz]),
            ([ hx, 0.0, -hz], [ hx, h, -hz]),
            ([ hx, 0.0,  hz], [ hx, h,  hz]),
            ([-hx, 0.0,  hz], [-hx, h,  hz])
        ]

        # 2. Vigas horizontales de repisas (en 3 alturas: base, intermedia, alta)
        self.vigas = []
        for ny in [0.2, 1.4, h]:
            # Frontal y trasera
            self.vigas.append(([-hx, ny,  hz], [ hx, ny,  hz]))
            self.vigas.append(([-hx, ny, -hz], [ hx, ny, -hz]))
            # Laterales
            self.vigas.append(([-hx, ny, -hz], [-hx, ny,  hz]))
            self.vigas.append(([ hx, ny, -hz], [ hx, ny,  hz]))

        # 3. Arriostramiento lateral en 'X' (refuerzo estructural)
        self.cruces = [
            # Lateral izquierdo
            ([-hx, 0.2, -hz], [-hx, 1.4,  hz]),
            ([-hx, 0.2,  hz], [-hx, 1.4, -hz]),
            # Lateral derecho
            ([ hx, 0.2, -hz], [ hx, 1.4,  hz]),
            ([ hx, 0.2,  hz], [ hx, 1.4, -hz])
        ]

        # 4. Cajas almacenadas en la repisa superior (inventario en altura)
        self.cajas_almacenadas = []
        for cz in [-0.8, 0.8]:
            cs = 0.28
            by = h
            pts = [
                [-cs, by, cz - cs], [ cs, by, cz - cs], [ cs, by, cz + cs], [-cs, by, cz + cs],
                [-cs, by + cs*2, cz - cs], [ cs, by + cs*2, cz - cs], [ cs, by + cs*2, cz + cs], [-cs, by + cs*2, cz + cs]
            ]
            edges = [
                (0,1), (1,2), (2,3), (3,0),
                (4,5), (5,6), (6,7), (7,4),
                (0,4), (1,5), (2,6), (3,7)
            ]
            self.cajas_almacenadas.append((pts, edges))

    def render(self, mv, proj, vp, op, iluminacion, robots):
        """Renderiza el estante industrial con OpMat3D y bresenham_2d."""
        op.push()
        op.translate(self.pos_x, 0.0, self.pos_z)

        # Colores de materiales
        col_postes = (0.25, 0.55, 0.90)  # Azul industrial postes
        col_vigas  = (0.95, 0.45, 0.08)  # Naranja vigas
        col_cajas  = (0.75, 0.55, 0.32)  # Cartón cajas

        # 1. Postes verticales
        for p1, p2 in self.columnas:
            t1 = op.transform([[p1[0], p1[1], p1[2], 1.0]])[0]
            t2 = op.transform([[p2[0], p2[1], p2[2], 1.0]])[0]
            mid = ((t1[0]+t2[0])*0.5, (t1[1]+t2[1])*0.5, (t1[2]+t2[2])*0.5)
            c = iluminacion.calcular_color(col_postes, mid, (0.0, 1.0, 0.0), robots)
            glColor3f(*c)
            wx1, wy1, _ = gluProject(t1[0], t1[1], t1[2], mv, proj, vp)
            wx2, wy2, _ = gluProject(t2[0], t2[1], t2[2], mv, proj, vp)
            bresenham_2d(wx1, wy1, wx2, wy2)

        # 2. Vigas horizontales y arriostramientos
        for p1, p2 in self.vigas + self.cruces:
            t1 = op.transform([[p1[0], p1[1], p1[2], 1.0]])[0]
            t2 = op.transform([[p2[0], p2[1], p2[2], 1.0]])[0]
            mid = ((t1[0]+t2[0])*0.5, (t1[1]+t2[1])*0.5, (t1[2]+t2[2])*0.5)
            c = iluminacion.calcular_color(col_vigas, mid, (0.0, 1.0, 0.0), robots)
            glColor3f(*c)
            wx1, wy1, _ = gluProject(t1[0], t1[1], t1[2], mv, proj, vp)
            wx2, wy2, _ = gluProject(t2[0], t2[1], t2[2], mv, proj, vp)
            bresenham_2d(wx1, wy1, wx2, wy2)

        # 3. Cajas en repisa superior
        for pts, edges in self.cajas_almacenadas:
            t_pts = [op.transform([[p[0], p[1], p[2], 1.0]])[0] for p in pts]
            pts_2d = [gluProject(p[0], p[1], p[2], mv, proj, vp)[:2] for p in t_pts]
            for e in edges:
                p1_3d = t_pts[e[0]]
                p2_3d = t_pts[e[1]]
                mid = ((p1_3d[0]+p2_3d[0])*0.5, (p1_3d[1]+p2_3d[1])*0.5, (p1_3d[2]+p2_3d[2])*0.5)
                c = iluminacion.calcular_color(col_cajas, mid, (0.0, 1.0, 0.0), robots)
                glColor3f(*c)
                p1 = pts_2d[e[0]]
                p2 = pts_2d[e[1]]
                bresenham_2d(p1[0], p1[1], p2[0], p2[1])

        op.pop()

def generar_estantes_por_codigo(almacen_m=20.0, almacen_n=20.0):
    """
    Instancia por código los bloques de estantes que forman los pasillos:
    - Pasillo Oeste (X ≈ -7.2)
    - Bloque de Estantes 1 (X = -4.2)
    - Pasillo Central (X ≈ 0.0)
    - Bloque de Estantes 2 (X = +4.2)
    - Pasillo Este (X ≈ +7.2)
    """
    estantes = []
    filas_x = [-4.2, 4.2]
    posiciones_z = [-4.5, 0.0, 4.5]

    for x in filas_x:
        for z in posiciones_z:
            estantes.append(Estante(pos_x=x, pos_z=z, ancho=1.6, alto=2.8, largo=3.2))

    return estantes
