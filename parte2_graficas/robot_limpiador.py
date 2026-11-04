import math
from OpenGL.GL import *
from OpenGL.GLU import *
from nucleo.OpMat import OpMat3D, matriz_T_Ry, matriz_T_Ry_Rx

def bresenham_2d(x0, y0, x1, y1):
    """
    Algoritmo Bresenham 2D estándar para rasterizar líneas píxel a píxel en coordenadas de ventana.
    Implementación pura de graficación por computadora.
    """
    x0, y0 = int(round(x0)), int(round(y0))
    x1, y1 = int(round(x1)), int(round(y1))

    dx = abs(x1 - x0)
    dy = abs(y1 - y0)
    sx = 1 if x1 > x0 else -1
    sy = 1 if y1 > y0 else -1
    err = dx - dy

    glBegin(GL_POINTS)
    while True:
        glVertex2i(x0, y0)
        if x0 == x1 and y0 == y1:
            break
        e2 = 2 * err
        if e2 > -dy:
            err -= dy
            x0 += sx
        if e2 < dx:
            err += dx
            y0 += sy
    glEnd()

class RobotLimpiador:
    """
    Modelo 3D jerárquico de Robot Limpiador industrial:
    - Transformaciones calculadas exclusivamente con OpMat3D (pila matricial propia).
    - Renderizado proyectado en 2D y rasterizado exclusivamente con bresenham_2d.
    - Chasis, cabina de sensores, sirena con reflector rotatorio y sensor de presión.
    - 4 Ruedas omnidireccionales con rodillos Mecanum a 45°.
    - Manipuladores mecánicos articulados con sujeción de cajas de cartón.
    - Capacidad de desplazamiento omnidireccional lateral (strafe).
    """
    def __init__(self, id_robot=0, pos_x=0.0, pos_z=0.0, rot_y=0.0, speed=0.06, color_sirena=(1.0, 0.2, 0.1)):
        self.id_robot = id_robot
        self.op = OpMat3D(post=True)  # jerárquico: M = M·T

        # Variables de posición y cinemática en el almacén
        self.pos_x = float(pos_x)
        self.pos_y = 0.5
        self.pos_z = float(pos_z)
        self.rot_y = float(rot_y)
        self.steering_angle = 0.0
        self.wheel_spin = 0.0
        self.strafe_offset = 0.0
        self.target_strafe = 0.0
        
        # Parámetros físicos y animación
        self.speed = float(speed)
        self.wheel_radius = 0.42
        self.anim_time = float(id_robot) * 1.5
        self.arm_angle = -5.0
        self.claw_angle = 15.0
        self.reflector_rot = 0.0
        self.color_sirena = color_sirena
        self.detenido = False
        
        # Manipulador y sensor de presión
        self.lleva_caja = False
        self.sensor_presion_activo = False

        # Rutas por pasillos
        self.waypoint_index = 0
        self.waypoints = []

        self._crear_geometrias_locales()

    def set_ruta(self, waypoints):
        """Asigna una secuencia cíclica de waypoints a través de los pasillos."""
        self.waypoints = waypoints
        self.waypoint_index = 0

    def get_bounds(self, margen=0.4):
        """Retorna la caja AABB del robot para detección de colisiones."""
        return (self.pos_x - 0.9 - margen, self.pos_x + 0.9 + margen,
                self.pos_z - 1.3 - margen, self.pos_z + 1.3 + margen)

    def _crear_geometrias_locales(self):
        """Define los vértices y aristas unitarios de cada componente del robot."""
        # 1. Chasis Principal (Prisma 1.6 x 0.8 x 2.4)
        w, h, l = 0.8, 0.4, 1.2
        self.chasis_pts = [
            [-w, -h, -l, 1.0], [ w, -h, -l, 1.0], [ w,  h, -l, 1.0], [-w,  h, -l, 1.0], # Atrás
            [-w, -h,  l, 1.0], [ w, -h,  l, 1.0], [ w,  h,  l, 1.0], [-w,  h,  l, 1.0]  # Frente
        ]
        self.chasis_edges = [
            (0,1), (1,2), (2,3), (3,0),
            (4,5), (5,6), (6,7), (7,4),
            (0,4), (1,5), (2,6), (3,7),
            # Aristas decorativas de paneles laterales
            (2,5), (3,4)
        ]

        # 2. Cabina Superior de Sensores
        cw, ch, cl = 0.35, 0.25, 0.35
        self.cabina_pts = [
            [-cw, -ch, -cl, 1.0], [ cw, -ch, -cl, 1.0], [ cw,  ch, -cl, 1.0], [-cw,  ch, -cl, 1.0],
            [-cw, -ch,  cl, 1.0], [ cw, -ch,  cl, 1.0], [ cw,  ch,  cl, 1.0], [-cw,  ch,  cl, 1.0]
        ]
        self.cabina_edges = [
            (0,1), (1,2), (2,3), (3,0),
            (4,5), (5,6), (6,7), (7,4),
            (0,4), (1,5), (2,6), (3,7)
        ]

        # 3. Sirena Superior (Cúpula cilíndrica octogonal y reflector rotatorio)
        sr = 0.14
        sh = 0.16
        self.sirena_pts = []
        for i in range(8):
            ang = math.radians(i * 45)
            self.sirena_pts.append([sr * math.cos(ang), 0.0, sr * math.sin(ang), 1.0])
            self.sirena_pts.append([sr * math.cos(ang), sh,  sr * math.sin(ang), 1.0])
        self.sirena_edges = []
        for i in range(8):
            next_i = (i + 1) % 8
            self.sirena_edges.append((i*2, next_i*2))         # Anillo base
            self.sirena_edges.append((i*2 + 1, next_i*2 + 1)) # Anillo superior
            self.sirena_edges.append((i*2, i*2 + 1))         # Postes verticales

        # Reflector interno de la sirena (Faro rotatorio)
        self.reflector_pts = [
            [0.0, 0.02, 0.0, 1.0],
            [-0.07, 0.12, 0.10, 1.0],
            [ 0.07, 0.12, 0.10, 1.0]
        ]
        self.reflector_edges = [(0, 1), (1, 2), (2, 0)]

        # 4. Rueda Omnidireccional Mecanum (Octágono con Rin y Rodillos a 45°)
        self.wheel_pts = []
        r = 0.42
        w = 0.12
        # Cara exterior (+w)
        for i in range(8):
            ang = math.radians(i * 45)
            self.wheel_pts.append([w, r * math.cos(ang), r * math.sin(ang), 1.0])
        # Cara interior (-w)
        for i in range(8):
            ang = math.radians(i * 45)
            self.wheel_pts.append([-w, r * math.cos(ang), r * math.sin(ang), 1.0])
        # Buje/Centro (índice 16)
        self.wheel_pts.append([w, 0.0, 0.0, 1.0])

        self.wheel_edges = [
            # Aro exterior
            (0,1), (1,2), (2,3), (3,4), (4,5), (5,6), (6,7), (7,0),
            # Aro interior
            (8,9), (9,10), (10,11), (11,12), (12,13), (13,14), (14,15), (15,8),
            # Banda de rodadura
            (0,8), (1,9), (2,10), (3,11), (4,12), (5,13), (6,14), (7,15),
            # Rayos del rin desde el centro
            (16,0), (16,2), (16,4), (16,6),
            # Rodillos Mecanum a 45 grados (líneas diagonales de rodillos omnidireccionales)
            (0,9), (1,10), (2,11), (3,12), (4,13), (5,14), (6,15), (7,8)
        ]

        # 5. Parachoques frontal y Sensor de Presión
        self.bumper_pts = [
            [-0.65, -0.18, 1.25, 1.0], [ 0.65, -0.18, 1.25, 1.0],
            [ 0.65, -0.06, 1.25, 1.0], [-0.65, -0.06, 1.25, 1.0]
        ]
        self.bumper_edges = [(0,1), (1,2), (2,3), (3,0)]

        # Sensor de presión (placa frontal indicadora)
        spw, sph = 0.15, 0.06
        self.sensor_pts = [
            [-spw, -sph, 1.28, 1.0], [ spw, -sph, 1.28, 1.0],
            [ spw,  sph, 1.28, 1.0], [-spw,  sph, 1.28, 1.0]
        ]
        self.sensor_edges = [(0,1), (1,2), (2,3), (3,0), (0,2), (1,3)]

        # 6. Manipuladores Mecánicos (Brazos y Pinzas)
        # Barra de anclaje transversal
        self.barra_pts = [
            [-0.55, 0.0, 0.0, 1.0], [0.55, 0.0, 0.0, 1.0],
            [-0.55, 0.0, 0.08, 1.0], [0.55, 0.0, 0.08, 1.0]
        ]
        self.barra_edges = [(0,1), (2,3), (0,2), (1,3)]

        # Brazo (longitudinal)
        self.brazo_pts = [
            [0.0, 0.0, 0.0, 1.0], [0.0, 0.0, 0.45, 1.0]
        ]
        self.brazo_edges = [(0, 1)]

        # Pinza (gancho 'L' articulado)
        self.pinza_izq_pts = [
            [0.0, 0.0, 0.0, 1.0], [0.0, 0.0, 0.35, 1.0], [0.22, 0.0, 0.35, 1.0]
        ]
        self.pinza_izq_edges = [(0, 1), (1, 2)]

        self.pinza_der_pts = [
            [0.0, 0.0, 0.0, 1.0], [0.0, 0.0, 0.35, 1.0], [-0.22, 0.0, 0.35, 1.0]
        ]
        self.pinza_der_edges = [(0, 1), (1, 2)]

        # 7. Caja transportada (Cubo wireframe entre las pinzas)
        cs = 0.28
        self.caja_cargo_pts = [
            [-cs, -cs, -cs, 1.0], [ cs, -cs, -cs, 1.0], [ cs,  cs, -cs, 1.0], [-cs,  cs, -cs, 1.0],
            [-cs, -cs,  cs, 1.0], [ cs, -cs,  cs, 1.0], [ cs,  cs,  cs, 1.0], [-cs,  cs,  cs, 1.0]
        ]
        self.caja_cargo_edges = [
            (0,1), (1,2), (2,3), (3,0),
            (4,5), (5,6), (6,7), (7,4),
            (0,4), (1,5), (2,6), (3,7),
            # Cinta de empaque superior
            (2,7), (3,6)
        ]

    def update(self):
        """Actualiza la cinemática, giros y desplazamiento del robot."""
        self.anim_time += 0.08
        self.reflector_rot = (self.reflector_rot + 14.0) % 360.0

        # Suavizado de desplazamiento omnidireccional lateral (strafe)
        self.strafe_offset += (self.target_strafe - self.strafe_offset) * 0.12

        # Estado del manipulador y sensor de presión
        if self.lleva_caja:
            self.sensor_presion_activo = True
            self.claw_angle = 6.0  # Pinzas sujetando la caja firmemente
            self.arm_angle = -2.0
        else:
            self.sensor_presion_activo = False
            self.claw_angle = 15.0 + 12.0 * math.sin(self.anim_time * 2.2)
            self.arm_angle = -5.0 + 6.0 * math.sin(self.anim_time * 1.1)

        if self.detenido:
            return # Pausado temporalmente por protocolo de ceder paso

        spin_factor = (1.0 / self.wheel_radius) * (180.0 / math.pi)

        # Navegación autónoma por waypoints
        if self.waypoints:
            target_x, target_z = self.waypoints[self.waypoint_index]
            dx = target_x - self.pos_x
            dz = target_z - self.pos_z
            dist = math.hypot(dx, dz)

            if dist < 0.35:
                self.waypoint_index = (self.waypoint_index + 1) % len(self.waypoints)
                target_x, target_z = self.waypoints[self.waypoint_index]
                dx = target_x - self.pos_x
                dz = target_z - self.pos_z

            target_rot = math.degrees(math.atan2(dx, dz))
            diff = (target_rot - self.rot_y + 180) % 360 - 180
            rot_step = max(-4.0, min(4.0, diff * 0.2))
            self.rot_y += rot_step
            self.steering_angle = max(-30.0, min(30.0, diff * 1.5))

            # Desplazamiento hacia adelante
            rad = math.radians(self.rot_y)
            self.pos_x += self.speed * math.sin(rad)
            self.pos_z += self.speed * math.cos(rad)
            self.wheel_spin = (self.wheel_spin + self.speed * spin_factor) % 360.0

    def _render_mesh(self, points, edges, color_base, mv, proj, vp, iluminacion, robots, normal=(0.0, 1.0, 0.0)):
        """
        1. Transforma los puntos locales a 3D de mundo usando OpMat3D.
        2. Proyecta de 3D a 2D de pantalla usando gluProject.
        3. Calcula la iluminación matemática en Python (luz direccional + 5 sirenas puntuales).
        4. Dibuja cada arista en 2D exclusivamente con bresenham_2d.
        """
        pts_3d = self.op.transform(points)
        pts_2d = []
        for p in pts_3d:
            wx, wy, _ = gluProject(p[0], p[1], p[2], mv, proj, vp)
            pts_2d.append((wx, wy))

        for e in edges:
            p1_3d = pts_3d[e[0]]
            p2_3d = pts_3d[e[1]]
            # Posición media de la arista en coordenadas de mundo
            mid_3d = (
                (p1_3d[0] + p2_3d[0]) * 0.5,
                (p1_3d[1] + p2_3d[1]) * 0.5,
                (p1_3d[2] + p2_3d[2]) * 0.5
            )

            # Cálculo de iluminación matemática
            color_final = iluminacion.calcular_color(color_base, mid_3d, normal, robots)
            glColor3f(*color_final)

            p1 = pts_2d[e[0]]
            p2 = pts_2d[e[1]]
            bresenham_2d(p1[0], p1[1], p2[0], p2[1])

    def render(self, mv, proj, vp, iluminacion, robots):
        """
        Renderiza jerárquicamente todo el modelo 3D del robot:
        - Utiliza la pila de transformaciones propia OpMat3D (push / pop).
        - Todo proyectado y dibujado arista por arista con bresenham_2d.
        """
        # ================= JERARQUÍA DE TRANSFORMACIONES =================
        self.op.reset()
        
        # 1. Posición y orientación global del robot con strafe omnidireccional
        rad_strafe = math.radians(self.rot_y + 90.0)
        sx = self.strafe_offset * math.sin(rad_strafe)
        sz = self.strafe_offset * math.cos(rad_strafe)
        # Colapsada: equivale a translate(...) seguido de rotateY(rot_y)
        self.op.M = matriz_T_Ry(self.pos_x + sx, self.pos_y, self.pos_z + sz, self.rot_y)

        # Colores de materiales
        col_chasis = (0.92, 0.70, 0.08)  # Amarillo industrial
        col_cabina = (0.45, 0.50, 0.55)  # Acero cabina
        col_rueda  = (0.50, 0.52, 0.58)  # Rin metálico
        col_brazo  = (0.95, 0.45, 0.05)  # Naranja manipulador
        col_pinza  = (0.65, 0.68, 0.72)  # Acero pinzas
        col_caja   = (0.78, 0.58, 0.35)  # Cartón corrugado

        # --- 2. Chasis Principal ---
        self._render_mesh(self.chasis_pts, self.chasis_edges, col_chasis, mv, proj, vp, iluminacion, robots)

        # --- 3. Parachoques frontal y Sensor de Presión ---
        self._render_mesh(self.bumper_pts, self.bumper_edges, (0.3, 0.3, 0.3), mv, proj, vp, iluminacion, robots)
        
        # Color del sensor de presión (Verde brillante si lleva caja)
        if self.sensor_presion_activo:
            col_sensor = (0.1, 1.0, 0.2)
        else:
            col_sensor = (0.2, 0.3, 0.2)
        self._render_mesh(self.sensor_pts, self.sensor_edges, col_sensor, mv, proj, vp, iluminacion, robots)

        # --- 4. Cabina Superior (Sensor) ---
        self.op.push()
        self.op.translate(0.0, 0.65, 0.2)
        self._render_mesh(self.cabina_pts, self.cabina_edges, col_cabina, mv, proj, vp, iluminacion, robots)

        # --- 5. Sirena sobre la Cabina (Luz puntual) ---
        self.op.push()
        self.op.translate(0.0, 0.25, 0.0)
        
        # Cúpula de sirena (brilla con su color característico)
        if self.detenido:
            col_sir = (1.0, 0.1, 0.1) # Alerta roja en parada
        else:
            col_sir = self.color_sirena
        self._render_mesh(self.sirena_pts, self.sirena_edges, col_sir, mv, proj, vp, iluminacion, robots)

        # Reflector interno rotatorio
        self.op.push()
        self.op.rotateY(self.reflector_rot)
        self._render_mesh(self.reflector_pts, self.reflector_edges, (1.0, 1.0, 0.8), mv, proj, vp, iluminacion, robots)
        self.op.pop() # Fin reflector

        self.op.pop() # Fin sirena
        self.op.pop() # Fin cabina

        # --- 6 y 7. Ruedas: T·Ry(dirección)·Rx(rodamiento) en una sola matriz ---
        # Traseras: solo rodamiento (phi = 0). Delanteras: dirección + rodamiento.
        ruedas = [
            ((-0.95, -0.1, -0.8), 0.0),
            ((0.95, -0.1, -0.8), 0.0),
            ((-0.95, -0.1, 0.8), self.steering_angle),
            ((0.95, -0.1, 0.8), self.steering_angle),
        ]
        for pos, phi in ruedas:
            self.op.push()
            self.op.multiplicar(matriz_T_Ry_Rx(*pos, phi, self.wheel_spin))
            self._render_mesh(self.wheel_pts, self.wheel_edges, col_rueda, mv, proj, vp, iluminacion, robots)
            self.op.pop()

        # --- 8. Sistema de Manipuladores Mecánicos (Brazos y Pinzas) ---
        self.op.push()
        self.op.translate(0.0, -0.15, 1.25)
        self.op.rotateX(self.arm_angle)
        self._render_mesh(self.barra_pts, self.barra_edges, (0.5, 0.5, 0.5), mv, proj, vp, iluminacion, robots)

        # Brazo y Pinza Izquierda
        self.op.push()
        self.op.translate(-0.55, 0.0, 0.0)
        self._render_mesh(self.brazo_pts, self.brazo_edges, col_brazo, mv, proj, vp, iluminacion, robots)
        self.op.translate(0.0, 0.0, 0.45)
        self.op.rotateY(-self.claw_angle)
        self._render_mesh(self.pinza_izq_pts, self.pinza_izq_edges, col_pinza, mv, proj, vp, iluminacion, robots)
        self.op.pop()

        # Brazo y Pinza Derecha
        self.op.push()
        self.op.translate(0.55, 0.0, 0.0)
        self._render_mesh(self.brazo_pts, self.brazo_edges, col_brazo, mv, proj, vp, iluminacion, robots)
        self.op.translate(0.0, 0.0, 0.45)
        self.op.rotateY(self.claw_angle)
        self._render_mesh(self.pinza_der_pts, self.pinza_der_edges, col_pinza, mv, proj, vp, iluminacion, robots)
        self.op.pop()

        # Caja sujeta entre las pinzas (si lleva carga)
        if self.lleva_caja:
            self.op.push()
            self.op.translate(0.0, 0.0, 0.70)
            self._render_mesh(self.caja_cargo_pts, self.caja_cargo_edges, col_caja, mv, proj, vp, iluminacion, robots)
            self.op.pop()

        self.op.pop() # Fin brazos
