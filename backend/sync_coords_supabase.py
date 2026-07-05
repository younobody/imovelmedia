"""
Sincroniza lat/lng/dist_parque_m do CSV final (imoveis_geocodificado_2026-06.csv)
com a tabela `properties` no Supabase.

O schema do Supabase usa nomes diferentes do SQLite:
  SQLite:   lat, lng, dist_parque_m, url
  Supabase: latitude, longitude, distance_to_landmark_m, source_url

Casa por source_url (mesma URL do anuncio = mesma coordenada fisica,
vale pra todos os snapshots historicos daquele imovel).

Uso (do diretorio backend, com o venv):
  .\.venv\Scripts\python.exe sync_coords_supabase.py
"""
import csv

from psycopg2.extras import execute_values

from db import get_cursor

CSV_PATH = r"E:\Claude Cowork\Claude code Imoveis\imoveis_geocodificado_2026-06.csv"
BATCH_SIZE = 500


def main():
    with open(CSV_PATH, encoding="utf-8-sig", newline="") as f:
        rows = [
            (r["url"], float(r["lat"]), float(r["lng"]), int(float(r["dist_parque_m"])))
            for r in csv.DictReader(f, delimiter=";")
            if r["lat"] and r["url"]
        ]

    print(f"Linhas com coordenada para sincronizar: {len(rows)}")

    total_updated = 0
    with get_cursor() as cur:
        for i in range(0, len(rows), BATCH_SIZE):
            batch = rows[i : i + BATCH_SIZE]
            execute_values(
                cur,
                """
                UPDATE properties AS p
                SET latitude = v.lat, longitude = v.lng, distance_to_landmark_m = v.dist
                FROM (VALUES %s) AS v(url, lat, lng, dist)
                WHERE p.source_url = v.url
                """,
                batch,
                template="(%s, %s, %s, %s)",
            )
            total_updated += cur.rowcount
            print(f"  lote {i // BATCH_SIZE + 1}: {cur.rowcount} linhas afetadas (acumulado: {total_updated})")

    with get_cursor() as cur:
        cur.execute("SELECT COUNT(*) AS n FROM properties WHERE latitude IS NOT NULL")
        n_com_lat = cur.fetchone()["n"]
        cur.execute("SELECT COUNT(*) AS n FROM properties")
        n_total = cur.fetchone()["n"]

    print(f"\nSupabase properties: {n_com_lat}/{n_total} com latitude preenchida")


if __name__ == "__main__":
    main()
