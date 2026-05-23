"""Servidor estático do Vue (SPA) — porta 8000 em produção split."""
import os
from http.server import SimpleHTTPRequestHandler, ThreadingHTTPServer
from pathlib import Path

DiretorioDist = Path(__file__).resolve().parent / "static" / "dist"

CABECALHO_SEM_CACHE = "no-cache, no-store, must-revalidate"
CABECALHO_ASSET = "public, max-age=31536000, immutable"


class HandlerSpa(SimpleHTTPRequestHandler):
    def __init__(self, *args, **kwargs):
        super().__init__(*args, directory=str(DiretorioDist), **kwargs)

    def do_GET(self):
        Caminho = self.translate_path(self.path)
        if not Path(Caminho).is_file():
            self.path = "/index.html"
        return super().do_GET()

    def end_headers(self):
        Caminho = self.path.split("?", 1)[0]
        Nome = Path(Caminho).name.lower()
        if "/assets/" in Caminho and Nome.endswith((".js", ".css", ".woff2")):
            self.send_header("Cache-Control", CABECALHO_ASSET)
        elif (
            Caminho in ("/", "/index.html")
            or Nome
            in (
                "index.html",
                "sw.js",
                "registersw.js",
                "manifest.webmanifest",
            )
            or (Nome.startswith("workbox-") and Nome.endswith(".js"))
        ):
            self.send_header("Cache-Control", CABECALHO_SEM_CACHE)
            self.send_header("Pragma", "no-cache")
        else:
            self.send_header("Cache-Control", CABECALHO_SEM_CACHE)
        super().end_headers()

    def log_message(self, formato, *args):
        if os.environ.get("TERM0_LOG_HTTP", "").lower() in ("1", "true"):
            super().log_message(formato, *args)


def main() -> None:
    Porta = int(os.environ.get("PORT", "8000"))
    if not (DiretorioDist / "index.html").is_file():
        raise SystemExit(
            f"Build ausente: {DiretorioDist}/index.html — rode make frontend-build"
        )
    Servidor = ThreadingHTTPServer(("0.0.0.0", Porta), HandlerSpa)
    print(f"Termo frontend em http://0.0.0.0:{Porta} ({DiretorioDist})")
    Servidor.serve_forever()


if __name__ == "__main__":
    main()
