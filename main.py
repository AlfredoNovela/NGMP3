from app.ui import MainUI
from app.database import init_db

if __name__ == "__main__":
    init_db()  # Cria o banco de dados se não existir
    app = MainUI()
    app.mainloop()