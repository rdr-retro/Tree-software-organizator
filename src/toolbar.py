from PySide6.QtCore import Qt, QRectF, QPointF, QRect
from PySide6.QtGui import QBrush, QPen, QColor, QFont, QLinearGradient, QPainterPath
import config
from utils import get_contrast_color

def draw_toolbar_island(painter, canvas, toolbar_rect, blurred_map=None):
    """Dibuja la isla dinámica con Glassmorphism usando el mapa de desenfoque"""
    s_rect = toolbar_rect.toRect()
    
    # 1. Aplicar desenfoque Liquid Glass (con Refracción y Aberración)
    if blurred_map and not blurred_map.isNull():
        painter.save()
        path = QPainterPath()
        path.addRoundedRect(toolbar_rect, config.TOOLBAR_RADIUS, config.TOOLBAR_RADIUS)
        painter.setClipPath(path)
        
        # Refracción
        zoom = config.GLASS_REFRACTION
        src_w, src_h = s_rect.width() / zoom, s_rect.height() / zoom
        src_x = s_rect.x() + (s_rect.width() - src_w) / 2
        src_y = s_rect.y() + (s_rect.height() - src_h) / 2
        src_rect = QRect(int(src_x), int(src_y), int(src_w), int(src_h))
        
        # Aberración Cromática RGB
        ab = config.GLASS_ABERRATION
        painter.setOpacity(0.4)
        painter.drawPixmap(s_rect.translated(-ab, 0), blurred_map, src_rect)
        painter.drawPixmap(s_rect.translated(ab, 0), blurred_map, src_rect)
        painter.setOpacity(1.0)
        painter.drawPixmap(s_rect, blurred_map, src_rect)
        
        painter.restore()
    
    # 2. Tinte plano (sin brillo) para que el blur sea el protagonista
    tinte = QColor(20, 20, 35, 120) 
    
    painter.setBrush(QBrush(tinte))
    painter.setPen(QPen(config.TOOLBAR_BORDER_COLOR, 1))
    painter.drawRoundedRect(toolbar_rect, config.TOOLBAR_RADIUS, config.TOOLBAR_RADIUS)
    
    # Texto "Herramientas" (collapsed mode)
    if canvas.toolbar_animation_progress < 0.7:
        opacity = 1.0 - (canvas.toolbar_animation_progress / 0.7)
        text_color = QColor(config.TEXT_COLOR)
        text_color.setAlphaF(opacity)
        painter.setPen(QPen(text_color))
        font_metrics = painter.fontMetrics()
        text = "Herramientas"
        text_x = toolbar_rect.x() + (toolbar_rect.width() - font_metrics.horizontalAdvance(text)) / 2
        text_y = toolbar_rect.y() + (toolbar_rect.height() + font_metrics.height()) / 2 - font_metrics.descent()
        painter.drawText(int(text_x), int(text_y), text)

def draw_tool_buttons(painter, canvas, toolbar_rect, opacity):
    start_y = toolbar_rect.y() + 60
    button_width = toolbar_rect.width() - (config.BUTTON_MARGIN * 2)
    for i, button in enumerate(config.TOOL_BUTTONS):
        button_y = start_y + (i * (config.BUTTON_HEIGHT + 10))
        button_rect = QRectF(toolbar_rect.x() + config.BUTTON_MARGIN, button_y, button_width, config.BUTTON_HEIGHT)
        if canvas.hovered_button == i:
            bg_color = QColor(70, 70, 90, int(210 * opacity))
            border_color = QColor(255, 255, 255, int(100 * opacity))
        else:
            bg_color = QColor(40, 40, 60, int(150 * opacity))
            border_color = QColor(255, 255, 255, int(40 * opacity))
        painter.setBrush(QBrush(bg_color))
        painter.setPen(QPen(border_color, 1))
        # Forma de píldora: el radio es la mitad de la altura
        pill_radius = config.BUTTON_HEIGHT / 2
        painter.drawRoundedRect(button_rect, pill_radius, pill_radius)
        
        text_color = QColor(config.TEXT_COLOR)
        text_color.setAlphaF(opacity)
        painter.setPen(QPen(text_color))
        icon_font = painter.font(); icon_font.setPointSize(20); painter.setFont(icon_font)
        painter.drawText(int(button_rect.x() + 15), int(button_rect.y() + 33), button["icon"])
        text_font = painter.font(); text_font.setPointSize(12); painter.setFont(text_font)
        painter.drawText(int(button_rect.x() + 50), int(button_rect.y() + 31), button["name"])

def draw_color_palette(painter, canvas, circle_rect, opacity, blurred_map=None):
    """Selector de colores con Glassmorphism"""
    s_rect = circle_rect.toRect()
    if blurred_map and not blurred_map.isNull():
        painter.save()
        path = QPainterPath()
        path.addRoundedRect(circle_rect, canvas.current_circle_radius, canvas.current_circle_radius)
        painter.setClipPath(path)
        
        # Refracción y Aberración en el selector de colores
        zoom = config.GLASS_REFRACTION
        src_w, src_h = s_rect.width() / zoom, s_rect.height() / zoom
        src_x = s_rect.x() + (s_rect.width() - src_w) / 2
        src_y = s_rect.y() + (s_rect.height() - src_h) / 2
        src_rect = QRect(int(src_x), int(src_y), int(src_w), int(src_h))
        
        ab = config.GLASS_ABERRATION
        painter.setOpacity(0.4)
        painter.drawPixmap(s_rect.translated(-ab, 1), blurred_map, src_rect)
        painter.drawPixmap(s_rect.translated(ab, -1), blurred_map, src_rect)
        painter.setOpacity(1.0)
        painter.drawPixmap(s_rect, blurred_map, src_rect)
        
        painter.restore()

        
    r = canvas.active_color.red() + (config.TOOLBAR_BG_COLOR.red() - canvas.active_color.red()) * canvas.circle_animation_progress
    g = canvas.active_color.green() + (config.TOOLBAR_BG_COLOR.green() - canvas.active_color.green()) * canvas.circle_animation_progress
    b = canvas.active_color.blue() + (config.TOOLBAR_BG_COLOR.blue() - canvas.active_color.blue()) * canvas.circle_animation_progress
    tint_color = QColor(int(r), int(g), int(b), 100)
    
    painter.setBrush(QBrush(tint_color))
    painter.setPen(QPen(config.TOOLBAR_BORDER_COLOR, 1))
    painter.drawRoundedRect(circle_rect, canvas.current_circle_radius, canvas.current_circle_radius)
    
    if canvas.circle_animation_progress > 0.3:
        _draw_palette_buttons(painter, canvas, circle_rect, (canvas.circle_animation_progress - 0.3) / 0.7)

def _draw_palette_buttons(painter, canvas, circle_rect, opacity):
    button_size = 28
    rows, cols = 16, 7
    spacing_x, spacing_y = 12, 14
    start_x = circle_rect.x() + (circle_rect.width() - (cols * button_size + (cols-1)*spacing_x)) / 2
    start_y = circle_rect.y() + (circle_rect.height() - (rows * button_size + (rows-1)*spacing_y)) / 2
    for i, button in enumerate(canvas.circle_buttons):
        row, col = i // cols, i % cols
        btn_rect = QRectF(start_x + col*(button_size+spacing_x), start_y + row*(button_size+spacing_y), button_size, button_size)
        color = QColor(button["color"]); color.setAlphaF(opacity)
        painter.setPen(QPen(get_contrast_color(color), 1.5 if canvas.circle_hovered_button != i else 3))
        painter.setBrush(QBrush(color.lighter(120) if canvas.circle_hovered_button == i else color))
        painter.drawEllipse(btn_rect)
        button["current_rect"] = btn_rect
def draw_vertical_menu(painter, canvas, menu_rect, opacity, blurred_map=None):
    """Menú vertical con 4 botones"""
    s_rect = menu_rect.toRect()
    if blurred_map and not blurred_map.isNull():
        painter.save()
        path = QPainterPath()
        # Radio dinámico según animación
        radius = config.TOOLBAR_RADIUS
        path.addRoundedRect(menu_rect, radius, radius)
        painter.setClipPath(path)
        
        zoom = config.GLASS_REFRACTION
        src_w, src_h = s_rect.width() / zoom, s_rect.height() / zoom
        src_x = s_rect.x() + (s_rect.width() - src_w) / 2
        src_y = s_rect.y() + (s_rect.height() - src_h) / 2
        src_rect = QRect(int(src_x), int(src_y), int(src_w), int(src_h))
        
        ab = config.GLASS_ABERRATION
        painter.setOpacity(0.4)
        painter.drawPixmap(s_rect.translated(-ab, 1), blurred_map, src_rect)
        painter.drawPixmap(s_rect.translated(ab, -1), blurred_map, src_rect)
        painter.setOpacity(1.0)
        painter.drawPixmap(s_rect, blurred_map, src_rect)
        painter.restore()

    tinte = QColor(25, 25, 45, 120)
    painter.setBrush(QBrush(tinte))
    painter.setPen(QPen(config.TOOLBAR_BORDER_COLOR, 1))
    painter.drawRoundedRect(menu_rect, config.TOOLBAR_RADIUS, config.TOOLBAR_RADIUS)

    # Dibujar botones internos si está expandido
    if opacity > 0.3:
        inner_opacity = (opacity - 0.3) / 0.7
        button_size = 38
        spacing = 12
        start_x = menu_rect.x() + (menu_rect.width() - button_size) / 2
        start_y = menu_rect.y() + 55 
        
        canvas.vertical_buttons_rects = []
        
        for i, tool in enumerate(config.VERTICAL_TOOLS):
            btn_y = start_y + i * (button_size + spacing)
            btn_rect = QRectF(start_x, btn_y, button_size, button_size)
            
            # Hit Rect más grande para facilitar selección (ancho completo y espacio vertical)
            hit_rect = QRectF(menu_rect.x(), btn_y - spacing/2, menu_rect.width(), button_size + spacing)
            
            # El botón se ve seleccionado si coincide con el índice
            is_selected = (getattr(canvas, "selected_vertical_tool", -1) == i)
            hover = (canvas.vertical_hovered_button == i)
            
            if is_selected:
                bg = QColor(0, 120, 215, int(220 * inner_opacity))
                border_color = QColor(255, 255, 255, int(200 * inner_opacity))
            elif hover:
                bg = QColor(80, 80, 110, int(200 * inner_opacity))
                border_color = QColor(255, 255, 255, int(120 * inner_opacity))
            else:
                bg = QColor(40, 40, 60, int(140 * inner_opacity))
                border_color = QColor(255, 255, 255, int(80 * inner_opacity))
            
            painter.setBrush(QBrush(bg))
            painter.setPen(QPen(border_color, 1))
            painter.drawEllipse(btn_rect)
            
            painter.setPen(QPen(QColor(255, 255, 255, int(255 * inner_opacity))))
            font = painter.font(); font.setPointSize(14); painter.setFont(font)
            painter.drawText(btn_rect, Qt.AlignCenter, tool["icon"])
            
            canvas.vertical_buttons_rects.append(hit_rect)

    # Botón principal (Trigger)
    trigger_rect = QRectF(menu_rect.x(), menu_rect.y(), menu_rect.width(), config.TOOLBAR_HEIGHT_COLLAPSED)
    
    # Cambiar icono si hay algo seleccionado
    sel_tool_idx = getattr(canvas, "selected_vertical_tool", None)
    icon = "⋮"
    if sel_tool_idx is not None:
        icon = config.VERTICAL_TOOLS[sel_tool_idx]["icon"]
        
    painter.setPen(QPen(QColor(255, 255, 255, 200)))
    font = painter.font(); font.setPointSize(16 if icon == "⋮" else 14); painter.setFont(font)
    painter.drawText(trigger_rect, Qt.AlignCenter, icon)

def draw_system_menu(painter, canvas, rect, blurred_map=None):
    """Menú de sistema flotante (Guardar / Abrir)"""
    s_rect = rect.toRect()
    
    # 1. Glassmorphism
    if blurred_map and not blurred_map.isNull():
        painter.save()
        path = QPainterPath(); path.addRoundedRect(rect, config.TOOLBAR_RADIUS, config.TOOLBAR_RADIUS); painter.setClipPath(path)
        
        refr_zoom = config.GLASS_REFRACTION
        src_w, src_h = s_rect.width() / refr_zoom, s_rect.height() / refr_zoom
        src_x, src_y = s_rect.x() + (s_rect.width() - src_w) / 2, s_rect.y() + (s_rect.height() - src_h) / 2
        src_rect = QRect(int(src_x), int(src_y), int(src_w), int(src_h))
        
        painter.setOpacity(0.4)
        ab = config.GLASS_ABERRATION
        painter.drawPixmap(s_rect.translated(-ab, 0), blurred_map, src_rect)
        painter.drawPixmap(s_rect.translated(ab, 0), blurred_map, src_rect)
        painter.setOpacity(1.0); painter.drawPixmap(s_rect, blurred_map, src_rect)
        painter.restore()

    # Tinte
    tinte = QColor(25, 25, 45, 120)
    painter.setBrush(QBrush(tinte))
    painter.setPen(QPen(config.TOOLBAR_BORDER_COLOR, 1))
    painter.drawRoundedRect(rect, config.TOOLBAR_RADIUS, config.TOOLBAR_RADIUS)
    
    # Botones: Guardar (Floppy) y Abrir (Folder)
    # Iconos unicode aproximados: 💾 (Save), 📂 (Open)
    # Usaremos texto simple si no hay fuente de iconos, o emojis si Qt los soporta bien (macOS suele hacerlo)
    
    btn_width = rect.width() / 2
    save_rect = QRectF(rect.x(), rect.y(), btn_width, rect.height())
    open_rect = QRectF(rect.x() + btn_width, rect.y(), btn_width, rect.height())
    
    # Hover effects
    mouse_pos = canvas.mapFromGlobal(canvas.cursor().pos())
    
    # Guardar
    if getattr(canvas, "hovered_system_btn", "") == "save":
        painter.setBrush(QBrush(QColor(255, 255, 255, 40)))
        painter.setPen(Qt.NoPen)
        painter.drawRoundedRect(save_rect.adjusted(2,2,-2,-2), 5, 5)
    
    painter.setPen(QPen(QColor(255, 255, 255, 220)))
    font = painter.font(); font.setPointSize(14); painter.setFont(font)
    painter.drawText(save_rect, Qt.AlignCenter, "💾")
    
    # Abrir
    if getattr(canvas, "hovered_system_btn", "") == "open":
        painter.setBrush(QBrush(QColor(255, 255, 255, 40)))
        painter.setPen(Qt.NoPen)
        painter.drawRoundedRect(open_rect.adjusted(2,2,-2,-2), 5, 5)
        
    painter.setPen(QPen(QColor(255, 255, 255, 220)))
    painter.drawText(open_rect, Qt.AlignCenter, "📂")
    
    # Guardar rects en canvas para hit testing
    canvas.system_btn_rects = {"save": save_rect, "open": open_rect}
