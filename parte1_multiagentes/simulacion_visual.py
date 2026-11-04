import pygame
import sys
from modelo_almacen import AlmacenModel

def ejecutar_simulacion_visual(m=14, n=14, k=25, num_robots=5, max_pasos=1000, estrategia='OPTIMIZADA', semilla=None):
    """
    Ejecuta la simulación multiagente con visualización gráfica interactiva 2D en Pygame.
    Permite alternar entre la estrategia BASE y OPTIMIZADA en tiempo real con la tecla [E].
    """
    pygame.init()
    pygame.font.init()

    # Dimensiones de ventana
    tam_celda = 42
    ancho_grilla = m * tam_celda
    alto_grilla = n * tam_celda
    ancho_panel = 370
    ancho_ventana = ancho_grilla + ancho_panel
    alto_ventana = max(alto_grilla, 640)

    pantalla = pygame.display.set_mode((ancho_ventana, alto_ventana))
    pygame.display.set_caption("TC2008B - Parte 1: Simulación Multiagente (5 Robots en Almacén)")

    font_title = pygame.font.Font(None, 24)
    font_bold = pygame.font.Font(None, 20)
    font_text = pygame.font.Font(None, 17)
    font_caja = pygame.font.Font(None, 22)

    colores_robots = [
        (225, 45, 45),   # Robot 0: Carmesí
        (45, 125, 235),  # Robot 1: Azul Zafiro
        (235, 155, 25),  # Robot 2: Ámbar Dorado
        (45, 195, 75),   # Robot 3: Verde Esmeralda
        (205, 45, 185)   # Robot 4: Magenta Orquídea
    ]

    estrategia_actual = estrategia
    modelo = AlmacenModel(
        m=m, n=n, k=k,
        num_robots=num_robots,
        max_pasos=max_pasos,
        estrategia=estrategia_actual,
        semilla=semilla
    )

    clock = pygame.time.Clock()
    fps = 12 # Velocidad inicial de pasos por segundo
    pausado = False
    running = True

    while running:
        for event in pygame.event.get():
            if event.type == pygame.QUIT or (event.type == pygame.KEYDOWN and event.key == pygame.K_ESCAPE):
                running = False
            elif event.type == pygame.KEYDOWN:
                if event.key == pygame.K_SPACE:
                    pausado = not pausado
                elif event.key == pygame.K_r:
                    # Reiniciar con misma estrategia
                    modelo = AlmacenModel(m=m, n=n, k=k, num_robots=num_robots, max_pasos=max_pasos, estrategia=estrategia_actual)
                elif event.key == pygame.K_e:
                    # Alternar estrategia BASE <-> OPTIMIZADA y reiniciar
                    estrategia_actual = 'BASE' if estrategia_actual == 'OPTIMIZADA' else 'OPTIMIZADA'
                    modelo = AlmacenModel(m=m, n=n, k=k, num_robots=num_robots, max_pasos=max_pasos, estrategia=estrategia_actual)
                elif event.key == pygame.K_UP:
                    fps = min(60, fps + 5)
                elif event.key == pygame.K_DOWN:
                    fps = max(2, fps - 5)

        # Avanzar modelo si no está en pausa
        if not pausado and not modelo.simulacion_terminada:
            modelo.step()

        pantalla.fill((20, 24, 32))

        # ==========================================================
        # 1. DIBUJAR CUADRÍCULA DEL ALMACÉN (M x N)
        # ==========================================================
        for y in range(n):
            for x in range(m):
                rect = pygame.Rect(x * tam_celda, y * tam_celda, tam_celda, tam_celda)

                # Celda de Borde / Muros perimetrales
                if x == 0 or x == m - 1 or y == 0 or y == n - 1:
                    pygame.draw.rect(pantalla, (45, 50, 60), rect)
                    pygame.draw.rect(pantalla, (30, 35, 42), rect, 1)
                else:
                    # Piso de concreto industrial
                    pygame.draw.rect(pantalla, (215, 218, 222), rect)
                    pygame.draw.rect(pantalla, (185, 190, 195), rect, 1)

                    # Si es celda de zona de pila oficial, dibujar marca en piso
                    if (x, y) in modelo.zonas_pilas:
                        pygame.draw.rect(pantalla, (200, 230, 210), rect)
                        pygame.draw.rect(pantalla, (100, 180, 120), rect, 1)

                    # Dibujar Cajas
                    num_c = modelo.cajas[y][x]
                    if num_c > 0:
                        margin = 5
                        rect_caja = pygame.Rect(
                            x * tam_celda + margin, y * tam_celda + margin,
                            tam_celda - margin * 2, tam_celda - margin * 2
                        )
                        
                        if num_c == 5:
                            # Pila completa de 5: Verde Éxito + Borde Dorado
                            pygame.draw.rect(pantalla, (35, 155, 80), rect_caja, border_radius=4)
                            pygame.draw.rect(pantalla, (255, 215, 0), rect_caja, 2, border_radius=4)
                        elif num_c > 1:
                            # Pila en consolidación
                            pygame.draw.rect(pantalla, (190, 120, 55), rect_caja, border_radius=4)
                            pygame.draw.rect(pantalla, (140, 85, 35), rect_caja, 1, border_radius=4)
                        else:
                            # 1 sola caja suelta en piso
                            pygame.draw.rect(pantalla, (210, 145, 80), rect_caja, border_radius=3)
                            pygame.draw.rect(pantalla, (150, 95, 45), rect_caja, 1, border_radius=3)

                        # Indicador numérico de cajas en la pila (1..5)
                        txt_num = font_caja.render(str(num_c), True, (255, 255, 255))
                        txt_rect = txt_num.get_rect(center=rect_caja.center)
                        pantalla.blit(txt_num, txt_rect)

                    # Dibujar Robots
                    robot = modelo.grid_robots[y][x]
                    if robot is not None:
                        cx = x * tam_celda + tam_celda // 2
                        cy = y * tam_celda + tam_celda // 2
                        radio = tam_celda // 2 - 4

                        color_r = colores_robots[robot.id_robot % len(colores_robots)]
                        
                        # Chasis circular omnidireccional
                        pygame.draw.circle(pantalla, color_r, (cx, cy), radio)
                        pygame.draw.circle(pantalla, (20, 20, 25), (cx, cy), radio, 2)

                        # Ojos / Sensores de orientación frontal
                        pygame.draw.circle(pantalla, (255, 255, 255), (cx - 4, cy - 3), 3)
                        pygame.draw.circle(pantalla, (255, 255, 255), (cx + 4, cy - 3), 3)

                        # Indicador de sensor de presión (manipulador mecánico)
                        if robot.lleva_caja:
                            # Caja miniatura sujeta en manipulador con halo verde
                            pygame.draw.rect(pantalla, (240, 160, 60), (cx - 7, cy + 3, 14, 11))
                            pygame.draw.rect(pantalla, (50, 255, 120), (cx - 7, cy + 3, 14, 11), 1)
                        else:
                            # Identificador ID
                            txt_id = font_text.render(f"R{robot.id_robot}", True, (255, 255, 255))
                            pantalla.blit(txt_id, (cx - 8, cy + 2))

        # ==========================================================
        # 2. PANEL LATERAL DE TELEMETRÍA Y MÉTRICAS (SICT0102 / STC0103)
        # ==========================================================
        panel_x = ancho_grilla + 15
        metricas = modelo.obtener_metricas()

        # Título y Subtítulo
        t_tit = font_title.render("ALMACÉN MULTIAGENTE", True, (255, 215, 0))
        t_sub = font_text.render("Parte 1: 5 Robots Autónomos (Mesa/OOP)", True, (180, 200, 225))
        pantalla.blit(t_tit, (panel_x, 15))
        pantalla.blit(t_sub, (panel_x, 38))
        pygame.draw.line(pantalla, (60, 75, 95), (panel_x, 58), (ancho_ventana - 15, 58), 1)

        # Estrategia y Estado Global
        col_est = (80, 220, 255) if estrategia_actual == 'OPTIMIZADA' else (255, 160, 80)
        pantalla.blit(font_bold.render(f"Estrategia: {estrategia_actual}", True, col_est), (panel_x, 68))
        
        st_txt = "ORDENADO (Éxito)" if metricas['exito_mision'] else ("PAUSADO" if pausado else "EN EJECUCIÓN")
        st_col = (80, 240, 120) if metricas['exito_mision'] else ((255, 180, 50) if pausado else (200, 220, 240))
        pantalla.blit(font_bold.render(f"Estado: {st_txt}", True, st_col), (panel_x, 90))
        pantalla.blit(font_text.render(f"Paso de tiempo: {modelo.paso_actual} / {max_pasos}", True, (220, 230, 240)), (panel_x, 112))
        pantalla.blit(font_text.render(f"Velocidad: {fps} fps (Flechas Arr/Abj)", True, (170, 190, 215)), (panel_x, 130))

        pygame.draw.line(pantalla, (60, 75, 95), (panel_x, 150), (ancho_ventana - 15, 150), 1)

        # Métricas Exigidas por el PDF
        pantalla.blit(font_bold.render("Métricas Cuantitativas:", True, (255, 230, 130)), (panel_x, 160))
        pantalla.blit(font_text.render(f"• Total Movimientos Flota: {metricas['movimientos_totales']}", True, (220, 230, 245)), (panel_x, 184))
        pantalla.blit(font_text.render(f"• Movimientos Promedio / Caja: {metricas['movimientos_por_caja']}", True, (220, 230, 245)), (panel_x, 202))
        pantalla.blit(font_text.render(f"• Pilas de 5 cajas completadas: {metricas['pilas_5_completadas']} / {metricas['pilas_5_esperadas']}", True, (90, 255, 140)), (panel_x, 220))
        pantalla.blit(font_text.render(f"• Cajas en pilas completas: {metricas['cajas_en_pilas_5']}", True, (200, 235, 210)), (panel_x, 238))
        pantalla.blit(font_text.render(f"• Cajas en pilas en proceso: {metricas['cajas_en_proceso']}", True, (240, 180, 110)), (panel_x, 256))
        pantalla.blit(font_text.render(f"• Cajas sueltas en piso: {metricas['cajas_sueltas']}", True, (230, 140, 140)), (panel_x, 274))
        pantalla.blit(font_text.render(f"• Cajas en transporte activo: {metricas['cajas_en_transporte']}", True, (200, 220, 240)), (panel_x, 292))
        pantalla.blit(font_text.render(f"• Carreras perdidas (conflicto): {metricas['intentos_fallidos_totales']}", True, (255, 120, 120)), (panel_x, 310))

        pygame.draw.line(pantalla, (60, 75, 95), (panel_x, 332), (ancho_ventana - 15, 332), 1)

        # Telemetría de la Flota (5 Robots)
        pantalla.blit(font_bold.render("Telemetría de la Flota:", True, (255, 230, 130)), (panel_x, 342))
        header_r = font_text.render("ID | Posición | Movs | Carga | Estado", True, (160, 180, 205))
        pantalla.blit(header_r, (panel_x, 362))

        for idx, r in enumerate(modelo.robots):
            ry = 382 + idx * 22
            color_dot = colores_robots[r.id_robot % len(colores_robots)]
            pygame.draw.circle(pantalla, color_dot, (panel_x + 6, ry + 6), 5)

            carga_txt = "📦 SÍ" if r.lleva_caja else "--"
            carga_col = (90, 255, 140) if r.lleva_caja else (150, 160, 170)
            
            info_txt = f"R{r.id_robot} | ({r.x:2d}, {r.y:2d})   | {r.movimientos_realizados:3d}  | {carga_txt} | {r.estado}"
            pantalla.blit(font_text.render(info_txt, True, carga_col if r.lleva_caja else (210, 220, 230)), (panel_x + 16, ry))

        # Panel de Controles
        pygame.draw.line(pantalla, (60, 75, 95), (panel_x, 502), (ancho_ventana - 15, 502), 1)
        pantalla.blit(font_bold.render("Controles Interactivos:", True, (255, 230, 130)), (panel_x, 512))
        pantalla.blit(font_text.render("[Espacio] Pausar / Reanudar", True, (200, 220, 240)), (panel_x, 532))
        pantalla.blit(font_text.render("[E] Alternar Estrategia (Base / Optimizada)", True, (255, 220, 120)), (panel_x, 550))
        pantalla.blit(font_text.render("[R] Reiniciar simulación", True, (200, 220, 240)), (panel_x, 568))
        pantalla.blit(font_text.render("[Flechas Arr / Abj] Modificar velocidad", True, (200, 220, 240)), (panel_x, 586))
        pantalla.blit(font_text.render("[ESC] Salir", True, (160, 180, 205)), (panel_x, 604))

        pygame.display.flip()
        clock.tick(fps)

    pygame.quit()

if __name__ == "__main__":
    ejecutar_simulacion_visual()
