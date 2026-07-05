"""
Aplica as coordenadas extraidas (coords_extraidas_2026-06.csv, status='ok')
ao imoveis.db. Casa por URL (uma URL pode ter varias linhas historicas —
mesma coordenada fisica vale para todas as data_coleta).

Recalcula dist_parque_m com a coordenada correta do Parque de Exposicoes
(-25.7322852, -53.0776012).

Uso: python aplicar_coords.py
"""
import csv
import math
import sqlite3

DB_PATH = r"E:\Claude Cowork\Claude code Imoveis\imoveis.db"
CSV_PATH = r"E:\Claude Cowork\Claude code Imoveis\coords_extraidas_2026-06.csv"

PARQUE_LAT = -25.7322852
PARQUE_LNG = -53.0776012


def haversine_m(lat1, lng1, lat2, lng2):
    R = 6371000.0
    p1, p2 = math.radians(lat1), math.radians(lat2)
    dphi = math.radians(lat2 - lat1)
    dlmb = math.radians(lng2 - lng1)
    a = math.sin(dphi / 2) ** 2 + math.cos(p1) * math.cos(p2) * math.sin(dlmb / 2) ** 2
    return 2 * R * math.asin(math.sqrt(a))


def main():
    conn = sqlite3.connect(DB_PATH)

    with open(CSV_PATH, encoding="utf-8-sig", newline="") as f:
        rows = [r for r in csv.DictReader(f, delimiter=";") if r["status"] == "ok"]

    print(f"Coordenadas 'ok' no CSV: {len(rows)}")

    n_updated_rows = 0
    n_urls_sem_match = 0

    for r in rows:
        lat, lng = float(r["lat"]), float(r["lng"])
        dist = round(haversine_m(lat, lng, PARQUE_LAT, PARQUE_LNG))
        cur = conn.execute(
            "UPDATE imoveis SET lat = ?, lng = ?, dist_parque_m = ? WHERE url = ?",
            (lat, lng, dist, r["url"]),
        )
        if cur.rowcount == 0:
            n_urls_sem_match += 1
        n_updated_rows += cur.rowcount

    conn.commit()

    total = conn.execute("SELECT COUNT(*) FROM imoveis").fetchone()[0]
    com_lat = conn.execute("SELECT COUNT(*) FROM imoveis WHERE lat IS NOT NULL").fetchone()[0]
    conn.close()

    print(f"Linhas do imoveis.db atualizadas: {n_updated_rows}")
    print(f"URLs do CSV sem correspondencia no banco: {n_urls_sem_match}")
    print(f"Total imoveis.db: {total} | com lat agora: {com_lat} ({100*com_lat/total:.1f}%)")


if __name__ == "__main__":
    main()
