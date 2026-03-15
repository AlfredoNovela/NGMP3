import customtkinter as ctk
import threading
from .downloader import download_audio, get_video_info
from .database import add_entry, get_all_history

# Configurações de estilo macOS
ctk.set_appearance_mode("dark")
ctk.set_default_color_theme("blue")

class MusicItemFrame(ctk.CTkFrame):
    def __init__(self, master, title, **kwargs):
        # Cor de fundo mais próxima do painel do macOS
        super().__init__(master, fg_color="#2D2D2D", corner_radius=12, **kwargs)
        
        self.grid_columnconfigure(0, weight=1)
        
        # Título da música (SF Pro Style)
        self.title_label = ctk.CTkLabel(
            self, text=title[:55] + "...", 
            font=("Helvetica Neue", 13, "bold"), 
            anchor="w", text_color="#FFFFFF"
        )
        self.title_label.grid(row=0, column=0, padx=(15, 10), pady=(12, 2), sticky="ew")
        
        # Badge de Status/Tamanho
        self.info_label = ctk.CTkLabel(
            self, text="Pendente", 
            font=("Helvetica Neue", 11), 
            text_color="#A0A0A0"
        )
        self.info_label.grid(row=0, column=1, padx=15, pady=(12, 2), sticky="e")
        
        # Barra de progresso fina e moderna
        self.progress_bar = ctk.CTkProgressBar(
            self, height=6, progress_color="#007AFF", # Azul clássico da Apple
            fg_color="#454545", border_width=0
        )
        self.progress_bar.set(0)
        self.progress_bar.grid(row=1, column=0, columnspan=2, padx=15, pady=(5, 15), sticky="ew")

    def update_progress(self, percent_str, size_str):
        try:
            if "Convertendo" in percent_str or "99%" in percent_str:
                self.progress_bar.configure(progress_color="#FF9500") # Laranja Apple para processamento
                self.info_label.configure(text="Finalizando MP3...", text_color="#FF9500")
                self.progress_bar.set(0.99)
            else:
                p = float(percent_str.replace('%', '')) / 100
                self.progress_bar.set(p)
                self.info_label.configure(text=f"{size_str} • {percent_str}")
        except:
            pass

    def set_finished(self):
        self.progress_bar.set(1.0)
        self.progress_bar.configure(progress_color="#28C840") # Verde Apple
        self.info_label.configure(text="Salvo com sucesso ✅", text_color="#28C840")

class MainUI(ctk.CTk):
    def __init__(self):
        super().__init__()
        self.title("NGMP3 Pro")
        self.geometry("850x680")
        self.configure(fg_color="#1E1E1E") # Fundo Dark Mode macOS
        
        self.queue_data = []
        self.queue_frames = {}

        # --- Header ---
        self.header = ctk.CTkFrame(self, fg_color="transparent")
        self.header.pack(fill="x", padx=30, pady=(30, 10))
        
        ctk.CTkLabel(self.header, text="NGMP3", font=("Helvetica Neue", 28, "bold"), text_color="#FFFFFF").pack(side="left")
        ctk.CTkLabel(self.header, text="DOWNLOADER", font=("Helvetica Neue", 12, "bold"), 
                    text_color="#007AFF", fg_color="#162D46", corner_radius=6, padx=8).pack(side="left", padx=15)

        # --- Input Bar (Floating Style) ---
        self.input_container = ctk.CTkFrame(self, fg_color="#2D2D2D", corner_radius=12, height=55)
        self.input_container.pack(fill="x", padx=30, pady=20)
        self.input_container.pack_propagate(False)
        
        self.url_entry = ctk.CTkEntry(
            self.input_container, placeholder_text="Cole o link do YouTube aqui...", 
            border_width=0, fg_color="transparent", font=("Helvetica Neue", 14),
            placeholder_text_color="#707070"
        )
        self.url_entry.pack(side="left", fill="x", expand=True, padx=15)
        
        self.add_btn = ctk.CTkButton(
            self.input_container, text="Analisar", width=100, height=32, 
            font=("Helvetica Neue", 12, "bold"), corner_radius=8,
            fg_color="#007AFF", hover_color="#005BBF", command=self.add_to_queue
        )
        self.add_btn.pack(side="right", padx=12)

        # --- Tabs ---
        self.tabview = ctk.CTkTabview(self, fg_color="transparent", segmented_button_fg_color="#2D2D2D",
                                     segmented_button_selected_color="#007AFF",
                                     segmented_button_selected_hover_color="#005BBF")
        self.tabview.pack(fill="both", expand=True, padx=30)
        self.tabview.add("Fila")
        self.tabview.add("Histórico")

        # Fila
        self.scroll_queue = ctk.CTkScrollableFrame(self.tabview.tab("Fila"), fg_color="transparent")
        self.scroll_queue.pack(fill="both", expand=True)

        # Histórico
        self.history_list = ctk.CTkTextbox(self.tabview.tab("Histórico"), font=("Helvetica Neue", 12), 
                                         fg_color="#2D2D2D", border_width=0, corner_radius=12)
        self.history_list.pack(fill="both", expand=True, pady=10)

        # --- Control Bar ---
        self.bottom_bar = ctk.CTkFrame(self, fg_color="transparent")
        self.bottom_bar.pack(fill="x", padx=30, pady=30)

        self.status_label = ctk.CTkLabel(self.bottom_bar, text="Pronto para iniciar", font=("Helvetica Neue", 12), text_color="#A0A0A0")
        self.status_label.pack(side="left")

        self.dl_btn = ctk.CTkButton(
            self.bottom_bar, text="Iniciar Downloads", height=42, width=180,
            font=("Helvetica Neue", 14, "bold"), fg_color="#28C840", hover_color="#20A032",
            corner_radius=10, command=self.start_thread
        )
        self.dl_btn.pack(side="right")
        
        self.refresh_history()

    def add_to_queue(self):
        url = self.url_entry.get().strip()
        if not url: return
        self.status_label.configure(text="🔍 Analisando links...", text_color="#FF9500")
        
        def fetch():
            try:
                entries = get_video_info(url)
                for entry in entries:
                    video_id = entry.get('id', 'temp')
                    title = entry.get('title', 'Vídeo sem título')
                    
                    item_data = {
                        "url": f"https://www.youtube.com/watch?v={video_id}" if 'id' in entry else url,
                        "title": title, "id": video_id
                    }
                    self.queue_data.append(item_data)
                    self.after(0, lambda t=title, vid=video_id: self.create_item_widget(t, vid))
                
                self.after(0, lambda: self.status_label.configure(text=f"✨ {len(entries)} itens prontos", text_color="#28C840"))
                self.url_entry.delete(0, 'end')
            except Exception:
                self.after(0, lambda: self.status_label.configure(text="❌ Erro no link", text_color="#FF3B30"))

        threading.Thread(target=fetch, daemon=True).start()

    def create_item_widget(self, title, video_id):
        frame = MusicItemFrame(self.scroll_queue, title=title)
        frame.pack(fill="x", pady=6)
        self.queue_frames[video_id] = frame

    def refresh_history(self):
        self.history_list.configure(state="normal")
        self.history_list.delete("1.0", "end")
        for item in get_all_history():
            self.history_list.insert("end", f"  •  {item[0]}\n\n")
        self.history_list.configure(state="disabled")

    def start_thread(self):
        threading.Thread(target=self.process_queue, daemon=True).start()

    def process_queue(self):
        self.dl_btn.configure(state="disabled", text="Processando...", fg_color="#555555")
        
        for item in self.queue_data:
            vid = item['id']
            frame = self.queue_frames.get(vid)
            if not frame: continue

            def progress_hook(p, speed, size):
                if frame:
                    self.after(0, lambda: frame.update_progress(p, size))

            try:
                # O código aguarda aqui até o FFmpeg terminar
                title = download_audio(item['url'], progress_callback=progress_hook)
                add_entry(title, item['url'], "Sucesso")
                # Agora sim, o arquivo existe!
                self.after(0, frame.set_finished)
            except:
                if frame: self.after(0, lambda: frame.info_label.configure(text="Erro ao converter ❌", text_color="#FF3B30"))
            
            self.refresh_history()
            
        self.status_label.configure(text="✅ Tudo concluído", text_color="#28C840")
        self.dl_btn.configure(state="normal", text="Iniciar Downloads", fg_color="#28C840")