import yt_dlp
import os

def get_ffmpeg_path():
    # Caminho correto para o seu Mac via Homebrew
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
                return info['entries']
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
                
                # Reporta o download real
                progress_callback(p, s, total)
            
            elif d['status'] == 'finished':
                # IMPORTANTE: Aqui o arquivo .webm terminou, mas o MP3 ainda não existe!
                # Avisamos a UI para mudar para estado de "Processamento"
                progress_callback("99%", "Convertendo...", "Criando MP3")

    ydl_opts = {
        'format': 'bestaudio/best/best',
        'ffmpeg_location': get_ffmpeg_path(),
        'outtmpl': f'{output_folder}/%(title)s.%(ext)s',
        'writethumbnail': True,
        'progress_hooks': [internal_hook],
        'postprocessors': [
            # 1. Converte para MP3 320kbps
            {
                'key': 'FFmpegExtractAudio',
                'preferredcodec': 'mp3',
                'preferredquality': '320',
            },
            # 2. Converte WebP para PNG/JPG e incorpora no MP3
            {
                'key': 'EmbedThumbnail',
            },
            # 3. Adiciona os metadados (Título, Artista)
            {
                'key': 'FFmpegMetadata',
                'add_metadata': True,
            },
        ],
        'prefer_ffmpeg': True,
        'keepvideo': False, # Deletar o arquivo de vídeo original após converter
        'extractor_args': {'youtube': {'skip': ['js_fallback']}},
        'noplaylist': True, 
    }

    # O bloco "with" garante que o Python espere TODOS os postprocessors terminarem
    with yt_dlp.YoutubeDL(ydl_opts) as ydl:
        info = ydl.extract_info(url, download=True)
        # SÓ RETORNA quando o arquivo final .mp3 estiver pronto na pasta
        return info.get('title', 'Sucesso')