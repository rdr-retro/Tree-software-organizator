import sys
from PySide6.QtWidgets import QWidget
from PySide6.QtCore import Qt, QPointF, QTimer, QRectF, QSize
# Alias para evitar conflicto con la función min/max de python si fuera necesario, o simple uso directo
def max_(a, b): return a if a > b else b

from PySide6.QtGui import QPainter, QPen, QColor, QWheelEvent, QMouseEvent, QBrush, QPixmap, QPolygonF

import config
import utils
import canvas_objects
import toolbar

class Canvas(QWidget):
    def __init__(self):
        super().__init__()
        self.offset_x = 0.0
        self.offset_y = 0.0
        self.zoom = 1.0
        self.min_zoom = 0.1
        self.max_zoom = 10.0
        self.dragging = False
        self.last_mouse_pos = QPointF(0, 0)
        
        # State
        self.toolbar_expanded = False
        self.toolbar_animation_progress = 0.0
        self.circle_expanded = False
        self.circle_animation_progress = 0.0
        self.vertical_menu_expanded = False
        self.vertical_menu_animation_progress = 0.0
        # Color por defecto Azul ("es azul")
        self.active_color = QColor(0, 120, 215)
        self.current_circle_radius = config.TOOLBAR_HEIGHT_COLLAPSED / 2
        self.vertical_hovered_button = None
        self.vertical_buttons_rects = []
        
        # Objects
        self.canvas_objects = []
        self.selected_objects = [] # Lista de índices seleccionados
        self.selected_object = None # Mantener para compatibilidad
        self.dragging_object = False
        self.selecting_text = False
        self.resizing_object = False
        self.selection_rect = None # QRectF en espacio pantalla
        self.selected_vertical_tool = None
        self.drawing_stroke_width = 2
        self.drawing_stroke_width = 2
        self.current_stroke = None
        self.is_drawing = False
        self.drawing_target_index = None
        self.is_erasing = False
        self.is_animating = False
        
        # Buffers de Renderizado (Cacheados para rendimiento fluido)
        self.world_pixmap = QPixmap()
        self.blurred_pixmap = QPixmap()
        self.full_scene_pixmap = QPixmap()
        self.final_blur_pixmap = QPixmap()
        self.last_blur_size = QSize(0,0)
        self.needs_blur_update = True
        
        self.animation_timer = QTimer()
        self.animation_timer.timeout.connect(self.update_animation)
        self.animation_timer.setInterval(16)
        
        self.setMouseTracking(True)
        self.setAcceptDrops(True) # Habilitar Drag & Drop
        self.setFocusPolicy(Qt.StrongFocus) # Permitir foco de teclado
        
        # Timer para parpadeo de cursor
        self.cursor_timer = QTimer()
        self.cursor_timer.timeout.connect(self.update)
        self.cursor_timer.start(500)
        
        self._init_colors()

    def _init_colors(self):
        self.circle_buttons = []
        for h_idx in range(16):
            hue = (h_idx / 16.0)
            for s_idx in range(7):
                sat = 0.8 if s_idx > 0 else 0.9
                val = [0.15, 0.35, 0.65, 0.85, 0.95, 1.0, 1.0][s_idx]
                if s_idx >= 5: sat = 0.4 if s_idx == 5 else 0.2
                self.circle_buttons.append({"color": QColor.fromHsvF(hue, sat, val)})

    def screen_to_world(self, sx, sy):
        return (sx - self.width()/2 - self.offset_x)/self.zoom, (sy - self.height()/2 - self.offset_y)/self.zoom
    
    def world_to_screen(self, wx, wy):
        return wx * self.zoom + self.width()/2 + self.offset_x, wy * self.zoom + self.height()/2 + self.offset_y

    def get_obj_dims(self, obj):
        """Devuelve (w, h) en unidades del mundo para cualquier objeto."""
        if "w" in obj and "h" in obj:
            return obj["w"], obj["h"]
        
        t = obj["type"]
        if t in ["cuadrado", "triangulo"]: return 100, 100
        if t == "ventana": return 200, 150
        if t == "markdown": return 300, 400
        if t == "codigo": return 500, 400
        if t == "texto": return 200, 50
        if t == "imagen":
            w_orig = obj.get("w_orig", obj.get("w", 100))
            h_orig = obj.get("h_orig", obj.get("h", 100))
            scale = min(300 / w_orig, 300 / h_orig)
            return w_orig * scale, h_orig * scale
        if t == "dibujo":
            return obj.get("w", 200), obj.get("h", 200)
        return 100, 100

    def update_animation(self):
        speed = 0.15
        t_target = 1.0 if self.toolbar_expanded else 0.0
        c_target = 1.0 if self.circle_expanded else 0.0
        v_target = 1.0 if self.vertical_menu_expanded else 0.0
        
        self.toolbar_animation_progress += (t_target - self.toolbar_animation_progress) * speed
        self.circle_animation_progress += (c_target - self.circle_animation_progress) * speed
        self.vertical_menu_animation_progress += (v_target - self.vertical_menu_animation_progress) * speed
        
        init_r = config.TOOLBAR_HEIGHT_COLLAPSED / 2
        self.current_circle_radius = init_r - (init_r - 25) * self.circle_animation_progress
        
        if abs(self.toolbar_animation_progress - t_target) < 0.01 and \
           abs(self.circle_animation_progress - c_target) < 0.01 and \
           abs(self.vertical_menu_animation_progress - v_target) < 0.01:
            self.toolbar_animation_progress = t_target
            self.circle_animation_progress = c_target
            self.vertical_menu_animation_progress = v_target
            self.animation_timer.stop()
            self.is_animating = False
        self.update()

    def paintEvent(self, event):
        if self.width() <= 0 or self.height() <= 0: return
        
        # 1. Preparar Buffers al tamaño de la ventana
        size = self.size()
        if self.world_pixmap.size() != size:
            self.world_pixmap = QPixmap(size)
            self.full_scene_pixmap = QPixmap(size)
            self.needs_blur_update = True
        
        # CAPA 1: FONDO Y CUADRÍCULA
        self.world_pixmap.fill(config.BG_COLOR)
        wp = QPainter()
        if wp.begin(self.world_pixmap):
            wp.setRenderHint(QPainter.Antialiasing)
            spacing = 100 * self.zoom
            wp.setPen(QPen(config.GRID_COLOR, 2))
            ox = (self.offset_x + self.width()/2) % spacing
            oy = (self.offset_y + self.height()/2) % spacing
            x = ox
            while x < self.width(): wp.drawLine(int(x), 0, int(x), self.height()); x += spacing
            y = oy
            while y < self.height(): wp.drawLine(0, int(y), self.width(), int(y)); y += spacing
            
            for i, obj in enumerate(self.canvas_objects):
                if obj["type"] == "imagen":
                    canvas_objects.draw_image_object(wp, obj, i, self.selected_object, self.zoom, self.world_to_screen)
            wp.end()
        
        # CAPA 2: DESENFOQUE ESTRUCTURAL
        # Desactivamos la optimización condicional para garantizar estabilidad visual
        self.blurred_pixmap = utils.apply_gaussian_blur(self.world_pixmap, config.GLASS_BLUR_RADIUS)
        self.needs_blur_update = False
        
        # CAPA 3: ESCENARIO COMPLETO
        self.full_scene_pixmap.fill(Qt.transparent)
        sp = QPainter()
        if sp.begin(self.full_scene_pixmap):
            sp.setRenderHint(QPainter.Antialiasing)
            sp.drawPixmap(0, 0, self.world_pixmap)
            
            for i, obj in enumerate(self.canvas_objects):
                t = obj["type"]
                is_selected = (i in self.selected_objects)
                sel_idx = i if is_selected else -1
                
                if t == "cuadrado": canvas_objects.draw_rounded_rect(sp, obj, i, sel_idx, self.zoom, self.world_to_screen, self.blurred_pixmap)
                elif t == "triangulo": canvas_objects.draw_triangle(sp, obj, i, sel_idx, self.zoom, self.world_to_screen, self.blurred_pixmap)
                elif t == "ventana": canvas_objects.draw_window(sp, obj, i, sel_idx, self.zoom, self.world_to_screen, self.blurred_pixmap)
                elif t == "texto": canvas_objects.draw_text_object(sp, obj, i, sel_idx, self.zoom, self.world_to_screen, config.TEXT_COLOR, self.blurred_pixmap)
                elif t == "markdown": canvas_objects.draw_markdown_object(sp, obj, i, sel_idx, self.zoom, self.world_to_screen, self.blurred_pixmap)
                elif t == "codigo": canvas_objects.draw_code_object(sp, obj, i, sel_idx, self.zoom, self.world_to_screen, self.blurred_pixmap)
                elif t == "dibujo": canvas_objects.draw_drawing_object(sp, obj, i, sel_idx, self.zoom, self.world_to_screen, self.blurred_pixmap)

            if self.is_drawing and self.current_stroke:
                sp.save()
                points = self.current_stroke["points"]
                style = self.current_stroke["style"]
                width = self.current_stroke["width"] * self.zoom
                # Usar el color guardado en el trazo o el activo por defecto
                color = QColor(self.current_stroke.get("color", self.active_color))
                
                if style == "rotulador": color.setAlpha(150); width *= 2
                
                sp.setPen(QPen(color, width, Qt.SolidLine, Qt.RoundCap, Qt.RoundJoin))
                poly = QPolygonF()
                for wx, wy in points:
                    sx, sy = self.world_to_screen(wx, wy)
                    poly.append(QPointF(sx, sy))
                sp.drawPolyline(poly)
                sp.restore()
            sp.end()
        
        # CAPA 4: DESENFOQUE FINAL PARA UI
        if not self.is_drawing and not self.is_animating:
            self.final_blur_pixmap = utils.apply_gaussian_blur(self.full_scene_pixmap, config.GLASS_BLUR_RADIUS)
        
        # CAPA 5: PRESENTACIÓN A PANTALLA
        final_painter = QPainter()
        if final_painter.begin(self):
            final_painter.setRenderHint(QPainter.Antialiasing)
            final_painter.drawPixmap(0, 0, self.full_scene_pixmap)
            
            tw = config.TOOLBAR_WIDTH_COLLAPSED + (config.TOOLBAR_WIDTH_EXPANDED - config.TOOLBAR_WIDTH_COLLAPSED) * self.toolbar_animation_progress
            th = config.TOOLBAR_HEIGHT_COLLAPSED + (config.TOOLBAR_HEIGHT_EXPANDED - config.TOOLBAR_HEIGHT_COLLAPSED) * self.toolbar_animation_progress
            toolbar_rect = QRectF((self.width() - tw)/2, config.TOOLBAR_MARGIN, tw, th)
            
            cw = config.TOOLBAR_HEIGHT_COLLAPSED + (config.CIRCLE_EXPANDED_WIDTH - config.TOOLBAR_HEIGHT_COLLAPSED) * self.circle_animation_progress
            ch = config.TOOLBAR_HEIGHT_COLLAPSED + (config.CIRCLE_EXPANDED_HEIGHT - config.TOOLBAR_HEIGHT_COLLAPSED) * self.circle_animation_progress
            circle_rect = QRectF(toolbar_rect.right() + 10, config.TOOLBAR_MARGIN, cw, ch)
            self.current_circle_rect = circle_rect
            
            vw = config.TOOLBAR_HEIGHT_COLLAPSED + (config.VERTICAL_MENU_EXPANDED_WIDTH - config.TOOLBAR_HEIGHT_COLLAPSED) * self.vertical_menu_animation_progress
            vh = config.TOOLBAR_HEIGHT_COLLAPSED + (config.VERTICAL_MENU_EXPANDED_HEIGHT - config.TOOLBAR_HEIGHT_COLLAPSED) * self.vertical_menu_animation_progress
            vertical_rect = QRectF(circle_rect.right() + 10, config.TOOLBAR_MARGIN, vw, vh)
            self.current_vertical_rect = vertical_rect
            
            toolbar.draw_vertical_menu(final_painter, self, vertical_rect, self.vertical_menu_animation_progress, self.final_blur_pixmap)
            toolbar.draw_color_palette(final_painter, self, circle_rect, self.circle_animation_progress, self.final_blur_pixmap)
            toolbar.draw_toolbar_island(final_painter, self, toolbar_rect, self.final_blur_pixmap)
            
            if self.toolbar_animation_progress > 0.3:
                toolbar.draw_tool_buttons(final_painter, self, toolbar_rect, (self.toolbar_animation_progress - 0.3) / 0.7)
            
            if self.selection_rect:
                final_painter.setPen(QPen(QColor(0, 120, 215, 255), 1))
                final_painter.setBrush(QBrush(QColor(0, 120, 215, 60)))
                final_painter.drawRect(self.selection_rect)
            
            self.draw_ui_info(final_painter)
            final_painter.end()



    def draw_ui_info(self, painter):
        painter.setPen(QPen(config.TEXT_COLOR))
        painter.drawText(10, 30, f"Zoom: {self.zoom:.2f}x")
        y = self.height() - 80
        for line in ["Rueda: Zoom", "Shift + Click: Pan", "ESC: Salir", "DEL: Eliminar"]:
            painter.drawText(10, y, line); y += 25

    # --- EVENTOS ---
    def wheelEvent(self, event):
        pos = event.position()
        wx, wy = self.screen_to_world(pos.x(), pos.y())
        
        # 1. Comprobar si estamos sobre un objeto markdown/codigo para hacer scroll
        for obj in reversed(self.canvas_objects):
            if obj["type"] in ["markdown", "codigo"]:
                ox, oy = obj["x"], obj["y"]
                # Detección precisa del área de contenido del markdown (300x400)
                if abs(wx - ox) < 150 and abs(wy - oy) < 200:
                    delta = event.angleDelta().y()
                    current_scroll = obj.get("scroll_y", 0)
                    # El scroll se aplica en sentido contrario al delta
                    new_scroll = current_scroll - delta / 2
                    obj["scroll_y"] = max(0, min(obj.get("max_scroll_y", 1000), new_scroll))
                    self.update()
                    return # Bloqueamos el zoom si estamos haciendo scroll

        # 2. Si no es markdown, hacer el zoom normal del canvas
        self.zoom = max(self.min_zoom, min(self.max_zoom, self.zoom * (1.1 if event.angleDelta().y() > 0 else 0.9)))
        nx, ny = self.world_to_screen(wx, wy)
        self.offset_x += pos.x() - nx
        self.offset_y += pos.y() - ny
        self.update()

    def mousePressEvent(self, event):
        self.setFocus() # IMPORTANTE: Capturar el foco de teclado al hacer clic
        pos = event.position()
        # Toolbar
        tr = QRectF((self.width() - (config.TOOLBAR_WIDTH_COLLAPSED + (config.TOOLBAR_WIDTH_EXPANDED - config.TOOLBAR_WIDTH_COLLAPSED) * self.toolbar_animation_progress))/2, config.TOOLBAR_MARGIN, config.TOOLBAR_WIDTH_COLLAPSED + (config.TOOLBAR_WIDTH_EXPANDED - config.TOOLBAR_WIDTH_COLLAPSED) * self.toolbar_animation_progress, config.TOOLBAR_HEIGHT_COLLAPSED + (config.TOOLBAR_HEIGHT_EXPANDED - config.TOOLBAR_HEIGHT_COLLAPSED) * self.toolbar_animation_progress)
        if self.toolbar_animation_progress > 0.5:
            for i in range(len(config.TOOL_BUTTONS)):
                brect = QRectF(tr.x() + config.BUTTON_MARGIN, tr.y() + 60 + i * (config.BUTTON_HEIGHT + 10), tr.width() - config.BUTTON_MARGIN*2, config.BUTTON_HEIGHT)
                if brect.contains(pos): self.selected_tool = i; self.create_obj(); return
        
        # Color Circle
        base_circle = QRectF(tr.right() + 10, config.TOOLBAR_MARGIN, config.TOOLBAR_HEIGHT_COLLAPSED, config.TOOLBAR_HEIGHT_COLLAPSED)
        if base_circle.contains(pos): self.circle_expanded = not self.circle_expanded; self._start_anim(); return
        
        if self.circle_expanded:
            for i, btn in enumerate(self.circle_buttons):
                if btn.get("current_rect") and btn["current_rect"].contains(pos):
                    self.active_color = btn["color"]
                    if self.selected_object is not None: self.canvas_objects[self.selected_object]["personal_color"] = btn["color"]
                    self.update(); return
            if not self.current_circle_rect.contains(pos): self.circle_expanded = False; self._start_anim()

        # Vertical Menu
        base_vertical = QRectF(self.current_circle_rect.right() + 10, config.TOOLBAR_MARGIN, config.TOOLBAR_HEIGHT_COLLAPSED, config.TOOLBAR_HEIGHT_COLLAPSED)
        if base_vertical.contains(pos): self.vertical_menu_expanded = not self.vertical_menu_expanded; self._start_anim(); return
        
        if self.vertical_menu_expanded:
            if hasattr(self, "vertical_buttons_rects"):
                for i, rect in enumerate(self.vertical_buttons_rects):
                    if rect.contains(pos): 
                        self.selected_vertical_tool = i if self.selected_vertical_tool != i else None
                        self.update(); return 
            if not self.current_vertical_rect.contains(pos): self.vertical_menu_expanded = False; self._start_anim()

        # Si hay herramienta de dibujo seleccionada
        if self.selected_vertical_tool is not None:
            # Primero ver si estamos pinchando en la UI
            if tr.contains(pos) or self.current_circle_rect.contains(pos) or self.current_vertical_rect.contains(pos):
                pass
            else:
                tool_name = config.VERTICAL_TOOLS[self.selected_vertical_tool]["name"].lower()
                
                if tool_name == "borrador":
                    # MODO BORRADOR VECTORIAL
                    self.is_erasing = True
                    self.perform_eraser_at(pos) # Borrar al hacer clic
                    return
                else:
                    # MODO DIBUJO (Lapicero / Rotulador)
                    
                    # 0. Primero comprobamos si el usuario quiere interactuar con un objeto ya seleccionado (Tiradores)
                    # Esto tiene prioridad sobre dibujar nuevo trazo
                    if self.selected_object is not None and self.selected_object < len(self.canvas_objects):
                        obj = self.canvas_objects[self.selected_object]
                        wx, wy = self.screen_to_world(pos.x(), pos.y())
                        ow, oh = self.get_obj_dims(obj)
                        
                        # Resize Handle
                        hx, hy = obj["x"] + ow/2, obj["y"] + oh/2
                        if abs(wx - hx) < (25/self.zoom) and abs(wy - hy) < (25/self.zoom):
                            self.resizing_object = True
                            self.drag_start_pos = pos
                            return
                            
                        # Delete Handle
                        dx, dy = obj["x"] - ow/2, obj["y"] - oh/2
                        if abs(wx - dx) < (25/self.zoom) and abs(wy - dy) < (25/self.zoom):
                             del self.canvas_objects[self.selected_object]
                             self.selected_object = None
                             self.selected_objects = []
                             self.needs_blur_update = True
                             self.update()
                             return

                    # 1. Comprobamos si quiere seleccionar/mover un objeto existente (incluidos dibujos)
                    wx, wy = self.screen_to_world(pos.x(), pos.y())
                    clicked_obj_idx = None
                    for i in range(len(self.canvas_objects)-1, -1, -1):
                        obj = self.canvas_objects[i]; ox, oy = obj["x"], obj["y"]
                        ow, oh = self.get_obj_dims(obj)
                        if abs(wx-ox)<(ow/2) and abs(wy-oy)<(oh/2):
                            clicked_obj_idx = i
                            break
                    
                    # Si clickamos un objeto dibujo, queremos dibujar DENTRO de él (fusión)
                    if clicked_obj_idx is not None and self.canvas_objects[clicked_obj_idx]["type"] == "dibujo":
                         self.drawing_target_index = clicked_obj_idx
                         # Continuamos abajo para iniciar el trazo...
                    
                    # Si clickamos OTRO tipo de objeto (texto, markdown, etc), queremos seleccionarlo no pintar encima
                    elif clicked_obj_idx is not None:
                        # Salimos de este bloque para que se ejecute la lógica de selección de abajo
                        pass 
                    else:
                        # Si es fondo limpio, iniciamos trazo normal
                        self.is_drawing = True
                        wx, wy = self.screen_to_world(pos.x(), pos.y())
                        self.current_stroke = {
                            "style": tool_name,
                            "width": self.drawing_stroke_width,
                            "color": QColor(self.active_color), 
                            "points": [(wx, wy)]
                        }
                        return

        # Reset dragging flags before starting a new action
        self.dragging = False
        self.dragging_object = False
        self.resizing_object = False
        self.selecting_text = False

        # 1. Comprobar si el clic es en el tirador de redimensionado del objeto seleccionado
        if self.selected_object is not None and self.selected_object < len(self.canvas_objects):
            obj = self.canvas_objects[self.selected_object]
            wx, wy = self.screen_to_world(pos.x(), pos.y())
            ow, oh = self.get_obj_dims(obj)
            
            # Tirador (Resize)
            hx, hy = obj["x"] + ow/2, obj["y"] + oh/2
            if abs(wx - hx) < (25/self.zoom) and abs(wy - hy) < (25/self.zoom):
                self.resizing_object = True
                self.drag_start_pos = pos
                return
            
            # Botón Eliminar (Delete) - Lógica inversa de coordenadas
            dx, dy = obj["x"] - ow/2, obj["y"] - oh/2
            if abs(wx - dx) < (25/self.zoom) and abs(wy - dy) < (25/self.zoom):
                # IMPORTANTE: Los dibujos NO se borran con botón, solo con borrador
                if obj["type"] != "dibujo":
                    del self.canvas_objects[self.selected_object]
                    self.selected_object = None
                    self.selected_objects = []
                    self.needs_blur_update = True
                    self.update()
                    return

        # Canvas Objects
        wx, wy = self.screen_to_world(pos.x(), pos.y())
        for i in range(len(self.canvas_objects)-1, -1, -1):
            obj = self.canvas_objects[i]; ox, oy = obj["x"], obj["y"]
            ow, oh = self.get_obj_dims(obj)
            
            if abs(wx-ox)<(ow/2) and abs(wy-oy)<(oh/2):
                # Si es Markdown o Code, primero ver si es clic de texto o de título
                if obj["type"] in ["markdown", "codigo"]:
                    if wy < (oy - oh/2 + 30 + 15): # Área de título
                        self.selected_object, self.dragging_object, self.drag_start_pos = i, True, pos
                    else: # Área de contenido -> Selección de texto
                        lx = wx - (ox - ow/2 + 15)
                        ly = wy - (oy - oh/2 + 30 + 15) + obj.get("scroll_y", 0)
                        padding = 15 if obj["type"] == "markdown" else 10 # Pequeño ajuste de padding
                        lx = wx - (ox - ow/2 + padding)
                        ly = wy - (oy - oh/2 + 30 + padding) + obj.get("scroll_y", 0)
                        
                        hit_idx = obj["doc"].documentLayout().hitTest(QPointF(lx, ly), Qt.FuzzyHit)
                        obj["sel_start"] = hit_idx
                        obj["sel_end"] = hit_idx
                        self.selected_object = i
                        if i not in self.selected_objects: self.selected_objects = [i] # IMPORTANTE: Actualizar visualmente la selección
                        self.selecting_text = True
                else:
                    self.selected_object, self.dragging_object, self.drag_start_pos = i, True, pos
                    if i not in self.selected_objects:
                        self.selected_objects = [i]
                
                self.update(); return
        
        # Nueva Selección o Paneo
        if event.modifiers() & Qt.ShiftModifier:
            self.selected_objects = []
            self.selected_object, self.dragging, self.last_mouse_pos = None, True, pos
        else:
            self.selected_objects = []
            self.selected_object = None
            self.selection_origin = pos # Guardamos el inicio del rectángulo
            self.selection_rect = QRectF(pos, pos)
        self.update()

    def mouseMoveEvent(self, event):
        pos = event.position()
        tr = QRectF((self.width() - (config.TOOLBAR_WIDTH_COLLAPSED + (config.TOOLBAR_WIDTH_EXPANDED - config.TOOLBAR_WIDTH_COLLAPSED) * self.toolbar_animation_progress))/2, config.TOOLBAR_MARGIN, config.TOOLBAR_WIDTH_COLLAPSED + (config.TOOLBAR_WIDTH_EXPANDED - config.TOOLBAR_WIDTH_COLLAPSED) * self.toolbar_animation_progress, config.TOOLBAR_HEIGHT_COLLAPSED + (config.TOOLBAR_HEIGHT_EXPANDED - config.TOOLBAR_HEIGHT_COLLAPSED) * self.toolbar_animation_progress)
        self.hovered_button = None
        if self.toolbar_animation_progress > 0.5:
            for i in range(len(config.TOOL_BUTTONS)):
                if QRectF(tr.x() + config.BUTTON_MARGIN, tr.y() + 60 + i * (config.BUTTON_HEIGHT + 10), tr.width() - config.BUTTON_MARGIN*2, config.BUTTON_HEIGHT).contains(pos): self.hovered_button = i; break
        self.circle_hovered_button = None
        if self.circle_expanded:
            for i, btn in enumerate(self.circle_buttons):
                if btn.get("current_rect") and btn["current_rect"].contains(pos): self.circle_hovered_button = i; break

        self.vertical_hovered_button = None
        if self.vertical_menu_expanded and hasattr(self, "vertical_buttons_rects"):
            for i, rect in enumerate(self.vertical_buttons_rects):
                if rect.contains(pos): self.vertical_hovered_button = i; break
        
        wx, wy = self.screen_to_world(pos.x(), pos.y())
        dist = ((pos.x() - (tr.x() + tr.width()/2))**2 + (pos.y() - (tr.y() + tr.height()/2))**2)**0.5
        
        # Cambio de cursor según hover
        self.setCursor(Qt.ArrowCursor)
        for i, obj in enumerate(reversed(self.canvas_objects)):
            # Usar índice Real ya que enumerate(reversed) da índices invertidos
            real_idx = len(self.canvas_objects) - 1 - i
            ox, oy = obj["x"], obj["y"]
            ow, oh = self.get_obj_dims(obj)
            
            # Tirador (Solo el actual seleccionado)
            if self.selected_object == real_idx:
                hx, hy = ox + ow/2, oy + oh/2
                if abs(wx - hx) < (25/self.zoom) and abs(wy - hy) < (25/self.zoom):
                    self.setCursor(Qt.SizeFDiagCursor); break

            # Cuerpo
            if abs(wx-ox)<(ow/2) and abs(wy-oy)<(oh/2):
                if obj["type"] in ["ventana", "texto", "markdown", "dibujo", "codigo"]:
                    if obj["type"] in ["markdown", "codigo"] and wy < (oy - oh/2 + 30 + 15):
                        self.setCursor(Qt.ArrowCursor)
                    else:
                        self.setCursor(Qt.IBeamCursor)
                else:
                    self.setCursor(Qt.ArrowCursor)
                break

        if dist < (config.TOOLBAR_HOVER_DISTANCE_COLLAPSE if self.toolbar_expanded else config.TOOLBAR_HOVER_DISTANCE_EXPAND):
            self.setCursor(Qt.ArrowCursor)

        new_e = dist < (config.TOOLBAR_HOVER_DISTANCE_COLLAPSE if self.toolbar_expanded else config.TOOLBAR_HOVER_DISTANCE_EXPAND)
        if new_e != self.toolbar_expanded: self.toolbar_expanded = new_e; self._start_anim()

        if self.is_drawing:
            wx, wy = self.screen_to_world(pos.x(), pos.y())
            self.current_stroke["points"].append((wx, wy))
            self.update(); return

        if self.is_erasing:
            self.perform_eraser_at(pos)
            return

        if self.dragging:
            self.offset_x += pos.x() - self.last_mouse_pos.x(); self.offset_y += pos.y() - self.last_mouse_pos.y()
            self.last_mouse_pos = pos; self.update()
        elif self.selection_rect is not None:
            # Actualizar el rectángulo de selección azul
            self.selection_rect = QRectF(self.selection_origin, pos).normalized()
            # Detectar objetos dentro del rectángulo
            new_selection = []
            for i, obj in enumerate(self.canvas_objects):
                ox, oy = obj["x"], obj["y"]
                screen_pos = QPointF(*self.world_to_screen(ox, oy))
                if self.selection_rect.contains(screen_pos):
                    new_selection.append(i)
            self.selected_objects = new_selection
            self.selected_object = new_selection[-1] if new_selection else None
            self.update()
        elif self.resizing_object:
            pw_x, pw_y = self.screen_to_world(self.drag_start_pos.x(), self.drag_start_pos.y())
            cw_x, cw_y = self.screen_to_world(pos.x(), pos.y())
            obj = self.canvas_objects[self.selected_object]
            
            # Inicializar dimensiones si no existen
            if "w" not in obj:
                if obj["type"] in ["cuadrado", "triangulo"]: obj["w"], obj["h"] = 100, 100
                elif obj["type"] == "ventana": obj["w"], obj["h"] = 200, 150
                elif obj["type"] == "markdown": obj["w"], obj["h"] = 300, 400
                elif obj["type"] == "texto": obj["w"], obj["h"] = 200, 40

            dx = (cw_x - pw_x) * 2
            dy = (cw_y - pw_y) * 2

            if obj["type"] == "triangulo":
                # Escala uniforme balanceada para el triángulo
                delta = (dx + dy) / 2
                obj["w"] = max(40, obj["w"] + delta)
                obj["h"] = max(40, obj["h"] + delta)
            else:
                obj["w"] = max(50, obj["w"] + dx)
                obj["h"] = max(30, obj["h"] + dy)
            
            self.drag_start_pos = pos; self.update()
        elif self.dragging_object:
            pw_x, pw_y = self.screen_to_world(self.drag_start_pos.x(), self.drag_start_pos.y())
            cw_x, cw_y = self.screen_to_world(pos.x(), pos.y())
            dx, dy = cw_x - pw_x, cw_y - pw_y
            # Mover TODOS los objetos seleccionados
            for idx in self.selected_objects:
                self.canvas_objects[idx]["x"] += dx
                self.canvas_objects[idx]["y"] += dy
            self.drag_start_pos = pos; self.update()
        elif getattr(self, "selecting_text", False) and self.selected_object is not None:
            obj = self.canvas_objects[self.selected_object]
            if obj["type"] in ["markdown", "codigo"]:
                ow, oh = self.get_obj_dims(obj)
                padding = 15 if obj["type"] == "markdown" else 10
                lx = wx - (obj["x"] - ow/2 + padding)
                ly = wy - (obj["y"] - oh/2 + 30 + padding) + obj.get("scroll_y", 0)
                hit_idx = obj["doc"].documentLayout().hitTest(QPointF(lx, ly), Qt.FuzzyHit)
                obj["sel_end"] = hit_idx
                self.update()

    def mouseReleaseEvent(self, event): 
        if self.is_drawing and self.current_stroke:
            self.is_drawing = False
            points = self.current_stroke["points"]
            if len(points) > 2:
                # CASO A: Añadir a objeto existente y redimensionar
                if self.drawing_target_index is not None and self.drawing_target_index < len(self.canvas_objects):
                    target_obj = self.canvas_objects[self.drawing_target_index]
                    
                    # 1. Recuperar todos los trazos en coordenadas MUNDIALES
                    all_strokes_world = []
                    
                    # Trazos existentes
                    tox, toy = target_obj["x"], target_obj["y"]
                    for s in target_obj.get("strokes", []):
                        world_pts = [(p[0] + tox, p[1] + toy) for p in s["points"]]
                        all_strokes_world.append({"style": s["style"], "width": s["width"], "color": s.get("color"), "points": world_pts})
                    
                    # Nuevo trazo (ya está en mundial)
                    new_s_copy = self.current_stroke.copy() # Copia para no alterar el original referencia
                    all_strokes_world.append(new_s_copy)
                    
                    # 2. Calcular nueva caja englobante de TODO
                    all_x, all_y = [], []
                    for s in all_strokes_world:
                        for p in s["points"]:
                            all_x.append(p[0]); all_y.append(p[1])
                    
                    min_x, max_x = min(all_x), max(all_x)
                    min_y, max_y = min(all_y), max(all_y)
                    
                    new_cx, new_cy = (min_x + max_x) / 2, (min_y + max_y) / 2
                    new_w = max_(100, max_x - min_x + 40) # Padding
                    new_h = max_(100, max_y - min_y + 40)
                    
                    # 3. Re-convertir todo a coordenadas LOCALES del nuevo centro
                    final_strokes = []
                    for s in all_strokes_world:
                        local_pts = [(p[0] - new_cx, p[1] - new_cy) for p in s["points"]]
                        s["points"] = local_pts
                        final_strokes.append(s)
                    
                    # 4. Actualizar objeto
                    target_obj["x"], target_obj["y"] = new_cx, new_cy
                    target_obj["w"], target_obj["h"] = new_w, new_h
                    target_obj["strokes"] = final_strokes
                    
                # CASO B: Crear nuevo objeto independiente
                else: 
                    # Calcular caja y centro
                    wxs = [p[0] for p in points]
                    wys = [p[1] for p in points]
                    min_x, max_x = min(wxs), max(wxs)
                    min_y, max_y = min(wys), max(wys)
                    cx, cy = (min_x + max_x) / 2, (min_y + max_y) / 2
                    
                    # Convertir puntos a locales (relativos al centro)
                    local_points = [(p[0] - cx, p[1] - cy) for p in points]
                    self.current_stroke["points"] = local_points
                    
                    new_obj = {
                        "type": "dibujo",
                        "x": cx, "y": cy,
                        "w": max(100, max_x - min_x + 40), "h": max(100, max_y - min_y + 40),
                        "strokes": [self.current_stroke]
                    }
                    self.canvas_objects.append(new_obj)
                
                self.needs_blur_update = True
            
            self.current_stroke = None
            self.drawing_target_index = None # Reset
            self.update()

        self.is_erasing = False
        self.dragging = self.dragging_object = self.resizing_object = False
        self.selecting_text = False
        self.selection_rect = None
        self.update()

    def perform_eraser_at(self, pos):
        """Elimina trazos individuales dentro de objetos de dibujo"""
        wx, wy = self.screen_to_world(pos.x(), pos.y())
        eraser_radius = 20 / self.zoom 
        
        indices_to_delete = []
        something_changed = False
        
        for i, obj in enumerate(self.canvas_objects):
            if obj["type"] != "dibujo": continue
            
            # 1. Caja rápida (si no estamos ni cerca, saltar)
            ox, oy = obj["x"], obj["y"]
            ow, oh = self.get_obj_dims(obj)
            if not (ox - ow/2 - eraser_radius < wx < ox + ow/2 + eraser_radius and 
                    oy - oh/2 - eraser_radius < wy < oy + oh/2 + eraser_radius):
                continue
            
            # 2. Filtrar trazos que NO colisionan con el borrador
            new_strokes = []
            strokes_changed_here = False
            
            for stroke in obj.get("strokes", []):
                stroke_hit = False
                for px, py in stroke.get("points", []):
                    # px, py son locales
                    gpx = ox + px
                    gpy = oy + py
                    if (gpx - wx)**2 + (gpy - wy)**2 < eraser_radius**2:
                        stroke_hit = True
                        break
                
                if not stroke_hit:
                    new_strokes.append(stroke)
                else:
                    strokes_changed_here = True
            
            if strokes_changed_here:
                obj["strokes"] = new_strokes
                something_changed = True
                if not new_strokes:
                    indices_to_delete.append(i)
        
        if indices_to_delete:
            for i in sorted(indices_to_delete, reverse=True):
                del self.canvas_objects[i]
            something_changed = True
            
        if something_changed:
            self.needs_blur_update = True
            self.update()

    # --- DRAG & DROP ---
    def dragEnterEvent(self, event):
        if event.mimeData().hasUrls(): event.acceptProposedAction()

    def dropEvent(self, event):
        urls = event.mimeData().urls()
        if not urls: return
        
        pos = event.position()
        count = 0
        for url in urls:
            path = url.toLocalFile()
            ext = path.lower()
            if ext.endswith(('.png', '.jpg', '.jpeg', '.bmp', '.gif', '.webp')):
                wx, wy = self.screen_to_world(pos.x() + count*20, pos.y() + count*20)
                pixmap = QPixmap(path)
                if not pixmap.isNull():
                    new_obj = {
                        "type": "imagen",
                        "x": wx,
                        "y": wy,
                        "path": path,
                        "pixmap": pixmap,
                        "w": pixmap.width(),
                        "h": pixmap.height()
                    }
                    self.canvas_objects.append(new_obj)
                    count += 1
            elif ext.endswith('.md'):
                wx, wy = self.screen_to_world(pos.x() + count*20, pos.y() + count*20)
                try:
                    with open(path, 'r', encoding='utf-8') as f:
                        content = f.read()
                    
                    new_obj = {
                        "type": "markdown",
                        "x": wx,
                        "y": wy,
                        "path": path,
                        "content": content,
                        "title": path.split('/')[-1]
                    }
                    self.canvas_objects.append(new_obj)
                    count += 1
                except Exception as e:
                    print(f"Error reading md file: {e}")
            elif ext.endswith(('.py', '.c', '.cpp', '.h', '.hpp', '.js', '.ts', '.html', '.css', '.json', '.xml', '.java', '.txt', '.sh')):
                wx, wy = self.screen_to_world(pos.x() + count*20, pos.y() + count*20)
                try:
                    with open(path, 'r', encoding='utf-8') as f:
                        content = f.read()
                    
                    new_obj = {
                        "type": "codigo",
                        "x": wx,
                        "y": wy,
                        "path": path,
                        "content": content,
                        "title": path.split('/')[-1],
                        "ext": "." + path.split('.')[-1] if '.' in path else ""
                    }
                    self.canvas_objects.append(new_obj)
                    count += 1
                except Exception as e:
                    print(f"Error reading code file: {e}")
        
        if count > 0: self.update()

    def _start_anim(self): 
        if not self.is_animating: self.animation_timer.start(); self.is_animating = True

    def create_obj(self):
        wx, wy = self.screen_to_world(self.width()/2, self.height()/2)
        tool = config.TOOL_BUTTONS[self.selected_tool]["name"]
        t = tool.lower().replace(" ", "_")
        if t == "texto_en_pantalla": t = "texto"
        elif t == "cuadrado": t = "cuadrado"
        new_obj = {"type": t, "x": wx, "y": wy}
        if t != "texto": new_obj["personal_color"] = QColor(self.active_color)
        if t == "ventana": new_obj["title"] = "Ventana"
        if t == "texto": new_obj["text"] = "" # Iniciamos vacío para que salga el placeholder
        self.canvas_objects.append(new_obj); self.update()

    def keyPressEvent(self, event):
        if event.key() == Qt.Key_Escape: self.window().close()
        
        # Lógica de escritura en objetos seleccionados
        if self.selected_object is not None:
            obj = self.canvas_objects[self.selected_object]
            
            # Lógica de Borrado (Backspace / Delete)
            is_delete = event.key() in [Qt.Key_Delete, Qt.Key_Backspace]
            
            if is_delete:
                # 1. Si hay texto, borramos el último caracter
                if obj["type"] == "ventana" and obj.get("content"):
                    obj["content"] = obj["content"][:-1]
                elif obj["type"] == "texto" and obj.get("text"):
                    obj["text"] = obj["text"][:-1]
                else:
                    # 2. Si NO hay texto (o es otro tipo de objeto), eliminamos el objeto entero
                    if self.selected_object < len(self.canvas_objects):
                        del self.canvas_objects[self.selected_object]
                        self.selected_object = None
                
                self.update()
                return

            # Lógica de Salto de Línea (Enter)
            if event.key() in [Qt.Key_Return, Qt.Key_Enter]:
                if obj["type"] in ["ventana", "texto"]:
                    key = "content" if obj["type"] == "ventana" else "text"
                    obj[key] = obj.get(key, "") + "\n"
                    self.update()
                return

            # Capturar texto normal
            text = event.text()
            if text and text.isprintable():
                if obj["type"] == "ventana":
                    obj["content"] = obj.get("content", "") + text
                    self.update()
                elif obj["type"] == "texto":
                    obj["text"] = obj.get("text", "") + text
                    self.update()
