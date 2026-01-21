from PySide6.QtCore import Qt, QRectF, QPointF, QRect, QSize
from PySide6.QtGui import QBrush, QPen, QColor, QPolygonF, QPainterPath, QLinearGradient, QPixmap, QPainter, QTextDocument, QAbstractTextDocumentLayout, QTextCursor, QPalette
import time
from utils import get_contrast_color
import config

def draw_resize_handle(painter, rect):
    painter.save()
    painter.setBrush(QColor(255, 255, 255, 200))
    painter.setPen(QPen(Qt.black, 1))
    handle_size = 8
    handle_rect = QRectF(rect.right() - handle_size/2, rect.bottom() - handle_size/2, handle_size, handle_size)
    painter.drawEllipse(handle_rect)
    painter.restore()

def draw_rounded_rect(painter, obj, index, selected_index, zoom, world_to_screen, blurred_map=None):
    world_x, world_y = obj["x"], obj["y"]
    screen_x, screen_y = world_to_screen(world_x, world_y)
    
    size_w = obj.get("w", 100) * zoom
    size_h = obj.get("h", 100) * zoom
    rect = QRectF(screen_x - size_w/2, screen_y - size_h/2, size_w, size_h)
    s_rect = rect.toRect()
    
    if blurred_map and not blurred_map.isNull():
        painter.save()
        path = QPainterPath()
        path.addRoundedRect(rect, 15, 15)
        painter.setClipPath(path)
        
        refr_zoom = config.GLASS_REFRACTION
        src_w = s_rect.width() / refr_zoom
        src_h = s_rect.height() / refr_zoom
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
    
    bg_color = obj.get("personal_color", QColor(60, 60, 80, 100))
    border_color = get_contrast_color(bg_color)
    width = 3 if selected_index == index else 1.5
    if selected_index != index: border_color.setAlphaF(0.6)
    
    painter.setBrush(Qt.NoBrush)
    painter.setPen(QPen(border_color, width))
    painter.drawRoundedRect(rect, 15, 15)
    
    if selected_index == index:
        draw_resize_handle(painter, rect)

def draw_triangle(painter, obj, index, selected_index, zoom, world_to_screen, blurred_map=None):
    world_x, world_y = obj["x"], obj["y"]
    screen_x, screen_y = world_to_screen(world_x, world_y)
    size_w = obj.get("w", 100) * zoom
    size_h = obj.get("h", 100) * zoom
    
    points = QPolygonF([
        QPointF(screen_x, screen_y - size_h/2),
        QPointF(screen_x - size_w/2, screen_y + size_h/2),
        QPointF(screen_x + size_w/2, screen_y + size_h/2)
    ])
    
    s_rect = QRect(int(screen_x - size_w/2), int(screen_y - size_h/2), int(size_w), int(size_h))
    
    if blurred_map and not blurred_map.isNull():
        painter.save()
        path = QPainterPath(); path.addPolygon(points); painter.setClipPath(path)
        
        refr_zoom = config.GLASS_REFRACTION
        src_w, src_h = s_rect.width() / refr_zoom, s_rect.height() / refr_zoom
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

    bg_color = obj.get("personal_color", QColor(60, 60, 80, 100))
    border_color = get_contrast_color(bg_color)
    width = 3 if selected_index == index else 1.5
    painter.setBrush(Qt.NoBrush); painter.setPen(QPen(border_color, width))
    painter.drawPolygon(points)
    
    if selected_index == index:
        rect = QRectF(screen_x - size_w/2, screen_y - size_h/2, size_w, size_h)
        draw_resize_handle(painter, rect)

def draw_window(painter, obj, index, selected_index, zoom, world_to_screen, blurred_map=None):
    world_x, world_y = obj["x"], obj["y"]
    screen_x, screen_y = world_to_screen(world_x, world_y)
    
    width = obj.get("w", 200) * zoom
    height = obj.get("h", 150) * zoom
    title_height = 30 * zoom
    main_rect = QRectF(screen_x - width/2, screen_y - height/2, width, height)
    title_rect = QRectF(screen_x - width/2, screen_y - height/2, width, title_height)
    
    s_rect = main_rect.toRect()
    if blurred_map and not blurred_map.isNull():
        painter.save()
        path = QPainterPath(); path.addRoundedRect(main_rect, 10, 10); painter.setClipPath(path)
        refr_zoom = config.GLASS_REFRACTION
        src_w, src_h = s_rect.width() / refr_zoom, s_rect.height() / refr_zoom
        src_x = s_rect.x() + (s_rect.width() - src_w) / 2
        src_y = s_rect.y() + (s_rect.height() - src_h) / 2
        src_rect = QRect(int(src_x), int(src_y), int(src_w), int(src_h))
        ab = config.GLASS_ABERRATION
        painter.setOpacity(0.4)
        painter.drawPixmap(s_rect.translated(-ab, 0), blurred_map, src_rect)
        painter.drawPixmap(s_rect.translated(ab, 0), blurred_map, src_rect)
        painter.setOpacity(1.0); painter.drawPixmap(s_rect, blurred_map, src_rect)
        painter.restore()
    
    painter.setBrush(Qt.NoBrush); painter.setPen(Qt.NoPen); painter.drawRoundedRect(main_rect, 10, 10)
    
    title_color = obj.get("personal_color", QColor(70, 70, 90, 230))
    painter.setBrush(QBrush(QColor(title_color.red(), title_color.green(), title_color.blue(), 180)))
    painter.drawRoundedRect(title_rect, 10, 10)
    painter.drawRect(QRectF(title_rect.x(), title_rect.y() + title_height/2, title_rect.width(), title_height/2))
    
    border_color = get_contrast_color(title_color)
    painter.setBrush(Qt.NoBrush); painter.setPen(QPen(border_color, 1.5))
    painter.drawRoundedRect(main_rect, 10, 10)
    
    painter.setPen(QPen(config.TEXT_COLOR))
    painter.drawText(title_rect, Qt.AlignCenter, obj.get("title", "Ventana"))
    
    content_rect = QRectF(main_rect.x() + 15, main_rect.y() + title_height + 15, main_rect.width() - 30, main_rect.height() - title_height - 30)
    content_text = obj.get("content", "")
    painter.setPen(QPen(QColor(255, 255, 255, 220)))
    font = painter.font(); font.setPointSize(int(13 * zoom)); painter.setFont(font)
    
    is_selected = (selected_index == index)
    cursor = "|" if (int(time.time() * 2) % 2 == 0) and is_selected else ""
    if not is_selected and not content_text:
        painter.setOpacity(0.4); painter.drawText(content_rect, Qt.AlignLeft | Qt.AlignTop | Qt.TextWordWrap, "Empieza a escribir..."); painter.setOpacity(1.0)
    else:
        display_text = content_text + cursor if is_selected else content_text
        painter.drawText(content_rect, Qt.AlignLeft | Qt.AlignTop | Qt.TextWordWrap, display_text)

    if selected_index == index:
        draw_resize_handle(painter, main_rect)

def draw_text_object(painter, obj, index, selected_index, zoom, world_to_screen, default_text_color, blurred_map=None):
    world_x, world_y = obj["x"], obj["y"]
    screen_x, screen_y = world_to_screen(world_x, world_y)
    text = obj.get("text", "")
    is_selected = (selected_index == index)
    cursor = "|" if (int(time.time() * 2) % 2 == 0) and is_selected else ""
    display_text = text if text or is_selected else "Empieza a escribir..."
    font = painter.font(); font.setPointSize(int(16 * min(zoom, 1.5))); painter.setFont(font)
    
    metrics = painter.fontMetrics()
    text_rect_base = metrics.boundingRect(QRect(0, 0, 1000, 1000), Qt.AlignCenter, display_text + "|")
    
    w_world = obj.get("w", text_rect_base.width() / zoom)
    h_world = obj.get("h", text_rect_base.height() / zoom)
    
    padding_x = 45 * zoom; padding_y = 25 * zoom
    rect = QRectF(screen_x - (w_world*zoom)/2 - padding_x, screen_y - (h_world*zoom)/2 - padding_y, w_world*zoom + padding_x*2, h_world*zoom + padding_y*2)
    s_rect = rect.toRect()

    if blurred_map and not blurred_map.isNull():
        painter.save()
        path = QPainterPath(); path.addRoundedRect(rect, 15, 15); painter.setClipPath(path)
        refr_zoom = config.GLASS_REFRACTION
        src_w, src_h = s_rect.width() / refr_zoom, s_rect.height() / refr_zoom
        src_x, src_y = s_rect.x() + (s_rect.width() - src_w) / 2, s_rect.y() + (s_rect.height() - src_h) / 2
        src_rect = QRect(int(src_x), int(src_y), int(src_w), int(src_h))
        ab = config.GLASS_ABERRATION
        painter.setOpacity(0.4)
        painter.drawPixmap(s_rect.translated(-ab, 0), blurred_map, src_rect)
        painter.drawPixmap(s_rect.translated(ab, 0), blurred_map, src_rect)
        painter.setOpacity(1.0); painter.drawPixmap(s_rect, blurred_map, src_rect)
        painter.restore()

    painter.setBrush(QBrush(QColor(20, 20, 35, 140))); painter.setPen(Qt.NoPen); painter.drawRoundedRect(rect, 15, 15)
    text_color = obj.get("personal_color", default_text_color)
    if is_selected: text_color = get_contrast_color(text_color)
    painter.setOpacity(0.4 if (not text and not is_selected) else 1.0)
    painter.setPen(QPen(text_color)); painter.drawText(rect, Qt.AlignCenter, display_text + cursor); painter.setOpacity(1.0)
    
    if is_selected: draw_resize_handle(painter, rect)

def draw_image_object(painter, obj, index, selected_index, zoom, world_to_screen):
    world_x, world_y = obj["x"], obj["y"]
    screen_x, screen_y = world_to_screen(world_x, world_y)
    
    w_orig, h_orig = obj.get("w_orig", obj.get("w", 300)), obj.get("h_orig", obj.get("h", 300))
    if "w_orig" not in obj: obj["w_orig"], obj["h_orig"] = w_orig, h_orig
    
    w_world = obj.get("w", w_orig)
    h_world = obj.get("h", h_orig)
    
    # Limitar tamaño inicial si no tiene dimensiones guardadas
    if "w" not in obj:
        scale = min(300 / w_orig, 300 / h_orig)
        w_world = w_orig * scale; h_world = h_orig * scale
        obj["w"], obj["h"] = w_world, h_world

    rect = QRectF(screen_x - (w_world*zoom)/2, screen_y - (h_world*zoom)/2, w_world*zoom, h_world*zoom)
    
    painter.save()
    path = QPainterPath(); path.addRoundedRect(rect, 20, 20); painter.setClipPath(path)
    painter.drawPixmap(rect.toRect(), obj["pixmap"]); painter.restore()
    
    border_color = QColor(255, 255, 255, 150)
    width = 2
    if selected_index == index:
        border_color = QColor(100, 200, 255, 255); width = 4
    painter.setBrush(Qt.NoBrush); painter.setPen(QPen(border_color, width)); painter.drawRoundedRect(rect, 20, 20)

    if selected_index == index: draw_resize_handle(painter, rect)

def draw_markdown_object(painter, obj, index, selected_index, zoom, world_to_screen, blurred_map=None):
    world_x, world_y = obj["x"], obj["y"]
    screen_x, screen_y = world_to_screen(world_x, world_y)
    
    width_world = obj.get("w", 300)
    height_world = obj.get("h", 400)
    width, height = width_world * zoom, height_world * zoom
    title_height = 30 * zoom
    
    rect = QRectF(screen_x - width/2, screen_y - height/2, width, height)
    title_rect = QRectF(screen_x - width/2, screen_y - height/2, width, title_height)
    
    s_rect = rect.toRect()
    if blurred_map and not blurred_map.isNull():
        painter.save()
        path = QPainterPath(); path.addRoundedRect(rect, 15, 15); painter.setClipPath(path)
        refr_zoom = config.GLASS_REFRACTION
        src_w, src_h = s_rect.width() / refr_zoom, s_rect.height() / refr_zoom
        src_x, src_y = s_rect.x() + (s_rect.width() - src_w) / 2, s_rect.y() + (s_rect.height() - src_h) / 2
        src_rect = QRect(int(src_x), int(src_y), int(src_w), int(src_h))
        ab = config.GLASS_ABERRATION
        painter.setOpacity(0.4)
        painter.drawPixmap(s_rect.translated(-ab, 0), blurred_map, src_rect)
        painter.drawPixmap(s_rect.translated(ab, 0), blurred_map, src_rect)
        painter.setOpacity(1.0); painter.drawPixmap(s_rect, blurred_map, src_rect)
        painter.restore()

    bg_color = obj.get("personal_color", QColor(30, 30, 45, 180))
    painter.setBrush(QBrush(bg_color))
    border_color = QColor(255, 255, 255, 100); border_width = 1.5
    if selected_index == index:
        border_color = QColor(100, 200, 255, 255); border_width = 3
    painter.setPen(QPen(border_color, border_width)); painter.drawRoundedRect(rect, 15, 15)
    
    title_bg = QColor(bg_color.red(), bg_color.green(), bg_color.blue(), 230)
    painter.setBrush(QBrush(title_bg)); painter.setPen(Qt.NoPen); painter.drawRoundedRect(title_rect, 15, 15)
    painter.drawRect(QRectF(title_rect.x(), title_rect.y() + title_height/2, title_rect.width(), title_height/2))
    
    painter.setPen(QPen(config.TEXT_COLOR))
    title_font = painter.font(); title_font.setBold(True); title_font.setPointSize(int(11 * zoom)); painter.setFont(title_font)
    painter.drawText(title_rect.adjusted(10, 0, -10, 0), Qt.AlignLeft | Qt.AlignVCenter, obj.get("title", "README.md"))
    
    padding = 15 * zoom
    content_rect = rect.adjusted(padding, title_height + padding, -padding, -padding)
    world_visible_width = content_rect.width() / zoom
    world_visible_height = content_rect.height() / zoom
    
    if "doc" not in obj:
        obj["doc"] = QTextDocument()
        obj["doc"].setDefaultStyleSheet("* { color: #ffffff; } h1 { font-size: 18px; font-weight: bold; } p { font-size: 12px; }")
        obj["doc"].setMarkdown(obj.get("content", ""))

    if obj["doc"].textWidth() != world_visible_width: obj["doc"].setTextWidth(world_visible_width)
    obj["max_scroll_y"] = max(0, obj["doc"].size().height() - world_visible_height)
    scroll_y = obj.get("scroll_y", 0)
    
    painter.save()
    painter.translate(content_rect.topLeft())
    clip_path = QPainterPath(); clip_path.addRoundedRect(QRectF(0, 0, content_rect.width(), content_rect.height()), 5, 5); painter.setClipPath(clip_path)
    painter.scale(zoom, zoom); painter.translate(0, -scroll_y)
    
    ctx = QAbstractTextDocumentLayout.PaintContext(); sel_pal = QPalette(); sel_pal.setColor(QPalette.Text, Qt.white); sel_pal.setColor(QPalette.Highlight, QColor(0, 122, 255, 180)); sel_pal.setColor(QPalette.HighlightedText, Qt.white); ctx.palette = sel_pal
    if obj.get("sel_start") is not None and obj.get("sel_end") is not None:
        selection = QAbstractTextDocumentLayout.Selection(); cursor = QTextCursor(obj["doc"]); cursor.setPosition(obj["sel_start"]); cursor.setPosition(obj["sel_end"], QTextCursor.KeepAnchor); selection.cursor = cursor; ctx.selections = [selection]
    painter.setPen(Qt.white); obj["doc"].documentLayout().draw(painter, ctx); painter.restore()
    
    if selected_index == index: draw_resize_handle(painter, rect)
