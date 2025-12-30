import tkinter as tk
import customtkinter as ctk
import matplotlib.pyplot as plt
from matplotlib.backends.backend_tkagg import FigureCanvasTkAgg
from utils import LANGUAGES, ACCENTS, ConfigManager
import psutil
import platform
import keyboard
import threading
import socket
from datetime import datetime
from tkinter import messagebox
from PIL import Image, ImageDraw

class StatCard(ctk.CTkFrame):
    def __init__(self, master, title, value, sub, accent_color, **kwargs):
        super().__init__(master, corner_radius=15, border_width=1, **kwargs)
        self.accent_color = accent_color
        
        self.lbl_sub = ctk.CTkLabel(self, text=sub, font=ctk.CTkFont(size=9, weight="bold"), text_color=accent_color)
        self.lbl_sub.pack(pady=(12, 0), padx=15, anchor="w")
        
        self.lbl_title = ctk.CTkLabel(self, text=title, font=ctk.CTkFont(size=13))
        self.lbl_title.pack(pady=(0, 1), padx=15, anchor="w")
        
        self.lbl_val = ctk.CTkLabel(self, text=value, font=ctk.CTkFont(size=19, weight="bold"))
        self.lbl_val.pack(pady=(0, 12), padx=15, anchor="w")
        
        self.prog = ctk.CTkProgressBar(self, height=5, corner_radius=3, progress_color=accent_color)
        self.prog.pack(padx=15, pady=(0, 15), fill="x")
        self.prog.set(0)

    def update(self, val_text, val_float, accent=None):
        self.lbl_val.configure(text=val_text)
        self.prog.set(val_float)
        if accent:
            self.lbl_sub.configure(text_color=accent)
            self.prog.configure(progress_color=accent)

class GaugeChart(ctk.CTkCanvas):
    def __init__(self, master, size=120, title="CPU", accent="#3a7ebf", **kwargs):
        super().__init__(master, width=size, height=size, highlightthickness=0, **kwargs)
        self.size = size
        self.title = title
        self.accent = accent
        self.value = 0
        self.draw()

    def draw(self):
        self.delete("all")
        is_dark = ctk.get_appearance_mode() == "Dark"
        bg_color = "#1a1a1a" if is_dark else "#f9f9f9"
        self.configure(bg=bg_color)
        bg_circle = "#2d2d2d" if is_dark else "#e0e0e0"
        txt_color = "#ffffff" if is_dark else "#333333"
        
        # Background arc
        self.create_arc(10, 10, self.size-10, self.size-10, start=-30, extent=240, style="arc", outline=bg_circle, width=8)
        
        # Value arc
        extent = (self.value / 100) * 240
        self.create_arc(10, 10, self.size-10, self.size-10, start=210, extent=-extent, style="arc", outline=self.accent, width=8)
        
        # Text
        self.create_text(self.size/2, self.size/2, text=f"{int(self.value)}%", fill=txt_color, font=("Outfit", 14, "bold"))
        self.create_text(self.size/2, self.size-25, text=self.title, fill=self.accent, font=("Outfit", 9, "bold"))

    def set_value(self, val, accent=None):
        self.value = val
        if accent: self.accent = accent
        self.draw()

class GhostOverlay(ctk.CTkToplevel):
    def __init__(self, master, accent):
        super().__init__(master)
        self.title("Overlay")
        self.geometry("220x160+20+20")
        self.overrideredirect(True)
        self.attributes("-topmost", True)
        self.attributes("-alpha", 0.7)
        self.wm_attributes("-transparentcolor", "#000001")
        self.config(bg="#000001")
        
        self.frame = ctk.CTkFrame(self, corner_radius=15, border_width=1, border_color=accent, fg_color="#1a1a1a")
        self.frame.pack(fill="both", expand=True)
        
        self.lbl_cpu = ctk.CTkLabel(self.frame, text="CPU: 0%", font=ctk.CTkFont(size=14, weight="bold"))
        self.lbl_cpu.pack(pady=(15, 2))
        self.lbl_ram = ctk.CTkLabel(self.frame, text="RAM: 0%", font=ctk.CTkFont(size=14, weight="bold"))
        self.lbl_ram.pack(pady=2)
        self.lbl_gpu = ctk.CTkLabel(self.frame, text="GPU: 0%", font=ctk.CTkFont(size=14, weight="bold"))
        self.lbl_gpu.pack(pady=2)
        self.lbl_fps = ctk.CTkLabel(self.frame, text="FPS: --", font=ctk.CTkFont(size=12), text_color=accent)
        self.lbl_fps.pack(pady=(2, 15))

    def update_stats(self, data):
        self.lbl_cpu.configure(text=f"CPU: {data['cpu']}% @ {data['cpu_t']:.0f}°C")
        self.lbl_ram.configure(text=f"RAM: {data['ram_p']}%")
        self.lbl_gpu.configure(text=f"GPU: {data['gpu_v']}% | {data['gpu_t']}°C")

class MainApp(ctk.CTk):
    def __init__(self, config, engine):
        super().__init__()
        self.config = config
        self.engine = engine
        self.is_mini = False
        
        # Apply initial config
        ctk.set_appearance_mode(config["theme"])
        self.accent_color = ACCENTS.get(config["accent"], "#3a7ebf")
        self.lang_code = config["language"]
        
        self.title(self.t("title"))
        self.geometry("1100x750")
        self.grid_columnconfigure(1, weight=1)
        self.grid_rowconfigure(0, weight=1)

        self.setup_ui()
        self.overlay = None
        self.protocol("WM_DELETE_WINDOW", self.on_closing)

    def t(self, key):
        return LANGUAGES.get(self.lang_code, LANGUAGES["English"]).get(key, key)

    def setup_ui(self):
        # Sidebar
        self.sidebar = ctk.CTkFrame(self, width=220, corner_radius=0)
        self.sidebar.grid(row=0, column=0, sticky="nsew")
        self.sidebar.grid_rowconfigure(15, weight=1)
        
        ctk.CTkLabel(self.sidebar, text="🚀 SysPulse", font=ctk.CTkFont(size=26, weight="bold")).grid(row=0, column=0, padx=20, pady=30)
        
        self.btn_dash = self.create_nav(self.t("dash"), lambda: self.show_page("dash"), 1)
        self.btn_info = self.create_nav(self.t("info"), lambda: self.show_page("info"), 2)
        self.btn_proc = self.create_nav(self.t("proc"), self.show_processes, 3)
        
        # Quick Settings
        ctk.CTkLabel(self.sidebar, text=self.t("refresh"), font=ctk.CTkFont(size=10)).grid(row=6, column=0, pady=(20, 0))
        self.refresh_slider = ctk.CTkSlider(self.sidebar, from_=0.5, to=5.0, number_of_steps=9, command=self.change_refresh)
        self.refresh_slider.set(self.config["refresh_rate"])
        self.refresh_slider.grid(row=7, column=0, padx=20, pady=5)
        self.accent_opt = ctk.CTkOptionMenu(self.sidebar, values=list(ACCENTS.keys()), command=self.change_accent, height=22)
        self.accent_opt.set(self.config["accent"])
        self.accent_opt.grid(row=9, column=0, padx=20, pady=5)
        
        self.theme_switch = ctk.CTkSwitch(self.sidebar, text=self.t("dark"), command=self.toggle_theme)
        if self.config["theme"] == "Dark": self.theme_switch.select()
        self.theme_switch.grid(row=10, column=0, padx=20, pady=10)
        
        self.mini_switch = ctk.CTkSwitch(self.sidebar, text=self.t("mini_mode"), command=self.toggle_mini)
        self.mini_switch.grid(row=11, column=0, padx=20, pady=10)
        
        # Terminator (Exit)
        ctk.CTkButton(self.sidebar, text="❌ EXIT", fg_color="#c0392b", hover_color="#962d22", font=ctk.CTkFont(weight="bold"), command=self.exit_app).grid(row=20, column=0, padx=20, pady=30, sticky="s")
        
        # Main Area
        self.container = ctk.CTkFrame(self, fg_color="transparent")
        self.container.grid(row=0, column=1, padx=20, pady=20, sticky="nsew")
        self.container.grid_columnconfigure(0, weight=1)
        self.container.grid_rowconfigure(1, weight=1)
        
        self.pages = {}
        self.setup_dash()
        self.setup_info()
        
        # Mini Mode Return Button (Hidden by default)
        self.mini_back_btn = ctk.CTkButton(self.container, text="🔙 Full Mode", width=80, height=24, fg_color="transparent", border_width=1, command=self.disable_mini)
        
        self.show_page("dash")

    def create_nav(self, text, cmd, row):
        btn = ctk.CTkButton(self.sidebar, text=text, command=cmd, fg_color="transparent", text_color=["#333333", "#dddddd"], hover_color=["#efefef", "#333333"], anchor="w")
        btn.grid(row=row, column=0, padx=20, pady=2, sticky="ew")
        return btn

    def setup_dash(self):
        page = ctk.CTkFrame(self.container, fg_color="transparent")
        self.pages["dash"] = page
        
        h_frame = ctk.CTkFrame(page, fg_color="transparent")
        h_frame.pack(fill="x", pady=(0, 20))
        ctk.CTkLabel(h_frame, text=self.t("overview"), font=ctk.CTkFont(size=22, weight="bold")).pack(side="left")
        self.ping_lbl = ctk.CTkLabel(h_frame, text="Ping: ...", font=ctk.CTkFont(size=12), text_color="gray")
        self.ping_lbl.pack(side="right")
        
        # Gauges
        g_frame = ctk.CTkFrame(page, fg_color="transparent")
        g_frame.pack(fill="x", pady=(0, 20))
        self.cpu_gauge = GaugeChart(g_frame, title="CPU", accent=self.accent_color)
        self.cpu_gauge.pack(side="left", padx=20)
        self.ram_gauge = GaugeChart(g_frame, title="RAM", accent=self.accent_color)
        self.ram_gauge.pack(side="left", padx=20)
        
        # Stat Cards
        c_grid = ctk.CTkFrame(page, fg_color="transparent")
        c_grid.pack(fill="x", pady=(0, 20))
        c_grid.grid_columnconfigure((0, 1, 2, 3), weight=1)
        
        self.cpu_card = StatCard(c_grid, self.t("cpu"), "0%", "CORE", self.accent_color)
        self.cpu_card.grid(row=0, column=0, padx=5, sticky="ew")
        self.ram_card = StatCard(c_grid, self.t("ram"), "0%", "GB", self.accent_color)
        self.ram_card.grid(row=0, column=1, padx=5, sticky="ew")
        self.gpu_card = StatCard(c_grid, self.t("gpu"), "N/A", "TEMP", self.accent_color)
        self.gpu_card.grid(row=0, column=2, padx=5, sticky="ew")
        self.bt_card = StatCard(c_grid, self.t("batt"), "N/A", "%", self.accent_color)
        self.bt_card.grid(row=0, column=3, padx=5, sticky="ew")
        
        # Additional info panel (IP + Net)
        self.extra_box = ctk.CTkFrame(page, corner_radius=15, border_width=1)
        self.extra_box.pack(fill="x", pady=(0, 20))
        self.ip_display = ctk.CTkLabel(self.extra_box, text="Searching IPs...", font=ctk.CTkFont(size=11))
        self.ip_display.pack(pady=10)
        
        # Disk Section (New)
        self.disk_f = ctk.CTkFrame(page, fg_color="transparent")
        self.disk_f.pack(fill="x", pady=(0, 20))
        self.disk_bars = {} # storage for dynamic bars

        # Graph
        self.graph_box = ctk.CTkFrame(page, corner_radius=15, border_width=1)
        self.graph_box.pack(fill="both", expand=True)
        self.setup_graph()

    def setup_info(self):
        page = ctk.CTkFrame(self.container, fg_color="transparent")
        self.pages["info"] = page
        
        ctk.CTkLabel(page, text="🖥️ Deep System Specification", font=ctk.CTkFont(size=22, weight="bold")).pack(pady=(0, 20), anchor="w")
        
        scroll = ctk.CTkScrollableFrame(page, corner_radius=15, border_width=1)
        scroll.pack(fill="both", expand=True)
        
        def add_section(title, data):
            f = ctk.CTkFrame(scroll, fg_color="transparent")
            f.pack(fill="x", pady=10, padx=10)
            ctk.CTkLabel(f, text=title, font=ctk.CTkFont(size=14, weight="bold"), text_color=self.accent_color).pack(anchor="w")
            for k, v in data.items():
                row = ctk.CTkFrame(f, fg_color="transparent")
                row.pack(fill="x", pady=1)
                ctk.CTkLabel(row, text=f"{k}:", font=ctk.CTkFont(size=11, weight="bold"), width=120, anchor="w").pack(side="left")
                ctk.CTkLabel(row, text=str(v), font=ctk.CTkFont(size=11), anchor="w").pack(side="left", padx=5)

        # OS Data
        u = platform.uname()
        os_data = {
            "OS": f"{u.system} {u.release}",
            "Build": platform.version(),
            "Architecture": u.machine,
            "Node Name": u.node,
            "Boot Time": datetime.fromtimestamp(psutil.boot_time()).strftime("%Y-%m-%d %H:%M:%S")
        }
        add_section("🌐 Operating System", os_data)

        # CPU Data
        cpu_data = {
            "Processor": u.processor,
            "Physical Cores": psutil.cpu_count(logical=False),
            "Total Threads": psutil.cpu_count(logical=True),
            "Max Frequency": f"{psutil.cpu_freq().max:.0f}MHz" if psutil.cpu_freq() else "N/A"
        }
        add_section("🧠 Processor (CPU)", cpu_data)

        # RAM Data
        svmem = psutil.virtual_memory()
        ram_data = {
            "Total RAM": f"{svmem.total / (1024**3):.2f} GB",
            "Available": f"{svmem.available / (1024**3):.2f} GB",
            "Swap Total": f"{psutil.swap_memory().total / (1024**3):.2f} GB"
        }
        add_section("⚡ Memory (RAM)", ram_data)

        # GPU Data
        gpu_data = {"Active GPU": self.engine.gpu_name}
        add_section("🎮 Graphics (GPU)", gpu_data)

        # Network Interfaces
        net_data = {}
        for interface, addrs in psutil.net_if_addrs().items():
            for addr in addrs:
                if addr.family == socket.AF_INET:
                    net_data[interface] = addr.address
        add_section("📡 Network Adapters", net_data)

        ctk.CTkLabel(scroll, text="Hotkeys: Alt+S (Toggle) | Alt+G (Overlay)", font=ctk.CTkFont(size=10), text_color="gray").pack(pady=20)

    def setup_graph(self):
        is_dark = ctk.get_appearance_mode() == "Dark"
        plt.style.use('dark_background' if is_dark else 'bmh')
        self.fig, self.ax = plt.subplots(figsize=(8, 3), dpi=100)
        self.fig.patch.set_facecolor('#1a1a1a' if is_dark else '#ffffff')
        self.ax.set_facecolor('#1e1e1e' if is_dark else '#f9f9f9')
        self.cpu_ln, = self.ax.plot(self.engine.history["cpu"], color=self.accent_color, label="CPU")
        self.ram_ln, = self.ax.plot(self.engine.history["ram"], color="#e91e63", label="RAM")
        self.ax.set_ylim(0, 105)
        self.ax.legend(loc="upper right", frameon=False)
        self.canvas = FigureCanvasTkAgg(self.fig, master=self.graph_box)
        self.canvas.draw()
        self.canvas.get_tk_widget().pack(fill="both", expand=True, padx=10, pady=10)

    def show_page(self, name):
        for p in self.pages.values(): p.pack_forget()
        self.pages[name].pack(fill="both", expand=True)

    def on_engine_data(self, data):
        self.cpu_gauge.set_value(data["cpu"], self.accent_color)
        self.ram_gauge.set_value(data["ram_p"], self.accent_color)
        self.cpu_card.update(f"{data['cpu']}% @ {data['cpu_t']:.0f}°C", data['cpu']/100, self.accent_color)
        self.ram_card.update(f"{data['ram_p']}%", data['ram_p']/100, self.accent_color)
        self.gpu_card.update(f"{data['gpu_v']}% | {data['vram']:.0f}% VRAM", data['gpu_v']/100, self.accent_color)
        if data["batt"]: self.bt_card.update(f"{data['batt'].percent}%", data['batt'].percent/100, self.accent_color)
        self.ping_lbl.configure(text=f"Ping: {data['ping']}")
        
        if self.overlay:
            self.overlay.update_stats(data)
        
        # Update Disks
        if "disks" in data:
            for d in data["disks"]:
                name = d["name"]
                if name not in self.disk_bars:
                    frame = ctk.CTkFrame(self.disk_f, fg_color="transparent")
                    frame.pack(fill="x", pady=2)
                    ctk.CTkLabel(frame, text=f"Disk {name}", font=ctk.CTkFont(size=10)).pack(side="left", padx=5)
                    pb = ctk.CTkProgressBar(frame, height=8, progress_color=self.accent_color)
                    pb.pack(side="left", fill="x", expand=True, padx=10)
                    self.disk_bars[name] = pb
                self.disk_bars[name].set(d["used"]/100)
        
        # Build IP + Adapter info
        txt = data["ip"]
        if data["adapters"]:
            txt += "\n" + " | ".join([f"{k}: {v:.1f}KB/s" for k,v in data["adapters"].items()][:2])
        self.ip_display.configure(text=txt)
        
        if not self.is_mini:
            self.cpu_ln.set_ydata(self.engine.history["cpu"])
            self.ram_ln.set_ydata(self.engine.history["ram"])
            self.canvas.draw_idle()

    def change_accent(self, name):
        self.accent_color = ACCENTS[name]
        self.config["accent"] = name
        self.setup_graph()
        ConfigManager.save(self.config)

    def change_refresh(self, val):
        self.engine.refresh_interval = val
        self.config["refresh_rate"] = val
        ConfigManager.save(self.config)

    def toggle_theme(self):
        new = "Dark" if self.theme_switch.get() else "Light"
        self.config["theme"] = new
        ctk.set_appearance_mode(new)
        self.setup_graph()
        ConfigManager.save(self.config)

    def toggle_mini(self):
        self.is_mini = self.mini_switch.get()
        if self.is_mini:
            self.geometry("280x260")
            self.sidebar.grid_forget()
            self.graph_box.pack_forget()
            self.mini_back_btn.pack(pady=(0, 10))
            self.attributes("-topmost", True)
        else:
            self.geometry("1100x750")
            self.mini_back_btn.pack_forget()
            self.sidebar.grid(row=0, column=0, sticky="nsew")
            self.graph_box.pack(fill="both", expand=True)
            self.attributes("-topmost", False)

    def disable_mini(self):
        self.mini_switch.deselect()
        self.toggle_mini()

    def toggle_overlay(self):
        if self.overlay:
            self.overlay.destroy()
            self.overlay = None
        else:
            self.overlay = GhostOverlay(self, self.accent_color)

    def toggle_visibility(self):
        if self.state() == "withdrawn":
            self.deiconify()
            self.attributes("-topmost", True)
            self.after(100, lambda: self.attributes("-topmost", False))
        else:
            self.withdraw()

    def show_processes(self):
        w = ctk.CTkToplevel(self); w.title("Apex Task Manager"); w.geometry("700x600")
        w.grid_columnconfigure(0, weight=1)
        
        header = ctk.CTkFrame(w, fg_color="transparent")
        header.pack(fill="x", pady=10)
        ctk.CTkLabel(header, text="Process Name", font=ctk.CTkFont(size=12, weight="bold"), width=180, anchor="w").pack(side="left", padx=10)
        ctk.CTkLabel(header, text="CPU%", font=ctk.CTkFont(size=12, weight="bold"), width=60).pack(side="left")
        ctk.CTkLabel(header, text="RAM (MB)", font=ctk.CTkFont(size=12, weight="bold"), width=80).pack(side="left")
        ctk.CTkLabel(header, text="Recommendation", font=ctk.CTkFont(size=12, weight="bold"), width=150).pack(side="left")
        
        scroll = ctk.CTkScrollableFrame(w)
        scroll.pack(fill="both", expand=True, padx=10, pady=5)
        
        def kill(pid, row_frame):
            if self.engine.kill_process(pid):
                row_frame.destroy()
                messagebox.showinfo("Success", f"PID {pid} terminated")
            else:
                messagebox.showerror("Error", "Critical System Process - Access Denied")

        def refresh():
            for child in scroll.winfo_children(): child.destroy()
            try:
                procs = []
                # Fetch more details: memory and status
                for p in psutil.process_iter(['pid', 'name', 'username', 'cpu_percent', 'memory_info', 'status']):
                    try: procs.append(p.info)
                    except: pass
                
                procs = sorted(procs, key=lambda x: x['cpu_percent'] or 0, reverse=True)[:20]
                
                for p in procs:
                    f = ctk.CTkFrame(scroll, fg_color="#2b2b2b" if ctk.get_appearance_mode() == "Dark" else "#f0f0f0")
                    f.pack(fill="x", pady=2)
                    
                    # Risk Assessment
                    is_sys = not p['username'] or any(s in p['username'].upper() for s in ['SYSTEM', 'LOCAL SERVICE', 'NETWORK SERVICE'])
                    risk_text = "⚠️ Danger (System)" if is_sys else "✅ Safe (App)"
                    risk_color = "#e74c3c" if is_sys else "#2ecc71"
                    if not is_sys and p['cpu_percent'] > 50:
                        risk_text = "⚡ High Load (Kill?)"
                        risk_color = "#f1c40f"
                    
                    mem_mb = p['memory_info'].rss / (1024 * 1024) if p['memory_info'] else 0
                    
                    ctk.CTkLabel(f, text=f"{p['name'][:22]}", width=180, anchor="w", font=ctk.CTkFont(size=11)).pack(side="left", padx=10)
                    ctk.CTkLabel(f, text=f"{p['cpu_percent']}%", width=60).pack(side="left")
                    ctk.CTkLabel(f, text=f"{mem_mb:.1f}", width=80).pack(side="left")
                    ctk.CTkLabel(f, text=risk_text, text_color=risk_color, width=150, font=ctk.CTkFont(size=10, weight="bold")).pack(side="left")
                    
                    btn = ctk.CTkButton(f, text="Kill", width=50, height=22, fg_color="#e74c3c", hover_color="#c0392b", command=lambda pid=p['pid'], rf=f: kill(pid, rf))
                    btn.pack(side="right", padx=10)
            except: pass

        ctk.CTkButton(w, text="🔄 Refresh List", command=refresh, width=200).pack(pady=15)
        refresh()

    def on_closing(self):
        self.withdraw() # Default to tray instead of exit
        return "break"

    def exit_app(self):
        self.engine.stop()
        self.destroy()
