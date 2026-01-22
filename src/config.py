from PySide6.QtGui import QColor

# Colores del Tema
BG_COLOR = QColor(20, 20, 30)
GRID_COLOR = QColor(100, 100, 130) # Brillo para ver el blur
TEXT_COLOR = QColor(200, 200, 200)
TOOLBAR_BG_COLOR = QColor(10, 10, 20, 80) # Súper transparente
TOOLBAR_BORDER_COLOR = QColor(255, 255, 255, 100)
GLASS_HIGHLIGHT = QColor(255, 255, 255, 60)
GLASS_BLUR_RADIUS = 80 # Desenfoque mucho más profundo
GLASS_REFRACTION = 1.1 # Factor de refracción (10% de aumento)
GLASS_ABERRATION = 3   # Separación RGB en píxeles (iPhone style)

# Configuración del Toolbar
TOOLBAR_MARGIN = 20
TOOLBAR_WIDTH_COLLAPSED = 120
TOOLBAR_HEIGHT_COLLAPSED = 40
TOOLBAR_WIDTH_EXPANDED = 200
TOOLBAR_HEIGHT_EXPANDED = 400
TOOLBAR_RADIUS = 20
TOOLBAR_HOVER_DISTANCE_EXPAND = 180
TOOLBAR_HOVER_DISTANCE_COLLAPSE = 250

# Configuración del Selector de Colores (Círculo Derecho)
CIRCLE_EXPANDED_WIDTH = 320
CIRCLE_EXPANDED_HEIGHT = 720

# Configuración del Menú Vertical (NUEVO)
VERTICAL_MENU_EXPANDED_WIDTH = 50
VERTICAL_MENU_EXPANDED_HEIGHT = 240

# Herramientas
TOOL_BUTTONS = [
    {"name": "Cuadrado", "icon": "□"},
    {"name": "Triangulo", "icon": "△"},
    {"name": "Ventana", "icon": "▢"},
    {"name": "Texto en pantalla", "icon": "T"}
]

VERTICAL_TOOLS = [
    {"name": "Lapiz", "icon": "✎"},
    {"name": "Rotulador", "icon": "✒"},
    {"name": "Borrador", "icon": "⌫"},
    {"name": "Grosor", "icon": "≡"}
]

BUTTON_HEIGHT = 50
BUTTON_MARGIN = 15
