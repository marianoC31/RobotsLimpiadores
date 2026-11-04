import math
import random
from robot_limpiador import RobotLimpiador

# -------------------------------------------------------------
# RUTAS PREDETERMINADAS A TRAVÉS DE LOS PASILLOS DEL ALMACÉN
# Las coordenadas corresponden a los pasillos formados por los estantes:
# - Pasillo Oeste: X ≈ -7.2
# - Pasillo Central Carril Sur: X ≈ -1.2
# - Pasillo Central Carril Norte: X ≈ +1.2
# - Pasillo Este: X ≈ +7.2
# - Pasillo Norte: Z ≈ -7.8
# - Pasillo Sur (Frente a Puerta): Z ≈ +7.8
# -------------------------------------------------------------

RUTAS_PASILLOS = [
    # Ruta 0: Circuito Pasillo Oeste + Pasillo Central (sentido Sur)
    [(-7.2, -7.8), (-1.2, -7.8), (-1.2, 7.8), (-7.2, 7.8)],
    
    # Ruta 1: Circuito Pasillo Central (sentido Norte) + Pasillo Este
    [(1.2, 7.8), (1.2, -7.8), (7.2, -7.8), (7.2, 7.8)],
    
    # Ruta 2: Gran Anillo Perimetral Exterior del Almacén
    [(-7.2, -7.8), (7.2, -7.8), (7.2, 7.8), (-7.2, 7.8)],
    
    # Ruta 3: Circuito en Ocho (recorre Pasillo Oeste, Central y Este cruzando)
    [(-7.2, -7.8), (-1.2, -7.8), (-1.2, 7.8), (7.2, 7.8), (7.2, -7.8), (1.2, -7.8), (1.2, 7.8), (-7.2, 7.8)],
    
    # Ruta 4: Circuito de Carga en Puerta Sur y Distribución
    [(0.0, 7.8), (7.2, 7.8), (7.2, -7.8), (-1.2, -7.8), (-1.2, 7.8)]
]

# Colores característicos para las sirenas de los 5 robots
COLORES_SIRENAS = [
    (1.0, 0.15, 0.10), # Robot 0: Rojo sirena clásica
    (0.15, 0.50, 1.00), # Robot 1: Azul policía / seguridad
    (1.00, 0.65, 0.05), # Robot 2: Ámbar industrial
    (0.10, 0.95, 0.35), # Robot 3: Verde esmeralda
    (0.95, 0.15, 0.85)  # Robot 4: Magenta de advertencia
]

# Posiciones de partida predeterminadas a lo largo de los pasillos
SPAWN_PASILLOS = [
    (-7.2, -4.0,   0.0), # Pasillo Oeste (Norte)
    (-7.2,  3.5, 180.0), # Pasillo Oeste (Sur)
    (-1.2, -3.0, 180.0), # Pasillo Central carril Sur
    ( 1.2,  3.0,   0.0), # Pasillo Central carril Norte
    ( 7.2, -4.0,   0.0), # Pasillo Este (Norte)
    ( 7.2,  3.5, 180.0), # Pasillo Este (Sur)
    (-3.5, -7.8,  90.0), # Pasillo Norte
    ( 3.5,  7.8, 270.0)  # Pasillo Sur
]

def crear_flota_robots(cantidad=5):
    """
    Instancia por código los robots requeridos (al menos 5 robots):
    - Posiciones iniciales predeterminadas en pasillos, asignadas aleatoriamente sin encimarse.
    - Velocidades asignadas aleatoriamente dentro de un rango predeterminado.
    - Rutas predeterminadas asignadas a través de los pasillos.
    - Sirena con luz puntual de color único para cada robot.
    - Configuración de manipuladores y sensores de presión.
    """
    robots = []
    
    spawns_disponibles = list(SPAWN_PASILLOS)
    random.shuffle(spawns_disponibles)

    for i in range(cantidad):
        spawn = spawns_disponibles[i]
        # Velocidad aleatoria en rango predeterminado [0.048, 0.076]
        vel = random.uniform(0.048, 0.076)
        color = COLORES_SIRENAS[i % len(COLORES_SIRENAS)]
        ruta = RUTAS_PASILLOS[i % len(RUTAS_PASILLOS)]

        r = RobotLimpiador(
            id_robot=i,
            pos_x=spawn[0],
            pos_z=spawn[1],
            rot_y=spawn[2],
            speed=vel,
            color_sirena=color
        )
        r.set_ruta(ruta)

        # Demostración inicial: algunos robots transportan caja (sensor de presión activo)
        if i in (0, 2):
            r.lleva_caja = True
            r.sensor_presion_activo = True

        robots.append(r)

    return robots

def gestionar_colisiones(robots, dist_seguridad=2.8, dist_critica=1.65):
    """
    Detección y Reacción a colisiones entre robots:
    1. Calcula distancias euclidianas y conos frontales de visión de cada par de robots.
    2. Cruce de Pasillos / Intersecciones:
       - El robot con menor ID tiene derecho de paso.
       - El robot con mayor ID se detiene previamente y cede el paso.
    3. Tráfico en convoy (mismo sentido):
       - El robot perseguidor mantiene la distancia de seguridad frenando suavemente.
    4. Evasión Omnidireccional:
       - El robot que cede el paso realiza un ligero desplazamiento lateral (strafe)
         con sus ruedas omnidireccionales hacia la orilla del pasillo.
    5. Seguridad crítica absoluta:
       - Si la distancia cae por debajo de dist_critica, ambos se detienen para impedir colisiones físicas.
    """
    estados_anteriores = {r.id_robot: r.detenido for r in robots}
    
    # Restablecer estado base antes de evaluación
    for r in robots:
        r.detenido = False
        r.target_strafe = 0.0

    n = len(robots)
    for i in range(n):
        for j in range(n):
            if i == j:
                continue

            r_a = robots[i]
            r_b = robots[j]

            dx = r_b.pos_x - r_a.pos_x
            dz = r_b.pos_z - r_a.pos_z
            dist = math.hypot(dx, dz)

            if dist < dist_seguridad:
                rad_a = math.radians(r_a.rot_y)
                dir_ax = math.sin(rad_a)
                dir_az = math.cos(rad_a)

                # Proyección en campo visual frontal de A
                dot_a = dir_ax * dx + dir_az * dz
                cos_a = dot_a / (dist + 1e-6)

                if cos_a > 0.35:
                    rad_b = math.radians(r_b.rot_y)
                    dir_bx = math.sin(rad_b)
                    dir_bz = math.cos(rad_b)
                    dot_b = dir_bx * (-dx) + dir_bz * (-dz)
                    cos_b = dot_b / (dist + 1e-6)

                    # Caso 1: Cruce de pasillo / convergencia
                    if cos_b > 0.25:
                        if r_a.id_robot > r_b.id_robot:
                            r_a.detenido = True
                            # Evasión lateral omnidireccional hacia la orilla del pasillo
                            r_a.target_strafe = 0.55
                            if not estados_anteriores.get(r_a.id_robot, False):
                                print(f"⚠️  [CRUCE DE PASILLO] Robot {r_a.id_robot} cede el paso a Robot {r_b.id_robot} (Prioridad ID {r_b.id_robot} < {r_a.id_robot} | Distancia: {dist:.2f}m)")
                        
                        if dist < dist_critica:
                            r_b.detenido = True

                    # Caso 2: Persecución en mismo sentido (A va detrás de B)
                    elif cos_b < -0.2:
                        r_a.detenido = True
                        if not estados_anteriores.get(r_a.id_robot, False):
                            print(f"🛑 [DISTANCIA DE SEGURIDAD] Robot {r_a.id_robot} guarda distancia detrás de Robot {r_b.id_robot} (Distancia: {dist:.2f}m)")

    # Notificar cuando se despeja el camino
    for r in robots:
        if estados_anteriores.get(r.id_robot, False) and not r.detenido:
            print(f"✅ [VÍA LIBRE] Robot {r.id_robot} reanuda su marcha por el pasillo.")
