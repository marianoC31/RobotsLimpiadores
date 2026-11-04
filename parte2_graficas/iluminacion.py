import math

class SistemaIluminacion:
    """
    Motor de Iluminación Matemática implementado desde cero en Python:
    - No utiliza GL_LIGHTING ni llamadas automáticas de OpenGL.
    - Calcula la iluminación vectorial combinando:
        1. Luz Ambiental global del almacén.
        2. Luz Direccional (cenital desde el techo).
        3. 5 Luces Puntuales tipo Sirena (montadas sobre cada robot, trasladándose dinámicamente).
    - Aplica atenuación cuadrática por distancia euclidiana y modulación de pulsos/alertas.
    """
    def __init__(self):
        self.luz_direccional_activa = True
        
        # Vector unitario de la luz direccional (hacia abajo y ligeramente inclinado)
        ld = (0.35, 0.90, 0.25)
        mag = math.sqrt(ld[0]**2 + ld[1]**2 + ld[2]**2)
        self.dir_vector = (ld[0] / mag, ld[1] / mag, ld[2] / mag)
        
        # Colores de luz
        self.color_ambiente = (0.28, 0.30, 0.34)
        self.color_direccional = (0.75, 0.75, 0.72)
        
        # Radio de alcance de las sirenas puntuales de los robots
        self.radio_luz_robot = 7.0

    def calcular_color(self, color_base, pos_mundo, normal_aprox=(0.0, 1.0, 0.0), robots=None):
        """
        Calcula el color RGB final [0.0, 1.0] para un punto en el espacio 3D (pos_mundo):
        - Suma luz ambiente.
        - Suma aporte direccional si está activa.
        - Suma el aporte de cada una de las 5 luces puntuales de las sirenas de los robots.
        """
        r_base, g_base, b_base = color_base

        # 1. Componente Ambiental
        r_total = r_base * self.color_ambiente[0]
        g_total = g_base * self.color_ambiente[1]
        b_total = b_base * self.color_ambiente[2]

        # 2. Componente Direccional (si está activa)
        if self.luz_direccional_activa:
            # Producto punto N . L aproximado
            dot = normal_aprox[0]*self.dir_vector[0] + normal_aprox[1]*self.dir_vector[1] + normal_aprox[2]*self.dir_vector[2]
            factor_dir = max(0.15, min(1.0, dot))
            r_total += r_base * self.color_direccional[0] * factor_dir
            g_total += g_base * self.color_direccional[1] * factor_dir
            b_total += b_base * self.color_direccional[2] * factor_dir

        # 3. Componentes Puntuales (Sirenas de los 5 Robots)
        if robots:
            px, py, pz = pos_mundo
            for r in robots:
                # Posición de la sirena montada sobre la cabina del robot
                lx = r.pos_x
                ly = r.pos_y + 1.25
                lz = r.pos_z

                dx = px - lx
                dy = py - ly
                dz = pz - lz
                dist = math.sqrt(dx*dx + dy*dy + dz*dz)

                if dist < self.radio_luz_robot:
                    # Atenuación suave por distancia (1 - d/R)^2
                    factor_dist = (1.0 - (dist / self.radio_luz_robot)) ** 2

                    # Pulso dinámico de la sirena
                    if r.detenido:
                        # Destello estroboscópico de alerta roja si está cediendo el paso
                        pulso = 1.6 if int(r.anim_time * 18.0) % 2 == 0 else 0.2
                        col_sirena = (1.0, 0.15, 0.10)
                    else:
                        pulso = 0.8 + 0.35 * math.sin(r.anim_time * 8.0 + r.id_robot * 1.5)
                        col_sirena = r.color_sirena

                    sr = col_sirena[0] * pulso * factor_dist * 1.2
                    sg = col_sirena[1] * pulso * factor_dist * 1.2
                    sb = col_sirena[2] * pulso * factor_dist * 1.2

                    r_total += sr
                    g_total += sg
                    b_total += sb

        # Clamping en rango [0.0, 1.0]
        return (
            max(0.0, min(1.0, r_total)),
            max(0.0, min(1.0, g_total)),
            max(0.0, min(1.0, b_total))
        )
