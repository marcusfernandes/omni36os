"""Cache de miniaturas para capas de jogos e screenshots.

Gera miniaturas redimensionadas uma vez e as guarda, para não decodificar imagens
grandes no laço de desenho do menu. Cada miniatura é de no máximo 256px, o que
reduz drasticamente o tempo de IMG_Load e SDL_CreateTextureFromSurface.
"""
import hashlib
import os

import omni

THUMB_DIR = f"{omni.HOME}/.config/omni36os/thumbs"
THUMB_SIZE = 256
THUMB_QUALITY = 85


def ensure_thumb_dir():
    """Cria a pasta de cache se não existir."""
    try:
        os.makedirs(THUMB_DIR, exist_ok=True)
    except OSError:
        pass


def thumb_path(image_path):
    """Calcula o caminho da miniatura a partir do caminho da imagem."""
    h = hashlib.md5(image_path.encode()).hexdigest()
    return os.path.join(THUMB_DIR, f"{h}.png")


def thumb_hash(image_path):
    """Hash da imagem original: se mudar, miniatura fica inválida."""
    try:
        st = os.stat(image_path)
        return f"{st.st_mtime:.0f}_{st.st_size}"
    except OSError:
        return ""


def thumb_info_path(image_path):
    """Arquivo que guarda metadados da miniatura (hash da imagem original)."""
    return thumb_path(image_path) + ".info"


def is_thumb_valid(image_path):
    """Verifica se a miniatura existe e é válida."""
    tp = thumb_path(image_path)
    info_p = thumb_info_path(image_path)
    
    if not (os.path.isfile(tp) and os.path.isfile(info_p)):
        return False
    
    try:
        with open(info_p) as f:
            stored = f.read().strip()
        return stored == thumb_hash(image_path)
    except OSError:
        return False


def get_or_generate(image_path, timeout=0.5):
    """Retorna o caminho da miniatura, gerando se necessário."""
    if not image_path or not os.path.isfile(image_path):
        return None
    
    ensure_thumb_dir()
    
    if is_thumb_valid(image_path):
        return thumb_path(image_path)
    
    try:
        _generate_thumb(image_path)
        return thumb_path(image_path)
    except Exception:
        return None


def _generate_thumb(image_path):
    """Carrega imagem, redimensiona e salva como PNG."""
    try:
        from PIL import Image
    except ImportError:
        # Se PIL não estiver disponível, retorna None
        return
    
    try:
        img = Image.open(image_path)
        img.thumbnail((THUMB_SIZE, THUMB_SIZE), Image.Resampling.LANCZOS)
        
        if img.mode == 'RGBA':
            bg = Image.new('RGB', img.size, (255, 255, 255))
            bg.paste(img, mask=img.split()[3])
            img = bg
        elif img.mode != 'RGB':
            img = img.convert('RGB')
        
        tp = thumb_path(image_path)
        img.save(tp, 'PNG', quality=THUMB_QUALITY)
        
        info_p = thumb_info_path(image_path)
        with open(info_p, 'w') as f:
            f.write(thumb_hash(image_path))
    except Exception:
        pass


def clear_unused():
    """Remove miniaturas de imagens que já não existem."""
    if not os.path.isdir(THUMB_DIR):
        return
    
    count = 0
    for f in os.listdir(THUMB_DIR):
        if not f.endswith('.png'):
            continue
        
        info_p = os.path.join(THUMB_DIR, f + '.info')
        if not os.path.isfile(info_p):
            try:
                os.unlink(os.path.join(THUMB_DIR, f))
                count += 1
            except OSError:
                pass
    
    if count > 0:
        print(f"Limpeza de miniaturas: {count} removidas")
