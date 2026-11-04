# RobotsLimpiadores — TC2008B Actividad Integradora

Un solo proyecto con las tareas previas y las dos partes de la integradora.
Todas las piezas gráficas comparten la misma matemática en `nucleo/`.

```text
RobotsLimpiadores/
├── run.py                    # Lanzador único (ver "Cómo correr")
├── requirements.txt          # pygame + PyOpenGL
│
├── nucleo/                   # Matemáticas compartidas por todo lo gráfico
│   ├── OpMat.py              #   Matrices 4x4: translate/rotate/scale, push/pop,
│   │                         #   matrices colapsadas (matriz_T_Ry, matriz_Rx_T_Ry, matriz_T_Ry_Rx)
│   ├── Bresenham.py          #   Rasterizado de líneas píxel por píxel
│   ├── Camara.py             #   Proyección en perspectiva 3D -> 2D (x·d/z)
│   └── Ejes.py               #   Ejes X/Y/Z de referencia
│
├── tareas/                   # Tareas anteriores (base de todo lo demás)
│   ├── piramide.py           #   Pivote + rotación (modo post=False: M = T·M)
│   ├── robot.py              #   Robot jerárquico (modo post=True: M = M·T, push/pop)
│   ├── main_piramide.py
│   └── main_robot.py
│
├── parte1_multiagentes/      # PARTE 1: simulación en cuadrícula MxN (sin gráficos 3D)
│   ├── modelo_almacen.py     #   El mundo: matriz de cajas, matriz de robots, pilas, reservas
│   ├── agente_robot.py       #   El agente: sensores, máquina de estados, BFS, estrategias
│   ├── simulacion_visual.py  #   Vista 2D con pygame
│   ├── simulacion_consola.py #   Vista en texto
│   ├── experimentos.py       #   Compara BASE vs OPTIMIZADA con varias réplicas
│   ├── main.py               #   Opciones de línea de comandos
│   └── DOCUMENTO_ENTREGA_PARTE_1.md / .html   # Documento de entrega
│
└── parte2_graficas/          # PARTE 2: almacén 3D con 5 robots
    ├── main.py               #   Ventana, cámara orbital, HUD, ciclo principal
    ├── almacen.py            #   Piso, paredes y puerta
    ├── estante.py            #   Estantes generados por código (pasillos)
    ├── caja.py               #   K cajas en piso / pilas de 5
    ├── robot_limpiador.py    #   El mismo robot jerárquico de tareas/robot.py, más detallado
    ├── gestor_robots.py      #   Rutas, velocidades aleatorias y colisiones
    ├── iluminacion.py        #   Luz direccional + luz puntual (sirena) por robot
    └── texturas.py, assets/  #   Texturas
```

## Cómo correr

Usa el entorno `../.venv313` (ya tiene pygame y PyOpenGL). En VS Code:
`Ctrl+Shift+P` → *Python: Select Interpreter* → `..\.venv313\Scripts\python.exe`.

```bash
python run.py parte1                           # simulación 2D
python run.py parte1 --consola -k 15 --semilla 1
python run.py parte1 --experimentos            # BASE vs OPTIMIZADA
python run.py parte2                           # almacén 3D
python run.py robot                            # tarea del robot
python run.py piramide                         # tarea de la pirámide
```

También funciona el botón ▶ de VS Code sobre cualquier `main*.py`.

## Cómo se conecta todo

**Una sola idea, tres tamaños:**

| Concepto | tareas/ | parte2_graficas/ | parte1_multiagentes/ |
|---|---|---|---|
| Robot | `robot.py` (1 robot, teclado) | `robot_limpiador.py` ×5 | `agente_robot.py` ×5 |
| Posición | `pos_x, pos_z` continuos | `pos_x, pos_z` continuos | `x, y` celdas enteras |
| Movimiento | óvalo fijo o teclado | waypoints por pasillos | BFS hacia la caja/pila |
| Matriz del cuerpo | `matriz_Rx_T_Ry` (incluye la vista) | `matriz_T_Ry` (la vista la pone OpenGL) | — |
| Ruedas | `matriz_T_Ry_Rx` | `matriz_T_Ry_Rx` | — |
| Brazos/pinzas | push → translate → rotate → pop | igual | `lleva_caja` (sensor de presión) |

**Diferencia clave entre las dos partes gráficas:**
- `tareas/` proyecta con **tu** `Camara.py` (`x·d/z`) y dibuja con `Bresenham.linea` sobre una superficie de pygame.
- `parte2_graficas/` usa **tu mismo OpMat** para mover los objetos, pero proyecta con `gluProject` de OpenGL (cámara orbital con `gluLookAt`) y dibuja con `bresenham_2d` (puntos `GL_POINTS`).

**Las partes 1 y 2 no están conectadas** (el PDF dice que no es necesario).
Si algún día se conectan: la celda `(x, y)` de la Parte 1 equivale al punto
`(x - M/2, 0, y - N/2)` del piso en la Parte 2.

## Orden sugerido para estudiarlo

1. `nucleo/OpMat.py`: entender `post=False` contra `post=True` y por qué las matrices colapsadas dan lo mismo.
2. `tareas/robot.py`: la jerarquía del robot.
3. `parte2_graficas/robot_limpiador.py`: el mismo robot, ahora instanciable 5 veces.
4. `parte2_graficas/gestor_robots.py`: rutas y colisiones.
5. `parte1_multiagentes/modelo_almacen.py` y luego `agente_robot.py`: el problema lógico.
