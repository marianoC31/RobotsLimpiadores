"""Caras sólidas con textura (mapeo UV).

Durante el render, cada modelo transforma sus vértices con OpMat3D (los mismos
que usa para sus aristas) y registra aquí sus caras: qué textura usan y qué
coordenada UV tiene cada esquina.  Al final del cuadro, dibujar() las pinta con
la cámara propia (Camara3D.cargar_en_opengl):

    color final = textura(u, v) × color del material

Coordenadas UV: (0,0) es una esquina de la imagen y (1,1) la opuesta.  Si una
cara usa UV de 0 a 2, la imagen se repite 2 veces (GL_REPEAT).
"""
from OpenGL.GL import *
from texturas import generar_texturas_por_defecto, obtener_textura

UV_CARA = ((0.0, 0.0), (1.0, 0.0), (1.0, 1.0), (0.0, 1.0))
ALFA_TRANSPARENTE = 0.28

# Caras de una caja cuyos 8 vértices vienen en este orden:
#   0(-x,-y,-z) 1(+x,-y,-z) 2(+x,+y,-z) 3(-x,+y,-z)
#   4(-x,-y,+z) 5(+x,-y,+z) 6(+x,+y,+z) 7(-x,+y,+z)
CARAS_CAJA = ((0, 1, 2, 3), (5, 4, 7, 6), (4, 0, 3, 7), (1, 5, 6, 2), (3, 2, 6, 7), (4, 5, 1, 0))

_texturas = {}        # nombre -> id de textura en la tarjeta de video
_caras = {}           # nombre -> [(vértices, uvs, color)]
_transparentes = {}   # igual, pero se pintan semitransparentes al final


def cargar_texturas():
    """Sube las imágenes de assets/textures a la tarjeta de video (requiere la ventana abierta)."""
    for nombre, ruta in generar_texturas_por_defecto().items():
        _texturas[nombre] = obtener_textura(ruta, repetir=True)


def agregar_quad(textura, vertices, uvs, color, transparente=False):
    destino = _transparentes if transparente else _caras
    destino.setdefault(textura, []).append((vertices, uvs, color))


def agregar_caja(textura, pts, color, orden=None):
    """Las 6 caras de una caja ya transformada (8 vértices en el orden de CARAS_CAJA)."""
    if orden is not None:
        pts = [pts[i] for i in orden]
    for cara in CARAS_CAJA:
        agregar_quad(textura, [pts[i] for i in cara], UV_CARA, color)


def _pintar(grupos, alfa):
    for nombre, caras in grupos.items():
        glBindTexture(GL_TEXTURE_2D, _texturas[nombre])
        glBegin(GL_QUADS)
        for vertices, uvs, (r, g, b) in caras:
            glColor4f(r, g, b, alfa)
            for (x, y, z), (u, v) in zip(vertices, uvs):
                glTexCoord2f(u, v)
                glVertex3f(x, y, z)
        glEnd()


def dibujar():
    glEnable(GL_TEXTURE_2D)
    glTexEnvi(GL_TEXTURE_ENV, GL_TEXTURE_ENV_MODE, GL_MODULATE)   # textura × color
    glEnable(GL_POLYGON_OFFSET_FILL)
    glPolygonOffset(1.0, 1.0)      # caras un poco atrás: las aristas quedan visibles encima
    _pintar(_caras, 1.0)
    # Transparentes al final, sin escribir profundidad (no ocultan lo que hay detrás)
    glEnable(GL_BLEND)
    glBlendFunc(GL_SRC_ALPHA, GL_ONE_MINUS_SRC_ALPHA)
    glDepthMask(GL_FALSE)
    _pintar(_transparentes, ALFA_TRANSPARENTE)
    glDepthMask(GL_TRUE)
    glDisable(GL_BLEND)
    glBindTexture(GL_TEXTURE_2D, 0)
    glDisable(GL_POLYGON_OFFSET_FILL)
    glDisable(GL_TEXTURE_2D)
    glColor4f(1.0, 1.0, 1.0, 1.0)
    _caras.clear()
    _transparentes.clear()
