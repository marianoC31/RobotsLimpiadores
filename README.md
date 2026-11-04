# RobotsLimpiadores — TC2008B Actividad Integradora

5 robots ordenan un almacén: recogen K cajas sueltas y las apilan en pilas de 5.
La **simulación** la decide AgentPy (`agentes/`) y la **gráfica 3D** (`parte2_graficas/`)
solo dibuja lo que decidió el modelo, con matemática propia (`nucleo/`).

```text
RobotsLimpiadores/
├── run.py                    # Lanzador único
├── requirements.txt          # pygame, PyOpenGL, agentpy
│
├── agentes/                  # MÓDULO EXTERNO DE AGENTES (AgentPy)
│   └── modelo.py             #   RobotAgente (ap.Agent) y AlmacenModelo (ap.Model, ap.Grid)
│
├── nucleo/                   # Matemáticas propias
│   └── OpMat.py              #   traslación, rotación, escala, push/pop, matrices colapsadas
│
├── parte2_graficas/          # AMBIENTE 3D
│   ├── main.py               #   ventana, ciclo: paso de AgentPy -> animación -> dibujo
│   ├── robot3d.py            #   clase Robot3D: update() (animación) y render() (dibujo)
│   ├── camara3d.py           #   proyección propia 3D -> pantalla (vista + perspectiva)
│   ├── bresenham.py          #   clase Bresenham: líneas 2D píxel por píxel, con profundidad
│   ├── superficies.py        #   caras con textura (mapeo UV)
│   ├── almacen.py, estante.py, caja.py    # piso/paredes/puerta, estantes, pilas de cajas
│   └── texturas.py, assets/  #   carga de imágenes
│
└── parte1_multiagentes/      # Versión 2D anterior de tu compañero (sin AgentPy)
```

## Cómo correr

```bash
python run.py parte2          # almacén 3D (ratón: girar, rueda: zoom, Espacio: pausa, R: reiniciar)
python run.py agentes 1       # solo la simulación, sin gráficos; imprime tiempo y movimientos
```

## Cómo cumple la rúbrica

| Dimensión | Dónde | Qué hay |
|---|---|---|
| **D1. Clase Robot y animación** | `parte2_graficas/robot3d.py` | `Robot3D.update(f)` anima (gira en su lugar, avanza entre celdas, baja brazos y cierra pinzas al recoger o apilar); `Robot3D.render(camara)` dibuja la jerarquía chasis → cabina, ruedas, brazos → pinzas → caja. |
| **D2. OpMat y transformaciones** | `nucleo/OpMat.py` | Traslación, rotación, escala, pila `push/pop`, modo jerárquico. **Optimización:** multiplicación afín (36 multiplicaciones en lugar de 64), traslación colapsada y matrices cerradas `matriz_T_Ry` y `matriz_T_Ry_Rx`. |
| **D3. Clase Bresenham y proyección** | `parte2_graficas/bresenham.py`, `camara3d.py` | Proyección propia: `P·V` se colapsa una vez por cuadro y cada punto cuesta 4 productos punto. Da los mismos resultados que `gluProject` (diferencia de 10⁻¹³). La clase `Bresenham` rasteriza cada arista píxel por píxel con `linea()`; OpenGL solo pinta los puntos ya calculados. |
| **D4. Ambiente gráfico y AgentPy** | `agentes/modelo.py` + `parte2_graficas/main.py` | El movimiento lo decide `AlmacenModelo` (AgentPy) con `sim_setup()` y `sim_step()`; cada paso, los `Robot3D` leen la posición, la orientación y la acción de su agente y la animan. |

Las caras sólidas con textura (piso, paredes, puerta, repisas, cajas y robots) se pintan con
OpenGL usando **las matrices de `camara3d.py`**, debajo de las aristas de Bresenham.

## Los agentes (agentes/modelo.py)

- Cuadrícula M × N (el borde es pared), K cajas sueltas al inicio, 4 estantes como obstáculos y 5 robots en celdas vacías aleatorias.
- **Sensores:** las 4 celdas vecinas (libre, pared, estante, cajas y cuántas, robot) y el sensor de presión (`lleva_caja`).
- **Acciones:** moverse a una celda vecina, recoger una caja vecina o dejarla en una pila vecina (máximo 5).
- **Estrategia cooperativa:** cada robot reserva su caja, para que dos robots no vayan por la misma; lleva la caja a la pila abierta más alta, para cerrar pilas de 5 cuanto antes; usa BFS para el camino más corto.
- **Métricas:** pasos hasta que todas las cajas están en pilas y movimientos totales. En 20 semillas terminó siempre, con 58 pasos y 252 movimientos en promedio.
