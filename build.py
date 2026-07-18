#!/usr/bin/env python3
"""Build script - generates the main adobe_stock_tagger.py"""

import os

OUT = os.path.join(os.path.dirname(os.path.abspath(__file__)), "adobe_stock_tagger.py")

CODE = r'''"""
Adobe Stock Metadata Tagger - AI Powered
Per-file metadata, drag-drop, dark mode, shortcuts, presets, CSV export
"""

import sys, os, struct, re, json, base64, csv, io, zlib, shutil, subprocess, ssl, time
import urllib.request, urllib.error
from pathlib import Path
from datetime import datetime

from PyQt6.QtWidgets import (
    QApplication, QMainWindow, QWidget, QVBoxLayout, QHBoxLayout,
    QLabel, QLineEdit, QTextEdit, QPushButton, QFileDialog,
    QListWidget, QListWidgetItem, QMessageBox, QSplitter, QGroupBox, QFormLayout,
    QStatusBar, QComboBox, QCheckBox, QProgressBar, QTabWidget,
    QAbstractItemView, QTableWidget, QTableWidgetItem, QHeaderView,
    QDialog, QDialogButtonBox, QMenu, QInputDialog,
)
from PyQt6.QtCore import Qt, QThread, pyqtSignal, QSize, QLocale
from PyQt6.QtGui import QPixmap, QIcon, QFont, QShortcut, QKeySequence

from PIL import Image


ADOBE_STOCK_CATEGORIES = {
    "Animals": "1", "Buildings and Architecture": "2", "Business": "3",
    "Drinks": "4", "The Environment": "5", "Food": "6",
    "Graphic Resources": "7", "Hobbies and Leisure": "8", "Industry": "9",
    "Landscapes": "10", "Lifestyle": "11", "Macro": "12", "Nature": "13",
    "Objects": "14", "People": "15", "Plants and Flowers": "16",
    "Science and Technology": "17", "Social Issues": "18",
    "Sports and Fitness": "19", "Transport": "20", "Travel": "21",
}
SHUTTERSTOCK_CATEGORIES = {
    "Abstract": "Abstract", "Animals/Wildlife": "Animals/Wildlife",
    "Arts": "Arts", "Backgrounds/Textures": "Backgrounds/Textures",
    "Beauty/Fashion": "Beauty/Fashion", "Buildings/Landmarks": "Buildings/Landmarks",
    "Business/Finance": "Business/Finance", "Celebrities": "Celebrities",
    "Education": "Education", "Food and Drink": "Food and Drink",
    "Healthcare/Medical": "Healthcare/Medical", "Holidays": "Holidays",
    "Industrial": "Industrial", "Interiors": "Interiors",
    "Miscellaneous": "Miscellaneous", "Nature": "Nature",
    "Objects": "Objects", "Parks/Outdoor": "Parks/Outdoor",
    "People": "People", "Religion": "Religion",
    "Science": "Science", "Signs/Symbols": "Signs/Symbols",
    "Sports/Recreation": "Sports/Recreation", "Technology": "Technology",
    "Transportation": "Transportation", "Vintage": "Vintage",
}
FREEPIK_CATEGORIES = {
    "Photos": "photos", "Vectors": "vectors", "PSD": "psd",
    "Icons": "icons", "Videos": "videos",
}
SUPPORTED_EXTENSIONS = {'.jpg', '.jpeg', '.png', '.tif', '.tiff'}
OLLAMA_URL = "http://127.0.0.1:11434"
TEMP_DIR = os.path.join(os.path.expanduser("~"), "AppData", "Local", "StockTagger", "pasted")
APP_VERSION = "1.0.0"
UPDATE_REPO = "ZUPE12/ZUPE12"  # e.g. "username/stock-tagger" (leave empty to disable)
def _get_app_data_dir():
    appdata = os.environ.get("APPDATA", os.path.expanduser("~"))
    d = os.path.join(appdata, "StockTagger")
    os.makedirs(d, exist_ok=True)
    return d

PRESETS_FILE = os.path.join(_get_app_data_dir(), "presets.json")

DARK_STYLE = """
QMainWindow { background-color: #1a1a2e; }
QWidget { background-color: #1a1a2e; color: #e0e0e0; }
QGroupBox {
    border: 1px solid #2a2a4a; border-radius: 8px; margin-top: 12px;
    padding: 12px 8px 8px 8px; font-weight: bold; background-color: #16213e;
}
QGroupBox::title { subcontrol-origin: margin; left: 12px; padding: 0 8px; color: #64b5f6; }
QLineEdit, QTextEdit, QComboBox {
    background-color: #0f3460; color: #e0e0e0; border: 1px solid #2a2a4a;
    border-radius: 6px; padding: 6px 8px; selection-background-color: #533483;
    font-size: 13px;
}
QLineEdit:focus, QTextEdit:focus { border: 1px solid #64b5f6; }
QPushButton {
    background-color: #533483; color: #e0e0e0; border: none;
    border-radius: 6px; padding: 7px 16px; font-weight: bold; font-size: 12px;
}
QPushButton:hover { background-color: #6a4c9c; }
QPushButton:pressed { background-color: #4a2c7a; }
QPushButton:disabled { background-color: #2a2a4a; color: #666; }
QListWidget {
    background-color: #0f3460; color: #e0e0e0; border: 1px solid #2a2a4a;
    border-radius: 6px; padding: 2px; outline: none; font-size: 12px;
}
QListWidget::item { padding: 4px 6px; border-radius: 4px; }
QListWidget::item:selected { background-color: #533483; color: white; }
QListWidget::item:hover { background-color: #1a1a4e; }
QTableWidget {
    background-color: #0f3460; color: #e0e0e0; border: 1px solid #2a2a4a;
    border-radius: 6px; gridline-color: #2a2a4a; font-size: 12px;
}
QTableWidget::item:selected { background-color: #533483; color: white; }
QProgressBar {
    border: 1px solid #2a2a4a; border-radius: 4px; text-align: center;
    background: #0f3460; max-height: 12px; font-size: 10px;
}
QProgressBar::chunk { background: qlineargradient(x1:0,y1:0,x2:1,y2:0,stop:0 #533483,stop:1 #64b5f6); border-radius: 3px; }
QStatusBar { background-color: #16213e; color: #b0b0d0; border-top: 1px solid #2a2a4a; font-size: 12px; }
QTabWidget::pane { border: 1px solid #2a2a4a; border-radius: 6px; background: #16213e; }
QTabBar::tab {
    background: #0f3460; color: #8080a0; border: 1px solid #2a2a4a;
    padding: 8px 20px; border-top-left-radius: 6px; border-top-right-radius: 6px;
    font-weight: bold; font-size: 12px; margin-right: 2px;
}
QTabBar::tab:selected { background: #16213e; color: #64b5f6; border-bottom: 2px solid #64b5f6; }
QTabBar::tab:hover:!selected { background: #1a1a4e; color: #b0b0d0; }
QHeaderView::section {
    background-color: #16213e; color: #b0b0d0; border: 1px solid #2a2a4a;
    padding: 6px; font-weight: bold; font-size: 12px;
}
QCheckBox { color: #e0e0e0; font-size: 12px; }
QCheckBox::indicator { width: 16px; height: 16px; border-radius: 3px; border: 1px solid #2a2a4a; background: #0f3460; }
QCheckBox::indicator:checked { background: #533483; border-color: #6a4c9c; }
QComboBox::drop-down { border: none; width: 24px; }
QComboBox::down-arrow { image: none; border-left: 5px solid transparent; border-right: 5px solid transparent; border-top: 6px solid #b0b0d0; margin-right: 8px; }
QComboBox QAbstractItemView { background-color: #0f3460; color: #e0e0e0; border: 1px solid #2a2a4a; selection-background-color: #533483; selection-color: white; outline: none; padding: 4px; }
QComboBox QAbstractItemView::item { padding: 6px 8px; min-height: 24px; }
QLabel { font-size: 12px; }
QSplitter::handle { background-color: #2a2a4a; width: 2px; }
"""


# ─────────────────────────── AI / Ollama ───────────────────────────

def check_ollama_connection():
    try:
        req = urllib.request.Request(f"{OLLAMA_URL}/api/tags")
        resp = urllib.request.urlopen(req, timeout=5)
        data = json.loads(resp.read().decode())
        models = [m["name"] for m in data.get("models", [])]
        return True, models
    except Exception:
        return False, []


def image_to_base64(filepath, max_size=1024):
    if not os.path.isfile(filepath):
        raise FileNotFoundError(f"Image not found: {filepath}")
    fsize = os.path.getsize(filepath)
    if fsize < 100:
        raise ValueError(f"File too small ({fsize} bytes), may be corrupted: {filepath}")
    img = Image.open(filepath)
    img.load()
    if img.mode in ("RGBA", "P", "LA"):
        img = img.convert("RGB")
    elif img.mode != "RGB":
        img = img.convert("RGB")
    w, h = img.size
    if w < 10 or h < 10:
        raise ValueError(f"Image too small ({w}x{h}), may be corrupted")
    if max(w, h) > max_size:
        ratio = max_size / max(w, h)
        img = img.resize((int(w * ratio), int(h * ratio)), Image.LANCZOS)
    buf = io.BytesIO()
    img.save(buf, format="JPEG", quality=85)
    encoded = base64.b64encode(buf.getvalue()).decode("utf-8")
    if len(encoded) < 100:
        raise ValueError("Base64 encoding failed - image may be corrupted")
    return encoded


def get_image_mp(filepath):
    try:
        img = Image.open(filepath)
        return round((img.size[0] * img.size[1]) / 1_000_000, 2)
    except Exception:
        return 0


def ollama_vision_analyze(filepath, model="llava", language="en", platform="adobe", mode="stock"):
    if not os.path.isfile(filepath):
        raise FileNotFoundError(f"File not found: {filepath}")
    prompt = _build_creative_prompt(language) if mode == "creative" else _build_stock_prompt(language, platform)
    try:
        img_b64 = image_to_base64(filepath)
    except Exception as e:
        raise ValueError(f"Failed to process image: {e}")
    payload = json.dumps({
        "model": model,
        "messages": [{"role": "user", "content": prompt, "images": [img_b64]}],
        "stream": False,
        "options": {"temperature": 0.4, "num_predict": 4096},
    }).encode("utf-8")
    req = urllib.request.Request(
        f"{OLLAMA_URL}/api/chat", data=payload,
        headers={"Content-Type": "application/json"}, method="POST",
    )
    try:
        resp = urllib.request.urlopen(req, timeout=300)
    except urllib.error.URLError as e:
        raise ConnectionError(f"Cannot connect to Ollama: {e}\nMake sure Ollama is running (ollama serve)")
    except Exception as e:
        raise ConnectionError(f"Ollama request failed: {e}")
    result = json.loads(resp.read().decode())
    response_text = result.get("message", {}).get("content", "")
    if not response_text:
        err = result.get("error", "")
        if err:
            raise ValueError(f"Ollama error: {err}")
        raise ValueError("Empty response from AI model")
    if mode == "creative":
        return _parse_creative_response(response_text)
    json_match = re.search(r"\{[\s\S]*\}", response_text)
    if json_match:
        try:
            parsed = json.loads(json_match.group())
            if "keywords" not in parsed:
                parsed["keywords"] = []
            if isinstance(parsed["keywords"], str):
                parsed["keywords"] = [k.strip() for k in parsed["keywords"].split(",") if k.strip()]
            parsed["keywords"] = _expand_keywords(parsed["keywords"], parsed.get("category", ""))
            return parsed
        except json.JSONDecodeError:
            pass
    return None


STOCK_BONUS_KEYWORDS = {
    "Animals": ["wildlife", "fauna", "pet", "creature", "habitat", "natural", "cute", "furry", "animal portrait", "nature lover"],
    "Buildings and Architecture": ["urban", "skyline", "skyscraper", "facade", "interior", "design", "structure", "construction", "modern", "cityscape", "real estate", "property"],
    "Business": ["corporate", "office", "teamwork", "meeting", "finance", "growth", "strategy", "handshake", "professional", "entrepreneur", "startup", "productivity", "success"],
    "Drinks": ["beverage", "refreshment", "cocktail", "juice", "coffee", "tea", "cold", "hot", "glass", "pour", "drink", "thirst"],
    "The Environment": ["ecology", "green", "climate", "recycle", "sustainable", "conservation", "pollution", "renewable", "organic", "earth", "planet", "clean energy"],
    "Food": ["cuisine", "dish", "meal", "ingredient", "fresh", "healthy", "delicious", "cooking", "recipe", "organic", "restaurant", "homemade", "appetizing", "gourmet"],
    "Graphic Resources": ["pattern", "texture", "background", "abstract", "design element", "illustration", "template", "frame", "border", "minimalist", "geometric", "seamless"],
    "Hobbies and Leisure": ["recreation", "fun", "relaxation", "weekend", "holiday", "leisure time", "entertainment", "outdoor", "indoor", "passion", "enjoyment"],
    "Industry": ["factory", "manufacturing", "production", "warehouse", "industrial", "machinery", "worker", "engineering", "assembly", "automation", "heavy duty"],
    "Landscapes": ["scenery", "panorama", "horizon", "mountain", "valley", "river", "forest", "sunset", "sunrise", " vista", "outdoor", "countryside", "wilderness", "breathtaking", "serene"],
    "Lifestyle": ["everyday", "casual", "daily life", "family", "friendship", "happiness", "modern life", "youth", "generation", "culture", "trend", "fashion", "wellness"],
    "Macro": ["close up", "detail", "texture", "micro", " magnified", "tiny", "pattern", "sharp focus", "bokeh", "shallow depth of field", "intricate", "minuscule"],
    "Nature": ["outdoor", "wilderness", "flora", "fauna", "ecosystem", "biodiversity", "season", "organic", "earth", "wild", "pristine", "serene", "majestic", "tranquil"],
    "Objects": ["still life", "item", "product", "item", "prop", "symbol", "isolated", "white background", "studio shot", "commercial", "commodity", "artifact"],
    "People": ["portrait", "face", "smile", "emotion", "diversity", "multiethnic", "group", "crowd", "individual", "lifestyle", "candid", "posed", "human", "expression", "connection"],
    "Plants and Flowers": ["botanical", "floral", "bloom", "garden", "leaf", "stem", "petal", "blossom", "tree", "greenery", "foliage", "spring", "fresh", "fragile", "delicate"],
    "Science and Technology": ["innovation", "digital", "data", "computer", "lab", "research", "tech", "AI", "robot", "circuit", "programming", "analysis", "discovery", "future"],
    "Social Issues": ["community", "charity", "volunteer", "awareness", "equality", "diversity", "inclusion", "help", "support", "welfare", "education", "poverty"],
    "Sports and Fitness": ["athletic", "workout", "exercise", "gym", "running", "competition", "champion", "training", "active", "energy", "stamina", "performance", "endurance"],
    "Transport": ["vehicle", "car", "truck", "bus", "train", "airplane", "bicycle", "road", "traffic", "commute", "logistics", "delivery", "travel"],
    "Travel": ["destination", "adventure", "exploration", "tourism", "vacation", "journey", "backpacking", "passport", "landmark", "exotic", "cultural", "bucket list", "wanderlust", "discover"],
}


def _expand_keywords(keywords, category):
    seen = set()
    result = []
    for kw in keywords:
        k = kw.strip().lower()
        if k and k not in seen:
            seen.add(k)
            result.append(k)
    if category in STOCK_BONUS_KEYWORDS:
        for bonus in STOCK_BONUS_KEYWORDS[category]:
            b = bonus.strip().lower()
            if b not in seen:
                seen.add(b)
                result.append(b)
    return result[:49]


class AIThread(QThread):
    progress = pyqtSignal(int, int, str)
    result_ready = pyqtSignal(str, dict)
    error_signal = pyqtSignal(str)
    finished_all = pyqtSignal(int, int)

    def __init__(self, files, model, language="en", provider="ollama", api_key="", platform="adobe", mode="stock"):
        super().__init__()
        self.files = files
        self.model = model
        self.language = language
        self.provider = provider
        self.api_key = api_key
        self.platform = platform
        self.mode = mode
        self._stop = False

    def stop(self):
        self._stop = True

    def _analyze(self, fp):
        if self.provider == "openai":
            return openai_vision_analyze(fp, self.model, self.api_key, self.language, self.platform, self.mode)
        elif self.provider == "gemini":
            return gemini_vision_analyze(fp, self.model, self.api_key, self.language, self.platform, self.mode)
        else:
            return ollama_vision_analyze(fp, self.model, self.language, self.platform, self.mode)

    def run(self):
        success = errors = 0
        total = len(self.files)
        self.progress.emit(0, total, "")
        for idx, fp in enumerate(self.files):
            if self._stop:
                break
            try:
                result = self._analyze(fp)
                if result:
                    self.result_ready.emit(fp, result)
                    success += 1
                else:
                    errors += 1
                    self.error_signal.emit(f"AI returned no data: {os.path.basename(fp)}")
            except Exception as e:
                errors += 1
                err_msg = str(e)
                self.error_signal.emit(f"{os.path.basename(fp)}: {err_msg}")
            self.progress.emit(idx + 1, total, os.path.basename(fp))
        self.finished_all.emit(success, errors)


# ─────────────────────────── XMP ───────────────────────────

def build_xmp_packet(title, description, keywords, category, creator="", copyright_text=""):
    keyword_lines = ""
    for kw in keywords:
        kw = kw.strip()
        if kw:
            keyword_lines += f'          <rdf:li>{_xml_escape(kw)}</rdf:li>\n'
    cat_num = ADOBE_STOCK_CATEGORIES.get(category, category)
    xmp = f"""<?xml version="1.0" encoding="UTF-8"?>
<x:xmpmeta xmlns:x="adobe:ns:meta/">
  <rdf:RDF xmlns:rdf="http://www.w3.org/1999/02/22-rdf-syntax-ns#">
    <rdf:Description rdf:about=""
      xmlns:dc="http://purl.org/dc/elements/1.1/"
      xmlns:photoshop="http://ns.adobe.com/photoshop/1.0/"
      xmlns:Iptc4xmpCore="http://iptc.org/std/Iptc4xmpCore/1.0/xmlns/"
      xmlns:WebMode="http://ns.adobe.com/xap/1.0/s/WebMode/"
      xmlns:xmpRights="http://ns.adobe.com/xap/1.0/rights/">
      <dc:title>
        <rdf:Alt>
          <rdf:li xml:lang="x-default">{_xml_escape(title)}</rdf:li>
        </rdf:Alt>
      </dc:title>
      <dc:description>
        <rdf:Alt>
          <rdf:li xml:lang="x-default">{_xml_escape(description)}</rdf:li>
        </rdf:Alt>
      </dc:description>
      <dc:subject>
        <rdf:Bag>
{keyword_lines}        </rdf:Bag>
      </dc:subject>
      <photoshop:Category>{_xml_escape(str(cat_num))}</photoshop:Category>
      <photoshop:TransmissionReference>{_xml_escape(title)}</photoshop:TransmissionReference>
      <dc:creator>
        <rdf:Seq>
          <rdf:li>{_xml_escape(creator)}</rdf:li>
        </rdf:Seq>
      </dc:creator>
      <photoshop:Copyright>{_xml_escape(copyright_text)}</photoshop:Copyright>
      <xmpRights:WebStatement>{_xml_escape(copyright_text)}</xmpRights:WebStatement>
    </rdf:Description>
  </rdf:RDF>
</x:xmpmeta>"""
    return xmp


def _xml_escape(text):
    for old, new in [("&", "&amp;"), ("<", "&lt;"), (">", "&gt;"), ('"', "&quot;"), ("'", "&apos;")]:
        text = text.replace(old, new)
    return text


def embed_xmp_jpeg(filepath, xmp_packet):
    with open(filepath, 'rb') as f:
        data = f.read()
    if data[:2] != b'\xff\xd8':
        raise ValueError("Not a valid JPEG file")
    xmp_bytes = xmp_packet.encode('utf-8')
    ns_uri = b'http://ns.adobe.com/xap/1.0/\x00'
    app1_payload = ns_uri + xmp_bytes
    app1_marker = b'\xff\xe1'
    app1_length = struct.pack('>H', len(app1_payload) + 2)
    app1_segment = app1_marker + app1_length + app1_payload
    i = 2
    while i < len(data) - 1:
        if data[i] == 0xFF:
            marker = data[i + 1]
            if marker == 0xD9 or marker == 0xDA:
                break
            if marker == 0x00:
                i += 1
                continue
            length = struct.unpack('>H', data[i + 2:i + 4])[0]
            if marker == 0xE1:
                seg_start = i + 2 + length
                if b'http://ns.adobe.com/xap/1.0/' in data[i:seg_start]:
                    data = data[:i] + app1_segment + data[seg_start:]
                    with open(filepath, 'wb') as f:
                        f.write(data)
                    return True
                i = seg_start
            else:
                i = 2 + length + i
        else:
            i += 1
    data = data[:2] + app1_segment + data[2:]
    with open(filepath, 'wb') as f:
        f.write(data)
    return True


def embed_xmp_png(filepath, xmp_packet):
    with open(filepath, 'rb') as f:
        data = f.read()
    if data[:8] != b'\x89PNG\r\n\x1a\n':
        raise ValueError("Not a valid PNG file")
    xmp_hex = xmp_packet.encode('utf-8').hex()
    itxt_keyword = b"Raw profile type xmp"
    itxt_text = xmp_hex.encode('latin-1')
    itxt_payload = itxt_keyword + b'\x00' + b'\x00' + b'\x00' + itxt_text
    chunk_type = b'iTXt'
    crc = struct.pack('>I', zlib.crc32(chunk_type + itxt_payload) & 0xFFFFFFFF)
    itxt_chunk = chunk_type + struct.pack('>I', len(itxt_payload)) + itxt_payload + crc
    iend_pos = data.rfind(b'IEND')
    if iend_pos > 0:
        iend_pos -= 4
        data = data[:iend_pos] + itxt_chunk + data[iend_pos:]
    with open(filepath, 'wb') as f:
        f.write(data)
    return True


def read_xmp_from_file(filepath):
    ext = Path(filepath).suffix.lower()
    try:
        with open(filepath, 'rb') as f:
            data = f.read()
    except Exception:
        return None
    if ext in ('.jpg', '.jpeg') and data[:2] == b'\xff\xd8':
        i = 2
        while i < len(data) - 1:
            if data[i] == 0xFF:
                marker = data[i + 1]
                if marker in (0xD9, 0xDA):
                    break
                if marker == 0x00:
                    i += 1
                    continue
                length = struct.unpack('>H', data[i + 2:i + 4])[0]
                if marker == 0xE1:
                    segment = data[i + 4:i + 2 + length]
                    if b'http://ns.adobe.com/xap/1.0/' in segment:
                        idx = segment.index(b'http://ns.adobe.com/xap/1.0/')
                        return segment[idx + 29:].decode('utf-8', errors='replace')
                i = 2 + length + i
            else:
                i += 1
    elif ext == '.png' and data[:8] == b'\x89PNG\r\n\x1a\n':
        i = 8
        while i < len(data) - 12:
            length = struct.unpack('>I', data[i:i + 4])[0]
            chunk_type = data[i + 4:i + 8]
            chunk_data = data[i + 8:i + 8 + length]
            if chunk_type == b'iTXt':
                null_pos = chunk_data.index(b'\x00')
                if chunk_data[:null_pos] == b'Raw profile type xmp':
                    hex_text = chunk_data[null_pos + 3:].decode('latin-1')
                    try:
                        return bytes.fromhex(hex_text).decode('utf-8', errors='replace')
                    except Exception:
                        pass
            i += 12 + length
    return None


def _build_stock_prompt(language="en", platform="adobe"):
    if platform == "shutterstock":
        cat_list = ", ".join(SHUTTERSTOCK_CATEGORIES.keys())
        platform_name = "Shutterstock"
        title_rule = (
            "- title: A factual sentence (one-line caption) describing the content. "
            "Max 2048 chars, but keep 50-100 chars. Describe: what is happening, who/what is in it, where/when if relevant. "
            "Focus on what the image actually shows. Do NOT guess or add details not visible. "
            "Do NOT read like a keyword list. No promotional language, no special characters (%, #, &), no all-caps.\n"
            "- description: Optional for commercial. 1-2 sentences adding context the title cannot fit.\n"
        )
        keyword_rule = (
            "- keywords: 7-50 keywords (use all 50 for max visibility). Individual words or compound words. "
            "All lowercase English, no duplicates. Must be relevant to the content. "
            "Focus on what the image actually shows - do not add keywords for things not visible. "
            "Think like a BUYER searching for this image. "
            "Place the most important keywords first (first 5 have highest ranking weight). "
            "Cover: subject, setting, mood, colors, style, use case, abstract concepts.\n"
        )
        strict_rules = (
            "STRICT RULES (Shutterstock Content Publishing Standards):\n"
            "- Do NOT use brand names, trademarks, or product names.\n"
            "- Do NOT include personally identifiable information (PII).\n"
            "- Do NOT use offensive, hateful, racist, derogatory, or discriminatory terminology.\n"
            "- Do NOT use emojis, spelling errors, or grammar errors.\n"
            "- Do NOT describe content as depicting an actual newsworthy event (unless editorial).\n"
            "- Do NOT use camera/gear technical terms.\n"
        )
    elif platform == "freepik":
        cat_list = ", ".join(FREEPIK_CATEGORIES.keys())
        platform_name = "Freepik"
        title_rule = (
            "- title: Coherent and relevant, answering WHO, WHAT, WHEN, WHERE. "
            "35-100 characters. Describe the concept and theme clearly in one sentence. "
            "Focus on what the image actually shows. Do NOT guess or add details not visible. "
            "Do NOT include file type references (EPS10, PSD, JPG). "
            "Do NOT include numbers or dates (except festivities like 4th July). "
            "Do NOT use special characters (#, @, quotes). "
            "Do NOT list keywords in the title.\n"
            "- description: Optional. Brief context if needed.\n"
        )
        keyword_rule = (
            "- keywords: 20-50 keywords (sweet spot is 20-25 relevant ones). "
            "All in English, singular form. No determiners, prepositions, or pronouns. "
            "No file type references (.eps, .psd, .jpg). No special characters. "
            "Each keyword separated by comma. Only use keywords that relate to the resource's content or format. "
            "Focus on what the image actually shows - do not add keywords for things not visible. "
            "Do NOT spam: no repeated words, no listing all colors (use 'colorful' instead), "
            "no unrelated seasonal keywords. "
            "Include style descriptors (flat design, realistic, minimalist, etc.) when applicable.\n"
        )
        strict_rules = (
            "STRICT RULES (Freepik Metadata Guidelines):\n"
            "- Do NOT use brand names, trademarks, or copyrighted characters.\n"
            "- Do NOT use keywords unrelated to the resource's content.\n"
            "- Do NOT repeat the same keyword in different forms (spam).\n"
            "- Do NOT list all colors as keywords (use 'colorful' if colors are important).\n"
            "- Do NOT use other seasons when depicting one season (e.g. don't add 'summer' for a spring image).\n"
            "- Do NOT use camera/gear technical terms.\n"
        )
    else:
        cat_list = ", ".join(ADOBE_STOCK_CATEGORIES.keys())
        platform_name = "Adobe Stock"
        title_rule = (
            "- title: Clear, descriptive English title, max 70 characters. "
            "Focus on what the image actually shows. Do NOT guess or add details not visible. "
            "Avoid overly technical or gear-heavy terms.\n"
            "- description: Detailed 3-5 sentence description in English. "
            "Include: subject, action, mood, lighting, colors, composition, potential use cases. "
            "Focus on what the image actually shows. Be specific and SEO-optimized for buyers searching stock images.\n"
        )
        keyword_rule = (
            "- keywords: 30-49 keywords, all lowercase English, no duplicates. "
            "Think like a BUYER searching for this image. "
            "Focus on what the image actually shows - do not add keywords for things not visible. "
            "Include: main subject, secondary objects, colors, emotions/moods, "
            "textures, composition style, season/weather if visible, "
            "abstract concepts (success, freedom, teamwork etc), "
            "industry terms, and related concepts. "
            "Put the 10 most important keywords first (they have the greatest influence on search ranking). "
            "Sort remaining from most specific to most general.\n"
        )
        strict_rules = (
            "STRICT RULES (Adobe Stock Submission Guidelines):\n"
            "- Do NOT use names of artists, real people, or fictional characters.\n"
            "- Do NOT use brand names, trademarks, or product names.\n"
            "- Do NOT reference creative works still in copyright.\n"
            "- Do NOT use names of government agencies.\n"
            "- Do NOT describe content as depicting an actual newsworthy event.\n"
            "- Do NOT use cliche or superlative words (best, amazing, stunning, perfect, number one).\n"
            "- Do NOT use camera/gear technical terms (50mm, bokeh, DSLR, RAW).\n"
        )

    if language == "th":
        title_rule = title_rule.replace("English", "Thai language")
        title_rule = title_rule.replace("max 70 characters", "max 70 characters in Thai")
        title_rule = title_rule.replace("35-100 characters", "35-100 characters in Thai")
        title_rule = title_rule.replace("50-100 chars", "50-100 chars in Thai")
        title_rule = title_rule.replace("Coherent and relevant, answering WHO, WHAT, WHEN, WHERE.",
            "Use Thai language. Coherent and relevant, answering WHO, WHAT, WHEN, WHERE.")
        title_rule = title_rule.replace("A factual sentence (one-line caption) describing the content.",
            "Use Thai language. A factual sentence (one-line caption) describing the content.")
        desc_extra = "- description: Use Thai language for the description.\n"
    else:
        desc_extra = ""

    return (
        f"You are an expert {platform_name} contributor. Analyze this stock photo.\n"
        "Return ONLY valid JSON, no markdown, no explanation.\n\n"
        + strict_rules +
        "REQUIREMENTS:\n"
        + title_rule + desc_extra + keyword_rule +
        "- category: one of: " + cat_list + "\n"
        "- potential_issues: Identify any trademark violations, visible brand logos, "
        "copyrighted designs, or recognizable faces/properties that would require releases. "
        "Return as an array of strings. Empty array [] if no issues found.\n\n"
        'JSON format:\n{\n'
        '  "title": "...",\n'
        '  "description": "...",\n'
        '  "keywords": ["...", "...", "..."],\n'
        '  "category": "...",\n'
        '  "potential_issues": []\n'
        "}"
    )


def _build_creative_prompt(language="en"):
    return (
        "Analyze the provided image and reverse-engineer it into a highly detailed text prompt "
        "for generative AI models like Midjourney, DALL-E, or Stable Diffusion.\n\n"
        "Guidelines:\n"
        "1. Describe the subject, composition, lighting, camera angle, style "
        "(e.g., photorealistic, watercolor, digital art), color palette, and atmospheric details.\n"
        "2. Formulate the description into a single, cohesive, descriptive paragraph optimized "
        "for AI image generation. Do not use conversational filler (e.g., 'This is a photo of...'). "
        "Start directly with the core visual elements.\n\n"
        "Focus on what the image actually shows. Do NOT guess or add details not visible.\n\n"
        'Return ONLY valid JSON with these keys: "prompt" (string) and "style_tags" (array of style keywords).\n'
        "Do not include any Markdown wrapping.\n\n"
        'JSON format:\n{\n'
        '  "prompt": "...",\n'
        '  "style_tags": ["...", "...", "..."]\n'
        "}"
    )


def _parse_ai_response(response_text):
    json_match = re.search(r"\{[\s\S]*\}", response_text)
    if json_match:
        try:
            parsed = json.loads(json_match.group())
            if "keywords" not in parsed:
                parsed["keywords"] = []
            if isinstance(parsed["keywords"], str):
                parsed["keywords"] = [k.strip() for k in parsed["keywords"].split(",") if k.strip()]
            parsed["keywords"] = _expand_keywords(parsed["keywords"], parsed.get("category", ""))
            if "potential_issues" not in parsed:
                parsed["potential_issues"] = []
            if not isinstance(parsed["potential_issues"], list):
                parsed["potential_issues"] = []
            return parsed
        except json.JSONDecodeError:
            pass
    return None


def _parse_creative_response(response_text):
    json_match = re.search(r"\{[\s\S]*\}", response_text)
    if json_match:
        try:
            parsed = json.loads(json_match.group())
            if "prompt" not in parsed:
                parsed["prompt"] = response_text.strip()
            if "style_tags" not in parsed:
                parsed["style_tags"] = []
            if isinstance(parsed["style_tags"], str):
                parsed["style_tags"] = [t.strip() for t in parsed["style_tags"].split(",") if t.strip()]
            return parsed
        except json.JSONDecodeError:
            pass
    return {"prompt": response_text.strip(), "style_tags": []}


def openai_vision_analyze(filepath, model="gpt-4o", api_key="", language="en", platform="adobe", mode="stock"):
    if not os.path.isfile(filepath):
        raise FileNotFoundError(f"File not found: {filepath}")
    if not api_key:
        raise ValueError("OpenAI API key is required")
    vision_models = ["gpt-4o", "gpt-4o-mini", "gpt-4-turbo", "gpt-4-vision-preview"]
    if model not in vision_models:
        raise ValueError(
            f"Model '{model}' does NOT support image input!\n\n"
            f"Use a vision model instead:\n"
            f"  - gpt-4o (best quality)\n"
            f"  - gpt-4o-mini (cheaper)\n\n"
            f"Click 'Fetch' to load available models,\n"
            f"or switch to Ollama/Gemini provider."
        )
    prompt = _build_creative_prompt(language) if mode == "creative" else _build_stock_prompt(language, platform)
    try:
        img_b64 = image_to_base64(filepath)
    except Exception as e:
        raise ValueError(f"Failed to process image: {e}")
    payload = json.dumps({
        "model": model,
        "messages": [{
            "role": "user",
            "content": [
                {"type": "text", "text": prompt},
                {"type": "image_url", "image_url": {"url": f"data:image/jpeg;base64,{img_b64}", "detail": "low"}}
            ]
        }],
        "max_tokens": 4096,
        "temperature": 0.4,
    }).encode("utf-8")
    req = urllib.request.Request(
        "https://api.openai.com/v1/chat/completions", data=payload,
        headers={"Content-Type": "application/json", "Authorization": f"Bearer {api_key}"},
        method="POST",
    )
    try:
        ctx = ssl.create_default_context()
        resp = urllib.request.urlopen(req, timeout=300, context=ctx)
    except ssl.SSLCertVerificationError:
        ctx = ssl._create_unverified_context()
        resp = urllib.request.urlopen(req, timeout=300, context=ctx)
    except urllib.error.HTTPError as e:
        body = e.read().decode("utf-8", errors="replace")
        raise ConnectionError(f"OpenAI API error {e.code}: {body[:300]}")
    except Exception as e:
        raise ConnectionError(f"OpenAI request failed: {e}")
    result = json.loads(resp.read().decode())
    response_text = result.get("choices", [{}])[0].get("message", {}).get("content", "")
    if not response_text:
        raise ValueError("Empty response from OpenAI")
    if mode == "creative":
        return _parse_creative_response(response_text)
    return _parse_ai_response(response_text)


def gemini_vision_analyze(filepath, model="gemini-2.0-flash", api_key="", language="en", platform="adobe", mode="stock"):
    if not os.path.isfile(filepath):
        raise FileNotFoundError(f"File not found: {filepath}")
    if not api_key:
        raise ValueError("Google Gemini API key is required")
    prompt = _build_creative_prompt(language) if mode == "creative" else _build_stock_prompt(language, platform)
    try:
        img_b64 = image_to_base64(filepath)
    except Exception as e:
        raise ValueError(f"Failed to process image: {e}")
    payload = json.dumps({
        "contents": [{
            "parts": [
                {"text": prompt},
                {"inline_data": {"mime_type": "image/jpeg", "data": img_b64}}
            ]
        }],
        "generationConfig": {"temperature": 0.4, "maxOutputTokens": 4096},
    }).encode("utf-8")
    url = f"https://generativelanguage.googleapis.com/v1beta/models/{model}:generateContent?key={api_key}"
    req = urllib.request.Request(
        url, data=payload,
        headers={"Content-Type": "application/json"}, method="POST",
    )
    try:
        ctx = ssl.create_default_context()
        resp = urllib.request.urlopen(req, timeout=300, context=ctx)
    except ssl.SSLCertVerificationError:
        ctx = ssl._create_unverified_context()
        resp = urllib.request.urlopen(req, timeout=300, context=ctx)
    except urllib.error.HTTPError as e:
        body = e.read().decode("utf-8", errors="replace")
        raise ConnectionError(f"Gemini API error {e.code}: {body[:300]}")
    except Exception as e:
        raise ConnectionError(f"Gemini request failed: {e}")
    result = json.loads(resp.read().decode())
    candidates = result.get("candidates", [])
    response_text = ""
    if candidates:
        parts = candidates[0].get("content", {}).get("parts", [])
        for p in parts:
            if "text" in p:
                response_text += p["text"]
    if not response_text:
        raise ValueError("Empty response from Gemini")
    if mode == "creative":
        return _parse_creative_response(response_text)
    return _parse_ai_response(response_text)


def parse_xmp_keywords(xmp_text):
    match = re.search(r'<dc:subject>.*?<rdf:Bag>(.*?)</rdf:Bag>', xmp_text, re.DOTALL)
    return re.findall(r'<rdf:li>(.*?)</rdf:li>', match.group(1)) if match else []


def parse_xmp_title(xmp_text):
    m = re.search(r'<dc:title>.*?<rdf:Alt>.*?<rdf:li[^>]*>(.*?)</rdf:li>', xmp_text, re.DOTALL)
    return m.group(1).strip() if m else ""


def parse_xmp_description(xmp_text):
    m = re.search(r'<dc:description>.*?<rdf:Alt>.*?<rdf:li[^>]*>(.*?)</rdf:li>', xmp_text, re.DOTALL)
    return m.group(1).strip() if m else ""


# ─────────────────────────── Process Thread ───────────────────────────

class ProcessThread(QThread):
    progress = pyqtSignal(int, int, str)
    finished_signal = pyqtSignal(int, int)
    error_signal = pyqtSignal(str)

    def __init__(self, files, metadata_map, output_dir=None):
        super().__init__()
        self.files = files
        self.metadata_map = metadata_map
        self.output_dir = output_dir
        self._stop = False

    def stop(self):
        self._stop = True

    def run(self):
        total = len(self.files)
        success = errors = 0
        self.progress.emit(0, total, "")
        for idx, filepath in enumerate(self.files):
            if self._stop:
                break
            try:
                target = filepath
                if self.output_dir:
                    dest = os.path.join(self.output_dir, os.path.basename(filepath))
                    shutil.copy2(filepath, dest)
                    target = dest
                meta = self.metadata_map.get(filepath, {})
                xmp = build_xmp_packet(
                    title=meta.get('title', ''),
                    description=meta.get('description', ''),
                    keywords=meta.get('keywords', []),
                    category=meta.get('category', ''),
                    creator=meta.get('creator', ''),
                    copyright_text=meta.get('copyright_text', ''),
                )
                ext = Path(target).suffix.lower()
                if ext in ('.jpg', '.jpeg'):
                    embed_xmp_jpeg(target, xmp)
                elif ext == '.png':
                    embed_xmp_png(target, xmp)
                elif ext in ('.tif', '.tiff'):
                    Image.open(target).save(
                        target, tiff_imageinfo={b'ImageDescription': xmp.encode('utf-8')}
                    )
                success += 1
            except Exception as e:
                errors += 1
                self.error_signal.emit(f"{os.path.basename(filepath)}: {e}")
            self.progress.emit(idx + 1, total, os.path.basename(filepath))
        self.finished_signal.emit(success, errors)


# ─────────────────────────── Presets ───────────────────────────

def load_presets():
    if os.path.exists(PRESETS_FILE):
        try:
            with open(PRESETS_FILE, 'r', encoding='utf-8') as f:
                return json.load(f)
        except Exception:
            pass
    return {"creator": "", "copyright_text": "", "category": "", "dark_mode": False}


def save_presets_to_file(data):
    with open(PRESETS_FILE, 'w', encoding='utf-8') as f:
        json.dump(data, f, indent=2, ensure_ascii=False)


# ─────────────────────────── Main Window ───────────────────────────

class TagViewerDialog(QDialog):
    def __init__(self, filepath, parent=None):
        super().__init__(parent)
        self.setWindowTitle(f"Tags: {os.path.basename(filepath)}")
        self.setMinimumSize(600, 500)
        layout = QVBoxLayout(self)

        pixmap = QPixmap(filepath)
        if not pixmap.isNull():
            img_label = QLabel()
            img_label.setPixmap(pixmap.scaled(580, 250, Qt.AspectRatioMode.KeepAspectRatio,
                                              Qt.TransformationMode.SmoothTransformation))
            img_label.setAlignment(Qt.AlignmentFlag.AlignCenter)
            layout.addWidget(img_label)

        xmp = read_xmp_from_file(filepath)
        if xmp:
            title = parse_xmp_title(xmp)
            desc = parse_xmp_description(xmp)
            kws = parse_xmp_keywords(xmp)

            info = QGroupBox("Embedded Tags")
            info_layout = QFormLayout()
            lbl_title = QLabel(title)
            lbl_title.setWordWrap(True)
            lbl_title.setTextInteractionFlags(Qt.TextInteractionFlag.TextSelectableByMouse)
            info_layout.addRow("Title:", lbl_title)
            lbl_desc = QLabel(desc)
            lbl_desc.setWordWrap(True)
            lbl_desc.setMaximumHeight(120)
            lbl_desc.setTextInteractionFlags(Qt.TextInteractionFlag.TextSelectableByMouse)
            info_layout.addRow("Description:", lbl_desc)
            lbl_kws = QLabel(", ".join(kws))
            lbl_kws.setWordWrap(True)
            lbl_kws.setTextInteractionFlags(Qt.TextInteractionFlag.TextSelectableByMouse)
            info_layout.addRow(f"Keywords ({len(kws)}):", lbl_kws)

            cat_text = ""
            for name, num in ADOBE_STOCK_CATEGORIES.items():
                if num == str(desc):
                    cat_text = f"{num}. {name}"
                    break
            cat_num = ""
            m = re.search(r'<photoshop:Category>(\d+)</photoshop:Category>', xmp)
            if m:
                cat_num = m.group(1)
                for name, num in ADOBE_STOCK_CATEGORIES.items():
                    if num == cat_num:
                        cat_text = f"{num}. {name}"
                        break
            if cat_text:
                info_layout.addRow("Category:", QLabel(cat_text))

            info.setLayout(info_layout)
            layout.addWidget(info)

            xmp_box = QGroupBox("Raw XMP")
            xmp_layout = QVBoxLayout()
            xmp_text = QTextEdit()
            xmp_text.setPlainText(xmp)
            xmp_text.setReadOnly(True)
            xmp_text.setFont(QFont("Consolas", 8))
            xmp_text.setMaximumHeight(150)
            xmp_layout.addWidget(xmp_text)
            xmp_box.setLayout(xmp_layout)
            layout.addWidget(xmp_box)
        else:
            layout.addWidget(QLabel("No tags embedded in this file."))

        btn_close = QPushButton("Close")
        btn_close.clicked.connect(self.close)
        layout.addWidget(btn_close)


class MainWindow(QMainWindow):
    def __init__(self):
        super().__init__()
        self.setWindowTitle("Adobe Stock Metadata Tagger")
        self.setMinimumSize(1200, 800)
        self.setAcceptDrops(True)
        self.files = []
        self.metadata_map = {}
        self.output_dir = None
        self.process_thread = None
        self.ai_thread = None
        self.presets = load_presets()
        self.dark_mode = self.presets.get("dark_mode", False)
        self._setup_ui()
        self._setup_shortcuts()
        self._load_presets_to_ui()
        self._check_ollama()

    def _setup_ui(self):
        central = QWidget()
        self.setCentralWidget(central)
        main_layout = QHBoxLayout(central)
        main_layout.setContentsMargins(8, 8, 8, 8)
        main_layout.setSpacing(6)

        left_panel = QWidget()
        left_layout = QVBoxLayout(left_panel)
        left_layout.setContentsMargins(0, 0, 0, 0)
        left_layout.setSpacing(6)
        left_panel.setFixedWidth(380)

        file_group = QGroupBox("  Files")
        file_layout = QVBoxLayout()
        file_layout.setSpacing(4)
        self.file_list = QListWidget()
        self.file_list.setSelectionMode(QAbstractItemView.SelectionMode.ExtendedSelection)
        self.file_list.currentRowChanged.connect(self._on_file_selected)
        self.file_list.setAlternatingRowColors(False)
        self.file_list.setIconSize(QSize(48, 48))
        self.file_list.setMovement(QListWidget.Movement.Static)
        self.file_list.setViewMode(QListWidget.ViewMode.ListMode)
        self.file_list.setSpacing(1)
        self.file_list.setContextMenuPolicy(Qt.ContextMenuPolicy.CustomContextMenu)
        self.file_list.customContextMenuRequested.connect(self._on_file_context_menu)
        file_layout.addWidget(self.file_list)

        btn_row = QHBoxLayout()
        btn_row.setSpacing(4)
        for text, slot in [("  Add Files  ", self._add_files), ("  Add Folder  ", self._add_folder)]:
            b = QPushButton(text)
            b.clicked.connect(slot)
            btn_row.addWidget(b)
        file_layout.addLayout(btn_row)

        btn_row2 = QHBoxLayout()
        btn_row2.setSpacing(4)
        for text, slot in [("  Remove  ", self._remove_selected), ("  Clear  ", self._clear_files)]:
            b = QPushButton(text)
            b.clicked.connect(slot)
            btn_row2.addWidget(b)
        file_layout.addLayout(btn_row2)

        btn_row3 = QHBoxLayout()
        btn_row3.setSpacing(4)
        btn_open_file = QPushButton("  Open File  ")
        btn_open_file.setStyleSheet(
            "QPushButton{background:#1565C0;color:white;border-radius:6px;padding:6px;font-size:11px;font-weight:bold;}"
            "QPushButton:hover{background:#1E88E5;}"
        )
        btn_open_file.clicked.connect(self._open_file_viewer)
        btn_row3.addWidget(btn_open_file)
        btn_open_loc = QPushButton("  Open File Location  ")
        btn_open_loc.setStyleSheet(
            "QPushButton{background:#00695C;color:white;border-radius:6px;padding:6px;font-size:11px;font-weight:bold;}"
            "QPushButton:hover{background:#00897B;}"
        )
        btn_open_loc.clicked.connect(self._open_file_location)
        btn_row3.addWidget(btn_open_loc)
        btn_reset = QPushButton("  Reset  ")
        btn_reset.setStyleSheet(
            "QPushButton{background:#e65100;color:white;border-radius:6px;padding:6px;font-size:11px;font-weight:bold;}"
            "QPushButton:hover{background:#F57C00;}"
        )
        btn_reset.clicked.connect(self._reset_all)
        btn_row3.addWidget(btn_reset)
        btn_exit = QPushButton("  Exit  ")
        btn_exit.setStyleSheet(
            "QPushButton{background:#b71c1c;color:white;border-radius:6px;padding:6px;font-size:11px;font-weight:bold;}"
            "QPushButton:hover{background:#e53935;}"
        )
        btn_exit.clicked.connect(self.close)
        btn_row3.addWidget(btn_exit)
        file_layout.addLayout(btn_row3)

        self.lbl_count = QLabel("0 files | 0 MP")
        self.lbl_count.setStyleSheet("color: #8080a0; font-size: 11px; padding: 2px;")
        file_layout.addWidget(self.lbl_count)
        file_group.setLayout(file_layout)
        left_layout.addWidget(file_group)

        preview_group = QGroupBox("  Preview")
        preview_layout = QVBoxLayout()
        preview_layout.setContentsMargins(4, 4, 4, 4)
        self.image_preview = QLabel("Select an image")
        self.image_preview.setAlignment(Qt.AlignmentFlag.AlignCenter)
        self.image_preview.setMinimumHeight(200)
        self.image_preview.setStyleSheet(
            "border: 1px solid #2a2a4a; background: #0a0a1a; border-radius: 6px; color: #555; font-size: 13px;"
        )
        preview_layout.addWidget(self.image_preview)
        preview_group.setLayout(preview_layout)
        left_layout.addWidget(preview_group)

        output_group = QGroupBox("  Output")
        output_layout = QHBoxLayout()
        output_layout.setSpacing(4)
        self.chk_save_copy = QCheckBox("  Save copy to:")
        self.chk_save_copy.setStyleSheet(
            "QCheckBox{font-weight:bold; color:#4FC3F7; font-size:12px; spacing:8px;}"
            "QCheckBox::indicator{width:18px;height:18px;border-radius:4px;border:2px solid #555;background:#1a1a2e;}"
            "QCheckBox::indicator:checked{background:#4FC3F7;border-color:#4FC3F7;}"
        )
        self.chk_save_copy.stateChanged.connect(self._toggle_output)
        self.output_path = QLineEdit()
        self.output_path.setPlaceholderText("Select output folder...")
        self.output_path.setEnabled(False)
        self.btn_browse_output = QPushButton("...")
        self.btn_browse_output.setFixedWidth(32)
        self.btn_browse_output.setEnabled(False)
        self.btn_browse_output.clicked.connect(self._browse_output)
        output_layout.addWidget(self.chk_save_copy)
        output_layout.addWidget(self.output_path)
        output_layout.addWidget(self.btn_browse_output)
        output_group.setLayout(output_layout)
        left_layout.addWidget(output_group)

        right_panel = QWidget()
        right_layout = QVBoxLayout(right_panel)
        right_layout.setContentsMargins(0, 0, 0, 0)
        right_layout.setSpacing(6)
        self.tabs = QTabWidget()

        # ──── Tab 1: AI Auto-Tag ────
        ai_tab = QWidget()
        ai_layout = QVBoxLayout(ai_tab)
        ai_layout.setSpacing(8)
        ai_settings = QGroupBox("  AI Settings")
        ai_form = QFormLayout()
        ai_form.setSpacing(6)

        self.combo_provider = QComboBox()
        self.combo_provider.addItem("Ollama (Local)", "ollama")
        self.combo_provider.addItem("OpenAI GPT-4o", "openai")
        self.combo_provider.addItem("Google Gemini", "gemini")
        self.combo_provider.currentIndexChanged.connect(self._on_provider_changed)
        ai_form.addRow("Provider:", self.combo_provider)

        self.inp_api_key = QLineEdit()
        self.inp_api_key.setPlaceholderText("Enter API key (not needed for Ollama)")
        self.inp_api_key.setEchoMode(QLineEdit.EchoMode.Password)
        self.inp_api_key.setMinimumWidth(200)
        self.lbl_api_key = QLabel("API Key:")
        self.inp_api_key.setVisible(False)
        self.lbl_api_key.setVisible(False)
        self.combo_api_keys = QComboBox()
        self.combo_api_keys.setMinimumWidth(200)
        self.combo_api_keys.setVisible(False)
        self.btn_save_key = QPushButton("  Save  ")
        self.btn_save_key.setFixedWidth(60)
        self.btn_save_key.clicked.connect(self._save_api_key)
        self.btn_save_key.setVisible(False)
        self.btn_delete_key = QPushButton("  Delete  ")
        self.btn_delete_key.setFixedWidth(65)
        self.btn_delete_key.clicked.connect(self._delete_api_key)
        self.btn_delete_key.setVisible(False)
        self.btn_edit_key = QPushButton("  Edit  ")
        self.btn_edit_key.setFixedWidth(55)
        self.btn_edit_key.clicked.connect(self._edit_api_key)
        self.btn_edit_key.setVisible(False)
        self.btn_show_key = QPushButton("  Show  ")
        self.btn_show_key.setFixedWidth(55)
        self.btn_show_key.clicked.connect(self._toggle_api_key_visibility)
        self.btn_show_key.setVisible(False)
        self.btn_test_api = QPushButton("  Test  ")
        self.btn_test_api.setFixedWidth(50)
        self.btn_test_api.clicked.connect(self._test_api_key)
        self.btn_test_api.setVisible(False)
        api_key_row = QHBoxLayout()
        api_key_row.setSpacing(4)
        api_key_row.addWidget(self.combo_api_keys)
        api_key_row.addWidget(self.inp_api_key)
        api_key_row.addWidget(self.btn_show_key)
        api_key_row.addWidget(self.btn_save_key)
        api_key_row.addWidget(self.btn_edit_key)
        api_key_row.addWidget(self.btn_delete_key)
        api_key_row.addWidget(self.btn_test_api)
        self.api_key_widgets = [self.lbl_api_key, self.combo_api_keys, self.inp_api_key,
                                 self.btn_show_key, self.btn_save_key, self.btn_edit_key,
                                 self.btn_delete_key, self.btn_test_api]
        ai_form.addRow(self.lbl_api_key, api_key_row)

        self.combo_model = QComboBox()
        self.combo_model.setMinimumWidth(250)
        self.btn_refresh_models = QPushButton("  Refresh  ")
        self.btn_refresh_models.setFixedWidth(90)
        self.btn_refresh_models.clicked.connect(self._check_ollama)
        model_row = QHBoxLayout()
        model_row.setSpacing(6)
        model_row.addWidget(self.combo_model)
        model_row.addWidget(self.btn_refresh_models)
        ai_form.addRow("Model:", model_row)

        self.lbl_ollama_status = QLabel("Select a provider")
        self.lbl_ollama_status.setStyleSheet("font-size: 11px;")
        self.btn_start_ollama = QPushButton("  Start  ")
        self.btn_start_ollama.setFixedWidth(60)
        self.btn_start_ollama.setStyleSheet(
            "QPushButton{background:#2E7D32;color:white;border-radius:4px;padding:4px;font-size:10px;font-weight:bold;}"
            "QPushButton:hover{background:#43A047;}"
        )
        self.btn_start_ollama.clicked.connect(self._start_ollama)
        self.btn_start_ollama.setVisible(False)
        self.btn_stop_ollama = QPushButton("  Stop  ")
        self.btn_stop_ollama.setFixedWidth(55)
        self.btn_stop_ollama.setStyleSheet(
            "QPushButton{background:#c62828;color:white;border-radius:4px;padding:4px;font-size:10px;font-weight:bold;}"
            "QPushButton:hover{background:#e53935;}"
        )
        self.btn_stop_ollama.clicked.connect(self._stop_ollama)
        self.btn_stop_ollama.setVisible(False)
        status_row = QHBoxLayout()
        status_row.setSpacing(4)
        status_row.addWidget(self.lbl_ollama_status)
        status_row.addWidget(self.btn_start_ollama)
        status_row.addWidget(self.btn_stop_ollama)
        status_row.addStretch()
        ai_form.addRow("Status:", status_row)

        self.combo_lang = QComboBox()
        self.combo_lang.addItem("English", "en")
        self.combo_lang.addItem("Thai", "th")
        ai_form.addRow("Language:", self.combo_lang)

        self.combo_platform = QComboBox()
        self.combo_platform.addItem("Adobe Stock", "adobe")
        self.combo_platform.addItem("Shutterstock", "shutterstock")
        self.combo_platform.addItem("Freepik", "freepik")
        self.combo_platform.currentIndexChanged.connect(self._on_platform_changed)
        ai_form.addRow("Platform:", self.combo_platform)

        self.combo_mode = QComboBox()
        self.combo_mode.addItem("Stock Metadata", "stock")
        self.combo_mode.addItem("AI Image Prompt (Creative)", "creative")
        self.combo_mode.currentIndexChanged.connect(self._on_mode_changed)
        ai_form.addRow("Mode:", self.combo_mode)
        ai_settings.setLayout(ai_form)
        ai_layout.addWidget(ai_settings)

        ai_btn_row = QHBoxLayout()
        ai_btn_row.setSpacing(8)
        self.btn_ai_analyze = QPushButton("  Analyze Selected  ")
        self.btn_ai_analyze.setStyleSheet(
            "QPushButton{background:qlineargradient(x1:0,y1:0,x2:1,y2:0,stop:0 #1565C0,stop:1 #1976D2);"
            "color:white;font-weight:bold;padding:10px 20px;border-radius:6px;font-size:13px;}"
            "QPushButton:hover{background:qlineargradient(x1:0,y1:0,x2:1,y2:0,stop:0 #1976D2,stop:1 #2196F3);}"
        )
        self.btn_ai_analyze.clicked.connect(self._ai_analyze_single)
        self.btn_ai_batch = QPushButton("  Batch All Files  ")
        self.btn_ai_batch.setStyleSheet(
            "QPushButton{background:qlineargradient(x1:0,y1:0,x2:1,y2:0,stop:0 #2E7D32,stop:1 #43A047);"
            "color:white;font-weight:bold;padding:10px 20px;border-radius:6px;font-size:13px;}"
            "QPushButton:hover{background:qlineargradient(x1:0,y1:0,x2:1,y2:0,stop:0 #43A047,stop:1 #66BB6A);}"
        )
        self.btn_ai_batch.clicked.connect(self._ai_analyze_batch)
        self.btn_ai_stop = QPushButton("  Stop  ")
        self.btn_ai_stop.setEnabled(False)
        self.btn_ai_stop.setStyleSheet(
            "QPushButton{background:#c62828;color:white;font-weight:bold;padding:10px 16px;border-radius:6px;font-size:13px;}"
            "QPushButton:hover{background:#e53935;}"
        )
        self.btn_ai_stop.clicked.connect(self._ai_stop)
        ai_btn_row.addWidget(self.btn_ai_analyze)
        ai_btn_row.addWidget(self.btn_ai_batch)
        ai_btn_row.addWidget(self.btn_ai_stop)
        ai_layout.addLayout(ai_btn_row)

        options_layout = QHBoxLayout()
        options_layout.setSpacing(16)
        self.chk_auto_embed = QCheckBox("  Auto-embed after AI")
        self.chk_auto_embed.setChecked(self.presets.get("auto_embed", True))
        self.chk_auto_embed.setStyleSheet(
            "QCheckBox{font-weight:bold; color:#66BB6A; font-size:12px; spacing:8px;}"
            "QCheckBox::indicator{width:18px;height:18px;border-radius:4px;border:2px solid #555;background:#1a1a2e;}"
            "QCheckBox::indicator:checked{background:#66BB6A;border-color:#66BB6A;}"
        )
        self.chk_auto_rename = QCheckBox("  Auto-rename to title")
        self.chk_auto_rename.setChecked(self.presets.get("auto_rename", True))
        self.chk_auto_rename.setStyleSheet(
            "QCheckBox{font-weight:bold; color:#FFA726; font-size:12px; spacing:8px;}"
            "QCheckBox::indicator{width:18px;height:18px;border-radius:4px;border:2px solid #555;background:#1a1a2e;}"
            "QCheckBox::indicator:checked{background:#FFA726;border-color:#FFA726;}"
        )
        options_layout.addWidget(self.chk_auto_embed)
        options_layout.addWidget(self.chk_auto_rename)
        options_layout.addStretch()
        self.chk_save_copy.setChecked(self.presets.get("save_copy", False))
        saved_output = self.presets.get("output_path", "")
        if saved_output:
            self.output_path.setText(saved_output)
        ai_layout.addLayout(options_layout)

        self.ai_progress = QProgressBar()
        self.ai_progress.setValue(0)
        self.ai_progress.setFixedHeight(22)
        self.ai_progress.setFormat("%v%")
        self.ai_progress.setStyleSheet(
            "QProgressBar{border:1px solid #444;border-radius:5px;background:#1a1a2e;text-align:center;color:white;font-size:11px;font-weight:bold;}"
            "QProgressBar::chunk{background:qlineargradient(x1:0,y1:0,x2:1,y2:0,stop:0 #1E88E5,stop:1 #42A5F5);border-radius:4px;}"
        )
        ai_layout.addWidget(self.ai_progress)
        self.lbl_ai_status = QLabel("Ready - Select an image and click Analyze")
        self.lbl_ai_status.setStyleSheet("color: #8080a0; font-size: 11px;")
        ai_layout.addWidget(self.lbl_ai_status)

        self.creative_group = QGroupBox("  AI Image Prompt Output")
        creative_layout = QVBoxLayout()
        creative_layout.setSpacing(6)
        self.inp_creative_prompt = QTextEdit()
        self.inp_creative_prompt.setPlaceholderText("Generated prompt will appear here...")
        self.inp_creative_prompt.setMinimumHeight(120)
        self.inp_creative_prompt.setReadOnly(True)
        creative_layout.addWidget(QLabel("Prompt:"))
        creative_layout.addWidget(self.inp_creative_prompt)
        self.inp_creative_tags = QLineEdit()
        self.inp_creative_tags.setPlaceholderText("Style tags will appear here...")
        self.inp_creative_tags.setReadOnly(True)
        creative_layout.addWidget(QLabel("Style Tags:"))
        creative_layout.addWidget(self.inp_creative_tags)
        creative_btn_row = QHBoxLayout()
        self.btn_copy_prompt = QPushButton("  Copy Prompt  ")
        self.btn_copy_prompt.setStyleSheet(
            "QPushButton{background:#1565C0;color:white;border-radius:4px;padding:5px 12px;font-weight:bold;}"
            "QPushButton:hover{background:#1976D2;}"
        )
        self.btn_copy_prompt.clicked.connect(self._copy_creative_prompt)
        self.btn_copy_tags = QPushButton("  Copy Style Tags  ")
        self.btn_copy_tags.setStyleSheet(
            "QPushButton{background:#6A1B9A;color:white;border-radius:4px;padding:5px 12px;font-weight:bold;}"
            "QPushButton:hover{background:#8E24AA;}"
        )
        self.btn_copy_tags.clicked.connect(self._copy_creative_tags)
        self.btn_copy_all = QPushButton("  Copy All  ")
        self.btn_copy_all.setStyleSheet(
            "QPushButton{background:#00695C;color:white;border-radius:4px;padding:5px 12px;font-weight:bold;}"
            "QPushButton:hover{background:#00897B;}"
        )
        self.btn_copy_all.clicked.connect(self._copy_creative_all)
        creative_btn_row.addWidget(self.btn_copy_prompt)
        creative_btn_row.addWidget(self.btn_copy_tags)
        creative_btn_row.addWidget(self.btn_copy_all)
        creative_btn_row.addStretch()
        creative_layout.addLayout(creative_btn_row)
        self.creative_group.setLayout(creative_layout)
        self.creative_group.setVisible(False)
        ai_layout.addWidget(self.creative_group)
        ai_layout.addStretch()
        self.tabs.addTab(ai_tab, "  AI Auto-Tag  ")

        # ──── Tab 2: Manual Metadata ────
        manual_tab = QWidget()
        manual_layout = QVBoxLayout(manual_tab)
        manual_layout.setSpacing(8)
        meta_form = QFormLayout()
        meta_form.setSpacing(6)
        meta_form.setLabelAlignment(Qt.AlignmentFlag.AlignRight)
        self.inp_title = QLineEdit()
        self.inp_title.setPlaceholderText("e.g. Sunset Over the Mountains")
        self.inp_title.setMinimumHeight(28)
        title_row = QHBoxLayout()
        title_row.setSpacing(4)
        title_row.addWidget(self.inp_title)
        btn_copy_title = QPushButton("  Copy  ")
        btn_copy_title.setFixedWidth(65)
        btn_copy_title.setStyleSheet("QPushButton{font-size:10px;padding:4px;}")
        btn_copy_title.clicked.connect(lambda: self._copy_to_clipboard(self.inp_title.text(), "Title"))
        title_row.addWidget(btn_copy_title)
        meta_form.addRow("Title *:", title_row)
        self.inp_description = QTextEdit()
        self.inp_description.setPlaceholderText("Detailed description (3-5 sentences, SEO-optimized)")
        self.inp_description.setMaximumHeight(80)
        meta_form.addRow("Description *:", self.inp_description)
        self.inp_keywords = QTextEdit()
        self.inp_keywords.setPlaceholderText("Comma-separated keywords (max 49)")
        self.inp_keywords.setMaximumHeight(80)
        kw_row = QHBoxLayout()
        kw_row.setSpacing(4)
        kw_row.addWidget(self.inp_keywords)
        btn_copy_kw = QPushButton("  Copy  ")
        btn_copy_kw.setFixedWidth(65)
        btn_copy_kw.setStyleSheet("QPushButton{font-size:10px;padding:4px;}")
        btn_copy_kw.clicked.connect(lambda: self._copy_to_clipboard(self.inp_keywords.toPlainText(), "Keywords"))
        kw_row.addWidget(btn_copy_kw)
        meta_form.addRow("Keywords *:", kw_row)
        self.combo_category = QComboBox()
        self.combo_category.addItem("-- Select Category --", "")
        for name, num in sorted(ADOBE_STOCK_CATEGORIES.items()):
            self.combo_category.addItem(f"{num}. {name}", name)
        meta_form.addRow("Category *:", self.combo_category)
        self.inp_creator = QLineEdit()
        self.inp_creator.setPlaceholderText("Your name")
        meta_form.addRow("Creator:", self.inp_creator)
        self.inp_copyright = QLineEdit()
        self.inp_copyright.setPlaceholderText("2026 Your Name")
        meta_form.addRow("Copyright:", self.inp_copyright)
        manual_layout.addLayout(meta_form)

        copy_btn_row = QHBoxLayout()
        copy_btn_row.setSpacing(8)
        btn_copy_all = QPushButton("  Copy All (for Adobe Stock Portal)  ")
        btn_copy_all.setStyleSheet(
            "QPushButton{background:qlineargradient(x1:0,y1:0,x2:1,y2:0,stop:0 #E65100,stop:1 #FB8C00);"
            "color:white;font-weight:bold;padding:10px 16px;border-radius:6px;font-size:13px;}"
            "QPushButton:hover{background:qlineargradient(x1:0,y1:0,x2:1,y2:0,stop:0 #FB8C00,stop:1 #FFB74D);}"
        )
        btn_copy_all.clicked.connect(self._copy_all_metadata)
        btn_copy_title_kw = QPushButton("  Copy Title + Keywords  ")
        btn_copy_title_kw.setStyleSheet(
            "QPushButton{background:#533483;color:white;font-weight:bold;padding:10px 16px;border-radius:6px;font-size:13px;}"
            "QPushButton:hover{background:#6a4c9c;}"
        )
        btn_copy_title_kw.clicked.connect(self._copy_title_keywords)
        copy_btn_row.addWidget(btn_copy_all)
        copy_btn_row.addWidget(btn_copy_title_kw)
        copy_btn_row.addStretch()
        manual_layout.addLayout(copy_btn_row)
        xmp_group = QGroupBox("  XMP Preview")
        xmp_layout = QVBoxLayout()
        self.xmp_preview = QTextEdit()
        self.xmp_preview.setReadOnly(True)
        self.xmp_preview.setFont(QFont("Consolas", 9))
        self.xmp_preview.setMaximumHeight(130)
        xmp_layout.addWidget(self.xmp_preview)
        btn_preview = QPushButton("  Update Preview  ")
        btn_preview.setFixedWidth(130)
        btn_preview.clicked.connect(self._update_preview)
        xmp_layout.addWidget(btn_preview)
        xmp_group.setLayout(xmp_layout)
        manual_layout.addWidget(xmp_group)
        self.tabs.addTab(manual_tab, "  Manual Metadata  ")

        # ──── Tab 3: Per-File Results ────
        perfile_tab = QWidget()
        pf_layout = QVBoxLayout(perfile_tab)
        pf_layout.setSpacing(6)
        hint = QLabel("AI results per file. Double-click to load into editor.")
        hint.setStyleSheet("color: #8080a0; font-size: 11px; padding: 4px;")
        pf_layout.addWidget(hint)
        self.file_table = QTableWidget()
        self.file_table.setColumnCount(4)
        self.file_table.setHorizontalHeaderLabels(["  File  ", "  Title  ", "  Keywords  ", "  Category  "])
        hdr = self.file_table.horizontalHeader()
        hdr.setSectionResizeMode(0, QHeaderView.ResizeMode.ResizeToContents)
        hdr.setSectionResizeMode(1, QHeaderView.ResizeMode.Stretch)
        hdr.setSectionResizeMode(2, QHeaderView.ResizeMode.Stretch)
        hdr.setSectionResizeMode(3, QHeaderView.ResizeMode.ResizeToContents)
        self.file_table.setSelectionBehavior(QAbstractItemView.SelectionBehavior.SelectRows)
        self.file_table.setEditTriggers(QAbstractItemView.EditTrigger.NoEditTriggers)
        self.file_table.doubleClicked.connect(self._load_row_to_editor)
        self.file_table.setAlternatingRowColors(False)
        pf_layout.addWidget(self.file_table)
        pf_btn_row = QHBoxLayout()
        pf_btn_row.setSpacing(6)
        btn_load_row = QPushButton("  Load to Editor  ")
        btn_load_row.clicked.connect(self._load_row_to_editor)
        btn_apply_all = QPushButton("  Apply to All  ")
        btn_apply_all.clicked.connect(self._apply_to_all)
        btn_export_csv = QPushButton("  Export CSV  ")
        btn_export_csv.clicked.connect(self._export_csv)
        pf_btn_row.addWidget(btn_load_row)
        pf_btn_row.addWidget(btn_apply_all)
        pf_btn_row.addWidget(btn_export_csv)
        pf_btn_row.addStretch()
        pf_layout.addLayout(pf_btn_row)
        self.tabs.addTab(perfile_tab, "  Per-File Results  ")

        right_layout.addWidget(self.tabs, 1)

        settings_row = QHBoxLayout()
        settings_row.setSpacing(8)
        settings_row.addStretch()
        btn_save_preset = QPushButton("  Save Presets  ")
        btn_save_preset.setFixedWidth(110)
        btn_save_preset.clicked.connect(self._save_presets)
        settings_row.addWidget(btn_save_preset)
        btn_load_preset = QPushButton("  Load Presets  ")
        btn_load_preset.setFixedWidth(110)
        btn_load_preset.clicked.connect(self._load_presets_to_ui)
        settings_row.addWidget(btn_load_preset)
        right_layout.addLayout(settings_row)

        action_group = QGroupBox("  Embed Metadata")
        action_layout = QVBoxLayout()
        action_layout.setSpacing(6)
        self.progress_bar = QProgressBar()
        self.progress_bar.setValue(0)
        self.progress_bar.setFixedHeight(22)
        self.progress_bar.setFormat("%v%")
        self.progress_bar.setStyleSheet(
            "QProgressBar{border:1px solid #444;border-radius:5px;background:#1a1a2e;text-align:center;color:white;font-size:11px;font-weight:bold;}"
            "QProgressBar::chunk{background:qlineargradient(x1:0,y1:0,x2:1,y2:0,stop:0 #1E88E5,stop:1 #42A5F5);border-radius:4px;}"
        )
        action_layout.addWidget(self.progress_bar)
        self.lbl_status = QLabel("Ready")
        self.lbl_status.setStyleSheet("color: #b0b0d0; font-size: 11px;")
        action_layout.addWidget(self.lbl_status)
        embed_row = QHBoxLayout()
        embed_row.setSpacing(8)
        self.btn_process = QPushButton("   EMBED TAGS - ALL FILES   ")
        self.btn_process.setStyleSheet(
            "QPushButton{background:qlineargradient(x1:0,y1:0,x2:1,y2:0,stop:0 #BF360C,stop:1 #E64A19);"
            "color:white;font-weight:bold;padding:12px 24px;border-radius:6px;font-size:14px;}"
            "QPushButton:hover{background:qlineargradient(x1:0,y1:0,x2:1,y2:0,stop:0 #E64A19,stop:1 #FF5722);}"
        )
        self.btn_process.clicked.connect(self._process_files)
        self.btn_read_tags = QPushButton("  Read Tags  ")
        self.btn_read_tags.setFixedWidth(100)
        self.btn_read_tags.clicked.connect(self._read_tags)
        self.btn_view_tags = QPushButton("  View Tags  ")
        self.btn_view_tags.setFixedWidth(100)
        self.btn_view_tags.clicked.connect(self._view_tags_popup)
        self.btn_stop = QPushButton("  Stop  ")
        self.btn_stop.setEnabled(False)
        self.btn_stop.setFixedWidth(70)
        self.btn_stop.setStyleSheet(
            "QPushButton{background:#c62828;color:white;font-weight:bold;padding:8px;border-radius:6px;}"
            "QPushButton:hover{background:#e53935;}"
        )
        self.btn_stop.clicked.connect(self._stop_process)
        embed_row.addWidget(self.btn_process)
        embed_row.addWidget(self.btn_read_tags)
        embed_row.addWidget(self.btn_view_tags)
        embed_row.addWidget(self.btn_stop)
        action_layout.addLayout(embed_row)
        action_group.setLayout(action_layout)
        right_layout.addWidget(action_group)

        splitter = QSplitter(Qt.Orientation.Horizontal)
        splitter.setHandleWidth(3)
        splitter.addWidget(left_panel)
        splitter.addWidget(right_panel)
        splitter.setSizes([380, 820])
        main_layout.addWidget(splitter)

        self.status_bar = QStatusBar()
        self.setStatusBar(self.status_bar)
        self.status_bar.showMessage("Ready")
        self.lbl_version = QLabel(f"v{APP_VERSION}")
        self.lbl_version.setStyleSheet("color:#8080a0;font-size:11px;padding:0 8px;")
        self.status_bar.addPermanentWidget(self.lbl_version)
        self.btn_check_update = QPushButton("Check Update")
        self.btn_check_update.setFlat(True)
        self.btn_check_update.setStyleSheet(
            "QPushButton{color:#8080a0;font-size:11px;border:none;padding:0 4px;}"
            "QPushButton:hover{color:#4FC3F7;text-decoration:underline;}"
        )
        self.btn_check_update.clicked.connect(self._check_for_update)
        self.btn_check_update.setContextMenuPolicy(Qt.ContextMenuPolicy.CustomContextMenu)
        self.btn_check_update.customContextMenuRequested.connect(self._update_settings)
        self.status_bar.addPermanentWidget(self.btn_check_update)

        if self.dark_mode:
            self._toggle_dark(2)

    def _setup_shortcuts(self):
        QShortcut(QKeySequence("Ctrl+O"), self, self._add_files)
        QShortcut(QKeySequence("Ctrl+V"), self, self._paste_image)
        QShortcut(QKeySequence("Delete"), self, self._remove_selected)
        QShortcut(QKeySequence("Ctrl+Return"), self, self._process_files)
        QShortcut(QKeySequence("Ctrl+D"), self, self._ai_analyze_single)
        QShortcut(QKeySequence("Ctrl+B"), self, self._ai_analyze_batch)
        QShortcut(QKeySequence("Ctrl+E"), self, self._export_csv)
        QShortcut(QKeySequence("Ctrl+S"), self, self._save_presets)
        QShortcut(QKeySequence("Ctrl+U"), self, self._check_for_update)
        QShortcut(QKeySequence("Ctrl+L"), self, self._open_file_location)

    def _get_github_headers(self):
        headers = {"Accept": "application/vnd.github.v3+json"}
        token = self.presets.get("github_token", "")
        if token:
            headers["Authorization"] = f"token {token}"
        return headers

    def _check_for_update(self):
        repo = self.presets.get("update_repo", UPDATE_REPO).strip()
        if not repo:
            QMessageBox.information(self, "Update", "No update repo configured.\n\n"
                "Go to Settings and set your GitHub repo\n"
                "(e.g. 'username/stock-tagger').")
            return
        self.btn_check_update.setEnabled(False)
        self.btn_check_update.setText("Checking...")
        QApplication.processEvents()
        try:
            ctx = None
            try:
                ctx = ssl.create_default_context()
            except Exception:
                ctx = ssl._create_unverified_context()
            url = f"https://raw.githubusercontent.com/{repo}/main/version.json"
            req = urllib.request.Request(url, headers=self._get_github_headers())
            resp = urllib.request.urlopen(req, timeout=15, context=ctx)
            data = json.loads(resp.read().decode("utf-8"))
            remote_ver = data.get("version", "0.0.0")
            remote_date = data.get("date", "")
            changelog = data.get("changelog", "")
            download_url = data.get("download_url", "")
            if self._version_compare(remote_ver, APP_VERSION) > 0:
                msg = (f"New version available: {remote_ver}\n"
                       f"Current: v{APP_VERSION}\n"
                       f"Date: {remote_date}\n\n"
                       f"{changelog}\n\n"
                       f"Download and replace current version?")
                reply = QMessageBox.information(
                    self, "Update Available", msg,
                    QMessageBox.StandardButton.Yes | QMessageBox.StandardButton.No,
                )
                if reply == QMessageBox.StandardButton.Yes:
                    self._download_update(repo, data)
            else:
                QMessageBox.information(self, "Up to Date",
                    f"You are running the latest version (v{APP_VERSION}).")
        except Exception as e:
            QMessageBox.warning(self, "Update Error", f"Failed to check for updates:\n{e}")
        finally:
            self.btn_check_update.setEnabled(True)
            self.btn_check_update.setText("Check Update")

    def _version_compare(self, remote, local):
        def parse(v):
            return [int(x) for x in v.split(".") if x.isdigit()]
        r = parse(remote)
        l = parse(local)
        for i in range(max(len(r), len(l))):
            rv = r[i] if i < len(r) else 0
            lv = l[i] if i < len(l) else 0
            if rv != lv:
                return 1 if rv > lv else -1
        return 0

    def _download_update(self, repo, version_data):
        download_url = version_data.get("download_url", "")
        self.btn_check_update.setEnabled(False)
        self.btn_check_update.setText("Downloading...")
        self.status_bar.showMessage("Downloading update...")
        QApplication.processEvents()
        try:
            ctx = None
            try:
                ctx = ssl.create_default_context()
            except Exception:
                ctx = ssl._create_unverified_context()
            headers = self._get_github_headers()

            build_url = f"https://raw.githubusercontent.com/{repo}/main/build.py"
            req = urllib.request.Request(build_url, headers=headers)
            resp = urllib.request.urlopen(req, timeout=30, context=ctx)
            build_content = resp.read().decode("utf-8")

            script_dir = os.path.dirname(os.path.abspath(sys.argv[0]))
            if getattr(sys, 'frozen', False):
                script_dir = os.path.dirname(sys.executable)
            build_path = os.path.join(script_dir, "build.py")
            with open(build_path, "w", encoding="utf-8") as f:
                f.write(build_content)

            ver_path = os.path.join(script_dir, "version.json")
            with open(ver_path, "w", encoding="utf-8") as f:
                json.dump(version_data, f, indent=2)

            self.status_bar.showMessage("Update downloaded! Running build...")
            QApplication.processEvents()

            if getattr(sys, 'frozen', False):
                result = subprocess.run(
                    [sys.executable, "--run", "build.py"],
                    capture_output=True, timeout=60,
                    creationflags=getattr(subprocess, 'CREATE_NO_WINDOW', 0),
                )
                if result.returncode == 0:
                    QMessageBox.information(self, "Updated!",
                        f"Updated to v{version_data.get('version', '?')}!\n\n"
                        "Please restart the application.")
                else:
                    QMessageBox.warning(self, "Build Error",
                        f"Downloaded update but build failed.\n"
                        f"Run 'python build.py' manually.")
            else:
                result = subprocess.run(
                    [sys.executable, build_path],
                    capture_output=True, timeout=60,
                )
                if result.returncode == 0:
                    reply = QMessageBox.information(self, "Updated!",
                        f"Updated to v{version_data.get('version', '?')}!\n\n"
                        "Restart now?",
                        QMessageBox.StandardButton.Yes | QMessageBox.StandardButton.No,
                    )
                    if reply == QMessageBox.StandardButton.Yes:
                        os.execv(sys.executable, [sys.executable] + sys.argv)
                else:
                    QMessageBox.warning(self, "Build Error",
                        "Downloaded update but build failed.\n"
                        f"Output:\n{result.stderr.decode('utf-8', errors='replace')[:500]}")
        except Exception as e:
            QMessageBox.warning(self, "Download Error", f"Failed to download update:\n{e}")
        finally:
            self.btn_check_update.setEnabled(True)
            self.btn_check_update.setText("Check Update")

    def _update_settings(self):
        dlg = QDialog(self)
        dlg.setWindowTitle("Update Settings")
        dlg.setMinimumWidth(450)
        dlg.setStyleSheet(self.styleSheet())
        layout = QFormLayout(dlg)
        inp_repo = QLineEdit(self.presets.get("update_repo", UPDATE_REPO))
        inp_repo.setPlaceholderText("username/stock-tagger")
        inp_token = QLineEdit(self.presets.get("github_token", ""))
        inp_token.setPlaceholderText("ghp_xxx (leave empty for public repos)")
        inp_token.setEchoMode(QLineEdit.EchoMode.Password)
        btn_toggle = QPushButton("  Show  ")
        btn_toggle.setFixedWidth(60)
        def _toggle():
            if inp_token.echoMode() == QLineEdit.EchoMode.Password:
                inp_token.setEchoMode(QLineEdit.EchoMode.Normal)
                btn_toggle.setText("  Hide  ")
            else:
                inp_token.setEchoMode(QLineEdit.EchoMode.Password)
                btn_toggle.setText("  Show  ")
        btn_toggle.clicked.connect(_toggle)
        token_row = QHBoxLayout()
        token_row.addWidget(inp_token)
        token_row.addWidget(btn_toggle)
        layout.addRow("GitHub Repo:", inp_repo)
        layout.addRow("GitHub Token:", token_row)
        note = QLabel("(Right-click 'Check Update' to open this)\n"
                       "Public repo: leave token empty\n"
                       "Private repo: create token at github.com/settings/tokens\n"
                       "Check 'repo' scope only.")
        note.setStyleSheet("color:#8080a0;font-size:10px;")
        layout.addRow("", note)
        btn_box = QHBoxLayout()
        btn_ok = QPushButton("  Save  ")
        btn_cancel = QPushButton("  Cancel  ")
        btn_ok.clicked.connect(dlg.accept)
        btn_cancel.clicked.connect(dlg.reject)
        btn_box.addWidget(btn_ok)
        btn_box.addWidget(btn_cancel)
        layout.addRow("", btn_box)
        if dlg.exec() == QDialog.DialogCode.Accepted:
            self.presets["update_repo"] = inp_repo.text().strip()
            self.presets["github_token"] = inp_token.text().strip()
            save_presets_to_file(self.presets)
            self.status_bar.showMessage("Update settings saved!", 3000)

    def dragEnterEvent(self, event):
        if event.mimeData().hasUrls():
            event.acceptProposedAction()

    def _paste_image(self):
        clipboard = QApplication.clipboard()
        mime = clipboard.mimeData()
        if mime.hasImage():
            image = clipboard.image()
            if image.isNull():
                QMessageBox.warning(self, "Warning", "Cannot read image from clipboard!")
                return
            os.makedirs(TEMP_DIR, exist_ok=True)
            ts = int(time.time() * 1000)
            fp = os.path.join(TEMP_DIR, f"paste_{ts}.png")
            image.save(fp, "PNG")
            if fp not in self.files:
                self.files.append(fp)
                self._add_file_with_icon(fp)
                self._update_count()
                self.status_bar.showMessage(f"Pasted image: {os.path.basename(fp)}", 3000)
        elif mime.hasUrls():
            for url in mime.urls():
                fp = url.toLocalFile()
                if os.path.isfile(fp) and Path(fp).suffix.lower() in SUPPORTED_EXTENSIONS:
                    if fp not in self.files:
                        self.files.append(fp)
                        self._add_file_with_icon(fp)
            self._update_count()
        else:
            QMessageBox.information(self, "Info", "No image in clipboard!\nCopy an image first, then Ctrl+V to paste.")

    def dropEvent(self, event):
        for url in event.mimeData().urls():
            fp = url.toLocalFile()
            if os.path.isfile(fp) and Path(fp).suffix.lower() in SUPPORTED_EXTENSIONS:
                if fp not in self.files:
                    self.files.append(fp)
                    self._add_file_with_icon(fp)
            elif os.path.isdir(fp):
                for root, _, fnames in os.walk(fp):
                    for fn in sorted(fnames):
                        if Path(fn).suffix.lower() in SUPPORTED_EXTENSIONS:
                            fpath = os.path.join(root, fn)
                            if fpath not in self.files:
                                self.files.append(fpath)
                                self._add_file_with_icon(fpath)
        self._update_count()

    def _on_provider_changed(self, index):
        provider = self.combo_provider.currentData()
        self.combo_model.clear()
        show_api = provider in ("openai", "gemini")
        for w in self.api_key_widgets:
            w.setVisible(show_api)
        self.inp_api_key.setVisible(False)
        self.btn_start_ollama.setVisible(provider == "ollama")
        self.btn_stop_ollama.setVisible(provider == "ollama")
        if provider == "ollama":
            self.btn_refresh_models.setVisible(True)
            self.btn_refresh_models.setText("  Refresh  ")
            try:
                self.btn_refresh_models.clicked.disconnect()
            except TypeError:
                pass
            self.btn_refresh_models.clicked.connect(self._check_ollama)
            self._check_ollama()
        elif provider == "openai":
            self.btn_refresh_models.setVisible(True)
            self.btn_refresh_models.setText("  Fetch  ")
            self.btn_refresh_models.clicked.disconnect()
            self.btn_refresh_models.clicked.connect(self._fetch_openai_models)
            for m in ["gpt-4o", "gpt-4o-mini"]:
                self.combo_model.addItem(m)
            self.lbl_ollama_status.setText("Select or enter OpenAI API key, click Fetch")
            self.lbl_ollama_status.setStyleSheet("color:#FFA726;font-size:11px;")
            self._load_api_keys_for_provider("openai")
        elif provider == "gemini":
            self.btn_refresh_models.setVisible(True)
            self.btn_refresh_models.setText("  Fetch  ")
            try:
                self.btn_refresh_models.clicked.disconnect()
            except TypeError:
                pass
            self.btn_refresh_models.clicked.connect(self._fetch_gemini_models)
            self.lbl_ollama_status.setText("Select API key, click Fetch to list models")
            self.lbl_ollama_status.setStyleSheet("color:#FFA726;font-size:11px;")
            self._load_api_keys_for_provider("gemini")

    def _on_platform_changed(self, index):
        platform = self.combo_platform.currentData()
        current_cat = self.combo_category.currentData() or ""
        self.combo_category.clear()
        self.combo_category.addItem("-- Select Category --", "")
        if platform == "shutterstock":
            for name in sorted(SHUTTERSTOCK_CATEGORIES.keys()):
                self.combo_category.addItem(name, name)
        elif platform == "freepik":
            for name, val in sorted(FREEPIK_CATEGORIES.items()):
                self.combo_category.addItem(name, val)
        else:
            for name, num in sorted(ADOBE_STOCK_CATEGORIES.items()):
                self.combo_category.addItem(f"{num}. {name}", name)
        idx = self.combo_category.findData(current_cat)
        if idx >= 0:
            self.combo_category.setCurrentIndex(idx)

    def _on_mode_changed(self, index):
        mode = self.combo_mode.currentData()
        is_creative = mode == "creative"
        self.creative_group.setVisible(is_creative)
        self.chk_auto_embed.setVisible(not is_creative)
        self.chk_auto_rename.setVisible(not is_creative)
        self.combo_platform.setVisible(not is_creative)

    def _copy_creative_prompt(self):
        text = self.inp_creative_prompt.toPlainText()
        if text:
            QApplication.clipboard().setText(text)
            self.status_bar.showMessage("Prompt copied!", 3000)

    def _copy_creative_tags(self):
        text = self.inp_creative_tags.text()
        if text:
            QApplication.clipboard().setText(text)
            self.status_bar.showMessage("Style tags copied!", 3000)

    def _copy_creative_all(self):
        parts = []
        prompt = self.inp_creative_prompt.toPlainText()
        tags = self.inp_creative_tags.text()
        if prompt:
            parts.append(f"Prompt:\n{prompt}")
        if tags:
            parts.append(f"\nStyle Tags:\n{tags}")
        if parts:
            QApplication.clipboard().setText("\n".join(parts))
            self.status_bar.showMessage("All copied!", 3000)

    def _fetch_gemini_models(self):
        api_key = self._get_current_api_key()
        if not api_key:
            QMessageBox.warning(self, "Warning", "Enter or select an API key first!")
            return
        self.combo_model.clear()
        self.btn_refresh_models.setEnabled(False)
        self.lbl_ollama_status.setText("Fetching available models...")
        self.lbl_ollama_status.setStyleSheet("color:#FFA726;font-size:11px;")
        QApplication.processEvents()
        try:
            ctx = None
            try:
                ctx = ssl.create_default_context()
            except Exception:
                ctx = ssl._create_unverified_context()
            conn_ssl = urllib.request.HTTPSHandler(context=ctx)
            opener = urllib.request.build_opener(conn_ssl)
            url = f"https://generativelanguage.googleapis.com/v1beta/models?key={api_key}"
            req = urllib.request.Request(url)
            resp = opener.open(req, timeout=15)
            data = json.loads(resp.read().decode('utf-8'))
            vision_models = []
            FREE_KEYWORDS = ["flash", "lite"]
            PAID_KEYWORDS = ["pro", "thinking", "ultra", "enterprise"]
            for m in data.get("models", []):
                name = m.get("name", "")
                display = name.replace("models/", "")
                methods = m.get("supportedGenerationMethods", [])
                if "generateContent" not in methods:
                    continue
                dl = display.lower()
                if any(pk in dl for pk in PAID_KEYWORDS):
                    continue
                if any(fk in dl for fk in FREE_KEYWORDS):
                    vision_models.append(display)
            vision_models.sort(reverse=True)
            if vision_models:
                for m in vision_models:
                    self.combo_model.addItem(m)
                self.lbl_ollama_status.setText(f"Found {len(vision_models)} models")
                self.lbl_ollama_status.setStyleSheet("color:#66BB6A;font-weight:bold;font-size:11px;")
            else:
                self.lbl_ollama_status.setText("No vision models found for this key")
                self.lbl_ollama_status.setStyleSheet("color:#e53935;font-size:11px;")
        except urllib.error.HTTPError as e:
            body = ""
            try:
                body = json.loads(e.read().decode("utf-8", errors="replace")).get("error", {}).get("message", "")
            except Exception:
                pass
            self.lbl_ollama_status.setText(f"API Error: {e.code}")
            self.lbl_ollama_status.setStyleSheet("color:#e53935;font-size:11px;")
            QMessageBox.critical(self, "Error", f"HTTP {e.code}: {body}")
        except Exception as e:
            self.lbl_ollama_status.setText(f"Error: {str(e)[:50]}")
            self.lbl_ollama_status.setStyleSheet("color:#e53935;font-size:11px;")
        finally:
            self.btn_refresh_models.setEnabled(True)

    def _fetch_openai_models(self):
        api_key = self._get_current_api_key()
        if not api_key:
            QMessageBox.warning(self, "Warning", "Enter or select an API key first!")
            return
        self.combo_model.clear()
        self.btn_refresh_models.setEnabled(False)
        self.lbl_ollama_status.setText("Fetching available models...")
        self.lbl_ollama_status.setStyleSheet("color:#FFA726;font-size:11px;")
        QApplication.processEvents()
        try:
            ctx = None
            try:
                ctx = ssl.create_default_context()
            except Exception:
                ctx = ssl._create_unverified_context()
            conn_ssl = urllib.request.HTTPSHandler(context=ctx)
            opener = urllib.request.build_opener(conn_ssl)
            url = "https://api.openai.com/v1/models"
            req = urllib.request.Request(url, headers={"Authorization": f"Bearer {api_key}"})
            resp = opener.open(req, timeout=15)
            data = json.loads(resp.read().decode('utf-8'))
            vision_models = []
            for m in data.get("data", []):
                mid = m.get("id", "")
                if "gpt-4o" in mid or "gpt-4" in mid:
                    vision_models.append(mid)
            vision_models.sort(reverse=True)
            if vision_models:
                for m in vision_models:
                    self.combo_model.addItem(m)
                self.lbl_ollama_status.setText(f"Found {len(vision_models)} vision models")
                self.lbl_ollama_status.setStyleSheet("color:#66BB6A;font-weight:bold;font-size:11px;")
            else:
                for m in ["gpt-4o", "gpt-4o-mini"]:
                    self.combo_model.addItem(m)
                self.lbl_ollama_status.setText("Using default models")
                self.lbl_ollama_status.setStyleSheet("color:#FFA726;font-size:11px;")
        except Exception as e:
            for m in ["gpt-4o", "gpt-4o-mini"]:
                self.combo_model.addItem(m)
            self.lbl_ollama_status.setText(f"Using defaults (fetch failed)")
            self.lbl_ollama_status.setStyleSheet("color:#FFA726;font-size:11px;")
        finally:
            self.btn_refresh_models.setEnabled(True)

    def _load_api_keys_for_provider(self, provider):
        self.combo_api_keys.blockSignals(True)
        self.combo_api_keys.clear()
        try:
            self.combo_api_keys.currentIndexChanged.disconnect(self._on_api_key_selected)
        except TypeError:
            pass
        saved_keys = self.presets.get("api_keys", {})
        keys = saved_keys.get(provider, [])
        for name, key in keys:
            label = f"{name} ({key[:8]}...)" if len(key) > 8 else f"{name} ({key})"
            self.combo_api_keys.addItem(label, key)
        self.combo_api_keys.addItem("+ Enter new key...", "NEW")
        self.combo_api_keys.currentIndexChanged.connect(self._on_api_key_selected)
        self.combo_api_keys.blockSignals(False)
        if keys:
            self.combo_api_keys.setCurrentIndex(0)
            self.inp_api_key.setVisible(False)
        else:
            self.combo_api_keys.setVisible(False)
            self.inp_api_key.setVisible(True)

    def _on_api_key_selected(self, index):
        key = self.combo_api_keys.currentData()
        if key == "NEW":
            self.combo_api_keys.setVisible(False)
            self.inp_api_key.setVisible(True)
            self.inp_api_key.clear()
        else:
            self.inp_api_key.setVisible(False)
            provider = self.combo_provider.currentData()
            if provider == "gemini":
                self._fetch_gemini_models()
            elif provider == "openai":
                self._fetch_openai_models()

    def _save_api_key(self):
        key = self.inp_api_key.text().strip()
        if not key:
            QMessageBox.warning(self, "Warning", "Enter an API key first!")
            return
        name, ok = QInputDialog.getText(self, "API Key Name", "Name this key:", text=f"Key {self.combo_api_keys.count()}")
        if not ok or not name.strip():
            return
        name = name.strip()
        provider = self.combo_provider.currentData()
        if not self.presets.get("api_keys"):
            self.presets["api_keys"] = {}
        if not self.presets["api_keys"].get(provider):
            self.presets["api_keys"][provider] = []
        keys = self.presets["api_keys"][provider]
        keys.append([name, key])
        save_presets_to_file(self.presets)
        self.combo_api_keys.blockSignals(True)
        label = f"{name} ({key[:8]}...)" if len(key) > 8 else f"{name} ({key})"
        self.combo_api_keys.insertItem(self.combo_api_keys.count() - 1, label, key)
        self.combo_api_keys.setCurrentIndex(self.combo_api_keys.count() - 2)
        self.combo_api_keys.blockSignals(False)
        self.inp_api_key.setVisible(False)
        self.status_bar.showMessage(f"API key '{name}' saved!", 3000)

    def _delete_api_key(self):
        idx = self.combo_api_keys.currentIndex()
        key = self.combo_api_keys.currentData()
        if key == "NEW" or idx < 0:
            return
        provider = self.combo_provider.currentData()
        keys = self.presets.get("api_keys", {}).get(provider, [])
        keys = [k for k in keys if k[1] != key]
        self.presets.setdefault("api_keys", {})[provider] = keys
        save_presets_to_file(self.presets)
        self.combo_api_keys.blockSignals(True)
        self.combo_api_keys.removeItem(idx)
        self.combo_api_keys.blockSignals(False)
        self.status_bar.showMessage("API key deleted!", 3000)

    def _edit_api_key(self):
        idx = self.combo_api_keys.currentIndex()
        key = self.combo_api_keys.currentData()
        if key == "NEW" or idx < 0:
            return
        provider = self.combo_provider.currentData()
        keys = self.presets.get("api_keys", {}).get(provider, [])
        old_name = ""
        for name, k in keys:
            if k == key:
                old_name = name
                break
        dlg = QDialog(self)
        dlg.setWindowTitle("Edit API Key")
        dlg.setMinimumWidth(420)
        dlg.setStyleSheet(self.styleSheet())
        layout = QFormLayout(dlg)
        inp_name = QLineEdit(old_name)
        inp_name.setPlaceholderText("Key name")
        inp_key = QLineEdit(key)
        inp_key.setPlaceholderText("API key")
        inp_key.setEchoMode(QLineEdit.EchoMode.Password)
        btn_toggle = QPushButton("  Show  ")
        btn_toggle.setFixedWidth(60)
        def _toggle():
            if inp_key.echoMode() == QLineEdit.EchoMode.Password:
                inp_key.setEchoMode(QLineEdit.EchoMode.Normal)
                btn_toggle.setText("  Hide  ")
            else:
                inp_key.setEchoMode(QLineEdit.EchoMode.Password)
                btn_toggle.setText("  Show  ")
        btn_toggle.clicked.connect(_toggle)
        key_row = QHBoxLayout()
        key_row.addWidget(inp_key)
        key_row.addWidget(btn_toggle)
        layout.addRow("Name:", inp_name)
        layout.addRow("API Key:", key_row)
        btn_box = QHBoxLayout()
        btn_ok = QPushButton("  Save  ")
        btn_cancel = QPushButton("  Cancel  ")
        btn_ok.clicked.connect(dlg.accept)
        btn_cancel.clicked.connect(dlg.reject)
        btn_box.addWidget(btn_ok)
        btn_box.addWidget(btn_cancel)
        layout.addRow("", btn_box)
        if dlg.exec() != QDialog.DialogCode.Accepted:
            return
        new_name = inp_name.text().strip()
        new_key = inp_key.text().strip()
        if not new_name or not new_key:
            QMessageBox.warning(self, "Warning", "Name and key cannot be empty!")
            return
        for i, (n, k) in enumerate(keys):
            if k == key:
                keys[i] = [new_name, new_key]
                break
        self.presets.setdefault("api_keys", {})[provider] = keys
        save_presets_to_file(self.presets)
        self.combo_api_keys.blockSignals(True)
        label = f"{new_name} ({new_key[:8]}...)" if len(new_key) > 8 else f"{new_name} ({new_key})"
        self.combo_api_keys.setItemText(idx, label)
        self.combo_api_keys.setItemData(idx, new_key)
        self.combo_api_keys.blockSignals(False)
        self.status_bar.showMessage(f"API key '{new_name}' updated!", 3000)

    def _toggle_api_key_visibility(self):
        if self.inp_api_key.isVisible():
            if self.inp_api_key.echoMode() == QLineEdit.EchoMode.Password:
                self.inp_api_key.setEchoMode(QLineEdit.EchoMode.Normal)
                self.btn_show_key.setText("  Hide  ")
            else:
                self.inp_api_key.setEchoMode(QLineEdit.EchoMode.Password)
                self.btn_show_key.setText("  Show  ")
        else:
            key = self.combo_api_keys.currentData()
            if key and key != "NEW":
                QMessageBox.information(self, "API Key", f"Selected key:\n\n{key}")

    def _test_api_key(self):
        api_key = self._get_current_api_key()
        provider = self.combo_provider.currentData()
        if not api_key:
            QMessageBox.warning(self, "Warning", "Enter or select an API key first!")
            return
        self.btn_test_api.setEnabled(False)
        self.lbl_ollama_status.setText("Testing API key...")
        self.lbl_ollama_status.setStyleSheet("color:#FFA726;font-size:11px;")
        QApplication.processEvents()
        try:
            ctx = None
            try:
                ctx = ssl.create_default_context()
            except Exception:
                ctx = ssl._create_unverified_context()
            conn_ssl = urllib.request.HTTPSHandler(context=ctx)
            opener = urllib.request.build_opener(conn_ssl)
            if provider == "gemini":
                model = self.combo_model.currentText() or "gemini-2.5-flash"
                url = f"https://generativelanguage.googleapis.com/v1beta/models/{model}:generateContent?key={api_key}"
                payload = json.dumps({"contents": [{"parts": [{"text": "Hi"}]}]}).encode('utf-8')
                req = urllib.request.Request(url, data=payload, headers={"Content-Type": "application/json"})
                resp = opener.open(req, timeout=15)
                headers = resp.headers
                info_lines = ["<b style='color:#66BB6A'>API Key OK!</b><br>"]
                quota_keys = [
                    ("x-ratelimit-remaining", "Requests remaining"),
                    ("x-ratelimit-limit", "Requests limit"),
                    ("x-ratelimit-reset", "Reset"),
                    ("x-ratelimit-requests-remaining", "RPM remaining"),
                    ("x-ratelimit-requests-limit", "RPM limit"),
                    ("x-ratelimit-tokens-remaining", "Tokens remaining/day"),
                    ("x-ratelimit-tokens-limit", "Tokens limit/day"),
                ]
                found = False
                for hk, label in quota_keys:
                    val = headers.get(hk)
                    if val:
                        found = True
                        info_lines.append(f"<b>{label}:</b> {val}")
                if not found:
                    info_lines.append("<i>No quota headers returned (request succeeded)</i>")
                self.lbl_ollama_status.setText("")
                self.lbl_ollama_status.setStyleSheet("")
                QMessageBox.information(self, "API Test - Gemini", "<br>".join(info_lines))
            elif provider == "openai":
                url = "https://api.openai.com/v1/models"
                req = urllib.request.Request(url, headers={
                    "Authorization": f"Bearer {api_key}",
                })
                resp = opener.open(req, timeout=15)
                data = json.loads(resp.read().decode('utf-8'))
                model_count = len(data.get("data", []))
                self.lbl_ollama_status.setText("")
                self.lbl_ollama_status.setStyleSheet("")
                QMessageBox.information(self, "API Test - OpenAI",
                    f"<b style='color:#66BB6A'>API Key OK!</b><br>"
                    f"<b>Accessible models:</b> {model_count}<br>"
                    f"<i>Note: OpenAI does not expose quota info via API</i>")
        except urllib.error.HTTPError as e:
            body = ""
            try:
                body = e.read().decode("utf-8", errors="replace")
                j = json.loads(body)
                body = j.get("error", {}).get("message", body)
            except Exception:
                pass
            self.lbl_ollama_status.setText(f"API Error: {e.code}")
            self.lbl_ollama_status.setStyleSheet("color:#EF5350;font-size:11px;")
            QMessageBox.critical(self, "API Test Failed",
                f"<b style='color:#EF5350'>HTTP {e.code}</b><br>{body}")
        except Exception as e:
            self.lbl_ollama_status.setText(f"Error: {str(e)[:50]}")
            self.lbl_ollama_status.setStyleSheet("color:#EF5350;font-size:11px;")
            QMessageBox.critical(self, "API Test Failed", f"<b style='color:#EF5350'>Error</b><br>{str(e)}")
        finally:
            self.btn_test_api.setEnabled(True)

    def _start_ollama(self):
        self.btn_start_ollama.setEnabled(False)
        self.lbl_ollama_status.setText("Starting Ollama...")
        self.lbl_ollama_status.setStyleSheet("color:#FFA726;font-size:11px;")
        QApplication.processEvents()
        try:
            ctx = None
            try:
                ctx = ssl.create_default_context()
            except Exception:
                ctx = ssl._create_unverified_context()
            try:
                req = urllib.request.Request("http://127.0.0.1:11434/api/tags")
                urllib.request.urlopen(req, timeout=2, context=ctx)
                self.lbl_ollama_status.setText("Already running!")
                self.lbl_ollama_status.setStyleSheet("color:#66BB6A;font-weight:bold;font-size:11px;")
                self._check_ollama()
                return
            except Exception:
                pass
            try:
                subprocess.Popen(["ollama", "serve"],
                    creationflags=getattr(subprocess, 'CREATE_NO_WINDOW', 0))
            except FileNotFoundError:
                self.lbl_ollama_status.setText("Ollama not installed!")
                self.lbl_ollama_status.setStyleSheet("color:#e53935;font-weight:bold;font-size:11px;")
                QMessageBox.critical(self, "Error", "Ollama not found!\nInstall: winget install Ollama.Ollama")
                return
            except Exception:
                try:
                    subprocess.Popen(["ollama.exe", "serve"],
                        creationflags=getattr(subprocess, 'CREATE_NO_WINDOW', 0))
                except FileNotFoundError:
                    self.lbl_ollama_status.setText("Ollama not installed!")
                    self.lbl_ollama_status.setStyleSheet("color:#e53935;font-weight:bold;font-size:11px;")
                    return
            import time
            for i in range(10):
                time.sleep(1)
                self.lbl_ollama_status.setText(f"Waiting for Ollama... ({i+1}/10)")
                QApplication.processEvents()
                try:
                    req = urllib.request.Request("http://127.0.0.1:11434/api/tags")
                    urllib.request.urlopen(req, timeout=2, context=ctx)
                    self._check_ollama()
                    return
                except Exception:
                    continue
            self.lbl_ollama_status.setText("Ollama not responding after 10s")
            self.lbl_ollama_status.setStyleSheet("color:#e53935;font-size:11px;")
            QMessageBox.warning(self, "Warning",
                "Ollama started but not responding.\n"
                "Try: Open terminal, run 'ollama serve' manually,\n"
                "or check if Ollama desktop app is installed.")
        except Exception as e:
            self.lbl_ollama_status.setText(f"Error: {str(e)[:40]}")
            self.lbl_ollama_status.setStyleSheet("color:#e53935;font-size:11px;")
        finally:
            self.btn_start_ollama.setEnabled(True)

    def _stop_ollama(self):
        reply = QMessageBox.question(
            self, "Stop Ollama",
            "Stop Ollama service?\nThis will kill the ollama process.",
            QMessageBox.StandardButton.Yes | QMessageBox.StandardButton.No,
        )
        if reply != QMessageBox.StandardButton.Yes:
            return
        self.btn_stop_ollama.setEnabled(False)
        self.lbl_ollama_status.setText("Stopping Ollama...")
        self.lbl_ollama_status.setStyleSheet("color:#FFA726;font-size:11px;")
        QApplication.processEvents()
        try:
            subprocess.run(["taskkill", "/F", "/IM", "ollama.exe"],
                          capture_output=True, creationflags=getattr(subprocess, 'CREATE_NO_WINDOW', 0))
            import time
            time.sleep(2)
            self.combo_model.clear()
            self.lbl_ollama_status.setText("Ollama stopped")
            self.lbl_ollama_status.setStyleSheet("color:#FFA726;font-size:11px;")
        except Exception as e:
            self.lbl_ollama_status.setText(f"Stop failed: {str(e)[:40]}")
            self.lbl_ollama_status.setStyleSheet("color:#e53935;font-size:11px;")
        finally:
            self.btn_stop_ollama.setEnabled(True)

    def _check_ollama(self):
        ok, models = check_ollama_connection()
        self.combo_model.clear()
        if ok:
            vision = [m for m in models if any(v in m.lower()
                      for v in ["llava", "moondream", "bakllava", "vision"])]
            if not vision:
                vision = models
            for m in vision:
                self.combo_model.addItem(m)
            self.lbl_ollama_status.setText(f"Connected ({len(vision)} models)")
            self.lbl_ollama_status.setStyleSheet("color:#66BB6A;font-weight:bold;font-size:11px;")
        else:
            self.lbl_ollama_status.setText("Ollama not running!")
            self.lbl_ollama_status.setStyleSheet("color:#e53935;font-weight:bold;font-size:11px;")

    def _add_files(self):
        exts = ' '.join(f'*{e}' for e in SUPPORTED_EXTENSIONS)
        files, _ = QFileDialog.getOpenFileNames(self, "Select Images", "", f"Images ({exts});;All (*)")
        for f in files:
            if f not in self.files:
                self.files.append(f)
                self._add_file_with_icon(f)
        self._update_count()

    def _add_folder(self):
        folder = QFileDialog.getExistingDirectory(self, "Select Folder")
        if folder:
            count = 0
            for root, _, fnames in os.walk(folder):
                for fname in sorted(fnames):
                    if Path(fname).suffix.lower() in SUPPORTED_EXTENSIONS:
                        fpath = os.path.join(root, fname)
                        if fpath not in self.files:
                            self.files.append(fpath)
                            self._add_file_with_icon(fpath)
                            count += 1
            self._update_count()
            self.status_bar.showMessage(f"Added {count} files")

    def _remove_selected(self):
        for item in reversed(self.file_list.selectedItems()):
            idx = self.file_list.row(item)
            self.file_list.takeItem(idx)
            del self.files[idx]
        self._update_count()

    def _clear_files(self):
        self.file_list.clear()
        self.files.clear()
        self.metadata_map.clear()
        self.file_table.setRowCount(0)
        self._update_count()

    def _open_file_viewer(self):
        selected = self.file_list.selectedItems()
        if not selected:
            QMessageBox.information(self, "Info", "Select a file first!")
            return
        filepath = self.files[self.file_list.row(selected[0])]
        if os.path.isfile(filepath):
            try:
                import ctypes
                ctypes.windll.shell32.ShellExecuteW(None, "open", filepath, None, None, 1)
            except Exception:
                os.startfile(filepath)

    def _open_file_location(self):
        selected = self.file_list.selectedItems()
        if not selected:
            QMessageBox.information(self, "Info", "Select a file first!")
            return
        filepath = self.files[self.file_list.row(selected[0])]
        dirpath = os.path.dirname(filepath)
        if os.path.isdir(dirpath):
            os.startfile(dirpath)

    def _on_file_context_menu(self, pos):
        item = self.file_list.itemAt(pos)
        if not item:
            return
        self.file_list.setCurrentItem(item)
        filepath = self.files[self.file_list.row(item)]
        menu = QMenu(self)
        menu.setStyleSheet(
            "QMenu{background:#16213e;color:#e0e0e0;border:1px solid #2a2a4a;border-radius:6px;padding:4px;}"
            "QMenu::item{padding:6px 20px;border-radius:4px;}"
            "QMenu::item:selected{background:#533483;}"
        )
        action_open = menu.addAction("  Open File Location  ")
        action_open_file = menu.addAction("  Open File  ")
        action_remove = menu.addAction("  Remove from List  ")
        action = menu.exec(self.file_list.mapToGlobal(pos))
        if action == action_open:
            dirpath = os.path.dirname(filepath)
            if os.path.isdir(dirpath):
                os.startfile(dirpath)
        elif action == action_open_file:
            if os.path.isfile(filepath):
                os.startfile(filepath)
        elif action == action_remove:
            idx = self.file_list.row(item)
            self.file_list.takeItem(idx)
            del self.files[idx]
            self._update_count()

    def _make_thumb(self, filepath, size=48):
        try:
            img = Image.open(filepath)
            img.thumbnail((size, size))
            if img.mode != "RGBA":
                img = img.convert("RGBA")
            buf = io.BytesIO()
            img.save(buf, format="PNG")
            buf.seek(0)
            pixmap = QPixmap()
            pixmap.loadFromData(buf.read())
            return QIcon(pixmap)
        except Exception:
            return QIcon()

    def _add_file_with_icon(self, filepath):
        item = QListWidgetItem(self._make_thumb(filepath), os.path.basename(filepath))
        item.setData(Qt.ItemDataRole.UserRole, filepath)
        self.file_list.addItem(item)

    def _update_count(self):
        total_mp = sum(get_image_mp(fp) for fp in self.files)
        self.lbl_count.setText(f"{len(self.files)} files | ~{total_mp:.1f} MP total")

    def _toggle_output(self, state):
        enabled = state == 2
        self.output_path.setEnabled(enabled)
        self.btn_browse_output.setEnabled(enabled)

    def _browse_output(self):
        folder = QFileDialog.getExistingDirectory(self, "Select Output Folder")
        if folder:
            self.output_path.setText(folder)
            self.output_dir = folder

    def _on_file_selected(self, row):
        if 0 <= row < len(self.files):
            filepath = self.files[row]
            try:
                img = Image.open(filepath)
                img.thumbnail((400, 400))
                if img.mode != "RGBA":
                    img = img.convert("RGBA")
                buf = io.BytesIO()
                img.save(buf, format="PNG")
                buf.seek(0)
                pixmap = QPixmap()
                pixmap.loadFromData(buf.read())
                if not pixmap.isNull():
                    self.image_preview.setPixmap(
                        pixmap.scaled(self.image_preview.size(),
                                      Qt.AspectRatioMode.KeepAspectRatio,
                                      Qt.TransformationMode.SmoothTransformation)
                    )
            except Exception:
                self.image_preview.setText("Preview unavailable")
            mp = get_image_mp(filepath)
            if mp < 4:
                self.status_bar.showMessage(
                    f"WARNING: {os.path.basename(filepath)} is {mp}MP (Adobe Stock requires 4MP+)", 8000
                )
            xmp = read_xmp_from_file(filepath)
            if xmp:
                title = parse_xmp_title(xmp)
                desc = parse_xmp_description(xmp)
                kws = parse_xmp_keywords(xmp)
                self.xmp_preview.setPlainText(xmp)
                preview_text = f"FILE: {os.path.basename(filepath)}\n"
                preview_text += f"TITLE: {title}\n"
                preview_text += f"DESC: {desc[:200]}...\n" if len(desc) > 200 else f"DESC: {desc}\n"
                preview_text += f"KEYWORDS ({len(kws)}): {', '.join(kws[:20])}"
                if len(kws) > 20:
                    preview_text += f" ... (+{len(kws)-20} more)"
                self.lbl_status.setText(preview_text)
            else:
                self.lbl_status.setText(f"{os.path.basename(filepath)} - No tags embedded yet")

    def _get_current_api_key(self):
        if self.inp_api_key.isVisible() and self.inp_api_key.text().strip():
            return self.inp_api_key.text().strip()
        key = self.combo_api_keys.currentData()
        if key and key != "NEW":
            return key
        return ""

    def _ai_analyze_single(self):
        selected = self.file_list.selectedItems()
        if not selected:
            QMessageBox.warning(self, "Warning", "Select an image first!")
            return
        model = self.combo_model.currentText()
        if not model:
            QMessageBox.warning(self, "Warning", "No vision model selected!\nPull one: ollama pull llava")
            return
        provider = self.combo_provider.currentData()
        api_key = self._get_current_api_key()
        if provider in ("openai", "gemini") and not api_key:
            QMessageBox.warning(self, "Warning", "Enter or select an API key first!")
            return
        filepath = self.files[self.file_list.row(selected[0])]
        self.btn_ai_analyze.setEnabled(False)
        self.btn_ai_batch.setEnabled(False)
        self.btn_ai_stop.setEnabled(True)
        self.lbl_ai_status.setText(f"Analyzing: {os.path.basename(filepath)}...")
        self.ai_progress.setMaximum(1)
        self.ai_progress.setValue(0)
        self.ai_progress.setFormat("0/1 (0%)")
        mode = self.combo_mode.currentData()
        self.ai_thread = AIThread([filepath], model, self.combo_lang.currentData(), provider, api_key, self.combo_platform.currentData(), mode)
        if mode == "creative":
            self.ai_thread.result_ready.connect(self._on_ai_result_single_creative)
        else:
            self.ai_thread.result_ready.connect(self._on_ai_result_single)
        self.ai_thread.error_signal.connect(self._on_ai_error)
        self.ai_thread.finished_all.connect(self._on_ai_done_single)
        self.ai_thread.start()

    def _ai_analyze_batch(self):
        if not self.files:
            QMessageBox.warning(self, "Warning", "Add files first!")
            return
        model = self.combo_model.currentText()
        if not model:
            QMessageBox.warning(self, "Warning", "No vision model selected!")
            return
        provider = self.combo_provider.currentData()
        api_key = self._get_current_api_key()
        if provider in ("openai", "gemini") and not api_key:
            QMessageBox.warning(self, "Warning", "Enter or select an API key first!")
            return
        reply = QMessageBox.question(
            self, "Batch AI",
            f"Analyze {len(self.files)} images with AI?\nThis may take a while.",
            QMessageBox.StandardButton.Yes | QMessageBox.StandardButton.No,
        )
        if reply != QMessageBox.StandardButton.Yes:
            return
        self.btn_ai_analyze.setEnabled(False)
        self.btn_ai_batch.setEnabled(False)
        self.btn_ai_stop.setEnabled(True)
        self.ai_progress.setMaximum(len(self.files))
        self.ai_progress.setValue(0)
        mode = self.combo_mode.currentData()
        self.ai_thread = AIThread(self.files, model, self.combo_lang.currentData(), provider, api_key, self.combo_platform.currentData(), mode)
        self.ai_thread.progress.connect(self._on_ai_progress)
        if mode == "creative":
            self.ai_thread.result_ready.connect(self._on_ai_result_batch_creative)
        else:
            self.ai_thread.result_ready.connect(self._on_ai_result_batch)
        self.ai_thread.error_signal.connect(self._on_ai_error)
        self.ai_thread.finished_all.connect(self._on_ai_done_batch)
        self.ai_thread.start()

    def _ai_stop(self):
        if self.ai_thread:
            self.ai_thread.stop()
            self.ai_thread = None
            self.btn_ai_analyze.setEnabled(True)
            self.btn_ai_batch.setEnabled(True)
            self.btn_ai_stop.setEnabled(False)
            self.ai_progress.setMaximum(1)
            self.lbl_ai_status.setText("Stopped.")

    def _on_ai_result_single(self, filepath, result):
        self.inp_title.setText(result.get("title", ""))
        self.inp_description.setPlainText(result.get("description", ""))
        kws = result.get("keywords", [])
        self.inp_keywords.setPlainText(", ".join(kws))
        cat = result.get("category", "")
        idx = self.combo_category.findData(cat)
        if idx >= 0:
            self.combo_category.setCurrentIndex(idx)
        creator = self.inp_creator.text().strip()
        cr = self.inp_copyright.text().strip()
        meta = {
            'title': result.get("title", ""), 'description': result.get("description", ""),
            'keywords': kws, 'category': cat, 'creator': creator, 'copyright_text': cr,
        }
        self.metadata_map[filepath] = meta
        self.tabs.setCurrentIndex(1)
        self._update_preview()
        msg_parts = []
        if self.chk_auto_rename.isChecked():
            filepath, err = self._rename_file(filepath, meta.get('title', ''))
            if err:
                msg_parts.append(f"Rename fail: {err}")
        if self.chk_auto_embed.isChecked():
            ok, err = self._embed_single(filepath, meta)
            if ok:
                msg_parts.append("Embedded")
            else:
                msg_parts.append(f"Embed fail: {err}")
        if msg_parts:
            self.status_bar.showMessage(f"{os.path.basename(filepath)}: {', '.join(msg_parts)}")
        else:
            self.status_bar.showMessage(f"AI done: {os.path.basename(filepath)}")

    def _on_ai_result_batch(self, filepath, result):
        creator = self.inp_creator.text().strip()
        cr = self.inp_copyright.text().strip()
        meta = {
            'title': result.get("title", ""), 'description': result.get("description", ""),
            'keywords': result.get("keywords", []), 'category': result.get("category", ""),
            'creator': creator, 'copyright_text': cr,
        }
        self.metadata_map[filepath] = meta
        msg_parts = []
        if self.chk_auto_rename.isChecked():
            filepath, err = self._rename_file(filepath, meta.get('title', ''))
            if err:
                msg_parts.append(f"Rename fail: {err}")
        if self.chk_auto_embed.isChecked():
            ok, err = self._embed_single(filepath, meta)
            if ok:
                msg_parts.append("Embedded")
            else:
                msg_parts.append(f"Embed fail: {err}")
        row = self.file_table.rowCount()
        self.file_table.insertRow(row)
        self.file_table.setItem(row, 0, QTableWidgetItem(os.path.basename(filepath)))
        self.file_table.setItem(row, 1, QTableWidgetItem(meta['title']))
        self.file_table.setItem(row, 2, QTableWidgetItem(", ".join(meta['keywords'][:10])))
        self.file_table.setItem(row, 3, QTableWidgetItem(meta['category']))
        status = f" ({', '.join(msg_parts)})" if msg_parts else ""
        self.lbl_ai_status.setText(f"{os.path.basename(filepath)}{status}")

    def _on_ai_error(self, msg):
        if "does not support image" in msg or "Cannot read" in msg:
            provider = self.combo_provider.currentData()
            model = self.combo_model.currentText()
            msg = (f"Model '{model}' does not support image input!\n\n"
                   "Fix: Use a vision-capable model.\n"
                   "  - OpenAI: gpt-4o, gpt-4o-mini\n"
                   "  - Gemini: gemini-2.5-flash, gemini-2.0-flash\n"
                   "  - Ollama: llava:latest\n\n"
                   "Or switch to Ollama/Gemini in the provider dropdown.")
        QMessageBox.warning(self, "AI Error", msg)
        self.status_bar.showMessage(msg.split("\n")[0], 8000)

    def _on_ai_done_single(self, success, errors):
        self.btn_ai_analyze.setEnabled(True)
        self.btn_ai_batch.setEnabled(True)
        self.btn_ai_stop.setEnabled(False)
        self.ai_progress.setMaximum(1)
        self.ai_progress.setValue(1)
        self.ai_progress.setFormat("1/1 (100%)")
        self.lbl_ai_status.setText(f"Done! OK: {success}, Errors: {errors}")

    def _on_ai_done_batch(self, success, errors):
        self.btn_ai_analyze.setEnabled(True)
        self.btn_ai_batch.setEnabled(True)
        self.btn_ai_stop.setEnabled(False)
        self.ai_progress.setMaximum(1)
        self.ai_progress.setValue(1)
        msg = f"Batch complete! OK: {success}, Errors: {errors}"
        self.lbl_ai_status.setText(msg)
        QMessageBox.information(self, "AI Batch Done", msg)

    def _on_ai_result_single_creative(self, filepath, result):
        self.inp_creative_prompt.setPlainText(result.get("prompt", ""))
        tags = result.get("style_tags", [])
        self.inp_creative_tags.setText(", ".join(tags))
        self.tabs.setCurrentIndex(0)
        self.status_bar.showMessage(f"Creative prompt generated: {os.path.basename(filepath)}")

    def _on_ai_result_batch_creative(self, filepath, result):
        row = self.file_table.rowCount()
        self.file_table.insertRow(row)
        self.file_table.setItem(row, 0, QTableWidgetItem(os.path.basename(filepath)))
        prompt = result.get("prompt", "")
        self.file_table.setItem(row, 1, QTableWidgetItem(prompt[:80] + "..." if len(prompt) > 80 else prompt))
        tags = result.get("style_tags", [])
        self.file_table.setItem(row, 2, QTableWidgetItem(", ".join(tags[:10])))
        self.file_table.setItem(row, 3, QTableWidgetItem("Creative"))
        self.lbl_ai_status.setText(f"{os.path.basename(filepath)} - Prompt generated")

    def _on_ai_progress(self, current, total, filename):
        self.ai_progress.setMaximum(total)
        self.ai_progress.setValue(current)
        pct = int(current / total * 100) if total > 0 else 0
        self.ai_progress.setFormat(f"{current}/{total} ({pct}%)")
        self.lbl_ai_status.setText(f"AI ({current}/{total}): {filename}")

    def _embed_single(self, filepath, meta):
        try:
            xmp = build_xmp_packet(
                title=meta.get('title', ''), description=meta.get('description', ''),
                keywords=meta.get('keywords', []), category=meta.get('category', ''),
                creator=meta.get('creator', ''), copyright_text=meta.get('copyright_text', ''),
            )
            ext = Path(filepath).suffix.lower()
            if ext in ('.jpg', '.jpeg'):
                embed_xmp_jpeg(filepath, xmp)
            elif ext == '.png':
                embed_xmp_png(filepath, xmp)
            elif ext in ('.tif', '.tiff'):
                Image.open(filepath).save(filepath, tiff_imageinfo={b'ImageDescription': xmp.encode('utf-8')})
            return True, ""
        except Exception as e:
            return False, str(e)

    def _sanitize_filename(self, title):
        safe = re.sub(r'[<>:"/\\|?*]', '', title)
        safe = re.sub(r'\s+', ' ', safe).strip()
        safe = safe[:150]
        return safe if safe else "untitled"

    def _rename_file(self, filepath, title):
        try:
            dirpath = os.path.dirname(filepath)
            ext = Path(filepath).suffix.lower()
            new_name = self._sanitize_filename(title) + ext
            new_path = os.path.join(dirpath, new_name)
            if os.path.abspath(new_path) == os.path.abspath(filepath):
                return filepath, ""
            if os.path.exists(new_path):
                base = self._sanitize_filename(title)
                for i in range(1, 100):
                    new_path = os.path.join(dirpath, f"{base} ({i}){ext}")
                    if not os.path.exists(new_path):
                        break
            os.rename(filepath, new_path)
            idx = self.files.index(filepath) if filepath in self.files else -1
            if idx >= 0:
                self.files[idx] = new_path
                self.file_list.item(idx).setText(os.path.basename(new_path))
            if filepath in self.metadata_map:
                self.metadata_map[new_path] = self.metadata_map.pop(filepath)
            return new_path, ""
        except Exception as e:
            return filepath, str(e)

    def _load_row_to_editor(self):
        selected = self.file_table.selectedItems()
        if not selected:
            return
        row = selected[0].row()
        basename = self.file_table.item(row, 0).text()
        for fp, meta in self.metadata_map.items():
            if os.path.basename(fp) == basename:
                self.inp_title.setText(meta.get('title', ''))
                self.inp_description.setPlainText(meta.get('description', ''))
                self.inp_keywords.setPlainText(", ".join(meta.get('keywords', [])))
                idx = self.combo_category.findData(meta.get('category', ''))
                if idx >= 0:
                    self.combo_category.setCurrentIndex(idx)
                self.tabs.setCurrentIndex(1)
                self.status_bar.showMessage(f"Loaded: {basename}")
                break

    def _apply_to_all(self):
        meta = self._get_metadata()
        if not meta['title']:
            QMessageBox.warning(self, "Warning", "Fill in metadata first!")
            return
        for fp in self.files:
            self.metadata_map[fp] = meta.copy()
        self.status_bar.showMessage(f"Applied metadata to {len(self.files)} files")

    def _export_csv(self):
        if not self.metadata_map:
            QMessageBox.warning(self, "Warning", "No metadata to export!")
            return
        path, _ = QFileDialog.getSaveFileName(self, "Export CSV", "adobe_stock_tags.csv", "CSV (*.csv)")
        if not path:
            return
        with open(path, 'w', newline='', encoding='utf-8') as f:
            writer = csv.writer(f)
            writer.writerow(["File", "Title", "Description", "Keywords", "Category", "Creator", "Copyright"])
            for fp, meta in self.metadata_map.items():
                writer.writerow([
                    os.path.basename(fp), meta.get('title', ''), meta.get('description', ''),
                    " | ".join(meta.get('keywords', [])), meta.get('category', ''),
                    meta.get('creator', ''), meta.get('copyright_text', ''),
                ])
        self.status_bar.showMessage(f"Exported to {path}")

    def _get_metadata(self):
        raw_kw = self.inp_keywords.toPlainText().strip()
        keywords = [k.strip() for k in re.split(r'[,\n]', raw_kw) if k.strip()]
        return {
            'title': self.inp_title.text().strip(),
            'description': self.inp_description.toPlainText().strip(),
            'keywords': keywords,
            'category': self.combo_category.currentData(),
            'creator': self.inp_creator.text().strip(),
            'copyright_text': self.inp_copyright.text().strip(),
        }

    def _copy_to_clipboard(self, text, label):
        if not text.strip():
            QMessageBox.information(self, "Info", f"No {label} to copy!")
            return
        QApplication.clipboard().setText(text.strip())
        self.status_bar.showMessage(f"Copied {label} to clipboard!", 3000)

    def _copy_all_metadata(self):
        meta = self._get_metadata()
        if not meta['title']:
            QMessageBox.warning(self, "Warning", "No metadata to copy!")
            return
        cat_display = meta['category']
        for name, num in ADOBE_STOCK_CATEGORIES.items():
            if name == meta['category']:
                cat_display = f"{num}. {name}"
                break
        text = f"Title: {meta['title']}\n"
        text += f"Description: {meta['description']}\n"
        text += f"Keywords: {', '.join(meta['keywords'])}\n"
        text += f"Category: {cat_display}"
        if meta.get('creator'):
            text += f"\nCreator: {meta['creator']}"
        if meta.get('copyright_text'):
            text += f"\nCopyright: {meta['copyright_text']}"
        QApplication.clipboard().setText(text)
        self.status_bar.showMessage("All metadata copied! Paste into Adobe Stock portal.", 4000)

    def _copy_title_keywords(self):
        meta = self._get_metadata()
        if not meta['title']:
            QMessageBox.warning(self, "Warning", "No metadata to copy!")
            return
        text = f"{meta['title']}\n{', '.join(meta['keywords'])}"
        QApplication.clipboard().setText(text)
        self.status_bar.showMessage("Title + Keywords copied!", 3000)

    def _update_preview(self):
        meta = self._get_metadata()
        self.xmp_preview.setPlainText(build_xmp_packet(**meta))

    def _process_files(self):
        if not self.files:
            QMessageBox.warning(self, "Warning", "Add files first!")
            return
        meta = self._get_metadata()
        if not meta['title'] or not meta['description'] or not meta['keywords'] or not meta['category']:
            QMessageBox.warning(self, "Warning", "Fill in Title, Description, Keywords, Category!")
            return
        output_dir = self.output_path.text() if self.chk_save_copy.isChecked() else None
        if self.chk_save_copy.isChecked() and not output_dir:
            QMessageBox.warning(self, "Warning", "Select output folder!")
            return
        metadata_map = {}
        for fp in self.files:
            metadata_map[fp] = meta.copy()
        for fp, stored in self.metadata_map.items():
            if stored.get('title'):
                metadata_map[fp] = stored
        self.btn_process.setEnabled(False)
        self.btn_stop.setEnabled(True)
        self.progress_bar.setMaximum(len(self.files))
        self.progress_bar.setValue(0)
        self.process_thread = ProcessThread(self.files, metadata_map, output_dir)
        self.process_thread.progress.connect(self._on_progress)
        self.process_thread.finished_signal.connect(self._on_finished)
        self.process_thread.error_signal.connect(lambda m: self.status_bar.showMessage(m, 5000))
        self.process_thread.start()

    def _on_progress(self, current, total, filename):
        self.progress_bar.setMaximum(total)
        self.progress_bar.setValue(current)
        pct = int(current / total * 100) if total > 0 else 0
        self.progress_bar.setFormat(f"{current}/{total} ({pct}%)")
        self.lbl_status.setText(f"Embedding: {filename} ({current}/{total})")

    def _on_finished(self, success, errors):
        self.btn_process.setEnabled(True)
        self.btn_stop.setEnabled(False)
        msg = f"Done! OK: {success}"
        if errors:
            msg += f", Errors: {errors}"
        if self.chk_save_copy.isChecked() and self.output_path.text():
            msg += f"\nOutput: {self.output_path.text()}"
        self.lbl_status.setText(msg)
        self.status_bar.showMessage(msg, 10000)
        if success > 0:
            QMessageBox.information(self, "Done",
                f"Embedded tags into {success} file(s)!"
                + (f"\nOutput folder: {self.output_path.text()}" if self.chk_save_copy.isChecked() and self.output_path.text() else "\nFiles modified in place"))

    def _stop_process(self):
        if self.process_thread:
            self.process_thread.stop()
            self.process_thread = None
            self.btn_process.setEnabled(True)
            self.btn_stop.setEnabled(False)
            self.lbl_status.setText("Stopped.")

    def _read_tags(self):
        selected = self.file_list.selectedItems()
        if not selected:
            QMessageBox.information(self, "Info", "Select a file first!")
            return
        filepath = self.files[self.file_list.row(selected[0])]
        xmp = read_xmp_from_file(filepath)
        if xmp:
            self.inp_title.setText(parse_xmp_title(xmp))
            self.inp_description.setPlainText(parse_xmp_description(xmp))
            self.inp_keywords.setPlainText(", ".join(parse_xmp_keywords(xmp)))
            cat_m = re.search(r'<photoshop:Category>(\d+)</photoshop:Category>', xmp)
            if cat_m:
                cat_num = cat_m.group(1)
                cat_name = ""
                for name, num in ADOBE_STOCK_CATEGORIES.items():
                    if num == cat_num:
                        cat_name = name
                        break
                if cat_name:
                    idx = self.combo_category.findData(cat_name)
                    if idx >= 0:
                        self.combo_category.setCurrentIndex(idx)
            self.xmp_preview.setPlainText(xmp)
            self.tabs.setCurrentIndex(1)
            self.status_bar.showMessage(f"Read tags from {os.path.basename(filepath)}")
        else:
            QMessageBox.information(self, "Info", f"No metadata in {os.path.basename(filepath)}")

    def _view_tags_popup(self):
        selected = self.file_list.selectedItems()
        if not selected:
            QMessageBox.information(self, "Info", "Select a file first!")
            return
        filepath = self.files[self.file_list.row(selected[0])]
        dlg = TagViewerDialog(filepath, self)
        dlg.exec()

    def _load_presets_to_ui(self):
        self.inp_creator.setText(self.presets.get("creator", ""))
        self.inp_copyright.setText(self.presets.get("copyright_text", ""))
        idx = self.combo_category.findData(self.presets.get("category", ""))
        if idx >= 0:
            self.combo_category.setCurrentIndex(idx)
        saved_provider = self.presets.get("provider", "ollama")
        saved_api_key = self.presets.get("api_key", "")
        saved_platform = self.presets.get("platform", "adobe")
        pidx = self.combo_provider.findData(saved_provider)
        if pidx >= 0:
            self.combo_provider.setCurrentIndex(pidx)
        else:
            self._on_provider_changed(0)
        plidx = self.combo_platform.findData(saved_platform)
        if plidx >= 0:
            self.combo_platform.setCurrentIndex(plidx)
        if saved_api_key:
            found = False
            for i in range(self.combo_api_keys.count()):
                if self.combo_api_keys.itemData(i) == saved_api_key:
                    self.combo_api_keys.setCurrentIndex(i)
                    found = True
                    break
            if not found:
                self.inp_api_key.setText(saved_api_key)
        saved_model = self.presets.get("model", "")
        if saved_model:
            midx = self.combo_model.findText(saved_model)
            if midx >= 0:
                self.combo_model.setCurrentIndex(midx)
        self.chk_auto_embed.setChecked(self.presets.get("auto_embed", True))
        self.chk_auto_rename.setChecked(self.presets.get("auto_rename", True))
        saved_mode = self.presets.get("mode", "stock")
        midx = self.combo_mode.findData(saved_mode)
        if midx >= 0:
            self.combo_mode.setCurrentIndex(midx)
        self.status_bar.showMessage("Presets loaded")

    def _save_presets(self):
        active_key = self._get_current_api_key()
        old_keys = self.presets.get("api_keys", {})
        self.presets = {
            "creator": self.inp_creator.text().strip(),
            "copyright_text": self.inp_copyright.text().strip(),
            "category": self.combo_category.currentData() or "",
            "dark_mode": self.dark_mode,
            "provider": self.combo_provider.currentData() or "ollama",
            "api_key": active_key,
            "model": self.combo_model.currentText(),
            "api_keys": old_keys,
            "auto_rename": self.chk_auto_rename.isChecked(),
            "auto_embed": self.chk_auto_embed.isChecked(),
            "save_copy": self.chk_save_copy.isChecked(),
            "output_path": self.output_path.text().strip(),
            "platform": self.combo_platform.currentData() or "adobe",
            "mode": self.combo_mode.currentData() or "stock",
            "update_repo": self.presets.get("update_repo", UPDATE_REPO),
            "github_token": self.presets.get("github_token", ""),
        }
        save_presets_to_file(self.presets)
        self.status_bar.showMessage("Presets saved!")

    def _reset_all(self):
        reply = QMessageBox.question(
            self, "Reset All",
            "Clear all files, results and metadata?\nThis cannot be undone.",
            QMessageBox.StandardButton.Yes | QMessageBox.StandardButton.No,
        )
        if reply != QMessageBox.StandardButton.Yes:
            return
        if self.ai_thread and self.ai_thread.isRunning():
            self.ai_thread.stop()
            self.ai_thread.wait(3000)
            self.ai_thread = None
        if self.process_thread and self.process_thread.isRunning():
            self.process_thread.stop()
            self.process_thread.wait(3000)
            self.process_thread = None
        self.files.clear()
        self.file_list.clear()
        self.metadata_map.clear()
        self.file_table.setRowCount(0)
        self.inp_title.clear()
        self.inp_description.clear()
        self.inp_keywords.clear()
        self.inp_creator.clear()
        self.inp_copyright.clear()
        self.combo_category.setCurrentIndex(0)
        self.xmp_preview.clear()
        self.progress_bar.setValue(0)
        self.progress_bar.setMaximum(1)
        self.progress_bar.setFormat("%v%")
        self.ai_progress.setValue(0)
        self.ai_progress.setMaximum(1)
        self.ai_progress.setFormat("%v%")
        self.lbl_status.setText("")
        self.lbl_ai_status.setText("")
        self.inp_creative_prompt.clear()
        self.inp_creative_tags.clear()
        self.btn_process.setEnabled(True)
        self.btn_stop.setEnabled(False)
        self.btn_ai_analyze.setEnabled(True)
        self.btn_ai_batch.setEnabled(True)
        self.btn_ai_stop.setEnabled(False)
        self.tabs.setCurrentIndex(0)
        self._update_count()
        self.status_bar.showMessage("All data cleared!", 5000)

    def _toggle_dark(self, state):
        self.dark_mode = state == 2
        app = QApplication.instance()
        app.setStyleSheet(DARK_STYLE if self.dark_mode else "")

    def closeEvent(self, event):
        for thread in [self.process_thread, self.ai_thread]:
            if thread and thread.isRunning():
                thread.stop()
                thread.wait(3000)
        event.accept()


def main():
    QLocale.setDefault(QLocale(QLocale.Language.English, QLocale.Country.UnitedStates))
    app = QApplication(sys.argv)
    app.setStyle("Fusion")
    app.setFont(QFont("Segoe UI", 9))
    window = MainWindow()
    window.show()
    sys.exit(app.exec())


if __name__ == "__main__":
    main()
'''

with open(OUT, 'w', encoding='utf-8') as f:
    f.write(CODE)

PYW = OUT.replace('.py', '.pyw')
import shutil
shutil.copy2(OUT, PYW)

print(f"Written {os.path.getsize(OUT)} bytes to {OUT}")
print(f"Copied to {PYW} (double-click to run, no console)")
