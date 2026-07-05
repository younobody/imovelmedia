"""
Sincroniza neighborhood_normalized no Supabase com a bairro_key limpa
calculada por geocode_imoveis.py (agrupa grafias diferentes do mesmo
bairro; achado nos dados: 591 -> 308 bairros distintos).

Quando bairro_key é None (endereco de rua puro, sem bairro identificavel
no texto), grava NULL em vez de manter o texto sujo antigo — mais honesto
pras estatisticas por bairro (esses imoveis ficam de fora da agregacao
por bairro, mas continuam contando nos totais gerais).

Casa por source_url, igual sync_coords_supabase.py.

Uso:
  .\.venv\Scripts\python.exe sync_bairro_supabase.py
"""
import csv

from psycopg2.extras import execute_values

from db import get_cursor

CSV_PATH = r"E:\Claude Cowork\Claude code Imoveis\imoveis_geocodificado_2026-06.csv"
BATCH_SIZE = 500


def main():
    with open(CSV_PATH, encoding="utf-8-sig", newline="") as f:
        rows = [
            (r["url"], r["bairro_key"] or None)
            for r in csv.DictReader(f, delimiter=";")
            if r["url"]
        ]

    print(f"Linhas para sincronizar: {len(rows)}")

    total_updated = 0
    with get_cursor() as cur:
        for i in range(0, len(rows), BATCH_SIZE):
            batch = rows[i : i + BATCH_SIZE]
            execute_values(
                cur,
                """
                UPDATE properties AS p
                SET neighborhood_normalized = v.bkey
                FROM (VALUES %s) AS v(url, bkey)
                WHERE p.source_url = v.url
                """,
                batch,
                template="(%s, %s)",
            )
            total_updated += len(batch)
            print(f"  lote {i // BATCH_SIZE + 1}: {len(batch)} linhas enviadas")

    with get_cursor() as cur:
        cur.execute(
            "SELECT COUNT(DISTINCT neighborhood_normalized) AS n FROM properties WHERE neighborhood_normalized IS NOT NULL"
        )
        n_bairros = cur.fetchone()["n"]
        cur.execute("SELECT COUNT(*) AS n FROM properties WHERE neighborhood_normalized IS NULL")
        n_null = cur.fetchone()["n"]

    print(f"\nSupabase properties: {n_bairros} bairros distintos, {n_null} sem bairro identificavel")


if __name__ == "__main__":
    main()
