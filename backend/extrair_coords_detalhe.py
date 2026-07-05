"""
Extração de coordenadas reais das páginas de detalhe dos anúncios.

Fontes com mapa embutido confirmado: NIDV (iframe lat/lng), DoceLar,
Tonietto, Cabredo, Realize (Leaflet setView). O script tenta TODOS os
padrões em TODAS as páginas (se outra fonte tiver mapa, pega também).

Características:
  - Retomável: salva progresso em coords_extraidas_2026-06.csv a cada 25
    páginas; ao reiniciar, pula o que já foi processado (menos os 'erro',
    que são tentados de novo).
  - Educado: ~2s entre requisições, User-Agent de navegador.
  - Robusto: 404 vira status 'removido' (anúncio saiu do ar — dado útil!),
    timeout tenta 1 vez de novo, coordenada fora da região vira flag.

Uso (do diretório backend):
  .\.venv\Scripts\python.exe extrair_coords_detalhe.py
Saída:
  E:\Claude Cowork\Claude code Imoveis\coords_extraidas_2026-06.csv
"""
import csv
import re
import sqlite3
import time
import urllib.error
import urllib.request
from pathlib import Path

DB_PATH = r"E:\Claude Cowork\Claude code Imoveis\imoveis.db"
OUT_CSV = Path(r"E:\Claude Cowork\Claude code Imoveis\coords_extraidas_2026-06.csv")

FONTES = ("NIDV", "DoceLar", "Tonietto", "Cabredo", "Realize")
SLEEP_SECONDS = 2.0
CHECKPOINT_EVERY = 25
USER_AGENT = "Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/126.0 Safari/537.36"

# Caixa generosa da região de Dois Vizinhos (inclui zona rural)
LAT_MIN, LAT_MAX = -26.5, -25.0
LNG_MIN, LNG_MAX = -53.8, -52.4

PATTERNS = [
    # NIDV: iframe do Google Maps com lat=...&lng=...
    re.compile(r"lat=(-?\d+\.\d+)&(?:amp;)?lng=(-?\d+\.\d+)"),
    # DoceLar/Tonietto/Cabredo/Realize: Leaflet setView([lat, lng]
    re.compile(r"setView\(\[\s*(-?\d+\.\d+)\s*,\s*(-?\d+\.\d+)"),
    # L.marker([lat, lng]) — variante Leaflet
    re.compile(r"L\.marker\(\[\s*(-?\d+\.\d+)\s*,\s*(-?\d+\.\d+)"),
    # Google Maps embed: !3d<lat>!4d<lng>
    re.compile(r"!3d(-?\d+\.\d+)!4d(-?\d+\.\d+)"),
    # data-lat / data-lng em atributos
    re.compile(r'data-lat=["\'](-?\d+\.\d+)["\'][^>]*data-ln?g=["\'](-?\d+\.\d+)["\']'),
]


def fetch(url: str, timeout: int = 20) -> tuple:
    """Retorna (html, http_status). html=None em erro."""
    req = urllib.request.Request(url, headers={"User-Agent": USER_AGENT})
    try:
        with urllib.request.urlopen(req, timeout=timeout) as resp:
            raw = resp.read()
            try:
                return raw.decode("utf-8", errors="replace"), resp.status
            except Exception:
                return raw.decode("latin-1", errors="replace"), resp.status
    except urllib.error.HTTPError as e:
        return None, e.code
    except Exception:
        return None, 0  # timeout/DNS/etc


def extract_coords(html: str) -> tuple:
    """Tenta todos os padrões; retorna (lat, lng) ou (None, None)."""
    for pat in PATTERNS:
        m = pat.search(html)
        if m:
            try:
                lat, lng = float(m.group(1)), float(m.group(2))
                if lat != 0 and lng != 0:
                    return lat, lng
            except ValueError:
                continue
    return None, None


def load_done() -> dict:
    """Carrega progresso anterior. Chave: url. 'erro' não conta (retenta)."""
    done = {}
    if OUT_CSV.exists():
        with open(OUT_CSV, encoding="utf-8-sig", newline="") as f:
            for row in csv.DictReader(f, delimiter=";"):
                if row["status"] != "erro":
                    done[row["url"]] = row
    return done


def save_all(rows: list):
    fieldnames = ["id", "fonte", "url", "lat", "lng", "status", "http_status"]
    with open(OUT_CSV, "w", encoding="utf-8-sig", newline="") as f:
        w = csv.DictWriter(f, fieldnames=fieldnames, delimiter=";")
        w.writeheader()
        w.writerows(rows)


def main():
    conn = sqlite3.connect(DB_PATH)
    conn.row_factory = sqlite3.Row
    rows = conn.execute(
        f"""SELECT id, fonte, url FROM imoveis
            WHERE lat IS NULL AND fonte IN ({','.join('?' * len(FONTES))})
              AND url IS NOT NULL AND url != ''
            GROUP BY url""",
        FONTES,
    ).fetchall()
    conn.close()

    done = load_done()
    results = list(done.values())
    todo = [r for r in rows if r["url"] not in done]
    total = len(todo)
    print(f"Total alvo: {len(rows)} | ja processados: {len(done)} | a fazer: {total}")
    if total == 0:
        print("Nada a fazer. CSV ja completo em:", OUT_CSV)
        return

    t0 = time.time()
    ok = removed = no_map = err = out_region = 0

    for i, r in enumerate(todo, 1):
        url = r["url"]
        html, status = fetch(url)
        if html is None and status == 0:
            # timeout/rede: tenta 1 vez de novo
            time.sleep(3)
            html, status = fetch(url, timeout=30)

        if html is None:
            if status in (404, 410):
                st, lat, lng = "removido", None, None
                removed += 1
            else:
                st, lat, lng = "erro", None, None
                err += 1
        else:
            lat, lng = extract_coords(html)
            if lat is None:
                st = "sem_mapa"
                no_map += 1
            elif LAT_MIN <= lat <= LAT_MAX and LNG_MIN <= lng <= LNG_MAX:
                st = "ok"
                ok += 1
            else:
                st = "fora_da_regiao"
                out_region += 1

        results.append(
            {
                "id": r["id"],
                "fonte": r["fonte"],
                "url": url,
                "lat": lat if lat is not None else "",
                "lng": lng if lng is not None else "",
                "status": st,
                "http_status": status,
            }
        )

        if i % CHECKPOINT_EVERY == 0 or i == total:
            save_all(results)
            elapsed = time.time() - t0
            rate = i / elapsed if elapsed else 0
            eta_min = (total - i) / rate / 60 if rate else 0
            print(
                f"[{i}/{total}] ok={ok} removido={removed} sem_mapa={no_map} "
                f"fora_regiao={out_region} erro={err} | ETA ~{eta_min:.0f} min",
                flush=True,
            )

        time.sleep(SLEEP_SECONDS)

    save_all(results)
    print("\n=== CONCLUIDO ===")
    print(f"ok={ok} removido={removed} sem_mapa={no_map} fora_regiao={out_region} erro={err}")
    print(f"CSV: {OUT_CSV}")
    print("Proximo passo: aplicar ao banco (script aplicar_coords.py — rodar depois, com revisao).")


if __name__ == "__main__":
    main()
