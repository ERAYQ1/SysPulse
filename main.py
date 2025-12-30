import customtkinter as ctk
from utils import ConfigManager, LANGUAGES, ACCENTS
from engine import SysEngine
from ui import MainApp
import threading
import keyboard
import pystray
from PIL import Image, ImageDraw
import os
import sys

class StartupDialog(ctk.CTk):
    def __init__(self):
        super().__init__()
        self.title("SysPulse | Setup")
        self.geometry("400x450")
        self.config = ConfigManager.DEFAULTS.copy()
        
        self.grid_columnconfigure(0, weight=1)
        
        ctk.CTkLabel(self, text="🚀 SysPulse Setup", font=ctk.CTkFont(size=22, weight="bold")).pack(pady=30)
        
        # Language
        ctk.CTkLabel(self, text="Select Language", font=ctk.CTkFont(size=12)).pack(pady=(10, 0))
        self.lang_opt = ctk.CTkOptionMenu(self, values=list(LANGUAGES.keys()), command=self.set_lang)
        self.lang_opt.pack(pady=5)
        
        # Theme
        ctk.CTkLabel(self, text="Select Theme", font=ctk.CTkFont(size=12)).pack(pady=(10, 0))
        self.theme_opt = ctk.CTkOptionMenu(self, values=["Dark", "Light"], command=self.set_theme)
        self.theme_opt.pack(pady=5)
        
        # Accent
        ctk.CTkLabel(self, text="Select Accent Color", font=ctk.CTkFont(size=12)).pack(pady=(10, 0))
        self.accent_opt = ctk.CTkOptionMenu(self, values=list(ACCENTS.keys()), command=self.set_accent)
        self.accent_opt.pack(pady=5)
        
        ctk.CTkButton(self, text="Start SysPulse", command=self.finish, height=40, font=ctk.CTkFont(weight="bold")).pack(pady=40)

    def set_lang(self, v): self.config["language"] = v
    def set_theme(self, v): self.config["theme"] = v
    def set_accent(self, v): self.config["accent"] = v
    
    def finish(self):
        ConfigManager.save(self.config)
        self.withdraw() # Hide window immediately
        self.quit()     # Stop mainloop

def create_tray_icon(app):
    def on_quit(icon, item):
        icon.stop()
        app.exit_app()

    def on_show(icon, item):
        app.after(0, app.toggle_visibility)

    # Simple 64x64 icon
    img = Image.new('RGB', (64, 64), color='#3a7ebf')
    d = ImageDraw.Draw(img)
    d.rectangle([16, 16, 48, 48], fill='white')
    
    menu = pystray.Menu(
        pystray.Item('Show/Hide', on_show),
        pystray.Item('Exit', on_quit)
    )
    icon = pystray.Icon("SysPulse", img, "SysPulse Elite", menu)
    icon.run()

def main():
    config = ConfigManager.load()
    
    if config.get("first_run", True):
        setup = StartupDialog()
        setup.mainloop()
        config = ConfigManager.load()
    
    engine = SysEngine()
    app = MainApp(config, engine)
    
    # Global Hotkeys
    keyboard.add_hotkey('alt+s', app.toggle_visibility)
    keyboard.add_hotkey('alt+g', app.toggle_overlay)
    
    # Start engine thread
    thread = threading.Thread(target=engine.update_loop, args=(app.on_engine_data,), daemon=True)
    thread.start()
    
    # Start Tray in background
    tray_thread = threading.Thread(target=create_tray_icon, args=(app,), daemon=True)
    tray_thread.start()
    
    app.mainloop()

if __name__ == "__main__":
    main()
