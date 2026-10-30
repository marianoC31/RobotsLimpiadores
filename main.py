# main.py
import sys
import pygame
from piramide import Piramide

def main():
    pygame.init()
    
    WIDTH, HEIGHT = 800, 600
    screen = pygame.display.set_mode((WIDTH, HEIGHT))
    pygame.display.set_caption("Pirámide 3D con Algoritmo de Bresenham")
    
    clock = pygame.time.Clock()
    objeto_piramide = Piramide(WIDTH, HEIGHT)

    running = True
    while running:
        for event in pygame.event.get():
            if event.type == pygame.QUIT:
                running = False
            if event.type == pygame.KEYDOWN and event.key == pygame.K_e:
                objeto_piramide.ejes_locales = not objeto_piramide.ejes_locales

        # Limpiar pantalla (Fondo negro)
        screen.fill((0, 0, 0))

        # Actualizar lógica y renderizar la pirámide
        objeto_piramide.update()
        objeto_piramide.render(screen)

        # Actualizar la ventana
        pygame.display.flip()
        clock.tick(60)  # 60 FPS

    pygame.quit()
    sys.exit()

if __name__ == "__main__":
    main()