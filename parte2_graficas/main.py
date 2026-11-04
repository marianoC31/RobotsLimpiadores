import os, sys
sys.path.insert(0, os.path.dirname(os.path.dirname(os.path.abspath(__file__))))  # raíz del proyecto -> permite "import nucleo"
sys.stdout.reconfigure(encoding="utf-8", errors="replace")  # emojis en consolas de Windows

import math
import pygame
from pygame.locals import *
from OpenGL.GL import *
from OpenGL.GLU import *

from nucleo.OpMat import OpMat3D
from robot_limpiador import bresenham_2d
from almacen import Almacen
from estante import generar_estantes_por_codigo
from caja import generar_cajas_aleatorias, generar_pilas_cajas
from iluminacion import SistemaIluminacion
from gestor_robots import crear_flota_robots, gestionar_colisiones

pygame.init()
screen_width = 1100
screen_height = 750

# Parámetros de proyección de cámara 3D
FOVY = 50.0
ZNEAR = 1.0
ZFAR = 500.0

# Parámetros de Cámara Orbital Interactiva
cam_distance = 28.0
cam_yaw = 32.0    # Ángulo horizontal (grados)
cam_pitch = 42.0  # Ángulo de elevación (grados)
cam_target = [0.0, 1.0, 0.0]
follow_robot_id = None # None = Vista general, 0..4 = Seguir robot

def Axis(mv, proj, vp):
    """Dibuja los ejes coordenados del mundo 3D usando bresenham_2d."""
    ejes = [
        ([0, 0, 0], [4.5, 0, 0], (1.0, 0.2, 0.2)), # X (Rojo)
        ([0, 0, 0], [0, 3.5, 0], (0.2, 1.0, 0.2)), # Y (Verde)
        ([0, 0, 0], [0, 0, 4.5], (0.2, 0.6, 1.0))  # Z (Azul)
    ]
    for p_ini, p_fin, color in ejes:
        wx1, wy1, _ = gluProject(*p_ini, mv, proj, vp)
        wx2, wy2, _ = gluProject(*p_fin, mv, proj, vp)
        glColor3f(*color)
        bresenham_2d(wx1, wy1, wx2, wy2)

class HUD:
    """
    Panel de visualización 2D (Head-Up Display) en tiempo real:
    - Estado de los 5 robots, velocidades, sirenas y sensores de presión.
    - Notificaciones de ceder paso y atajos de teclado interactivos.
    """
    def __init__(self, w=450, h=300):
        self.w = w
        self.h = h
        self.visible = True
        pygame.font.init()
        self.font_h1 = pygame.font.Font(None, 22)
        self.font_txt = pygame.font.Font(None, 16)
        self.surf = pygame.Surface((w, h), pygame.SRCALPHA)
        self.tex_id = glGenTextures(1)
        glBindTexture(GL_TEXTURE_2D, self.tex_id)
        glTexParameteri(GL_TEXTURE_2D, GL_TEXTURE_MIN_FILTER, GL_LINEAR)
        glTexParameteri(GL_TEXTURE_2D, GL_TEXTURE_MAG_FILTER, GL_LINEAR)
        glBindTexture(GL_TEXTURE_2D, 0)

    def render(self, screen_w, screen_h, robots, iluminacion, modo_pilas, pausado, follow_id, fps, num_cajas):
        if not self.visible:
            return

        self.surf.fill((12, 16, 24, 225))
        pygame.draw.rect(self.surf, (60, 80, 110, 240), (0, 0, self.w, self.h), 2)
        
        # 1. Encabezado
        t1 = self.font_h1.render("TC2008B - ALMACÉN INTELIGENTE 3D", True, (255, 215, 0))
        t2 = self.font_txt.render("Graficación pura con OpMat3D y Bresenham 2D (Sin motor 3D de OpenGL)", True, (180, 205, 230))
        self.surf.blit(t1, (12, 10))
        self.surf.blit(t2, (12, 32))
        pygame.draw.line(self.surf, (50, 70, 95), (12, 50), (self.w - 12, 50), 1)

        # 2. Estado Global de Iluminación y Cajas
        estado_luz = "ENCENDIDA (Día)" if iluminacion.luz_direccional_activa else "APAGADA (Sirenas Activas)"
        color_luz = (110, 255, 130) if iluminacion.luz_direccional_activa else (255, 165, 60)
        estado_modo = "Pilas de hasta 5 cajas" if modo_pilas else f"Nivel piso (K={num_cajas} cajas)"
        estado_pausa = "PAUSADO" if pausado else f"{int(fps)} FPS"
        
        info_luz = self.font_txt.render(f"Luz Direccional: {estado_luz} | 5 Sirenas: ACTIVAS", True, color_luz)
        info_sim = self.font_txt.render(f"Cajas: {estado_modo} | Estado: {estado_pausa}", True, (215, 228, 242))
        self.surf.blit(info_luz, (12, 56))
        self.surf.blit(info_sim, (12, 74))

        # 3. Estado de Cámara
        cam_info = f"Cámara: Siguiendo a Robot {follow_id}" if follow_id is not None else "Cámara: Vista General Orbital"
        t_cam = self.font_txt.render(cam_info, True, (255, 230, 120))
        self.surf.blit(t_cam, (12, 92))
        pygame.draw.line(self.surf, (50, 70, 95), (12, 110), (self.w - 12, 110), 1)

        # 4. Tabla de Estado de los 5 Robots
        header = self.font_txt.render("Robot  | Posición (X, Z) | Vel   | Estado Pasillo       | Sensor Presión", True, (155, 180, 210))
        self.surf.blit(header, (12, 115))

        for idx, r in enumerate(robots):
            y = 133 + idx * 18
            r_col = [int(c * 255) for c in r.color_sirena]
            pygame.draw.circle(self.surf, r_col, (18, y + 6), 5)
            
            if r.detenido:
                st_txt = "🛑 Cede Paso"
                st_col = (255, 90, 80)
            else:
                st_txt = "🟢 En Ruta  "
                st_col = (90, 240, 120)

            if r.sensor_presion_activo:
                pres_txt = "[📦 Caja Sujeta: SÍ]"
                pres_col = (90, 255, 140)
            else:
                pres_txt = "[-- Vacío --]"
                pres_col = (160, 170, 180)

            linea = f"R{r.id_robot}  | ({r.pos_x:5.1f}, {r.pos_z:5.1f}) | {r.speed:.2f} | {st_txt} | "
            self.surf.blit(self.font_txt.render(linea, True, st_col), (28, y))
            self.surf.blit(self.font_txt.render(pres_txt, True, pres_col), (290, y))

        # 5. Atajos de Teclado
        pygame.draw.line(self.surf, (50, 70, 95), (12, 226), (self.w - 12, 226), 1)
        c1 = self.font_txt.render("[1-5] Seguir Robot | [0] Vista General | [L] Luz Direccional", True, (245, 215, 110))
        c2 = self.font_txt.render("[C] Cajas/Presión | [P] Pilas 5 Cajas | [R] Reset Cajas | [F] Flota", True, (200, 225, 245))
        c3 = self.font_txt.render("[Espacio] Pausa | [H] Ocultar HUD | [Arrastrar Mouse/Rueda] Órbita", True, (160, 195, 225))
        self.surf.blit(c1, (12, 232))
        self.surf.blit(c2, (12, 250))
        self.surf.blit(c3, (12, 268))

        # Transferir textura al framebuffer OpenGL
        raw_data = pygame.image.tostring(self.surf, "RGBA", False)
        glBindTexture(GL_TEXTURE_2D, self.tex_id)
        glTexImage2D(GL_TEXTURE_2D, 0, GL_RGBA, self.w, self.h, 0, GL_RGBA, GL_UNSIGNED_BYTE, raw_data)

        glEnable(GL_BLEND)
        glBlendFunc(GL_SRC_ALPHA, GL_ONE_MINUS_SRC_ALPHA)
        glEnable(GL_TEXTURE_2D)

        glColor3f(1.0, 1.0, 1.0)
        x_pos, y_pos = 14, 14
        glBegin(GL_QUADS)
        glTexCoord2f(0.0, 0.0); glVertex2f(x_pos, screen_h - y_pos)
        glTexCoord2f(1.0, 0.0); glVertex2f(x_pos + self.w, screen_h - y_pos)
        glTexCoord2f(1.0, 1.0); glVertex2f(x_pos + self.w, screen_h - (y_pos + self.h))
        glTexCoord2f(0.0, 1.0); glVertex2f(x_pos, screen_h - (y_pos + self.h))
        glEnd()

        glBindTexture(GL_TEXTURE_2D, 0)
        glDisable(GL_TEXTURE_2D)
        glDisable(GL_BLEND)

def Init():
    pygame.display.set_mode((screen_width, screen_height), DOUBLEBUF | OPENGL)
    pygame.display.set_caption("TC2008B - Almacén Inteligente 3D (OpMat3D & Bresenham 2D)")
    
    glMatrixMode(GL_PROJECTION)
    glLoadIdentity()
    gluPerspective(FOVY, screen_width / screen_height, ZNEAR, ZFAR)
    
    glMatrixMode(GL_MODELVIEW)
    glClearColor(0.03, 0.04, 0.06, 1.0)

def update_camera(robots):
    """Calcula la posición de la cámara orbital o de seguimiento y aplica gluLookAt."""
    global cam_target, cam_distance
    
    if follow_robot_id is not None and follow_robot_id < len(robots):
        r = robots[follow_robot_id]
        cam_target[0] += (r.pos_x - cam_target[0]) * 0.15
        cam_target[1] += (r.pos_y + 0.6 - cam_target[1]) * 0.15
        cam_target[2] += (r.pos_z - cam_target[2]) * 0.15
    else:
        cam_target[0] += (0.0 - cam_target[0]) * 0.1
        cam_target[1] += (1.0 - cam_target[1]) * 0.1
        cam_target[2] += (0.0 - cam_target[2]) * 0.1

    rad_yaw = math.radians(cam_yaw)
    rad_pitch = math.radians(cam_pitch)
    
    eye_x = cam_target[0] + cam_distance * math.cos(rad_pitch) * math.sin(rad_yaw)
    eye_y = cam_target[1] + cam_distance * math.sin(rad_pitch)
    eye_z = cam_target[2] + cam_distance * math.cos(rad_pitch) * math.cos(rad_yaw)
    
    glMatrixMode(GL_MODELVIEW)
    glLoadIdentity()
    gluLookAt(eye_x, eye_y, eye_z, cam_target[0], cam_target[1], cam_target[2], 0.0, 1.0, 0.0)

if __name__ == "__main__":
    Init()
    
    # 1. Sistema de Iluminación Matemática en Python (Luz Direccional + 5 Luces Sirena Puntuales)
    iluminacion = SistemaIluminacion()
    
    # 2. Instancia de OpMat3D para cálculo de transformaciones matriciales
    op_aux = OpMat3D(post=True)  # jerárquico: M = M·T
    
    # 3. Almacén de M x N espacios (Piso, Paredes y Puerta)
    almacen = Almacen(m=20.0, n=20.0, altura=4.0)
    
    # 4. Estantes instanciados por código formando pasillos organizados
    estantes = generar_estantes_por_codigo(almacen.m, almacen.n)
    
    # 5. K Cajas iniciales instanciadas por código en posiciones aleatorias a nivel de piso
    K = 18
    modo_pilas = False
    cajas = generar_cajas_aleatorias(k=K, almacen_m=almacen.m, almacen_n=almacen.n, estantes=estantes)
    
    # 6. Flota de 5 Robots con rutas predeterminadas, velocidades y posiciones aleatorias
    NUM_ROBOTS = 5
    robots = crear_flota_robots(cantidad=NUM_ROBOTS)

    # 7. Interfaz On-Screen Display (HUD)
    hud = HUD(w=450, h=290)

    clock = pygame.time.Clock()
    running = True
    pausado = False
    
    mouse_dragging = False
    last_mouse_pos = (0, 0)
    
    print("\n" + "="*70)
    print("🚀  TC2008B - ALMACÉN INTELIGENTE 3D (PARTE 2)")
    print("    Implementado con OpMat3D y Bresenham 2D (Sin entorno 3D de OpenGL)")
    print("="*70)
    print("  • 5 Robots omnidireccionales con rutas y velocidades predeterminadas.")
    print("  • Iluminación matemática en Python: Luz direccional + 5 sirenas puntuales.")
    print("  • Manipuladores con sujeción de cajas y sensor de presión frontal.")
    print("  • Detección de colisiones con asignación de paso y evasión lateral.")
    print("  • Controles: [1-5] Seguir robot, [0] Vista general, [L] Luz, [C] Cajas, [P] Pilas")
    print("="*70 + "\n")

    while running:
        dt = clock.tick(30)
        fps = clock.get_fps()

        for event in pygame.event.get():
            if event.type == pygame.QUIT or (event.type == KEYDOWN and event.key == K_ESCAPE):
                running = False
            elif event.type == KEYDOWN:
                if event.key == K_SPACE:
                    pausado = not pausado
                    print("⏸️  Simulación pausada." if pausado else "▶️  Simulación reanudada.")
                elif event.key == K_h:
                    hud.visible = not hud.visible
                elif event.key == K_r:
                    modo_pilas = False
                    cajas = generar_cajas_aleatorias(k=K, almacen_m=almacen.m, almacen_n=almacen.n, estantes=estantes)
                    print(f"🔄 Se regeneraron {K} cajas en posiciones aleatorias a nivel de piso.")
                elif event.key == K_p:
                    modo_pilas = not modo_pilas
                    if modo_pilas:
                        cajas = generar_pilas_cajas(k=K, almacen_m=almacen.m, almacen_n=almacen.n, estantes=estantes)
                        print(f"📦 Modo Pilas: {K} cajas organizadas en pilas de hasta 5 cajas.")
                    else:
                        cajas = generar_cajas_aleatorias(k=K, almacen_m=almacen.m, almacen_n=almacen.n, estantes=estantes)
                        print(f"📦 Modo Piso: {K} cajas dispersas a nivel de piso (sin pilas).")
                elif event.key == K_c:
                    for r in robots:
                        r.lleva_caja = not r.lleva_caja
                        r.sensor_presion_activo = r.lleva_caja
                    print(f"🤖 Manipuladores actualizados: Lleva caja = {robots[0].lleva_caja} (Sensor de presión activo).")
                elif event.key == K_f:
                    robots = crear_flota_robots(cantidad=NUM_ROBOTS)
                    print("🔄 Flota reinicializada con nuevas posiciones y velocidades predeterminadas aleatorias.")
                elif event.key == K_l:
                    iluminacion.luz_direccional_activa = not iluminacion.luz_direccional_activa
                    if iluminacion.luz_direccional_activa:
                        print("💡 Luz direccional ACTIVADA (Modo Día).")
                    else:
                        print("🌙 Luz direccional DESACTIVADA (Modo Noche: Sirenas puntuales resaltadas).")
                elif event.key in (K_1, K_2, K_3, K_4, K_5):
                    idx = event.key - K_1
                    if idx < len(robots):
                        follow_robot_id = idx
                        cam_distance = 11.0
                        print(f"🎥 Cámara siguiendo a Robot {idx}.")
                elif event.key == K_0:
                    follow_robot_id = None
                    cam_distance = 28.0
                    print("🎥 Cámara restaurada a Vista General del Almacén.")
                elif event.key == K_UP:
                    cam_pitch = min(85.0, cam_pitch + 4.0)
                elif event.key == K_DOWN:
                    cam_pitch = max(5.0, cam_pitch - 4.0)
                elif event.key == K_LEFT:
                    cam_yaw -= 5.0
                elif event.key == K_RIGHT:
                    cam_yaw += 5.0
                elif event.key in (K_PLUS, K_KP_PLUS, K_e):
                    cam_distance = max(6.0, cam_distance - 1.5)
                elif event.key in (K_MINUS, K_KP_MINUS, K_q):
                    cam_distance = min(60.0, cam_distance + 1.5)

            elif event.type == MOUSEBUTTONDOWN:
                if event.button == 1:
                    mouse_dragging = True
                    last_mouse_pos = event.pos
                elif event.button == 4:
                    cam_distance = max(6.0, cam_distance - 1.5)
                elif event.button == 5:
                    cam_distance = min(60.0, cam_distance + 1.5)
            elif event.type == MOUSEBUTTONUP:
                if event.button == 1:
                    mouse_dragging = False
            elif event.type == MOUSEMOTION and mouse_dragging:
                dx = event.pos[0] - last_mouse_pos[0]
                dy = event.pos[1] - last_mouse_pos[1]
                last_mouse_pos = event.pos
                cam_yaw += dx * 0.4
                cam_pitch = max(5.0, min(85.0, cam_pitch + dy * 0.4))

        glClear(GL_COLOR_BUFFER_BIT)
        
        # 1. Configuración de Cámara en Perspectiva 3D
        update_camera(robots)
        
        # 2. Detección y Reacción a Colisiones entre Robots (Prioridad y Evasión Omnidireccional)
        if not pausado:
            gestionar_colisiones(robots, dist_seguridad=2.8, dist_critica=1.65)
            for r in robots:
                r.update()

        # 3. Obtener matrices de vista y proyección 3D para la proyección a pantalla
        mv = glGetDoublev(GL_MODELVIEW_MATRIX)
        proj = glGetDoublev(GL_PROJECTION_MATRIX)
        vp = glGetIntegerv(GL_VIEWPORT)

        # 4. Cambiar a proyección 2D ortogonal para rasterizado de píxeles con Bresenham
        glMatrixMode(GL_PROJECTION)
        glPushMatrix()
        glLoadIdentity()
        gluOrtho2D(0, vp[2], 0, vp[3])
        glMatrixMode(GL_MODELVIEW)
        glPushMatrix()
        glLoadIdentity()
        glPointSize(1.8)

        # 5. Ejes coordenados del mundo con Bresenham
        Axis(mv, proj, vp)

        # 6. Renderizado del Almacén (Piso M x N, demarcaciones, paredes y puerta)
        almacen.render(mv, proj, vp, iluminacion, robots)

        # 7. Renderizado de Estantes (Pasillos, vigas y cajas almacenadas)
        for e in estantes:
            e.render(mv, proj, vp, op_aux, iluminacion, robots)

        # 8. Renderizado de Cajas (Piso / Pilas de hasta 5)
        for c in cajas:
            c.render(mv, proj, vp, op_aux, iluminacion, robots)

        # 9. Renderizado de los 5 Robots (Chasis, cabina, sirena, ruedas Mecanum y pinzas)
        for r in robots:
            r.render(mv, proj, vp, iluminacion, robots)

        # 10. Panel HUD con telemetría en tiempo real
        hud.render(screen_width, screen_height, robots, iluminacion, modo_pilas, pausado, follow_robot_id, fps, len(cajas))

        # 11. Restaurar proyección 3D
        glPopMatrix()
        glMatrixMode(GL_PROJECTION)
        glPopMatrix()
        glMatrixMode(GL_MODELVIEW)
        
        pygame.display.flip()
    
    pygame.quit()
