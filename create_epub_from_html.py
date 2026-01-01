# ------------------------------------------------------------------------------------------
# Erstelle ein EPUB Buch aus einer HTML Datei mit eingebetteten Bildern und Fonts
# Anpassung für flache Struktur: CSS, Fonts und Bilder liegen im selben Verzeichnis wie die HTML-Dateien
# Geschrieben mit Hilfe von Gemini 3
# 
# Hans Straßgütl
# Prerequesites:
#       pip install ebooklib beautifulsoup4 requests
#       
#       Im index.html sind <break> Tags als Kapiteltrenner eingefügt
#                     sind <iframe src="..."> Tags für HTML seiten eingefügt. Diese werden gelöscht und gegen Bilder ersetzt
#                     Die Bilder müssen im selben Verzeichnis liegen wie die HTML und zuvor erstellt worden sein.  
# Stand:  
#       2025-12-31      Start coding
#       2026-01-01      Preface Einbindung hinzugefügt
#                       Iframe zu Bild Umwandlung hinzugefügt. Hyperlinks entfernt.
#                       mit <hide> Sektionen ausblenden.
#                       "Zurück zum Index" Links und Darstellung angepasst.
#                       Jetzt mit JSON Steuerung
#                       JSON hardened.
# 
# ------------------------------------------------------------------------------------------

import os
import sys
import re
import json
from bs4 import BeautifulSoup, Tag, Comment
from ebooklib import epub
from datetime import datetime, timezone
from pathlib import Path

# --- Konfiguration ---
BASE_DIR = os.path.dirname(os.path.abspath(__file__))

DEFAULT_CONFIG = {
    "metadata": {
        "title": "Dein Buchtitel - Wert im JSON individuell definieren ",
        "author": "Name des Authors",
        "language": "de",
        "description": "Buchbeschreibung. Wert im JSON individuell definieren ",
        "publisher": "Name des Authors",
        "rights": "Alle Rechte vorbehalten",
        "subject": "Marokko, Motorradreise"
    },
    "config": {
        "source_html": "index.html",
        "source_css": "style.css",
        "folder_fonts": "fonts",
        "folder_bilder": "bilder",
        "cover_image": "cover.jpg",
        "output_epub": "Reisebegleiter.epub"
    }
}

# ------------------------------------------------------------------------------------------
#      _ ____   ___  _   _ 
#     | / ___| / _ \| \ | |
#  _  | \___ \| | | |  \| |
# | |_| |___) | |_| | |\  |
#  \___/|____/ \___/|_| \_|
# ------------------------------------------------------------------------------------------
def load_json(json_file_name=None):
    my_script = IchSelbst()
    if json_file_name is None:
        json_file_name = my_script.path_name_without_suffix + ".json"

    data = {}
    needs_update = False

    # 1. Laden oder Neuerstellen
    if not os.path.exists(json_file_name):
        print(f"HINWEIS: {json_file_name} nicht gefunden. Erstelle Default-JSON.")
        data = DEFAULT_CONFIG
        needs_update = True
    else:
        try:
            with open(json_file_name, 'r', encoding='utf-8') as f:
                data = json.load(f)
        except Exception as e:
            print(f"FEHLER beim Lesen der JSON ({e}). Nutze Defaults.")
            data = DEFAULT_CONFIG
            needs_update = True

    # 2. Key-Check (Selbstheilung)
    for section, keys in DEFAULT_CONFIG.items():
        if section not in data:
            data[section] = keys
            print(f"FEHLER: Sektion '{section}' fehlte. Wiederhergestellt.")
            needs_update = True
        else:
            for k, v in keys.items():
                if k not in data[section]:
                    data[section][k] = v
                    print(f"FEHLER: Parameter '{section}->{k}' fehlte. Default gesetzt.")
                    needs_update = True

    # 3. Speichern wenn nötig
    if needs_update:
        with open(json_file_name, 'w', encoding='utf-8') as f:
            json.dump(data, f, indent=4, ensure_ascii=False)
    
    return data

def check_resources(config):
    """Prüft, ob alle in der Config genannten Dateien und Ordner existieren."""
    missing_items = []
    
    # Pfade aus der Config für die Prüfung vorbereiten
    folder_bilder = config.get('folder_bilder', 'bilder')
    
    # 1. Verzeichnisse prüfen
    for key in ['folder_fonts', 'folder_bilder']:
        path = os.path.join(BASE_DIR, config.get(key))
        if not os.path.exists(path):
            missing_items.append(f"Ordner: {path}")

    # 2. Einzeldateien an der Wurzel prüfen
    for key in ['source_html', 'source_css']:
        path = os.path.join(BASE_DIR, config.get(key))
        if not os.path.exists(path):
            missing_items.append(f"Datei (Wurzel): {path}")

    # Preface nur prüfen, wenn es nicht auf "none" steht
    preface_file = config.get('preface', 'none')
    if preface_file.lower() != "none":
        preface_path = os.path.join(BASE_DIR, preface_file)
        if not os.path.exists(preface_path):
            missing_items.append(f"Preface-Datei: {preface_path}")

    # 3. Das Cover-Bild im Bilder-Ordner prüfen (Der Fix)
    cover_filename = config.get('cover_image')
    # Wir kombinieren BASE_DIR + Bilder-Ordner + Dateiname
    cover_path = os.path.join(BASE_DIR, folder_bilder, cover_filename)
    
    if not os.path.exists(cover_path):
        missing_items.append(f"Cover-Bild (im Bilder-Ordner): {cover_path}")
    
    if missing_items:
        print("\n" + "!"*60)
        print("KRITISCHE RESSOURCEN FEHLEN:")
        for item in missing_items:
            print(f" -> {item}")
        print("!"*60 + "\n")
        
        # Abbruch-Bedingung
        html_path = os.path.join(BASE_DIR, config.get('source_html'))
        if not os.path.exists(html_path):
            print("Abbruch: Quell-HTML fehlt.")
            sys.exit(1)



def get_font_mime(filename):
    ext = os.path.splitext(filename)[1].lower()
    mapping = {'.ttf': 'font/ttf', '.otf': 'font/otf', '.woff': 'font/woff', '.woff2': 'font/woff2'}
    return mapping.get(ext, 'application/vnd.ms-opentype')


def create_epub():
    # 1. JSON laden (mit Auto-Repair Logik)
    translate_table = load_json(None)               # Lade in deine eigene Translation Tabelle
    config_dict = translate_table.get("config")
    
    # 2. Alle Ressourcen prüfen (HIER NEU)
    check_resources(config_dict)
    
    # 3. Pfade setzen
    SOURCE_HTML = os.path.join(BASE_DIR, config_dict.get("source_html"))
    SOURCE_CSS = os.path.join(BASE_DIR, config_dict.get("source_css"))
    FOLDER_FONTS = os.path.join(BASE_DIR, config_dict.get("folder_fonts"))
    FOLDER_BILDER = os.path.join(BASE_DIR, config_dict.get("folder_bilder"))
    OUTPUT_EPUB = config_dict.get("output_epub")

    print("--- Starte EPUB-Generierung ---")
    print(f"Verwende Quell-HTML: {SOURCE_HTML}")
    # Erzeugt automatisch: 2025-12-31T18:36:00+00:00 (Beispiel)
    current_time = datetime.now(timezone.utc).strftime('%Y-%m-%dT%H:%M:%S+00:00')
    
    # 3. ePub Metadata setzen
    book = epub.EpubBook()
    metadata_dict = translate_table.get("metadata") # get from json
    book.set_title(metadata_dict.get("title"))
    book.add_author(metadata_dict.get("author"))
    book.set_language(metadata_dict.get("language"))
    book.add_metadata('DC', 'date', current_time)
    book.add_metadata('DC', 'description', (metadata_dict.get("description")))
    book.add_metadata('DC', 'publisher', (metadata_dict.get("publisher")))
    book.add_metadata('DC', 'rights', (metadata_dict.get("rights")))
    book.add_metadata('DC', 'language', 'Deutsch')
    book.add_metadata('dcterms', 'created', current_time)
    book.add_metadata(None, 'meta', current_time, {
        'property': 'dcterms:created'
    })
    book.add_metadata('DC', 'subject',  (metadata_dict.get("subject")))
   
    # --- COVER DEFINIEREN ---
    # Pfad zu deinem Cover-Bild (muss im Ordner 'bilder' liegen)
    cover_path = os.path.join(FOLDER_BILDER, config_dict.get("cover_image")) 
    if os.path.exists(cover_path):
        # set_cover macht zwei Dinge: Bild hinzufügen und als Cover markieren
        book.set_cover(config_dict.get("cover_image"), open(cover_path, 'rb').read())
        print("Cover-Bild wurde hinzugefügt.")
    else:
        print("HINWEIS: cover.jpg wurde im Bilder-Ordner nicht gefunden.")

    # 1. CSS & FONTS (Pfade für flache Struktur anpassen)
    css_content = ""
    if os.path.exists(SOURCE_CSS):
        with open(SOURCE_CSS, 'r', encoding='utf-8') as f:
            css_content = f.read()
        
        font_urls = re.findall(r'url\([\'"]?([^)\'"]+)[\'"]?\)', css_content)
        for full_url in set(font_urls):
            clean_path = full_url.split('?')[0].split('#')[0]
            f_name = os.path.basename(clean_path)
            local_font = os.path.join(FOLDER_FONTS, f_name)
            
            if os.path.exists(local_font):
                uid = f"font_{f_name.replace('.', '_')}"
                with open(local_font, 'rb') as ff:
                    # Fonts liegen jetzt im selben "Verzeichnis" wie das CSS
                    font_item = epub.EpubItem(uid=uid, file_name=f_name, 
                                             media_type=get_font_mime(f_name), content=ff.read())
                    book.add_item(font_item)
                # In der flachen Struktur ist der Pfad einfach der Dateiname
                css_content = css_content.replace(full_url, f_name)
                print(f"Font bereitgestellt: {f_name}")

    # CSS Datei erstellen (flache Ebene)
    style_item = epub.EpubItem(uid="style_hans", file_name="hans.css", media_type="text/css", content=css_content)
    book.add_item(style_item)

    # 2. HTML LADEN
    with open(SOURCE_HTML, 'r', encoding='utf-8') as f:
        soup = BeautifulSoup(f, 'html.parser')

    # Erst die unerwünschten Sektionen löschen
    for hide_tag in soup.find_all('hide'):
        hide_tag.decompose()

    # --- IFRAME ZU BILD WANDELN (START) ---
    for iframe in soup.find_all('iframe'):
        src = iframe.get('src', '')
        if src:
            # Extrahiert den Dateinamen (z.B. TAG05.html)
            file_name_ext = os.path.basename(src)
            if file_name_ext.lower().endswith('.html'):
                # Ersetzt .html durch .jpg (z.B. TAG05.jpg)
                new_img_name = os.path.splitext(file_name_ext)[0] + '.jpg'
                
                # Erstellt ein neues img-Tag
                new_img = soup.new_tag('img', src=new_img_name)
                
                # Kopiert vorhandene Attribute (optional, falls width/height bleiben sollen)
                if iframe.get('width'): new_img['width'] = iframe['width']
                
                # Ersetzt das iframe durch das neue img
                iframe.replace_with(new_img)
    # --- IFRAME ZU BILD WANDELN (ENDE) ---

    body = soup.find('body')

    # --- PREFACE EINBINDEN (STEUERUNG ÜBER JSON) ---
    preface_config = config_dict.get("preface", "none")
    print(preface_config)
    preface_item = None
    if preface_config.lower() != "none":
        preface_path = os.path.join(BASE_DIR, preface_config)
        print(preface_path)
        
        if os.path.exists(preface_path):
            with open(preface_path, 'r', encoding='utf-8') as f:
                preface_raw = f.read()
            
            p_soup = BeautifulSoup(preface_raw, 'html.parser')
            p_content = "".join([str(c) for c in p_soup.body.contents]) if p_soup.body else preface_raw

            # Wir nutzen den Dateinamen aus der Config auch als internen Namen im EPUB
            preface_item = epub.EpubHtml(title='Vorwort', file_name=preface_config, lang='de')
            # preface_item.content = f'<html><head><link rel="stylesheet" href="hans.css" type="text/css"/></head><body>{p_content}</body></html>'
            preface_item.content = (
                f'<html><head><link rel="stylesheet" href="{SOURCE_CSS}" type="text/css"/></head>'
                f'<body>{p_content}</body></html>'
            )
            book.add_item(preface_item)
            print(f"Datei '{preface_config}' wurde als Vorwort geladen.")
    else:
        print("Info: Kein Vorwort (preface: none) konfiguriert.")
    # --- PREFACE EINBINDEN (ENDE) ---

    # 3. KAPITEL-SPLITTING
    sections = []
    current_section = []
    for element in body.contents:
        if isinstance(element, Comment): continue
        if isinstance(element, Tag) and element.name in ['hr']: continue        # Werfe die HR Elemente raus die du so dringend in der Webseite benötigst.
        # if isinstance(element, Tag) and element.name in ['h1', 'h2']:         # Alternative Kapiteltrenner, 31.12.2025 außer Betrieb gesetzt. lässt sich mit break besser steuern.
        if isinstance(element, Tag) and element.name in ['break']:
            if current_section: sections.append(current_section)
            current_section = [element]
        else:
            current_section.append(element)
    if current_section: sections.append(current_section)

    chapters = []
    for i, section in enumerate(sections):
        title = f"Kapitel {i+1}"
        for item in section:
            if isinstance(item, Tag) and item.name in ['h1', 'h2']:
                title = item.get_text(strip=True)[:80]
                break
        
        # HTML Dokument (flache Struktur: CSS ist einfach "hans.css")
        chap_soup = BeautifulSoup('<html><head><link rel="stylesheet" href="hans.css" type="text/css"/></head><body></body></html>', 'html.parser')
        
        valuable = False
        for item in section:
            node = BeautifulSoup(str(item), 'html.parser').contents[0]
            if isinstance(node, Tag):
                # Bilder-Pfade auf flache Ebene korrigieren
                # 1. Alle Bilder (img-Tags) korrigieren
                for img in node.find_all('img'):
                    old_src = img.get('src', '')
                    f_name = os.path.basename(old_src) # Nur der Dateiname, z.B. TAG05.jpg
                    
                    # Pfad zur lokalen Datei auf deinem PC prüfen
                    local_img = os.path.join(FOLDER_BILDER, f_name)
                    if os.path.exists(local_img):
                        img_uid = f"img_{f_name.replace('.', '_')}"
                        # Bild nur hinzufügen, wenn es noch nicht im Buch ist
                        if img_uid not in [it.id for it in book.items]:
                            ext = f_name.split('.')[-1].lower()
                            mtype = "image/png" if ext == 'png' else "image/jpeg"
                            with open(local_img, 'rb') as imf:
                                img_item = epub.EpubItem(uid=img_uid, file_name=f_name, media_type=mtype, content=imf.read())
                                book.add_item(img_item)
                                print(f"Bild hinzugefügt: {f_name}")
                        
                        # WICHTIG: Die Quelle im HTML auf den lokalen Namen setzen
                        img['src'] = f_name 
            
                # Alle "Zurück zum Index" Links im Kapitel finden
                for a_link in node.find_all('a', href=True):
                    if a_link['href'] == "#index":
                        # Link zum generierten Inhaltsverzeichnis des EPUBs umleiten
                        a_link['href'] = "nav.xhtml"

                        # Falls ein Button-Tag darin ist, entfernen wir es und behalten nur den Text
                        btn = a_link.find('button')
                        if btn:
                            # Wir geben dem Link eine Klasse für das CSS-Styling
                            # a_link['class'] = a_link.get('class', []) + ['btn-back']
                            a_link['class'] = a_link.get('class', []) + ['button']
                            a_link.string = btn.get_text() # Setzt "Zurück zum Index" als Text

                # 2. Falls Bilder in Links (a-Tags) eingebettet sind (Lightbox-Stil)
                for a_link in node.find_all('a'):
                    link_href = a_link.get('href', '')
                    # Prüfen, ob der Link auf ein Bild verweist
                    if link_href.lower().endswith(('.jpg', '.jpeg', '.png')):
                        a_name = os.path.basename(link_href)
                        # Link im Buch auf die lokale Datei umbiegen
                        a_link['href'] = a_name

                if node.get_text(strip=True) or node.find('img'):
                    valuable = True
            chap_soup.body.append(node)
            chap_soup.body.append(node)

        if valuable:
            # Dateiname ohne Unterordner
            chap = epub.EpubHtml(title=title, file_name=f'chap_{i}.xhtml', lang='de')
            chap.content = chap_soup.encode(formatter="html").decode('utf-8')
            # WICHTIG: Hier wird das Stylesheet dem Kapitel zugewiesen
            chap.add_item(style_item)
            book.add_item(chap)
            chapters.append(chap)

    # 4. FINISH
    # book.toc = tuple(chapters)
    # book.add_item(epub.EpubNcx())
    # book.add_item(epub.EpubNav())
    # book.spine = ['nav'] + chapters
    # 4. ABSCHLUSS
    if not chapters:
        print("FEHLER: Keine Kapitel gefunden.")
        return

    # Inhaltsverzeichnis (TOC) zusammenstellen
    # Wir verwenden nur das bereits existierende preface_item Objekt
    if preface_item:
        full_toc = [preface_item] + chapters
    else:
        full_toc = chapters

    book.toc = tuple(full_toc)
    
    # Navigationselemente hinzufügen
    book.add_item(epub.EpubNcx())
    book.add_item(epub.EpubNav())

    # Die 'spine' bestimmt die Lesereihenfolge
    # WICHTIG: preface_item ist das Objekt, das wir oben mit book.add_item hinzugefügt haben
    if preface_item:
        book.spine = ['nav', preface_item] + chapters
    else:
        book.spine = ['nav'] + chapters

    # Buch schreiben
    epub.write_epub(OUTPUT_EPUB, book)
    print(f"FERTIG: {OUTPUT_EPUB} erstellt mit {len(chapters)} Kapiteln.")


# -------------------------------------------------------------
#  ____  _             _     ____            _       _     
# / ___|| |_ __ _ _ __| |_  / ___|  ___ _ __(_)_ __ | |_ 
# \___ \| __/ _` | '__| __| \___ \ / __| '__| | '_ \| __|
#  ___) | || (_| | |  | |_   ___) | (__| |  | | |_) | |_ 
# |____/ \__\__,_|_|   \__| |____/ \___|_|  |_| .__/ \__|
#                                             |_|        
#  ____                                _            
# |  _ \ __ _ _ __ __ _ _ __ ___   ___| |_ ___ _ __ 
# | |_) / _` | '__/ _` | '_ ` _ \ / _ \ __/ _ \ '__|
# |  __/ (_| | | | (_| | | | | | |  __/ ||  __/ |   
# |_|   \__,_|_|  \__,_|_| |_| |_|\___|\__\___|_|   
# -------------------------------------------------------------
class IchSelbst:
    '''
    Make Names from running Script.
    sys.argv[0] zeigt, wenn man die py laufen lässt, auf den Python Interpreter bzw. die py.
    Sobald die py zur Exe wird zeigt der Pfad zur Working Directory des Callers, also des GPX das ich Droppe. 
    Damit müsste immer dort wo die GPX liegt auch die JSON liegen. 
    sys.executable ist der Workaround. 
    Mehr dazu hier: https://pyinstaller.org/en/stable/runtime-information.html 

    self.script_with_path           ->  c:\SynologyDrive\Python\00_test\test2.py
    self.script                     ->  test2.py
    self.name                       ->  test2
    self.path                       ->  c:\SynologyDrive\Python\00_test
    self.path_name_without_suffix   ->  c:\SynologyDrive\Python\00_test\test2
    '''
    def __init__(self):
        if getattr(sys, 'frozen', False):                                   # Code is running from a compiled executable
            SysArg0  = sys.executable
        else:                                                               # Code is running as a regular Python script
            SysArg0 = sys.argv[0]

        self.script_with_path           = SysArg0                               # Script mit vollem Path
        self.script_with_suffix         = Path(SysArg0).name                    # Der Dateiname mit Suffix
        self.script_without_suffix      = Path(SysArg0).stem                    # Das ist der DateiName OHNE Suffix
        self.path                       = Path(SysArg0).parent                  # Das ist der Path ohne trailing \
        self.path_name_without_suffix   = str(Path(SysArg0).parent) + "\\" + Path(SysArg0).stem
        # ----------------------------------------------------------------------------------------
        # Here comes some code that maybe used in case the JSON file is included in the EXE file. 
        # ----------------------------------------------------------------------------------------
        if getattr(sys, 'frozen', False):                                   # Code is running from a compiled executable
            try:
                base_path = sys._MEIPASS
            except AttributeError:
                base_path = os.path.abspath(".")
            # By compiling the JSON into the package, the path uses the name of the JSON as a subfolder, 
            # for that the Path(SysArg0).stem var needs to be added twice
            self.data_file = base_path + "\\" + Path(SysArg0).stem + ".json\\" + Path(SysArg0).stem 
        else:
            self.data_file = self.path_name_without_suffix


if __name__ == '__main__':
    os.system('cls')
    print("Version v1.0 dated 01/2026")
    print("Written by Hans Strassguetl - mail@hs58.de")
    print("Licenced under [https://creativecommons.org/licenses/by-sa/4.0/](https://creativecommons.org/licenses/by-sa/4.0/)")
    create_epub()