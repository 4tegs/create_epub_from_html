# 📚EPUB-Generator from HTML

Dieses Python-Skript konvertiert HTML-Inhalte in ein professionelles E-Book im EPUB-Format für die Offline-Nutzung.

## Version and licence
Version v1.0 dated 01/2026<br/>
Written by Hans Strassguetl - mail@hs58.de<br/>
Licenced under [https://creativecommons.org/licenses/by-sa/4.0/](https://creativecommons.org/licenses/by-sa/4.0/)

## About
Ich plane Urlaubsreisen indem ich diese auf Webseiten entwickle und zur Verfügung stelle. Auf Reisen habe ich oft keinen Internetzugriff und benötige die Seiten somit als Buch auf dem Handy.
Mit diesem Programm können die Webseiten mit geringem Aufwand umgewandelt werden.

## 🛠 Voraussetzungen
Bevor du das Skript startest, müssen Python (ab Version 3.10) und die benötigten Bibliotheken installiert sein.

Installiere die benötigten Bibliotheken mit folgendem Befehl in deinem Terminal:

```bash
pip install ebooklib beautifulsoup4 lxml
```

### 📂 Projektstruktur
Für einen reibungslosen Ablauf sollte dein Arbeitsverzeichnis so aussehen:

/dein-projektordner<br/>
│<br/>
├── create_epub_from_html.py   </br>
├── create_epub_from_html.json </br>
├── index.html                 </br>
├── style.css                  </br>
├── preface.xhtml              </br>
│<br/>
├── /bilder                    </br>
└── /fonts                     </br>

| was | wo | JSON Definition |
| --- | --- | --- |
| create_epub_from_html.py | Das Hauptprogramm | |
| create_epub_from_html.json | Die Konfigurationsdatei | |
| index.html | Die Quell-HTML. | x |
| style.css | Das Stylesheet für das Buch. | x |
| preface.xhtml | Dein optionales Vorwort. Du benötigst das nicht für die Webseite, jedoch für ein Buch.<br/> Sehr strikt im Code! | x |
| /bilder | Ordner für Fotos und das cover.jpg | x |
| /fonts | Ordner für Schriftarten | x |

## ⚙️ Konfiguration (JSON)

Die Parameter werden in der JSON-Datei gesteuert. Falls die Datei fehlt, erstellt das Skript automatisch eine Version mit Standardwerten.

| Sektion | Parameter | Beschreibung |
| --- | --- | --- | 
| config | source_html | Die HTML-Datei, die als Basis dient. | 
|  | source_css | Die css-Datei, die zur Darstellungssteuerung dient. | 
|  | folder_fonts | Der Folder in dem die Fonts liegen die dein css nutzt. | 
|  | folder_bilder | Der Folder in dem die Bilder gespeichert sind die dein index.html nutzt. | 
|  | cover_image | Der Dateiname des Covers im Bilder-Ordner. |
|  | output_epub | Der Dateiname deines Buches mit Endung. |
|  | preface | Setze diesen Wert auf "none", wenn du kein Vorwort möchtest, oder gib den Dateinamen an (z. B. "preface.xhtml"). |
| metadata | title | Der Titel deines Buches. | 
|  | author | Der Titel deines Buches. | 
|  | language | Die Spache deines Buches. | 
|  | description | Beschreibe in wenigen Worten den Inhalt deines Buches. | 
|  | publisher | Der Herausgeber. | 
|  | rights | Die Rechte deines Buches. | 
|  | subject | Stichworte zum Buch. | 



## 🚀 Funktionen des Skripts
1. Ressourcen-Check: Prüft vor dem Start, ob alle Dateien und Pfade existieren.
3. Kapitel-Split: Zerlegt die index.html anhand von <strong>\<break></strong>-Tags in einzelne Buchkapitel. Das ist zuverlässiger als sich auf \<h1> oder \<h2> Tags zu verlassen.
4. Kapitel-Hide: Manche Kapitel sind wichtig im Web, sind aber im Buch überflüssig. Setze den Text der verschwinden soll zwischen 
<strong>\<hide> </strong> und 
<strong>\</hide></strong>
4. Iframe-Ersatz: Ich benutze Web-Iframes (Karten). Diese werden durch lokale Bilder aus dem Bilder-Ordner ersetzt. Das Bild muss den gleichen Namen haben wie das iframe: Aus Tag001.html wird Tag001.jpg. Dazu ist natürlich etwas Handarbeit von nöten.
5. Self-Healing: Repariert unvollständige JSON-Konfigurationen automatisch.


## Use
* Kopiere dieses Script ins Quellverzeichnis deiner Webseite.
* Platziere ebenfalls die JSON Datei im selben Verzeichnis. Wenn keine JSON vorhanden ist, wird eine basis erstellt.

## Fonts
Wenn du Fonts benötigst, meine Quelle ist [https://www.fontsquirrel.com/fonts](https://www.fontsquirrel.com/fonts)
