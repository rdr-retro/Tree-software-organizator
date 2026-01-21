import sys
from PySide6.QtWidgets import QWidget
from PySide6.QtCore import Qt, QPointF, QTimer, QRectF
from PySide6.QtGui import QPainter, QPen, QColor, QWheelEvent, QMouseEvent, QBrush, QPixmap

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
        self.active_color = QColor(40, 40, 50, 230)
        self.current_circle_radius = config.TOOLBAR_HEIGHT_COLLAPSED / 2
        
        # Objects
        self.canvas_objects = []
        self.selected_object = None
        self.dragging_object = False
        self.selecting_text = False
        self.resizing_object = False
        self.is_animating = False
        
        # Buffers de Renderizado (El corazón del sistema)
        self.world_pixmap = None      # Captura de cuadrícula y objetos sólidos
        self.blurred_pixmap = None    # Versión Gaussiana del mundo
        
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

    def update_animation(self):
        speed = 0.15
        t_target = 1.0 if self.toolbar_expanded else 0.0
        c_target = 1.0 if self.circle_expanded else 0.0
        
        self.toolbar_animation_progress += (t_target - self.toolbar_animation_progress) * speed
        self.circle_animation_progress += (c_target - self.circle_animation_progress) * speed
        
        init_r = config.TOOLBAR_HEIGHT_COLLAPSED / 2
        self.current_circle_radius = init_r - (init_r - 25) * self.circle_animation_progress
        
        if abs(self.toolbar_animation_progress - t_target) < 0.01 and abs(self.circle_animation_progress - c_target) < 0.01:
            self.toolbar_animation_progress, self.circle_animation_progress = t_target, c_target
            self.animation_timer.stop()
            self.is_animating = False
        self.update()

    def paintEvent(self, event):
        if self.width() <= 0 or self.height() <= 0: return
        
        painter = QPainter(self)
        painter.setRenderHint(QPainter.Antialiasing)
        
        # --- CAPA 1: FONDO Y CUADRÍCULA + OBJETOS SÓLIDOS (Imágenes) ---
        world_pix = QPixmap(self.size())
        world_pix.fill(config.BG_COLOR)
        wp = QPainter(world_pix)
        wp.setRenderHint(QPainter.Antialiasing)
        
        # 1.1 Dibujar Cuadrícula
        spacing = 100 * self.zoom
        wp.setPen(QPen(config.GRID_COLOR, 2))
        ox = (self.offset_x + self.width()/2) % spacing
        oy = (self.offset_y + self.height()/2) % spacing
        x = ox
        while x < self.width(): wp.drawLine(int(x), 0, int(x), self.height()); x += spacing
        y = oy
        while y < self.height(): wp.drawLine(0, int(y), self.width(), int(y)); y += spacing
        
        # 1.2 Dibujar Imágenes (Son sólidos, para que el cristal los desenfoque)
        for i, obj in enumerate(self.canvas_objects):
            if obj["type"] == "imagen":
                canvas_objects.draw_image_object(wp, obj, i, self.selected_object, self.zoom, self.world_to_screen)
        wp.end()
        
        # --- CAPA 2: DESENFOQUE DE TODO LO SÓLIDO (Fondo + Imágenes) ---
        full_solids_blur = utils.apply_gaussian_blur(world_pix, config.GLASS_BLUR_RADIUS)
        
        # --- CAPA 3: DIBUJAR ESCENARIO COMPLETO (Sólidos + Cristales) ---
        full_scene_pix = QPixmap(self.size())
        full_scene_pix.fill(Qt.transparent)
        sp = QPainter(full_scene_pix)
        sp.setRenderHint(QPainter.Antialiasing)
        
        # Dibujamos el fondo ya con imágenes nítidas
        sp.drawPixmap(0, 0, world_pix)
        
        # Dibujamos los objetos de cristal y el texto (que ahora tiene fondo de cristal)
        for i, obj in enumerate(self.canvas_objects):
            t = obj["type"]
            if t == "cuadrado":
                canvas_objects.draw_rounded_rect(sp, obj, i, self.selected_object, self.zoom, self.world_to_screen, full_solids_blur)
            elif t == "triangulo":
                canvas_objects.draw_triangle(sp, obj, i, self.selected_object, self.zoom, self.world_to_screen, full_solids_blur)
            elif t == "ventana":
                canvas_objects.draw_window(sp, obj, i, self.selected_object, self.zoom, self.world_to_screen, full_solids_blur)
            elif t == "texto":
                canvas_objects.draw_text_object(sp, obj, i, self.selected_object, self.zoom, self.world_to_screen, config.TEXT_COLOR, full_solids_blur)
            elif t == "markdown":
                canvas_objects.draw_markdown_object(sp, obj, i, self.selected_object, self.zoom, self.world_to_screen, full_solids_blur)
        sp.end()
        
        # --- CAPA 4: DESENFOQUE FINAL PARA UI (Contiene TODO) ---
        final_blur_map = utils.apply_gaussian_blur(full_scene_pix, config.GLASS_BLUR_RADIUS)
        
        # --- CAPA 5: DIBUJO A PANTALLA ---
        # 5.1 Dibujar la escena completa tal cual
        painter.drawPixmap(0, 0, full_scene_pix)
        
        # 5.2 Dibujar Interfaz (Usa final_blur_map para desenfocar TODO)
        tw = config.TOOLBAR_WIDTH_COLLAPSED + (config.TOOLBAR_WIDTH_EXPANDED - config.TOOLBAR_WIDTH_COLLAPSED) * self.toolbar_animation_progress
        th = config.TOOLBAR_HEIGHT_COLLAPSED + (config.TOOLBAR_HEIGHT_EXPANDED - config.TOOLBAR_HEIGHT_COLLAPSED) * self.toolbar_animation_progress
        toolbar_rect = QRectF((self.width() - tw)/2, config.TOOLBAR_MARGIN, tw, th)
        
        cw = config.TOOLBAR_HEIGHT_COLLAPSED + (config.CIRCLE_EXPANDED_WIDTH - config.TOOLBAR_HEIGHT_COLLAPSED) * self.circle_animation_progress
        ch = config.TOOLBAR_HEIGHT_COLLAPSED + (config.CIRCLE_EXPANDED_HEIGHT - config.TOOLBAR_HEIGHT_COLLAPSED) * self.circle_animation_progress
        circle_rect = QRectF(toolbar_rect.right() + 10, config.TOOLBAR_MARGIN, cw, ch)
        self.current_circle_rect = circle_rect
        
        # La interfaz ahora desenfoca tanto la cuadrícula como los objetos debajo
        toolbar.draw_color_palette(painter, self, circle_rect, self.circle_animation_progress, final_blur_map)
        toolbar.draw_toolbar_island(painter, self, toolbar_rect, final_blur_map)
        
        if self.toolbar_animation_progress > 0.3:
            toolbar.draw_tool_buttons(painter, self, toolbar_rect, (self.toolbar_animation_progress - 0.3) / 0.7)
        
        self.draw_ui_info(painter)



    def draw_ui_info(self, painter):
        painter.setPen(QPen(config.TEXT_COLOR))
        painter.drawText(10, 30, f"Zoom: {self.zoom:.2f}x")
        y = self.height() - 80
        for line in ["Rueda: Zoom", "Click Izq: Pan", "ESC: Salir", "DEL: Eliminar"]:
            painter.drawText(10, y, line); y += 25

    # --- EVENTOS ---
    def wheelEvent(self, event):
        pos = event.position()
        wx, wy = self.screen_to_world(pos.x(), pos.y())
        
        # 1. Comprobar si estamos sobre un objeto markdown para hacer scroll
        for obj in reversed(self.canvas_objects):
            if obj["type"] == "markdown":
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

        # 1. Comprobar si el clic es en el tirador de redimensionado del objeto seleccionado
        if self.selected_object is not None:
            obj = self.canvas_objects[self.selected_object]
            wx, wy = self.screen_to_world(pos.x(), pos.y())
            # Tamaño en mundo
            ow = obj.get("w", 100 if obj["type"] in ["cuadrado", "triangulo"] else (200 if obj["type"]=="ventana" else (300 if obj["type"]=="markdown" else obj.get("w_orig", 100))))
            oh = obj.get("h", 100 if obj["type"] in ["cuadrado", "triangulo"] else (150 if obj["type"]=="ventana" else (400 if obj["type"]=="markdown" else obj.get("h_orig", 100))))
            
            hx, hy = obj["x"] + ow/2, obj["y"] + oh/2
            if abs(wx - hx) < (15/self.zoom) and abs(wy - hy) < (15/self.zoom):
                self.resizing_object = True
                self.drag_start_pos = pos
                return

        # Canvas Objects
        wx, wy = self.screen_to_world(pos.x(), pos.y())
        for i in range(len(self.canvas_objects)-1, -1, -1):
            obj = self.canvas_objects[i]; ox, oy = obj["x"], obj["y"]
            
            # Caso especial: Selección de texto en Markdown
            if obj["type"] == "markdown":
                mw, mh = obj.get("w", 300), obj.get("h", 400)
                if abs(wx-ox)<(mw/2) and abs(wy-oy)<(mh/2):
                    # Si pinchamos en el área de título (arriba), permitimos arrastrar el objeto
                    if wy < (oy - mh/2 + 30 + 15): 
                        self.selected_object, self.dragging_object, self.drag_start_pos = i, True, pos
                        self.update(); return
                    
                    # Si pinchamos en el contenido, iniciamos selección de texto
                    lx = wx - (ox - mw/2 + 15)
                    ly = wy - (oy - mh/2 + 30 + 15) + obj.get("scroll_y", 0)
                    hit_idx = obj["doc"].documentLayout().hitTest(QPointF(lx, ly), Qt.FuzzyHit)
                    obj["sel_start"] = hit_idx
                    obj["sel_end"] = hit_idx
                    self.selected_object = i
                    self.selecting_text = True
                    self.update(); return

            # Colisión genérica basada en dimensiones reales
            ow = obj.get("w", 100 if obj["type"] in ["cuadrado", "triangulo"] else (200 if obj["type"]=="ventana" else (300 if obj["type"]=="markdown" else (obj.get("w_orig", 100) if obj["type"]=="imagen" else 100))))
            oh = obj.get("h", 100 if obj["type"] in ["cuadrado", "triangulo"] else (150 if obj["type"]=="ventana" else (400 if obj["type"]=="markdown" else (obj.get("h_orig", 100) if obj["type"]=="imagen" else 40))))
            
            if abs(wx-ox)<(ow/2) and abs(wy-oy)<(oh/2):
                self.selected_object, self.dragging_object, self.drag_start_pos = i, True, pos; self.update(); return
        
        self.selected_object, self.dragging, self.last_mouse_pos = None, True, pos

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
        
        wx, wy = self.screen_to_world(pos.x(), pos.y())
        dist = ((pos.x() - (tr.x() + tr.width()/2))**2 + (pos.y() - (tr.y() + tr.height()/2))**2)**0.5
        
        # Cambio de cursor según hover
        over_editable = False
        over_resize = False
        for obj in self.canvas_objects:
            ox, oy = obj["x"], obj["y"]
            ow = obj.get("w", 100 if obj["type"] in ["cuadrado", "triangulo"] else (200 if obj["type"]=="ventana" else (300 if obj["type"]=="markdown" else 100)))
            oh = obj.get("h", 100 if obj["type"] in ["cuadrado", "triangulo"] else (150 if obj["type"]=="ventana" else (400 if obj["type"]=="markdown" else 40)))
            
            # Hover sobre el tirador de redimensionado
            hx, hy = ox + ow/2, oy + oh/2
            if abs(wx - hx) < (15/self.zoom) and abs(wy - hy) < (15/self.zoom):
                over_resize = True; break

            if (obj["type"] == "ventana" and abs(wx-ox)<(ow/2) and abs(wy-oy)<(oh/2)) or (obj["type"]=="texto" and abs(wx-ox)<(ow/2) and abs(wy-oy)<(oh/2)) or (obj["type"] == "markdown" and abs(wx-ox)<(ow/2) and abs(wy-oy)<(oh/2)):
                over_editable = True; break
        
        if over_resize:
            self.setCursor(Qt.SizeFDiagCursor)
        elif over_editable:
            self.setCursor(Qt.IBeamCursor)
        elif dist < (config.TOOLBAR_HOVER_DISTANCE_COLLAPSE if self.toolbar_expanded else config.TOOLBAR_HOVER_DISTANCE_EXPAND):
            self.setCursor(Qt.ArrowCursor)
        else:
            self.setCursor(Qt.ArrowCursor)

        new_e = dist < (config.TOOLBAR_HOVER_DISTANCE_COLLAPSE if self.toolbar_expanded else config.TOOLBAR_HOVER_DISTANCE_EXPAND)
        if new_e != self.toolbar_expanded: self.toolbar_expanded = new_e; self._start_anim()

        if self.dragging:
            self.offset_x += pos.x() - self.last_mouse_pos.x(); self.offset_y += pos.y() - self.last_mouse_pos.y()
            self.last_mouse_pos = pos; self.update()
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
            self.canvas_objects[self.selected_object]["x"] += cw_x - pw_x
            self.canvas_objects[self.selected_object]["y"] += cw_y - pw_y
            self.drag_start_pos = pos; self.update()
        elif getattr(self, "selecting_text", False) and self.selected_object is not None:
            obj = self.canvas_objects[self.selected_object]
            if obj["type"] == "markdown":
                mw, mh = obj.get("w", 300), obj.get("h", 400)
                lx = wx - (obj["x"] - mw/2 + 15)
                ly = wy - (obj["y"] - mh/2 + 30 + 15) + obj.get("scroll_y", 0)
                hit_idx = obj["doc"].documentLayout().hitTest(QPointF(lx, ly), Qt.FuzzyHit)
                obj["sel_end"] = hit_idx
                self.update()

    def mouseReleaseEvent(self, event): 
        self.dragging = self.dragging_object = self.resizing_object = False
        self.selecting_text = False

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
