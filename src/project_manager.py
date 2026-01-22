import os
import shutil
import json
from PySide6.QtGui import QColor, QPixmap
from PySide6.QtCore import QPointF

import os
import re
import shutil
import json
from PySide6.QtGui import QColor, QPixmap
from PySide6.QtCore import QPointF

class TreeParser:
    def __init__(self, canvas, project_dir):
        self.canvas = canvas
        self.project_dir = project_dir
        self.variables = {}
        self.templates = {}
        
        self.current_obj = None
        self.current_template_name = None
        self.current_template_lines = []
        self.current_text_block = None
        self.current_text_indent = 0

    def evaluate(self, expr):
        """Evalúa expresiones matemáticas y sustituye variables"""
        if not isinstance(expr, str): return expr
        
        # Sustitución de variables: $var_name
        # Usamos regex para evitar sustituciones parciales (ej: $v en $var)
        for var in sorted(self.variables.keys(), key=len, reverse=True):
            placeholder = f"${var}"
            if placeholder in expr:
                expr = expr.replace(placeholder, str(self.variables[var]))
        
        # Si parece una expresión matemática (contiene operadores)
        if any(op in expr for op in "+-*/") or re.match(r'^\d', expr.strip()):
            # Limpiar para seguridad (solo números, puntos, operadores y paréntesis)
            clean_expr = re.sub(r'[^0-9\.\+\-\*\/\(\)\s]', '', expr)
            try:
                # eval seguro con entorno limitado
                if clean_expr.strip():
                    return eval(clean_expr, {"__builtins__": None}, {})
            except:
                pass
        
        return expr

    def parse_file(self, filepath):
        if not os.path.exists(filepath): return
        
        with open(filepath, 'r', encoding='utf-8') as f:
            lines = f.readlines()
        
        self.canvas.canvas_objects = []
        
        idx = 0
        while idx < len(lines):
            line = lines[idx]
            stripped = line.strip()
            
            # 1. Comentarios y vacíos
            if not stripped or stripped.startswith("#"):
                idx += 1
                continue
            
            # 2. Definición de Variables ($VAR name = value)
            if stripped.startswith("$VAR"):
                match = re.match(r'\$VAR\s+(\w+)\s*=\s*(.*)', stripped)
                if match:
                    name, val_expr = match.groups()
                    self.variables[name] = self.evaluate(val_expr)
                idx += 1
                continue

            # 3. Definición de Plantillas ($DEF [NAME])
            if stripped.startswith("$DEF"):
                match = re.match(r'\$DEF\s+\[(\w+)\]', stripped)
                if match:
                    t_name = match.group(1)
                    idx += 1
                    t_lines = []
                    # Leer hasta encontrar una línea con menos sangría que las propiedades
                    while idx < len(lines):
                        if lines[idx].strip() and not lines[idx].startswith("  "):
                            break
                        t_lines.append(lines[idx])
                        idx += 1
                    self.templates[t_name] = t_lines
                    continue
            
            # 4. Detección de Bloque de Objeto o Instancia (> [TIPO])
            if line.startswith(">"):
                self._flush_object()
                
                parts = stripped.split("]", 1)
                obj_type_raw = parts[0][2:].strip().upper()
                title = parts[1].strip() if len(parts) > 1 else "Object"
                
                # Caso especial: Instancia de plantilla [USE:NAME]
                if obj_type_raw.startswith("USE:"):
                    template_name = obj_type_raw.split(":", 1)[1]
                    if template_name in self.templates:
                        # Crear objeto base de la plantilla
                        self.current_obj = {"type": "cuadrado", "title": title} # Default
                        # Aplicar líneas de la plantilla como si fueran del archivo
                        self._process_properties(self.templates[template_name])
                    else:
                        print(f"Warning: Template {template_name} not found")
                        self.current_obj = {"type": "placeholder", "title": f"ERR: {template_name}"}
                else:
                    self.current_obj = {"type": obj_type_raw.lower(), "title": title}
                
                idx += 1
                continue

            # 5. Propiedades del objeto actual
            if self.current_obj is not None:
                # Si estamos en un bloque de texto multilínea
                if self.current_text_block:
                    indent = len(line) - len(line.lstrip())
                    if indent >= self.current_text_indent:
                        self.current_obj[self.current_text_block] += line[self.current_text_indent:].rstrip() + "\n"
                        idx += 1
                        continue
                    else:
                        self.current_text_block = None

                # Propiedad normal clave: valor
                if ":" in stripped:
                    self._parse_property_line(stripped)
                
            idx += 1
            
        self._flush_object()
        self.canvas.update()

    def _process_properties(self, lines):
        """Procesa una lista de líneas de propiedades (usado para plantillas)"""
        for line in lines:
            stripped = line.strip()
            if ":" in stripped:
                self._parse_property_line(stripped)

    def _parse_property_line(self, stripped):
        key, value = stripped.split(":", 1)
        key = key.strip()
        value = value.strip()
        
        if key in ["x", "y", "w", "h"]:
            res = self.evaluate(value)
            try: self.current_obj[key] = float(res)
            except: self.current_obj[key] = 0.0
        
        elif key == "color":
            try:
                # El valor del color también puede usar variables para componentes
                processed_val = str(self.evaluate(value))
                rgba = list(map(int, processed_val.split(",")))
                self.current_obj["personal_color"] = QColor(*rgba)
            except:
                self.current_obj["personal_color"] = QColor(200, 200, 200, 255)
        
        elif key == "ext":
            self.current_obj["ext"] = value
        
        elif key == "path":
            full_path = os.path.join(self.project_dir, value)
            self.current_obj["path"] = full_path
            
            if self.current_obj["type"] == "imagen":
                if os.path.exists(full_path):
                    pix = QPixmap(full_path)
                    self.current_obj["pixmap"] = pix
                    if "w" not in self.current_obj: self.current_obj["w"] = pix.width()
                    if "h" not in self.current_obj: self.current_obj["h"] = pix.height()
                else:
                    self.current_obj["missing_asset"] = True
            
            elif self.current_obj["type"] == "dibujo":
                if os.path.exists(full_path):
                    try:
                        with open(full_path, 'r') as df:
                            strokes_data = json.load(df)
                        strokes = []
                        for s in strokes_data:
                            c = s.get("color", [255,255,255,255])
                            col = QColor(c[0], c[1], c[2], c[3])
                            strokes.append({
                                "style": s["style"],
                                "width": s["width"],
                                "color": col,
                                "points": [tuple(p) for p in s["points"]]
                            })
                        self.current_obj["strokes"] = strokes
                    except:
                        pass

        elif key in ["content", "text"] and value == "|":
            self.current_text_block = key
            self.current_obj[key] = ""
            self.current_text_indent = 4

    def _flush_object(self):
        if self.current_obj:
            # Validaciones básicas antes de añadir
            if "x" not in self.current_obj: self.current_obj["x"] = 0.0
            if "y" not in self.current_obj: self.current_obj["y"] = 0.0
            self.canvas.canvas_objects.append(self.current_obj)
            self.current_obj = None

class ProjectManager:
    @staticmethod
    def save_project(canvas, filepath):
        """Guarda el estado del canvas en un archivo .tree y sus assets"""
        project_dir = os.path.dirname(filepath)
        filename = os.path.basename(filepath)
        project_name = os.path.splitext(filename)[0]
        
        img_dir = os.path.join(project_dir, "imagenes")
        drawings_dir = os.path.join(project_dir, "drawings")
        os.makedirs(img_dir, exist_ok=True)
        os.makedirs(drawings_dir, exist_ok=True)
        
        script_content = f"# Tree Project: {project_name}\n# Generated by Tree Software\n\n"
        
        for i, obj in enumerate(canvas.canvas_objects):
            obj_type = obj["type"]
            script_content += f"> [{obj_type.upper()}] {obj.get('title', f'Object {i}')}\n"
            
            script_content += f"  x: {obj['x']:.2f}\n"
            script_content += f"  y: {obj['y']:.2f}\n"
            if "w" in obj: script_content += f"  w: {obj['w']:.2f}\n"
            if "h" in obj: script_content += f"  h: {obj['h']:.2f}\n"
            
            if "personal_color" in obj and isinstance(obj["personal_color"], QColor):
                c = obj["personal_color"]
                script_content += f"  color: {c.red()},{c.green()},{c.blue()},{c.alpha()}\n"

            if obj_type in ["ventana", "texto", "markdown", "codigo"]:
                content_key = "text" if obj_type == "texto" else "content"
                content = obj.get(content_key, "")
                if obj_type == "codigo" and "ext" in obj:
                    script_content += f"  ext: {obj['ext']}\n"

                script_content += f"  {content_key}: |\n"
                for line in content.splitlines():
                    script_content += f"    {line}\n"
            
            elif obj_type == "imagen":
                original_path = obj.get("path")
                if original_path and os.path.exists(original_path):
                    img_name = os.path.basename(original_path)
                    dest_path = os.path.join(img_dir, img_name)
                    try:
                        if original_path != dest_path:
                            shutil.copy2(original_path, dest_path)
                        script_content += f"  path: imagenes/{img_name}\n"
                    except:
                         script_content += f"  path: {original_path}\n"
            
            elif obj_type == "dibujo":
                strokes_filename = f"drawing_{i}.json"
                strokes_path = os.path.join(drawings_dir, strokes_filename)
                
                strokes_data = []
                for stroke in obj.get("strokes", []):
                    s_data = {
                        "style": stroke.get("style", "lapicero"),
                        "width": stroke.get("width", 2),
                        "points": stroke.get("points", [])
                    }
                    sc = stroke.get("color")
                    if isinstance(sc, QColor):
                        s_data["color"] = [sc.red(), sc.green(), sc.blue(), sc.alpha()]
                    else:
                         s_data["color"] = [255, 255, 255, 255]
                    strokes_data.append(s_data)
                
                with open(strokes_path, 'w') as f:
                    json.dump(strokes_data, f)
                
                script_content += f"  path: drawings/{strokes_filename}\n"
            
            script_content += "\n"

        with open(filepath, 'w', encoding='utf-8') as f:
            f.write(script_content)

    @staticmethod
    def load_project(canvas, filepath):
        """Carga un proyecto desde un archivo .tree utilizando TreeParser"""
        if not os.path.exists(filepath): return
        project_dir = os.path.dirname(filepath)
        parser = TreeParser(canvas, project_dir)
        parser.parse_file(filepath)
