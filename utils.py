import json
import os

LANGUAGES = {
    "English": {
        "title": "SysPulse Ultimate", "dash": "📊 Dashboard", "info": "ℹ️ System Info", "proc": "⚙️ Processes",
        "log": "💾 Export Log", "refresh": "Refresh (s)", "appearance": "Theme", "dark": "Dark", "light": "Light",
        "lang": "Language", "overview": "System Overview", "cpu": "CPU Load", "ram": "RAM Usage", "gpu": "GPU Power",
        "batt": "Battery", "disk": "Disk Capacity", "net": "Network Traffic", "proc_list": "Top Processes",
        "refresh_btn": "Refresh", "mini_mode": "Mini Mode", "accent": "Accent Color", "history": "Performance History (10m)",
        "ping": "Latency (Ping)", "save": "Save Settings", "start_msg": "Initial Configuration"
    },
    "Türkçe": {
        "title": "SysPulse Ultimate", "dash": "📊 Panel", "info": "ℹ️ Sistem Bilgisi", "proc": "⚙️ İşlemler",
        "log": "💾 Günlüğü Kaydet", "refresh": "Yenileme (s)", "appearance": "Tema", "dark": "Karanlık", "light": "Aydınlık",
        "lang": "Dil", "overview": "Sistem Özeti", "cpu": "İşlemci", "ram": "Bellek", "gpu": "Ekran Kartı",
        "batt": "Pil", "disk": "Disk Doluluğu", "net": "Ağ Trafiği", "proc_list": "En Çok Tüketenler",
        "refresh_btn": "Yenile", "mini_mode": "Mini Mod", "accent": "Vurgu Rengi", "history": "Performans Geçmişi (10dk)",
        "ping": "Gecikme (Ping)", "save": "Ayarları Kaydet", "start_msg": "İlk Yapılandırma"
    },
    "Deutsch": {
        "title": "SysPulse Ultimate", "dash": "📊 Dashboard", "info": "ℹ️ Systeminfo", "proc": "⚙️ Prozesse",
        "log": "💾 Protokoll", "refresh": "Rate (s)", "appearance": "Thema", "dark": "Dunkel", "light": "Hell",
        "lang": "Sprache", "overview": "Systemübersicht", "cpu": "CPU-Last", "ram": "Speicher", "gpu": "GPU-Leistung",
        "batt": "Batterie", "disk": "Speicherkapazität", "net": "Netzwerktraffic", "proc_list": "Top-Prozesse",
        "refresh_btn": "Aktualisieren", "mini_mode": "Mini-Modus", "accent": "Akzentfarbe", "history": "Leistungsverlauf (10m)",
        "ping": "Latenz (Ping)", "save": "Einstellungen speichern", "start_msg": "Erstkonfiguration"
    }
}

ACCENTS = {
    "Blue": "#3a7ebf", 
    "Green": "#2ecc71", 
    "Purple": "#9b59b6", 
    "Orange": "#e67e22",
    "Cyan": "#1abc9c",
    "Pink": "#e91e63"
}

class ConfigManager:
    FILE = "config.json"
    DEFAULTS = {
        "language": "English",
        "theme": "Dark",
        "accent": "Blue",
        "refresh_rate": 1.0,
        "first_run": True
    }

    @staticmethod
    def load():
        if not os.path.exists(ConfigManager.FILE):
            return ConfigManager.DEFAULTS
        try:
            with open(ConfigManager.FILE, "r") as f:
                return json.load(f)
        except:
            return ConfigManager.DEFAULTS

    @staticmethod
    def save(config):
        config["first_run"] = False
        with open(ConfigManager.FILE, "w") as f:
            json.dump(config, f, indent=4)
