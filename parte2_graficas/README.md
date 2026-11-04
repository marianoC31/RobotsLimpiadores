# TC2008B - Modelación de Sistemas Multiagentes con Gráficas Computacionales
## Actividad Integradora - Parte 2: Gráficas Computacionales (Implementación Pura en Python)

Esta solución está desarrollada **100% desde cero en Python**, siguiendo la misma arquitectura y metodología de las tareas anteriores (`Carrito` y `Pirámide`):
- **Sin motor 3D de OpenGL**: No se utilizan llamadas 3D de OpenGL (`glBegin(GL_QUADS)`, `glRotatef`, `glTranslatef`, `GL_LIGHTING`, etc.).
- **Matemáticas Propias con `OpMat3D`**: Todas las transformaciones matriciales 3D (traslación, rotación, escala, jerarquías de componentes con `push()` y `pop()`) se calculan a mano en Python.
- **Rasterizado Puro con `bresenham_2d`**: Las líneas y aristas de todos los modelos se proyectan a pantalla y se dibujan píxel por píxel con el algoritmo de Bresenham.
- **Iluminación Vectorial en Python**: El cálculo de la luz direccional y las 5 luces puntuales de sirenas se realiza matemáticamente mediante vectores y atenuación euclidiana.

---

### 📋 Cumplimiento de Requerimientos del Reto

| Requerimiento del Reto | Archivo | Descripción de la Solución Pura |
| :--- | :--- | :--- |
| **Almacén (M x N espacios: piso, paredes y puerta)** | `almacen.py` | Modelo de 20x20 m. Piso con cuadrícula de celdas y líneas amarillas de delimitación de pasillos. Paredes perimetrales con zócalo industrial y portón seccional en la pared Sur. |
| **Estantes por código (Pasillos)** | `estante.py` | Filas de estanterías industriales con 4 columnas verticales, vigas horizontales en 3 niveles, arriostramiento en 'X' y cajas de inventario en la repisa superior, formando la red de pasillos. |
| **K Cajas iniciales (Piso y Pilas de 5)** | `caja.py` | K=18 cajas iniciales dispersas a nivel de piso sin solapamiento (modo inicial obligatorio). Incluye función para alternar a pilas de hasta 5 cajas (tecla `P`). |
| **Flota de 5 Robots** | `robot_limpiador.py`, `gestor_robots.py` | 5 robots con chasis, cabina de sensores, cúpula de sirena con reflector interno rotatorio, manipuladores articulados (brazos y pinzas) y 4 ruedas omnidireccionales Mecanum con rodillos a 45°. |
| **Animación en pasillos** | `robot_limpiador.py`, `main.py` | Desplazamiento autónomo por waypoints a lo largo de los pasillos, dirección de ruedas delanteras al doblar, rodamiento según velocidad y articulación dinámica de pinzas. |
| **Iluminación Direccional** | `iluminacion.py` | Vector de luz cenital calculado matemáticamente. Se puede encender y apagar en vivo (tecla `L`). |
| **5 Luces Puntuales tipo Sirena (sobre cada robot)** | `iluminacion.py` | Cada robot proyecta su propia luz puntual con color característico (Rojo, Azul, Ámbar, Verde, Magenta). Se traslada con el robot en tiempo real, iluminando con atenuación cuadrática $(1 - d/R)^2$ el piso, estantes y cajas cercanas. Destello estroboscópico rojo en alerta. |
| **Rutas predeterminadas** | `gestor_robots.py` | 5 circuitos cerrados coordinados por los pasillos Oeste, Central (carriles Sur y Norte), Este y perimetrales. |
| **Velocidades predeterminadas (aleatorias)** | `gestor_robots.py` | Asignadas aleatoriamente a cada robot en el rango predeterminado [0.048, 0.076]. |
| **Posiciones de inicio predeterminadas (aleatorias)** | `gestor_robots.py` | 8 posiciones válidas en pasillos seleccionadas aleatoriamente sin colisión inicial. |
| **Detección y Reacción a Colisiones** | `gestor_robots.py` | Sistema de radar frontal por producto punto y distancia euclidiana: en cruces de pasillo el robot con menor ID tiene prioridad y el de mayor ID se detiene previamente; el robot que cede el paso aplica **evasión omnidireccional lateral (*strafe*)** hacia la orilla del pasillo. Control de distancia en convoy. |
| **Ruedas omnidireccionales (4 direcciones)** | `robot_limpiador.py` | Modelado de ruedas Mecanum con rodillos a 45° y capacidad de desplazamiento lateral sin rotar (*strafe*) para ceder el paso. |
| **Sensores de presión y manipuladores** | `robot_limpiador.py` | Pinzas mecánicas para sujetar cajas y LED indicador del sensor de presión frontal que brilla en verde esmeralda al transportar carga (tecla `C`). |
| **Cámara interactiva y HUD 2D** | `main.py` | Cámara orbital 3D interactiva, seguimiento individual de robots (teclas `1`-`5`, `0` para vista general) y panel HUD en pantalla con telemetría en tiempo real. |

---

### 🎮 Controles de la Simulación

| Tecla / Control | Acción |
| :--- | :--- |
| **Click Izquierdo + Arrastrar** | Orbitar la cámara alrededor del almacén |
| **Rueda del Mouse / Teclas `+` y `-`** | Acercar / Alejar zoom de la cámara |
| **Flechas (`↑`, `↓`, `←`, `→`)** | Orientar elevación y rotación de la cámara por teclado |
| **Teclas `1`, `2`, `3`, `4`, `5`** | **Cámara de seguimiento**: enfocar de cerca al Robot 0, 1, 2, 3 o 4 |
| **Tecla `0`** | Restaurar la cámara a la **Vista General** del almacén |
| **Tecla `L`** | **Alternar Luz Direccional** (Día / Noche: resalta las 5 luces puntuales tipo sirena) |
| **Tecla `C`** | **Manipuladores / Sensor de Presión**: Alternar sujeción de caja en robots |
| **Tecla `P`** | **Alternar Modo Pilas**: Cambiar entre cajas en piso y pilas de hasta 5 cajas |
| **Tecla `R`** | **Regenerar Cajas**: Reposicionar aleatoriamente las K cajas a nivel de piso |
| **Tecla `F`** | **Reiniciar Flota**: Nuevas posiciones y velocidades aleatorias para los 5 robots |
| **Barra Espaciadora (`SPACE`)** | Pausar / Reanudar la simulación |
| **Tecla `H`** | Mostrar / Ocultar panel de información en pantalla (HUD) |
| **Tecla `ESC`** | Salir de la simulación |

---

### 💻 Cómo Ejecutar el Proyecto

1. Activa tu entorno virtual:
   ```bash
   source entorno/bin/activate
   ```

2. Ejecuta la simulación:
   ```bash
   python main.py
   ```
