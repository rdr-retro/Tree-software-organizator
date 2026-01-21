# Tree Software Organization 🌳

Una herramienta de organización visual premium diseñada con una estética **Liquid Glass** y alta interactividad. Este software permite crear pizarras dinámicas integrando formas geométricas, ventanas de texto editables e imágenes, todo bajo una atmósfera de diseño moderno y fluidas animaciones.

## ✨ Características Principales

- **Estética Liquid Glass**: Efectos avanzados de desenfoque gaussiano, refracción (magnificación) y aberración cromática (estilo iPhone) aplicados en tiempo real.
- **Lienzo Infinito**: Navegación fluida con zoom dinámico y paneo suave.
- **Herramientas de Dibujo**:
  - **Cuadrados y Triángulos**: Figuras geométricas con bordes suaves y efectos de vidrio.
  - **Ventanas de Cristal**: Áreas de organización con títulos y contenido de texto editable.
  - **Texto Dinámico**: Escritura multilínea directa sobre el lienzo con "píldoras" de desenfoque dinámico para máxima legibilidad.
- **Importación Inteligente**: Soporte para **Drag & Drop** de imágenes externas (`.png`, `.jpg`, etc.) con escalado automático y esquinas redondeadas.
- **Interfaz Fluida**: Toolbar dinámica y paleta de colores circular con animaciones orgánicas y feedback visual al pasar el ratón.
- **Escritura Interactiva**: Cursor parpadeante, soporte para saltos de línea y placeholder guía ("Empieza a escribir...").

## 🚀 Instalación y Ejecución

El proyecto está diseñado para ser fácil de arrancar en entornos macOS y Linux.

### Requisitos Previos

- Python 3.12 o superior.
- Pip (instalador de paquetes de Python).

### Cómo ejecutar

Simplemente abre una terminal en la carpeta raíz del proyecto y ejecuta el script de inicio:

```bash
chmod +x run.sh
./run.sh
```

El script se encargará automáticamente de:
1. Crear un entorno virtual (`venv`).
2. Instalar la dependencia principal (`PySide6`).
3. Ejecutar la aplicación localizada en la carpeta `src/`.

## 🖱️ Controles Rápidos

- **Rueda del ratón**: Zoom in / Zoom out.
- **Click izquierdo (arrastrar)**: Moverse por el lienzo (Pan).
- **Click en objeto**: Seleccionar y arrastrar objetos individuales.
- **Teclado (objeto seleccionado)**: 
  - Escribir directamente.
  - `Enter`: Salto de línea.
  - `Backspace / Delete`: Borrar texto o eliminar el objeto si está vacío.
- **Drag & Drop**: Arrastra cualquier imagen desde tu explorador de archivos al lienzo.

## 📁 Estructura del Proyecto

```text
Tree Software Organization/
├── src/                # Código fuente del proyecto
│   ├── main.py         # Punto de entrada de la aplicación
│   ├── canvas_widget.py# Lógica del lienzo y eventos
│   ├── canvas_objects.py# Renderizado de figuras, texto e imágenes
│   ├── toolbar.py      # UI de la barra de herramientas y paleta
│   ├── config.py       # Configuración visual y constantes
│   └── utils.py        # Funciones auxiliares (Desenfoque, Colores)
├── run.sh              # Bash script para ejecución rápida
└── README.md           # Documentación principal
```

---
*Desarrollado con ❤️ para una experiencia de organización visual única.*
