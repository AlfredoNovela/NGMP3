# NGMP3 - YouTube to MP3 Downloader 🎵

O **NGMP3** é um aplicativo desktop moderno construído em Python para baixar áudios do YouTube em formato MP3, garantindo a melhor qualidade e embutindo automaticamente a capa (thumbnail) e os metadados no arquivo.

## ✨ Funcionalidades
- **Download em Lote:** Adicione múltiplos links em uma fila e baixe todos de uma vez.
- **Capas Automáticas:** Embutimento de miniatura e informações da música (Título/Artista).
- **Histórico Local:** Banco de dados SQLite integrado para manter registro de músicas baixadas.
- **Interface Moderna:** Desenvolvido com CustomTkinter para um visual nativo e escuro.
- **Modular:** Estrutura organizada para fácil manutenção e escalabilidade.

## 🛠️ Tecnologias Utilizadas
- [Python 3.14+](https://www.python.org/)
- [yt-dlp](https://github.com/yt-dlp/yt-dlp) (Motor de download)
- [CustomTkinter](https://github.com/TomSchimansky/CustomTkinter) (Interface Gráfica)
- [SQLite3](https://www.sqlite.org/index.html) (Banco de dados)
- [FFmpeg](https://ffmpeg.org/) (Processamento de áudio e imagem)

## 🚀 Como Executar

### Pré-requisitos
É necessário ter o **FFmpeg** instalado no sistema:
- **macOS (Homebrew):** `brew install ffmpeg`
- **Windows:** Baixe o binário no site oficial e adicione ao PATH.

### Instalação
1. Clone o repositório:
   ```bash
   git clone [https://github.com/seu-usuario/NGMP3.git](https://github.com/seu-usuario/NGMP3.git)
   cd NGMP3