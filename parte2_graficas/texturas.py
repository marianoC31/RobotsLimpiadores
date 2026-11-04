import os
import pygame
from OpenGL.GL import *

BASE_DIR = os.path.dirname(os.path.abspath(__file__))
TEXTURES_DIR = os.path.join(BASE_DIR, "assets", "textures")

def generar_texturas_por_defecto(forzar=False):
    """Genera archivos PNG procedurales de alta calidad si no existen en disco (o si forzar=True)."""
    os.makedirs(TEXTURES_DIR, exist_ok=True)
    
    rutas = {
        "piso": os.path.join(TEXTURES_DIR, "piso.png"),
        "pared": os.path.join(TEXTURES_DIR, "pared.png"),
        "puerta": os.path.join(TEXTURES_DIR, "puerta.png"),
        "caja": os.path.join(TEXTURES_DIR, "caja.png"),
        "estante": os.path.join(TEXTURES_DIR, "estante.png"),
        "robot_metal": os.path.join(TEXTURES_DIR, "robot_metal.png")
    }

    # 1. TEXTURA DE PISO (Baldosas de concreto industrial con cuadrícula de celdas)
    if forzar or not os.path.exists(rutas["piso"]):
        surf = pygame.Surface((256, 256))
        surf.fill((165, 168, 172)) # Base gris concreto pulido
        # Juntas de dilatación / cuadrícula
        pygame.draw.rect(surf, (75, 78, 82), (0, 0, 256, 256), 4)
        pygame.draw.line(surf, (100, 104, 110), (0, 128), (256, 128), 2)
        pygame.draw.line(surf, (100, 104, 110), (128, 0), (128, 256), 2)
        # Detalle de textura sutil de piso industrial
        for i in range(16, 256, 32):
            pygame.draw.circle(surf, (140, 143, 148), (i, i), 2)
            pygame.draw.circle(surf, (185, 188, 192), (256 - i, i), 2)
        pygame.image.save(surf, rutas["piso"])

    # 2. TEXTURA DE PARED (Muro de hormigón con franja/zócalo inferior)
    if forzar or not os.path.exists(rutas["pared"]):
        surf = pygame.Surface((256, 256))
        surf.fill((215, 220, 225)) # Gris claro industrial
        # Bloques o paneles de hormigón
        for y in range(0, 256, 64):
            pygame.draw.line(surf, (165, 170, 175), (0, y), (256, y), 2)
        for x in range(0, 256, 128):
            pygame.draw.line(surf, (165, 170, 175), (x, 0), (x, 256), 2)
        # Zócalo inferior reforzado (base oscura)
        pygame.draw.rect(surf, (80, 85, 92), (0, 220, 256, 36))
        pygame.draw.line(surf, (55, 60, 66), (0, 220), (256, 220), 3)
        pygame.image.save(surf, rutas["pared"])

    # 3. TEXTURA DE PUERTA (Portón metálico seccional con marco y franjas de seguridad)
    if forzar or not os.path.exists(rutas["puerta"]):
        surf = pygame.Surface((256, 256))
        surf.fill((65, 70, 76)) # Metal oscuro portón
        # Paneles seccionales horizontales
        for y in range(20, 236, 36):
            pygame.draw.rect(surf, (85, 92, 98), (20, y, 216, 32))
            pygame.draw.rect(surf, (40, 44, 48), (20, y, 216, 32), 2)
        # Marco exterior de acero
        pygame.draw.rect(surf, (35, 38, 42), (0, 0, 256, 256), 18)
        # Franja de seguridad amarilla y negra (Hazard stripes) en la base
        for i in range(0, 256, 24):
            pygame.draw.polygon(surf, (245, 205, 10), [(i, 236), (i + 14, 236), (i + 24, 256), (i + 10, 256)])
        # Manija o panel de acceso
        pygame.draw.rect(surf, (210, 45, 45), (220, 120, 12, 24)) # Botón de emergencia
        pygame.image.save(surf, rutas["puerta"])

    # 4. TEXTURA DE CAJA (Cartón con cinta de embalaje, etiquetas y código de barras)
    if forzar or not os.path.exists(rutas["caja"]):
        surf = pygame.Surface((256, 256))
        surf.fill((195, 145, 88)) # Tono cartón corrugado
        # Bordes de la caja
        pygame.draw.rect(surf, (155, 110, 60), (0, 0, 256, 256), 6)
        # Cinta adhesiva central
        pygame.draw.rect(surf, (228, 192, 132), (0, 108, 256, 40))
        pygame.draw.line(surf, (175, 135, 75), (0, 108), (256, 108), 2)
        pygame.draw.line(surf, (175, 135, 75), (0, 148), (256, 148), 2)
        # Etiqueta de envío blanca con código de barras
        pygame.draw.rect(surf, (245, 245, 245), (32, 32, 90, 56))
        pygame.draw.rect(surf, (180, 180, 180), (32, 32, 90, 56), 1)
        # Líneas simulando código de barras
        for bx in range(40, 112, 4):
            ancho_linea = 2 if bx % 8 == 0 else 1
            pygame.draw.line(surf, (20, 20, 20), (bx, 42), (bx, 68), ancho_linea)
        # Icono "Hacia Arriba" (flechas)
        pygame.draw.line(surf, (40, 30, 20), (190, 60), (190, 40), 3)
        pygame.draw.polygon(surf, (40, 30, 20), [(185, 45), (195, 45), (190, 35)])
        pygame.image.save(surf, rutas["caja"])

    # 5. TEXTURA DE ESTANTE (Vigas metálicas naranja/azul industrial)
    if forzar or not os.path.exists(rutas["estante"]):
        surf = pygame.Surface((256, 256))
        surf.fill((35, 65, 115)) # Azul industrial
        # Perforaciones en los postes
        for y in range(16, 256, 32):
            pygame.draw.circle(surf, (20, 40, 75), (32, y), 8)
            pygame.draw.circle(surf, (20, 40, 75), (224, y), 8)
        # Viga transversal naranja
        pygame.draw.rect(surf, (235, 105, 18), (0, 96, 256, 64))
        pygame.draw.rect(surf, (175, 65, 10), (0, 96, 256, 64), 3)
        pygame.image.save(surf, rutas["estante"])

    # 6. TEXTURA DEL ROBOT (Metal amarillo industrial con placas de advertencia)
    if forzar or not os.path.exists(rutas["robot_metal"]):
        surf = pygame.Surface((256, 256))
        surf.fill((235, 175, 20)) # Amarillo Caterpillar industrial
        # Placas y remaches
        pygame.draw.rect(surf, (190, 135, 15), (0, 0, 256, 256), 6)
        # Franja de advertencia diagonal en el centro
        for i in range(-50, 300, 32):
            pygame.draw.polygon(surf, (30, 30, 35), [(i, 0), (i + 16, 0), (i + 16 - 80, 256), (i - 80, 256)])
        # Panel metálico interior
        pygame.draw.rect(surf, (70, 75, 80), (64, 64, 128, 128))
        pygame.draw.rect(surf, (45, 50, 55), (64, 64, 128, 128), 3)
        # Remaches en las esquinas
        for cx, cy in [(16, 16), (240, 16), (16, 240), (240, 240), (80, 80), (176, 80), (80, 176), (176, 176)]:
            pygame.draw.circle(surf, (50, 50, 55), (cx, cy), 4)
            pygame.draw.circle(surf, (120, 125, 130), (cx - 1, cy - 1), 2)
        pygame.image.save(surf, rutas["robot_metal"])

    return rutas

def cargar_textura(ruta_archivo, repetir=True):
    """
    Carga una imagen y la registra en OpenGL, retornando su ID de textura.
    Configura el filtro de textura y el modo de repetición/envoltura (UV wrapping).
    """
    if not os.path.isabs(ruta_archivo):
        ruta_archivo = os.path.join(BASE_DIR, ruta_archivo)
    if not os.path.exists(ruta_archivo):
        raise FileNotFoundError(f"No se encontró el archivo de textura: {ruta_archivo}")

    # Cargar usando pygame e invertir verticalmente para el sistema de coordenadas de OpenGL
    superficie = pygame.image.load(ruta_archivo)
    if pygame.display.get_surface() is not None:
        superficie = superficie.convert_alpha()
    ancho, alto = superficie.get_size()
    datos_imagen = pygame.image.tostring(superficie, "RGBA", True)

    tex_id = glGenTextures(1)
    glBindTexture(GL_TEXTURE_2D, tex_id)

    # Configuración de filtrado bilineal
    glTexParameteri(GL_TEXTURE_2D, GL_TEXTURE_MIN_FILTER, GL_LINEAR)
    glTexParameteri(GL_TEXTURE_2D, GL_TEXTURE_MAG_FILTER, GL_LINEAR)

    # Envoltura UV (GL_REPEAT para patrones continuos como pisos y paredes)
    modo_wrap = GL_REPEAT if repetir else GL_CLAMP_TO_EDGE
    glTexParameteri(GL_TEXTURE_2D, GL_TEXTURE_WRAP_S, modo_wrap)
    glTexParameteri(GL_TEXTURE_2D, GL_TEXTURE_WRAP_T, modo_wrap)

    # Transferencia de píxeles a la GPU
    glTexImage2D(GL_TEXTURE_2D, 0, GL_RGBA, ancho, alto, 0, GL_RGBA, GL_UNSIGNED_BYTE, datos_imagen)
    glBindTexture(GL_TEXTURE_2D, 0)

    return tex_id

_CACHE_TEXTURAS = {}

def obtener_textura(ruta_archivo, repetir=True):
    """Retorna el ID de textura de OpenGL reutilizando instancias cargadas previamente."""
    if ruta_archivo not in _CACHE_TEXTURAS:
        _CACHE_TEXTURAS[ruta_archivo] = cargar_textura(ruta_archivo, repetir)
    return _CACHE_TEXTURAS[ruta_archivo]


