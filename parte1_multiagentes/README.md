# TC2008B - Parte 1: Simulación de Sistemas Multiagentes

Implementación completa y rigurosa del sistema multiagente de almacenamiento y logística para la **Evidencia 1 (Semana 12)** de la materia TC2008B en el Tecnológico de Monterrey.

Cumple con el nivel **Destacado** en las dos subcompetencias de evaluación de Canvas:
- **SICT0102 Demostración del funcionamiento de los sistemas computacionales:** Diseño experimental Monte Carlo pareado que demuestra relaciones causa-efecto entre coordinación estigmérgica, heurística de empaquetado, reducción de conflictos y eficiencia energética.
- **STC0103 Generación de modelos computacionales:** Modelo formal verificable con ciclo PDA, sensores ortogonales de 4 celdas, sensor de presión, navegación óptima BFS y respeto estricto del límite de 5 cajas por pila.

---

## 🚀 Guía de Ejecución Rápida

### 1. Simulación Visual Interactiva 2D (Pygame)
Abre la cuadrícula animada del almacén con telemetría en tiempo real de los 5 robots y las pilas de cajas:
```bash
# Desde la raíz del repositorio
python run_parte_1.py

# O con entorno virtual
./entorno/bin/python run_parte_1.py
```

**Controles interactivos en la ventana:**
- <kbd>ESPACIO</kbd>: Pausar / Reanudar la simulación.
- <kbd>E</kbd>: Alternar en vivo entre la estrategia `BASE` y `OPTIMIZADA` (reinicia para comparar visualmente el comportamiento).
- <kbd>R</kbd>: Reiniciar simulación con nueva distribución aleatoria de cajas.
- <kbd>↑</kbd> / <kbd>↓</kbd>: Aumentar o disminuir la velocidad de pasos por segundo.
- <kbd>ESC</kbd>: Salir.

---

### 2. Simulación en Consola (Modo Texto ASCII)
Ideal para entornos remotos o sin soporte de pantalla:
```bash
python run_parte_1.py --consola -k 25 --estrategia OPTIMIZADA
```

---

### 3. Batería de Experimentación Científica Monte Carlo (`SICT0102`)
Ejecuta automáticamente la batería de pruebas pareadas (120 simulaciones) sobre $K \in \{15, 25, 40\}$:
```bash
python run_parte_1.py --experimentos --replicas 20
```
Genera la tabla comparativa con medias, desviaciones estándar y porcentaje de reducción de movimientos y conflictos.

---

## 📄 Documento de Entrega Técnico y Generación de PDF

El reporte técnico completo que cumple con todos los requisitos del Canvas se encuentra en:
- Markdown formal: [`DOCUMENTO_ENTREGA_PARTE_1.md`](DOCUMENTO_ENTREGA_PARTE_1.md)
- Versión lista para exportar a PDF: [`DOCUMENTO_ENTREGA_PARTE_1.html`](DOCUMENTO_ENTREGA_PARTE_1.html)

Para generar el PDF:
1. Abre `DOCUMENTO_ENTREGA_PARTE_1.html` en tu navegador web (Chrome, Edge o Safari).
2. Haz clic en el botón azul superior **"🖨️ Guardar como PDF / Imprimir"** (o presiona `Cmd+P` / `Ctrl+P`).
3. Selecciona "Guardar como PDF".

---

## 📁 Estructura del Código

- `agente_robot.py`: Clase `RobotAgent` con sensores (4 celdas + presión), FSM de control, planificador BFS ortogonal y lógica de deliberación para estrategias `BASE` y `OPTIMIZADA`.
- `modelo_almacen.py`: Clase `AlmacenModel` que representa la cuadrícula $M \times N$, gestiona las pilas (máx. 5), administra las reservas estigmérgicas y recolecta métricas de telemetría.
- `simulacion_visual.py`: Renderizador gráfico en Pygame con HUD lateral y codificación por color.
- `simulacion_consola.py`: Ejecutor en modo consola con animación ASCII en terminal.
- `experimentos.py`: Módulo de experimentación científica Monte Carlo con muestras pareadas.
- `main.py`: Interfaz de línea de comandos (CLI) con soporte de argumentos.
- `generar_pdf_html.py`: Script generador de la versión HTML imprimible.
