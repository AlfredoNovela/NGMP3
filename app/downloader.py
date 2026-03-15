import yt_dlp
import os

def get_ffmpeg_path():
    # Mantendo o caminho do seu Mac
    return '/usr/local/bin/ffmpeg'

def get_video_info(url):
    """Extrai info rápido para a fila sem baixar nada."""
    ydl_opts = {
        'extract_flat': 'in_playlist',
        'quiet': True,
        'skip_download': True,
    }
    with yt_dlp.YoutubeDL(ydl_opts) as ydl:
        try:
            info = ydl.extract_info(url, download=False)
            if 'entries' in info:
                # Filtrar entradas nulas que às vezes aparecem em playlists privadas/deletadas
                return [e for e in info['entries'] if e is not None]
            return [info]
        except Exception as e:
            print(f"Erro ao extrair info: {e}")
            return []

def download_audio(url, progress_callback=None, output_folder="downloads"):
    if not os.path.exists(output_folder):
        os.makedirs(output_folder)

    def internal_hook(d):
        if progress_callback:
            if d['status'] == 'downloading':
                p = d.get('_percent_str', '0%').replace('\x1b[0;32m', '').replace('\x1b[0m', '').strip()
                s = d.get('_speed_str', 'N/A')
                total = d.get('_total_bytes_str', d.get('_total_bytes_estimate_str', 'N/A'))
                progress_callback(p, s, total)
            
            elif d['status'] == 'finished':
                # Indica o início da fase de conversão do FFmpeg
                progress_callback("99%", "Convertendo...", "MP3 + Capa")

    ydl_opts = {
        'format': 'bestaudio/best',
        'ffmpeg_location': get_ffmpeg_path(),
        'outtmpl': f'{output_folder}/%(title)s.%(ext)s',
        'writethumbnail': True,
        'progress_hooks': [internal_hook],
        
        # --- OTIMIZAÇÕES DE VELOCIDADE ---
        'n_threads': 4,                       # Threads para post-processing
        'concurrent_fragment_downloads': 5,    # Baixa múltiplos fragmentos do áudio simultaneamente
        'buffersize': 1024 * 16,               # Aumenta o buffer de rede
        'retries': 10,                         # Mais tentativas em caso de oscilação
        # ---------------------------------

        'postprocessors': [
            {
                'key': 'FFmpegExtractAudio',
                'preferredcodec': 'mp3',
                'preferredquality': '320',
            },
            {
                'key': 'EmbedThumbnail',
            },
            {
                'key': 'FFmpegMetadata',
                'add_metadata': True,
            },
        ],
        'prefer_ffmpeg': True,
        'keepvideo': False,
        'extractor_args': {'youtube': {'skip': ['js_fallback']}},
        'noplaylist': True, 
    }

    with yt_dlp.YoutubeDL(ydl_opts) as ydl:
        # O yt-dlp gerencia o download e a execução do FFmpeg de forma sequencial por arquivo
        info = ydl.extract_info(url, download=True)
        return info.get('title', 'Sucesso')