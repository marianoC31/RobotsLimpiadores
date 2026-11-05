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
└── parte1_multiagentes/      # Versión consola dela simulación de agentes
```

## Cómo correr

```bash
python run.py parte2          # almacén 3D (ratón: girar, rueda: zoom, Espacio: pausa, R: reiniciar, T: caras con textura sí/no)
python run.py parte1      # solo la simulación, sin gráficos; imprime tiempo y movimientos
```



