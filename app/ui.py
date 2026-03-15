import customtkinter as ctk
import threading
from concurrent.futures import ThreadPoolExecutor
from .downloader import download_audio, get_video_info
from .database import add_entry, get_all_history

# Configurações de estilo macOS
ctk.set_appearance_mode("dark")
ctk.set_default_color_theme("blue")

class MusicItemFrame(ctk.CTkFrame):
    def __init__(self, master, title, vid_id, remove_callback, **kwargs):
        super().__init__(master, fg_color="#2D2D2D", corner_radius=12, **kwargs)
        self.grid_columnconfigure(0, weight=1)
        
        # Título
        self.title_label = ctk.CTkLabel(self, text=title[:55] + "...", 
                                      font=("Helvetica Neue", 13, "bold"), anchor="w")
        self.title_label.grid(row=0, column=0, padx=(15, 10), pady=(12, 2), sticky="ew")
        
        # Info Status
        self.info_label = ctk.CTkLabel(self, text="Aguardando...", font=("Helvetica Neue", 11), text_color="#A0A0A0")
        self.info_label.grid(row=0, column=1, padx=5, pady=(12, 2), sticky="e")

        # Botão Remover (X)
        self.remove_btn = ctk.CTkButton(self, text="✕", width=28, height=28, fg_color="transparent", 
                                       hover_color="#FF3B30", text_color="#707070",
                                       command=lambda: remove_callback(vid_id))
        self.remove_btn.grid(row=0, column=2, rowspan=2, padx=10, pady=5)
        
        # Barra de progresso
        self.progress_bar = ctk.CTkProgressBar(self, height=6, progress_color="#007AFF", fg_color="#454545")
        self.progress_bar.set(0)
        self.progress_bar.grid(row=1, column=0, columnspan=2, padx=15, pady=(5, 15), sticky="ew")

    def update_progress(self, percent_str, speed, size_str):
        try:
            if "Convertendo" in percent_str or "99" in percent_str:
                self.progress_bar.configure(progress_color="#FF9500")
                self.info_label.configure(text="Processando MP3...", text_color="#FF9500")
                self.progress_bar.set(0.99)
            else:
                p = float(percent_str.replace('%', '')) / 100
                self.progress_bar.set(p)
                self.info_label.configure(text=f"{size_str} • {percent_str}", text_color="#A0A0A0")
        except: pass

    def set_finished(self):
        self.progress_bar.set(1.0)
        self.progress_bar.configure(progress_color="#28C840")
        self.info_label.configure(text="Concluído ✅", text_color="#28C840")
        self.remove_btn.configure(state="disabled")

    def set_error(self):
        self.progress_bar.set(1.0)
        self.progress_bar.configure(progress_color="#FF3B30")
        self.info_label.configure(text="Falhou ❌", text_color="#FF3B30")

class MainUI(ctk.CTk):
    def __init__(self):
        super().__init__()
        self.title("NGMP3 Pro")
        self.geometry("900x720")
        self.configure(fg_color="#1E1E1E")
        
        self.queue_data = []
        self.queue_frames = {}
        self.is_running = False

        # --- Header ---
        self.header = ctk.CTkFrame(self, fg_color="transparent")
        self.header.pack(fill="x", padx=30, pady=(25, 10))
        
        ctk.CTkLabel(self.header, text="NGMP3", font=("Helvetica Neue", 28, "bold")).pack(side="left")
        
        # Stats Badges
        self.stats_frame = ctk.CTkFrame(self.header, fg_color="transparent")
        self.stats_frame.pack(side="right")
        self.count_waiting = self.create_stat_badge("Fila", "#007AFF")
        self.count_done = self.create_stat_badge("Ok", "#28C840")
        self.count_error = self.create_stat_badge("Erro", "#FF3B30")

        # --- Input ---
        self.input_container = ctk.CTkFrame(self, fg_color="#2D2D2D", corner_radius=12, height=55)
        self.input_container.pack(fill="x", padx=30, pady=15)
        self.input_container.pack_propagate(False)
        
        self.url_entry = ctk.CTkEntry(self.input_container, placeholder_text="URL do vídeo ou playlist...", 
                                     border_width=0, fg_color="transparent", font=("Helvetica Neue", 14))
        self.url_entry.pack(side="left", fill="x", expand=True, padx=15)
        
        self.add_btn = ctk.CTkButton(self.input_container, text="Analisar", width=90, height=30, 
                                    fg_color="#333333", hover_color="#444444", command=self.add_to_queue)
        self.add_btn.pack(side="right", padx=12)

        # --- Tabs ---
        self.tabview = ctk.CTkTabview(self, fg_color="transparent", segmented_button_selected_color="#007AFF")
        self.tabview.pack(fill="both", expand=True, padx=30)
        self.tabview.add("Downloads")
        self.tabview.add("Histórico")

        # Fila Scroll
        self.scroll_queue = ctk.CTkScrollableFrame(self.tabview.tab("Downloads"), fg_color="transparent")
        self.scroll_queue.pack(fill="both", expand=True)

        # Histórico Scroll
        self.scroll_history = ctk.CTkScrollableFrame(self.tabview.tab("Histórico"), fg_color="transparent")
        self.scroll_history.pack(fill="both", expand=True)

        # --- Bottom Bar ---
        self.bottom_bar = ctk.CTkFrame(self, fg_color="transparent")
        self.bottom_bar.pack(fill="x", padx=30, pady=25)

        self.status_label = ctk.CTkLabel(self.bottom_bar, text="Aguardando link...", font=("Helvetica Neue", 12), text_color="#707070")
        self.status_label.pack(side="left")

        self.dl_btn = ctk.CTkButton(self.bottom_bar, text="Iniciar Downloads", height=42, width=160,
                                   fg_color="#28C840", hover_color="#20A032", command=self.start_download_manager)
        self.dl_btn.pack(side="right", padx=5)

        self.stop_btn = ctk.CTkButton(self.bottom_bar, text="Parar", height=42, width=80,
                                     fg_color="#333333", hover_color="#FF3B30", command=self.stop_process)
        self.stop_btn.pack(side="right", padx=5)
        
        self.refresh_history()

    def create_stat_badge(self, label, color):
        f = ctk.CTkFrame(self.stats_frame, fg_color="#2D2D2D", corner_radius=8)
        f.pack(side="left", padx=4)
        ctk.CTkLabel(f, text=label, font=("Helvetica Neue", 9, "bold"), text_color=color).pack(padx=8, pady=(2, 0))
        val = ctk.CTkLabel(f, text="0", font=("Helvetica Neue", 13, "bold"))
        val.pack(padx=8, pady=(0, 2))
        return val

    def update_stats(self):
        done = sum(1 for item in self.queue_data if item.get('status') == 'done')
        waiting = sum(1 for item in self.queue_data if item.get('status') == 'waiting')
        error = sum(1 for item in self.queue_data if item.get('status') == 'error')
        self.count_done.configure(text=str(done))
        self.count_waiting.configure(text=str(waiting))
        self.count_error.configure(text=str(error))

    def add_to_queue(self):
        # Captura o texto bruto da entrada
        raw_input = self.url_entry.get().strip()
        if not raw_input: return
        
        self.status_label.configure(text="🔍 Analisando links...", text_color="#FF9500")
        
        def fetch():
            # Lógica para separar por vírgula OU por quebra de linha
            # Primeiro, trocamos vírgulas por espaços, depois quebras de linha por espaços
            clean_input = raw_input.replace(',', ' ').replace('\n', ' ')
            # Criamos uma lista de links únicos, removendo espaços vazios
            urls = [u.strip() for u in clean_input.split() if u.strip().startswith('http')]
            
            if not urls:
                self.after(0, lambda: self.status_label.configure(text="❌ Nenhum link válido encontrado", text_color="#FF3B30"))
                return

            total_added = 0
            for url in urls:
                try:
                    entries = get_video_info(url)
                    for entry in entries:
                        vid_id = entry.get('id', 'temp')
                        title = entry.get('title', 'Vídeo')
                        
                        # Evita duplicados na fila visual
                        if vid_id not in self.queue_frames:
                            self.queue_data.append({
                                "url": url if len(entries) == 1 else f"https://youtube.com/watch?v={vid_id}", 
                                "id": vid_id, 
                                "status": "waiting"
                            })
                            self.after(0, lambda t=title, v=vid_id: self.create_item_widget(t, v))
                            total_added += 1
                except Exception as e:
                    print(f"Erro ao processar {url}: {e}")

            self.after(0, self.update_stats)
            self.after(0, lambda n=total_added: self.status_label.configure(
                text=f"✅ {n} novos itens na fila", text_color="#28C840"))
            self.after(0, lambda: self.url_entry.delete(0, 'end'))

        threading.Thread(target=fetch, daemon=True).start()

    def create_item_widget(self, title, vid_id):
        frame = MusicItemFrame(self.scroll_queue, title=title, vid_id=vid_id, remove_callback=self.remove_from_queue)
        frame.pack(fill="x", pady=5)
        self.queue_frames[vid_id] = frame

    def remove_from_queue(self, vid_id):
        if vid_id in self.queue_frames:
            self.queue_frames[vid_id].destroy()
            del self.queue_frames[vid_id]
            self.queue_data = [i for i in self.queue_data if i['id'] != vid_id]
            self.update_stats()

    def stop_process(self):
        self.is_running = False
        self.status_label.configure(text="🛑 Parando processamento...")

    def start_download_manager(self):
        if not self.is_running:
            self.is_running = True
            self.dl_btn.configure(state="disabled")
            threading.Thread(target=self.run_pool, daemon=True).start()

    def run_pool(self):
        # Baixa 3 simultâneos para máxima velocidade sem travar
        with ThreadPoolExecutor(max_workers=3) as executor:
            futures = []
            for item in self.queue_data:
                if not self.is_running: break
                if item['status'] == 'done': continue
                
                futures.append(executor.submit(self.task_download, item))
            
            for f in futures: f.result()
        
        self.after(0, self.finish_ui)

    def task_download(self, item):
        vid = item['id']
        frame = self.queue_frames.get(vid)
        try:
            title = download_audio(item['url'], progress_callback=frame.update_progress)
            item['status'] = 'done'
            self.after(0, frame.set_finished)
            add_entry(title, item['url'], "Sucesso")
        except:
            item['status'] = 'error'
            self.after(0, frame.set_error)
        self.after(0, self.update_stats)

    def finish_ui(self):
        self.is_running = False
        self.dl_btn.configure(state="normal")
        self.status_label.configure(text="✅ Processo finalizado", text_color="#28C840")
        self.refresh_history()

    def refresh_history(self):
        for widget in self.scroll_history.winfo_children(): widget.destroy()
        for item in get_all_history():
            h = ctk.CTkFrame(self.scroll_history, fg_color="#262626", corner_radius=8)
            h.pack(fill="x", pady=3)
            ctk.CTkLabel(h, text=f"🎵 {item[0][:60]}...", font=("Helvetica Neue", 12)).pack(side="left", padx=15, pady=8)
            ctk.CTkLabel(h, text=item[2], font=("Helvetica Neue", 10), text_color="#666666").pack(side="right", padx=15)

if __name__ == "__main__":
    app = MainUI()
    app.mainloop()