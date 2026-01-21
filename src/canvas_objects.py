from PySide6.QtCore import Qt, QRectF, QPointF, QRect
from PySide6.QtGui import QBrush, QPen, QColor, QPolygonF, QPainterPath, QLinearGradient, QPixmap, QPainter
import time
from utils import get_contrast_color
import config

def draw_rounded_rect(painter, obj, index, selected_index, zoom, world_to_screen, blurred_map=None):
    world_x, world_y = obj["x"], obj["y"]
    screen_x, screen_y = world_to_screen(world_x, world_y)
    
    size = 100 * zoom
    rect = QRectF(screen_x - size/2, screen_y - size/2, size, size)
    s_rect = rect.toRect()
    
    # Efecto Liquid Glass (Desenfoque + Refracción/Magnificación)
    if blurred_map and not blurred_map.isNull():
        painter.save()
        path = QPainterPath()
        path.addRoundedRect(rect, 15, 15)
        painter.setClipPath(path)
        
        # Lógica de Refracción: Tomamos un trozo más pequeño del fondo y lo estiramos
        zoom = config.GLASS_REFRACTION
        src_w = s_rect.width() / zoom
        src_h = s_rect.height() / zoom
        src_x = s_rect.x() + (s_rect.width() - src_w) / 2
        src_y = s_rect.y() + (s_rect.height() - src_h) / 2
        src_rect = QRect(int(src_x), int(src_y), int(src_w), int(src_h))
        
        # --- ABERRACIÓN CROMÁTICA (iPhone style RGB separation) ---
        ab = config.GLASS_ABERRATION
        # Pase 1: Sombra Roja (Shift Izquierda)
        painter.setOpacity(0.4)
        painter.drawPixmap(s_rect.translated(-ab, 0), blurred_map, src_rect)
        # Pase 2: Sombra Azul (Shift Derecha)
        painter.drawPixmap(s_rect.translated(ab, 0), blurred_map, src_rect)
        # Pase 3: Centro nítido
        painter.setOpacity(1.0)
        painter.drawPixmap(s_rect, blurred_map, src_rect)
        
        painter.restore()
    
    bg_color = obj.get("personal_color", QColor(60, 60, 80, 100))
    border_color = get_contrast_color(bg_color)
    
    width = 3 if selected_index == index else 1.5
    if selected_index != index:
        border_color.setAlphaF(0.6)
    
    painter.setBrush(Qt.NoBrush) # Sin capa por encima
    painter.setPen(QPen(border_color, width))
    painter.drawRoundedRect(rect, 15, 15)


def draw_triangle(painter, obj, index, selected_index, zoom, world_to_screen, blurred_map=None):
    world_x, world_y = obj["x"], obj["y"]
    screen_x, screen_y = world_to_screen(world_x, world_y)
    size = 100 * zoom
    
    points = QPolygonF([
        QPointF(screen_x, screen_y - size/2),
        QPointF(screen_x - size/2, screen_y + size/2),
        QPointF(screen_x + size/2, screen_y + size/2)
    ])
    
    # Efecto Liquid Glass (Desenfoque + Refracción) en Triángulo
    if blurred_map and not blurred_map.isNull():
        painter.save()
        path = QPainterPath()
        path.addPolygon(points)
        painter.setClipPath(path)
        
        zoom = config.GLASS_REFRACTION
        s_rect = QRect(int(screen_x - size/2), int(screen_y - size/2), int(size), int(size))
        src_w, src_h = s_rect.width() / zoom, s_rect.height() / zoom
        src_x = s_rect.x() + (s_rect.width() - src_w) / 2
        src_y = s_rect.y() + (s_rect.height() - src_h) / 2
        src_rect = QRect(int(src_x), int(src_y), int(src_w), int(src_h))
        
        # --- ABERRACIÓN CROMÁTICA en Triángulo ---
        ab = config.GLASS_ABERRATION
        painter.setOpacity(0.4)
        painter.drawPixmap(s_rect.translated(-ab, 1), blurred_map, src_rect)
        painter.drawPixmap(s_rect.translated(ab, -1), blurred_map, src_rect)
        painter.setOpacity(1.0)
        painter.drawPixmap(s_rect, blurred_map, src_rect)
        
        painter.restore()

    bg_color = obj.get("personal_color", QColor(60, 60, 80, 100))
    border_color = get_contrast_color(bg_color)
    
    width = 3 if selected_index == index else 1.5
    painter.setBrush(Qt.NoBrush) # Sin capa por encima
    painter.setPen(QPen(border_color, width))
    painter.drawPolygon(points)


def draw_window(painter, obj, index, selected_index, zoom, world_to_screen, blurred_map=None):
    world_x, world_y = obj["x"], obj["y"]
    screen_x, screen_y = world_to_screen(world_x, world_y)
    
    width, height = 200 * zoom, 150 * zoom
    title_height = 30 * zoom
    main_rect = QRectF(screen_x - width/2, screen_y - height/2, width, height)
    title_rect = QRectF(screen_x - width/2, screen_y - height/2, width, title_height)
    
    # 1. Cuerpo Liquid Glass (Refracción 10%)
    s_rect = main_rect.toRect()
    if blurred_map and not blurred_map.isNull():
        painter.save()
        path = QPainterPath()
        path.addRoundedRect(main_rect, 10, 10)
        painter.setClipPath(path)
        
        zoom = config.GLASS_REFRACTION
        src_w, src_h = s_rect.width() / zoom, s_rect.height() / zoom
        src_x = s_rect.x() + (s_rect.width() - src_w) / 2
        src_y = s_rect.y() + (s_rect.height() - src_h) / 2
        src_rect = QRect(int(src_x), int(src_y), int(src_w), int(src_h))
        
        # --- ABERRACIÓN CROMÁTICA en Ventana ---
        ab = config.GLASS_ABERRATION
        painter.setOpacity(0.4)
        painter.drawPixmap(s_rect.translated(-ab, 0), blurred_map, src_rect)
        painter.drawPixmap(s_rect.translated(ab, 0), blurred_map, src_rect)
        painter.setOpacity(1.0)
        painter.drawPixmap(s_rect, blurred_map, src_rect)
        
        painter.restore()
    
    painter.setBrush(Qt.NoBrush) # Sin capa de tinte en el cuerpo
    painter.setPen(Qt.NoPen)
    painter.drawRoundedRect(main_rect, 10, 10)

    
    # 2. Título
    title_color = obj.get("personal_color", QColor(70, 70, 90, 230))
    painter.setBrush(QBrush(QColor(title_color.red(), title_color.green(), title_color.blue(), 180)))
    painter.drawRoundedRect(title_rect, 10, 10)
    painter.drawRect(QRectF(title_rect.x(), title_rect.y() + title_height/2, title_rect.width(), title_height/2))
    
    # 3. Borde
    border_color = get_contrast_color(title_color)
    painter.setBrush(Qt.NoBrush)
    painter.setPen(QPen(border_color, 1.5))
    painter.drawRoundedRect(main_rect, 10, 10)
    
    painter.setPen(QPen(config.TEXT_COLOR))
    painter.drawText(title_rect, Qt.AlignCenter, obj.get("title", "Ventana"))
    
    # 4. Contenido de la ventana (Texto editable)
    content_rect = QRectF(main_rect.x() + 15, main_rect.y() + title_height + 15, main_rect.width() - 30, main_rect.height() - title_height - 30)
    content_text = obj.get("content", "")
    
    painter.setPen(QPen(QColor(255, 255, 255, 220)))
    font = painter.font()
    font.setPointSize(int(13 * zoom))
    painter.setFont(font)
    
    is_selected = (selected_index == index)
    # Cursor parpadeante
    cursor = "|" if (int(time.time() * 2) % 2 == 0) and is_selected else ""
    
    # Si NO está seleccionado y está vacío: Mostramos el texto de ayuda sutilmente.
    if not is_selected and not content_text:
        painter.setOpacity(0.4)
        painter.drawText(content_rect, Qt.AlignLeft | Qt.AlignTop | Qt.TextWordWrap, "Empieza a escribir...")
        painter.setOpacity(1.0)
    else:
        # Si está seleccionado, añadimos el cursor al texto (aunque esté vacío)
        display_text = content_text + cursor if is_selected else content_text
        painter.drawText(content_rect, Qt.AlignLeft | Qt.AlignTop | Qt.TextWordWrap, display_text)

def draw_text_object(painter, obj, index, selected_index, zoom, world_to_screen, default_text_color, blurred_map=None):
    world_x, world_y = obj["x"], obj["y"]
    screen_x, screen_y = world_to_screen(world_x, world_y)
    text = obj.get("text", "")
    
    is_selected = (selected_index == index)
    cursor = "|" if (int(time.time() * 2) % 2 == 0) and is_selected else ""
    display_text = text if text or is_selected else "Empieza a escribir..."
    
    font = painter.font()
    font.setPointSize(int(16 * min(zoom, 1.5)))
    painter.setFont(font)
    
    # 1. Calcular área del texto para centrar la "píldora" (Maneja múltiples líneas)
    metrics = painter.fontMetrics()
    # Usamos un rectángulo enorme como referencia para que boundingRect nos dé el tamaño real necesario
    text_rect = metrics.boundingRect(QRect(0, 0, 1000, 1000), Qt.AlignCenter, display_text + "|")
    text_w = text_rect.width()
    text_h = text_rect.height()
    
    padding_x = 45 * zoom
    padding_y = 25 * zoom
    
    rect = QRectF(screen_x - text_w/2 - padding_x, screen_y - text_h/2 - padding_y, text_w + padding_x*2, text_h + padding_y*2)
    s_rect = rect.toRect()

    # 2. Dibujar fondo Liquid Glass uniforme
    if blurred_map and not blurred_map.isNull():
        painter.save()
        path = QPainterPath()
        path.addRoundedRect(rect, 15, 15)
        painter.setClipPath(path)
        
        zoom_factor = config.GLASS_REFRACTION
        src_w, src_h = s_rect.width() / zoom_factor, s_rect.height() / zoom_factor
        src_x = s_rect.x() + (s_rect.width() - src_w) / 2
        src_y = s_rect.y() + (s_rect.height() - src_h) / 2
        src_rect = QRect(int(src_x), int(src_y), int(src_w), int(src_h))
        
        ab = config.GLASS_ABERRATION
        painter.setOpacity(0.4)
        painter.drawPixmap(s_rect.translated(-ab, 0), blurred_map, src_rect)
        painter.drawPixmap(s_rect.translated(ab, 0), blurred_map, src_rect)
        painter.setOpacity(1.0)
        painter.drawPixmap(s_rect, blurred_map, src_rect)
        painter.restore()

    # 3. Tinte sin borde
    painter.setBrush(QBrush(QColor(20, 20, 35, 140)))
    painter.setPen(Qt.NoPen)
    painter.drawRoundedRect(rect, 15, 15)

    # 4. Texto
    text_color = obj.get("personal_color", default_text_color)
    if is_selected: text_color = get_contrast_color(text_color)
    
    painter.setOpacity(0.4 if (not text and not is_selected) else 1.0)
    painter.setPen(QPen(text_color))
    painter.drawText(rect, Qt.AlignCenter, display_text + cursor)
    painter.setOpacity(1.0)

def draw_image_object(painter, obj, index, selected_index, zoom, world_to_screen):
    world_x, world_y = obj["x"], obj["y"]
    screen_x, screen_y = world_to_screen(world_x, world_y)
    
    # Tamaño base limitado para que no ocupe toda la pantalla al importar
    max_side = 300 * zoom
    img_w, img_h = obj["w"], obj["h"]
    scale = min(max_side / img_w, max_side / img_h)
    w, h = img_w * scale, img_h * scale
    
    rect = QRectF(screen_x - w/2, screen_y - h/2, w, h)
    
    painter.save()
    # 1. Esquinas redondeadas (Clipping)
    path = QPainterPath()
    path.addRoundedRect(rect, 20, 20)
    painter.setClipPath(path)
    
    # 2. Dibujar Imagen
    painter.drawPixmap(rect.toRect(), obj["pixmap"])
    painter.restore()
    
    # 3. Borde elegante (iPhone style)
    border_color = QColor(255, 255, 255, 150)
    if selected_index == index:
        border_color = QColor(100, 200, 255, 255)
        width = 4
    else:
        width = 2
        
    painter.setBrush(Qt.NoBrush)
    painter.setPen(QPen(border_color, width))
    painter.drawRoundedRect(rect, 20, 20)
