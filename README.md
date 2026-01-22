# Tree Software Organization

Una herramienta de organización visual premium diseñada con una estética **Liquid Glass** y alta interactividad. Este software permite crear pizarras dinámicas integrando formas geométricas, documentos Markdown, ventanas de texto editables e imágenes, todo bajo una atmósfera de diseño moderno y animaciones fluidas.

## Características Principales

- **Estética Liquid Glass**: Efectos avanzados de desenfoque gaussiano, refracción (magnificación) y aberración cromática (estilo iPhone) aplicados en tiempo real.
- **Lienzo Infinito**: Navegación fluida con zoom dinámico y una cámara totalmente controlable.
- **Gestión de Objetos Profesional**:
  - **Selección Múltiple**: Cuadro de selección azul (Windows-style) para agrupar y mover múltiples elementos a la vez.
  - **Redimensionado Universal**: Tiradores de esquina en todos los objetos para ajustar dimensiones en tiempo real.
  - **Escala Inteligente**: Los triángulos mantienen su proporción geométrica automáticamente durante el redimensionado.
- **Visualizador de Markdown**: Soporte nativo para archivos `.md` con renderizado elegante, scroll interno y selección de texto para copiar/pegar.
- **Herramientas de Dibujo**:
  - **Cuadrados y Triángulos**: Figuras geométricas con bordes suaves y efectos de vidrio.
  - **Ventanas de Cristal**: Áreas de organización con títulos y contenido de texto editable.
  - **Texto Dinámico**: Escritura multilínea directa sobre el lienzo con "píldoras" de desenfoque dinámico.
- **Importación Inteligente**: Soporte para **Drag & Drop** de imágenes (.png, .jpg, .webp) y archivos Markdown (.md).
- **Interfaz Premium**: Barra de herramientas dinámica con botones tipo píldora y paleta de colores circular animada.

## Instalación y Ejecución

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
1. Crear un entorno virtual (venv).
2. Instalar la dependencia principal (**PySide6**).
3. Ejecutar la aplicación localizada en la carpeta `src/`.

## Controles e Interacción

- **Navegación**:
  - **Rueda del ratón**: Zoom in / Zoom out (centrado en el cursor).
  - **Shift + Click Izquierdo (arrastrar)**: Moverse por el lienzo (Pan).
- **Selección**:
  - **Click simple**: Seleccionar un objeto individual (se resalta en azul).
  - **Arrastrar en vacío**: Crea un **cuadro azul de selección** para marcar múltiples objetos.
- **Edición**:
  - **Arrastrar Objeto**: Mueve los elementos seleccionados.
  - **Tirador de Esquina (Círculo blanco)**: Redimensiona el objeto seleccionado.
  - **Rueda sobre Markdown**: Hace scroll dentro del contenido del documento.
- **Teclado (objeto seleccionado)**: 
  - Escribir directamente en ventanas o textos.
  - **Enter**: Salto de línea.
  - **Backspace / Delete**: Borrar texto o eliminar el objeto.
- **Drag & Drop**: Arrastra cualquier imagen o archivo `.md` desde tu explorador al lienzo.

## Estructura del Proyecto

```text
Tree Software Organization/
├── src/                # Código fuente del proyecto
│   ├── main.py         # Punto de entrada de la aplicación
│   ├── canvas_widget.py# Lógica del lienzo, eventos y selección
│   ├── canvas_objects.py# Renderizado avanzado de figuras y Markdown
│   ├── toolbar.py      # UI de la barra de herramientas y paleta
│   ├── config.py       # Configuración visual y constantes
│   └── utils.py        # Motores de desenfoque y utilidades de color
├── run.sh              # Bash script para ejecución rápida
└── README.md           # Documentación principal
```

---
*Desarrollado para una experiencia de organización visual de última generación.*
