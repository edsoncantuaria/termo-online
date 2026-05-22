"""Servidor estático do Vue (SPA) — porta 8000 em produção split."""
import os
from http.server import SimpleHTTPRequestHandler, ThreadingHTTPServer
from pathlib import Path

DiretorioDist = Path(__file__).resolve().parent / "static" / "dist"


class HandlerSpa(SimpleHTTPRequestHandler):
    def __init__(self, *args, **kwargs):
        super().__init__(*args, directory=str(DiretorioDist), **kwargs)

    def do_GET(self):
        Caminho = self.translate_path(self.path)
        if not Path(Caminho).is_file():
            self.path = "/index.html"
        return super().do_GET()

    def log_message(self, formato, *args):
        if os.environ.get("TERM0_LOG_HTTP", "").lower() in ("1", "true"):
            super().log_message(formato, *args)


def main() -> None:
    Porta = int(os.environ.get("PORT", "8000"))
    if not (DiretorioDist / "index.html").is_file():
        raise SystemExit(f"Build ausente: {DiretorioDist}/index.html — rode make frontend-build")
    Servidor = ThreadingHTTPServer(("0.0.0.0", Porta), HandlerSpa)
    print(f"Termo frontend em http://0.0.0.0:{Porta} ({DiretorioDist})")
    Servidor.serve_forever()


if __name__ == "__main__":
    main()
