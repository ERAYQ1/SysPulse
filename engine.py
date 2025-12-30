import psutil
import threading
import time
import socket
import requests
import platform
import os
try:
    import wmi
    HAS_WMI = True
except ImportError:
    HAS_WMI = False
import winsound
from datetime import datetime
try:
    import pynvml
    HAS_GPU = True
except ImportError:
    HAS_GPU = False

class SysEngine:
    def __init__(self):
        self.is_running = True
        self.stats = {}
        self.history = {"cpu": [0] * 600, "ram": [0] * 600}
        self.refresh_interval = 1.0
        self.gpu_handle = None
        self.wmi_conn = None
        
        try:
            if HAS_WMI:
                self.wmi_conn = wmi.WMI(namespace="root\\wmi")
        except: pass

        if HAS_GPU:
            try:
                pynvml.nvmlInit()
                self.gpu_handle = pynvml.nvmlDeviceGetHandleByIndex(0)
                gpu_name = pynvml.nvmlDeviceGetName(self.gpu_handle)
                if isinstance(gpu_name, bytes): gpu_name = gpu_name.decode()
                self.gpu_name = gpu_name
            except:
                self.gpu_name = "N/A"
        else:
            self.gpu_name = "N/A"

    def get_cpu_temp(self):
        try:
            if HAS_WMI and self.wmi_conn:
                temps = self.wmi_conn.MSAcpi_ThermalZoneTemperature()
                if temps:
                    return (temps[0].CurrentTemperature / 10.0) - 273.15
            return 0
        except: return 0

    def play_alert(self):
        try: winsound.Beep(1000, 200)
        except: pass

    def get_ips(self):
        try:
            local_ip = socket.gethostbyname(socket.gethostname())
            public_ip = requests.get('https://api.ipify.org', timeout=2).text
            return local_ip, public_ip
        except:
            return "127.0.0.1", "Unknown"

    def get_ping(self):
        try:
            # Simple ping test to a fast DNS
            s = socket.socket(socket.AF_INET, socket.SOCK_STREAM)
            s.settimeout(1)
            start = time.time()
            s.connect(("8.8.8.8", 53))
            ping = (time.time() - start) * 1000
            s.close()
            return f"{int(ping)} ms"
        except:
            return "N/A"

    def kill_process(self, pid):
        try:
            p = psutil.Process(pid)
            p.terminate()
            return True
        except:
            return False

    def log_peak(self, metric, val):
        fn = f"peak_log_{datetime.now().strftime('%Y%m%d')}.txt"
        with open(fn, "a") as f:
            f.write(f"[{datetime.now().strftime('%H:%M:%S')}] PEAK: {metric} @ {val}%\n")

    def update_loop(self, callback):
        local_ip, public_ip = self.get_ips()
        ping_counter = 0
        current_ping = "..."

        while self.is_running:
            try:
                cpu = psutil.cpu_percent()
                ram = psutil.virtual_memory()
                net_speed = 0
                adapter_speeds = {}
                
                # Disk
                disks = []
                for part in psutil.disk_partitions():
                    if 'fixed' in part.opts or 'rw' in part.opts:
                        try:
                            usage = psutil.disk_usage(part.mountpoint)
                            disks.append({"name": part.device, "total": usage.total, "used": usage.percent})
                        except: pass

                if cpu > 92 or ram.percent > 92:
                    self.play_alert()
                    if cpu > 92: self.log_peak("CPU", cpu)
                    if ram.percent > 92: self.log_peak("RAM", ram.percent)

                ctemp = self.get_cpu_temp()

                # GPU & VRAM
                gv, gt, vram = 0, 0, 0
                if self.gpu_handle:
                    try:
                        res = pynvml.nvmlDeviceGetUtilizationRates(self.gpu_handle)
                        gv = res.gpu
                        gt = pynvml.nvmlDeviceGetTemperature(self.gpu_handle, 0)
                        v_info = pynvml.nvmlDeviceGetMemoryInfo(self.gpu_handle)
                        vram = (v_info.used / v_info.total) * 100
                    except: pass
                
                # Battery
                batt = psutil.sensors_battery()
                
                if ping_counter % 8 == 0:
                    current_ping = self.get_ping()
                ping_counter += 1

                self.history["cpu"].append(cpu)
                self.history["cpu"].pop(0)
                self.history["ram"].append(ram.percent)
                self.history["ram"].pop(0)

                self.stats = {
                    "cpu": cpu,
                    "cpu_t": ctemp,
                    "ram_p": ram.percent,
                    "ram_gb": f"{ram.used/(1024**3):.1f}GB",
                    "gpu_v": gv,
                    "gpu_t": gt,
                    "vram": vram,
                    "net": net_speed,
                    "adapters": adapter_speeds,
                    "ping": current_ping,
                    "batt": batt,
                    "disks": disks,
                    "ip": f"L: {local_ip} | P: {public_ip}"
                }
                
                callback(self.stats)
                time.sleep(max(0.1, self.refresh_interval - 0.5))
            except Exception as e:
                pass

    def stop(self):
        self.is_running = False
        if self.gpu_handle:
            try: pynvml.nvmlShutdown()
            except: pass
