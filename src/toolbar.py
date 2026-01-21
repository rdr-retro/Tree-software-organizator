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
        painter.drawRoundedRect(button_rect, 8, 8)
        
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
