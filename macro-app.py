import json
import os
import subprocess
import threading
import shutil
import serial
import serial.tools.list_ports
import customtkinter as ctk
from datetime import datetime
import pystray
from PIL import Image, ImageDraw

CONFIG_FILE = "promicro_config.json"

class ProMicroLiveApp(ctk.CTk):
    def __init__(self):
                # System Tray State Management Tracks
        self.tray_icon = None

        super().__init__()
        
        self.title("Pro Micro Smart Macro Configurator")
        self.geometry("720x800")
        ctk.set_appearance_mode("dark")
        
        self.ser = None
        self.running = False
        self.listen_thread = None
        self.active_port = None
        self.auto_reconnect_mode = False
        self.macros = {}
        for r in range(4):
            for c in range(4):
                self.macros[f"BTN_{r}_{c}"] = ""
                
        self.load_config()
        self.create_widgets()
        
    def create_widgets(self):
        # 1. Connection Header Frame
        self.top_frame = ctk.CTkFrame(self)
        self.top_frame.pack(pady=10, padx=10, fill="x")
        
        self.port_label = ctk.CTkLabel(self.top_frame, text="Select Pro Micro Port:")
        self.port_label.pack(side="left", padx=10)
        
        ports = [p.device for p in serial.tools.list_ports.comports()]
        self.port_dropdown = ctk.CTkComboBox(self.top_frame, values=ports if ports else ["No Ports Found"])
        self.port_dropdown.pack(side="left", padx=10)
        
        self.connect_btn = ctk.CTkButton(self.top_frame, text="Sync Device", command=self.connect_hardware)
        self.connect_btn.pack(side="left", padx=10)
        
        # 2. Syntax Reference Cheat Sheet Box (Permanently at the top)
        self.syntax_frame = ctk.CTkMoplevelFrame if hasattr(ctk, 'CTkMoplevelFrame') else ctk.CTkFrame(self, fg_color="#1a1a24", border_width=1, border_color="#333344")
        self.syntax_frame.pack(pady=5, padx=10, fill="x")
        
        syntax_title = ctk.CTkLabel(self.syntax_frame, text="💡 MACRO PAD SYNTAX QUICK REFERENCE", font=("Arial", 11, "bold"), text_color="#528bff")
        syntax_title.pack(anchor="w", padx=12, pady=(8, 2))
        
        syntax_text = (
            "• Multimedia Keys:\n"
            "   media:volup      ➔  Raises System Volume\n"
            "   media:voldown    ➔  Lowers System Volume\n"
            "   media:play       ➔  Toggles Play / Pause\n"
            "   media:skip       ➔  Skips to the Next Track\n"
            "   media:prev       ➔  Returns to the Previous Track\n\n"
            "• Program Launchers:\n"
            "   run:https://     ➔  Launches Google Chrome\n"
            "   run:spotify      ➔  Launches Spotify (Handles standard or Microsoft Store versions)\n"
            "   run:discord      ➔  Launches Discord\n"
            "   run:C:\\Path\\...  ➔  Launches any custom executable file path natively\n\n"
            "• Windows Shortcuts & Hotkeys:\n"
            "   ctrl+c           ➔  Copies Highlighted Clipboard Text\n"
            "   ctrl+v           ➔  Pastes Clipboard Stream Data\n"
            "   alt+tab          ➔  Toggles Active Windows\n\n"
            "• Standard Text String Generation:\n"
            "   [Plain Text]     ➔  Type anything else (e.g. your email address) to type it out directly."
        )
        self.syntax_guide = ctk.CTkLabel(self.syntax_frame, text=syntax_text, font=("Consolas", 10), justify="left", text_color="#d0d0d5")
        self.syntax_guide.pack(anchor="w", padx=15, pady=(2, 10))
        
        # 3. Interactive Key Grid
        self.grid_frame = ctk.CTkFrame(self)
        self.grid_frame.pack(pady=5, padx=10, fill="both", expand=True)
        
        self.entries = {}
        for r in range(4):
            self.grid_frame.grid_rowconfigure(r, weight=1)
            for c in range(4):
                self.grid_frame.grid_columnconfigure(c, weight=1)
                
                btn_key = f"BTN_{r}_{c}"
                frame = ctk.CTkFrame(self.grid_frame)
                frame.grid(row=r, column=c, padx=3, pady=3, sticky="nsew")
                
                label = ctk.CTkLabel(frame, text=f"Key {r+1},{c+1}", font=("Arial", 9, "bold"))
                label.pack(pady=1)
                
                entry = ctk.CTkEntry(frame, placeholder_text="Enter macro syntax...")
                entry.insert(0, self.macros[btn_key])
                entry.pack(padx=5, pady=1, fill="x")
                
                entry.bind("<KeyRelease>", lambda event, k=btn_key: self.push_macro_to_hardware(k))
                self.entries[btn_key] = entry

        # 4. Scrollable Live Console Monitor Panel
        self.log_frame = ctk.CTkFrame(self, fg_color="#111111")
        self.log_frame.pack(pady=10, padx=10, fill="x")
        
        self.log_label = ctk.CTkLabel(self.log_frame, text="Live Console Output & System Errors Monitor:", font=("Arial", 10, "bold"), text_color="cyan")
        self.log_label.pack(anchor="w", padx=10, pady=2)
        
        self.log_box = ctk.CTkTextbox(self.log_frame, height=140, font=("Consolas", 11), fg_color="#151515")
        self.log_box.pack(padx=10, pady=5, fill="x")
        self.log_box.configure(state="disabled")
        
        self.write_log("Application initialized. Smart look-up indexing engine online.", "SYSTEM")

    def write_log(self, message, log_type="INFO"):
        timestamp = datetime.now().strftime("%H:%M:%S")
        formatted_line = f"[{timestamp}] [{log_type}] {message}\n"
        
        self.log_box.configure(state="normal")
        self.log_box.insert("end", formatted_line)
        self.log_box.see("end")
        self.log_box.configure(state="disabled")

    def load_config(self):
        if os.path.exists(CONFIG_FILE):
            try:
                with open(CONFIG_FILE, "r") as f:
                    self.macros.update(json.load(f))
            except Exception:
                pass
    def connect_hardware(self):
        port = self.port_dropdown.get()
        if port and port != "No Ports Found":
            self.active_port = port
            self.auto_reconnect_mode = True
            try: 
                self.running = True
                if self.ser and self.ser.is_open:
                    self.ser.close()
                
                # ⚡ FIXED ALIGNMENT: Safely outside the "if self.ser" cleanup check
                self.ser = serial.Serial(port, 115200, timeout=0.1)
                self.running = True
                self.connect_btn.configure(text="Synced ✓", fg_color="green", hover_color="darkgreen")
                self.write_log(f"Matrix connection link open on {port}!", "SUCCESS")
            
                for btn_key in self.macros:
                    self.push_macro_to_hardware(btn_key, silent=True)
            
                self.listen_thread = threading.Thread(target=self.listen_for_hardware_logs, daemon=True)
                self.listen_thread.start()
            except Exception as e:
                self.connect_btn.configure(text="Sync Failed", fg_color="red")
                self.write_log(f"Failed to open hardware pipeline: {str(e)}", "ERROR")


    def listen_for_hardware_logs(self):
        while self.running:
            if self.ser and self.ser.is_open and self.ser.in_waiting > 0:
                try:
                    line = self.ser.readline().decode('utf-8').strip()
                    
                    if line.startswith("EXEC_KEY:"):
                        key_info = line[9:].strip()
                        self.write_log(f"Key Stroke Tapped: Matrix Location {key_info}", "KEYPRESS")
                        
                    elif line.startswith("RUN_CMD:run:"):
                        app_name = line[12:].strip()
                        self.write_log(f"Resolving shortcut path index for target: '{app_name}'", "SHELL")
                        
                        threading.Thread(target=self.smart_launch_app, args=(app_name,), daemon=True).start()
                except Exception:
                    pass

    def smart_launch_app(self, target):
        executable = target
        if not executable.lower().endswith(".exe") and not "\\" in executable:
            executable += ".exe"

        resolved_path = shutil.which(executable)
        
        if resolved_path:
            self.write_log(f"Match found! Launching local binary: '{resolved_path}'", "EXECUTE")
            subprocess.Popen(resolved_path, shell=True)
            return

        self.write_log(f"Local binary not indexed. Falling back to native system protocol scheme layout...", "WARN")
        try:
            protocol_name = target.replace(".exe", "").lower()
            subprocess.Popen(f"start {protocol_name}:", shell=True)
            self.write_log(f"Sent protocol payload call for standard execution name: '{protocol_name}:'", "SUCCESS")
        except Exception as err:
            self.write_log(f"CRITICAL ACCESS ERROR: Windows was unable to find or run '{target}'. Details: {str(err)}", "ERROR")

    def push_macro_to_hardware(self, btn_key, silent=False):
        raw_text = self.entries[btn_key].get().strip()
        self.macros[btn_key] = raw_text
        
        with open(CONFIG_FILE, "w") as f:
            json.dump(self.macros, f)
            
        if self.ser and self.ser.is_open:
            coord_str = btn_key.replace("BTN_", "")
            packet = f"SET:{coord_str}:{raw_text}\n"
            try:
                self.ser.write(packet.encode('utf-8'))
                if not silent:
                    self.write_log(f"Updated slot memory cells for {btn_key.replace('BTN_','Key ')} ➔ '{raw_text}'", "SYNC")
            except Exception as e:
                if not silent:
                    self.write_log(f"Failed to stream memory block write for {btn_key}: {str(e)}", "ERROR")
    def hardware_reconnect_loop(self):
        import time
        import os
        while True:
            time.sleep(2.0)
            
            try:
                current_ports = [p.device for p in serial.tools.list_ports.comports()]
                if current_ports:
                    self.port_dropdown.configure(values=current_ports)
            except Exception:
                pass

            if self.auto_reconnect_mode:
                if self.running and (self.ser is None or not self.ser.is_open or not os.path.exists(self.active_port if os.name == 'nt' else '/dev')):
                    self.running = False
                    self.connect_btn.configure(text="Reconnecting...", fg_color="#7a2424")
                    self.write_log(f"Hardware connection line dropped on {self.active_port}. Scanning USB hubs...", "WARN")
                
                if not self.running:
                    ports = [p.device for p in serial.tools.list_ports.comports()]
                    
                    if self.active_port in ports:
                        self.port_dropdown.set(self.active_port)
                        self.connect_hardware()
                        if self.running:
                            self.write_log(f"Auto-Recovery Success! Restored link on {self.active_port}.", "SUCCESS")
                            
                    elif len(ports) > 0:
                        fallback_port = ports[0]
                        self.port_dropdown.set(fallback_port)
                        self.connect_hardware()
                        if self.running:
                            self.active_port = fallback_port
                            self.write_log(f"Auto-Recovery Success! Discovered alternative node {fallback_port}.", "SUCCESS")
    def create_tray_icon(self):
        # Dynamically draws a simple 16x16 cyan dot icon for your system tray
        image = Image.new("RGBA", (16, 16), (0, 0, 0, 0))
        draw = ImageDraw.Draw(image)
        draw.ellipse((2, 2, 14, 14), fill="cyan")
        
        # Build the right-click system tray context menu items
        menu = pystray.Menu(
            pystray.MenuItem("Open Dashboard", self.restore_from_tray, default=True),
            pystray.MenuItem("Exit Completely", self.exit_application)
        )
        
        self.tray_icon = pystray.Icon("MacroPadApp", image, "Pro Micro Configurator", menu)
        # Fire up the tray icon asset loop on a completely separate background thread
        threading.Thread(target=self.tray_icon.run, daemon=True).start()

    def check_minimize_event(self, event):
        # Catch when the user clicks the native standard Windows minimize minus line
        if self.state() == "iconic":
            self.minimize_to_tray()

    def minimize_to_tray(self):
        self.withdraw() # Completely hides the window from your screen and taskbar
        if not self.tray_icon:
            self.create_tray_icon()
        self.write_log("Application window minimized securely to your system tray tracker.", "SYSTEM")

    def restore_from_tray(self, icon=None, item=None):
        self.deiconify() # Pulls the window container back onto your desktop screen
        self.state("normal")
        self.focus()

    def exit_application(self, icon=None, item=None):
        self.running = False
        if self.ser and self.ser.is_open:
            self.ser.close()
        if self.tray_icon:
            self.tray_icon.stop()
        self.destroy() # Completely terminates the window loop environment thread footprint
if __name__ == "__main__":
    app = ProMicroLiveApp()
    
    # ⚡ AUTOMATED STARTUP-TO-TRAY ENGINE
    def safe_tray_bindings():
        # 1. Bind our tray protocols safely after the window draws
        app.protocol("WM_DELETE_WINDOW", app.minimize_to_tray)
        app.bind("<Unmap>", lambda e: app.check_minimize_event(e))
        
        # 2. HIDDEN BYPASS ACTION: Instantly force the window to hide into the tray on boot
        app.withdraw()
        if not app.tray_icon:
            app.create_tray_icon()
        
        # 3. Kick off the background hardware auto-reconnect loop thread
        threading.Thread(target=app.hardware_reconnect_loop, daemon=True).start()
        
        # 4. HANDS-FREE BOOT AUTOCONNECT ENGINE (Runs silently in the background)
        app.write_log("Running automated startup hardware probe scan...", "SYSTEM")
        ports = [p.device for p in serial.tools.list_ports.comports()]
        
        if ports:
            target_port = app.macros.get("LAST_SAVED_PORT", ports[0])
            if target_port not in ports:
                target_port = ports[0]
                
            app.port_dropdown.set(target_port)
            app.write_log(f"Auto-Connecting silently to hardware pad on port {target_port}...", "SUCCESS")
            app.connect_hardware()
        else:
            app.write_log("No active hardware ports discovered on startup. Standing by for auto-reconnect...", "WARN")

    # Schedule the safe hidden setup to trigger 150 milliseconds after layout build
    app.after(150, safe_tray_bindings)
    
    app.mainloop()