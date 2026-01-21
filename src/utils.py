from PySide6.QtCore import Qt
from PySide6.QtGui import QColor, QPixmap, QPainter
from PySide6.QtWidgets import QGraphicsBlurEffect, QGraphicsScene, QGraphicsPixmapItem
import config

def apply_gaussian_blur(pixmap, radius):
    """Aplica un desenfoque ultra-profundo manteniendo una resolución nítida (Anti-aliasing HD)."""
    if pixmap.isNull(): return pixmap
    
    w, h = pixmap.width(), pixmap.height()
    img = pixmap.toImage()
    
    # Técnica de 3 capas progresivas para evitar pixelado en dibujos grandes
    # Paso 1: Suavizado estructural (HD)
    s1 = img.scaled(w // 2, h // 2, Qt.IgnoreAspectRatio, Qt.SmoothTransformation)
    s1 = s1.scaled(w, h, Qt.IgnoreAspectRatio, Qt.SmoothTransformation)
    
    # Paso 2: Difusión de color (SD)
    s2 = s1.scaled(w // 4, h // 4, Qt.IgnoreAspectRatio, Qt.SmoothTransformation)
    s2 = s2.scaled(w, h, Qt.IgnoreAspectRatio, Qt.SmoothTransformation)
    
    # Paso 3: Profundidad Bokeh (Capa final de mezcla)
    # Al procesar sobre s2 ya suavizado, eliminamos el banding y el pixelado
    s3 = s2.scaled(w // 8, h // 8, Qt.IgnoreAspectRatio, Qt.SmoothTransformation)
    final_img = s3.scaled(w, h, Qt.IgnoreAspectRatio, Qt.SmoothTransformation)
    
    return QPixmap.fromImage(final_img)


def get_contrast_color(color):
    """Calcula un color complementario elegante"""
    h, s, v, a = color.getHsvF()
    new_h = (h + 0.5) % 1.0
    new_s = min(s, 0.45) 
    new_v = 0.95 if v < 0.6 else 0.35
    return QColor.fromHsvF(new_h, new_s, new_v)
