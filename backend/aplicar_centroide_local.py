"""
Preenche lat/lng no imoveis.db LOCAL para registros sem coordenada, usando
centroide de bairro (mediana das coordenadas reais existentes) -- mesmo
metodo ja usado em geocode_imoveis.py e ja aplicado no Supabase (1.643/1.988).

So escreve em linhas com lat IS NULL. Nao mexe em quem ja tem coordenada.

Uso:
  python aplicar_centroide_local.py
"""
import math
import sqlite3
import statistics
import sys

sys.path.insert(0, r"E:\Claude Cowork\Claude code Imoveis\backend")
from geocode_imoveis import bairro_key, norm_lat_lng, haversine_m, PARQUE_LAT, PARQUE_LNG

DB_PATH = r"E:\Claude Cowork\Claude code Imoveis\imoveis.db"


def main():
    conn = sqlite3.connect(DB_PATH)
    conn.row_factory = sqlite3.Row
    rows = conn.execute("SELECT id, bairro_norm, lat, lng FROM imoveis").fetchall()
    print(f"Lidas {len(rows)} linhas do SQLite")

    def _prep(r):
        lat, lng = norm_lat_lng(r["lat"], r["lng"])
        return {"id": r["id"], "lat": lat, "lng": lng, "key": bairro_key(r["bairro_norm"])}

    prepped = [_prep(r) for r in rows]

    coords_por_key: dict = {}
    for r in prepped:
        if r["lat"] is not None and r["key"] is not None:
            coords_por_key.setdefault(r["key"], []).append((r["lat"], r["lng"]))

    updates = []
    for r in prepped:
        if r["lat"] is not None or r["key"] is None:
            continue
        pts = coords_por_key.get(r["key"])
        if not pts:
            continue
        c_lat = statistics.median(p[0] for p in pts)
        c_lng = statistics.median(p[1] for p in pts)
        dist_parque_m = round(haversine_m(c_lat, c_lng, PARQUE_LAT, PARQUE_LNG))
        updates.append((c_lat, c_lng, dist_parque_m, r["id"]))

    cur = conn.cursor()
    cur.executemany(
        "UPDATE imoveis SET lat = ?, lng = ?, dist_parque_m = ? WHERE id = ?", updates
    )
    conn.commit()

    total = conn.execute("SELECT COUNT(*) FROM imoveis").fetchone()[0]
    com_coord = conn.execute(
        "SELECT COUNT(*) FROM imoveis WHERE lat IS NOT NULL AND lng IS NOT NULL"
    ).fetchone()[0]
    sem_coord = total - com_coord
    conn.close()

    print("\n=== RESUMO ===")
    print(f"Registros atualizados nesta rodada: {len(updates)}")
    print(f"Total geocodado no banco: {com_coord} / {total}")
    print(f"Ainda sem coordenada (sem dado de bairro pra centroide): {sem_coord}")


if __name__ == "__main__":
    main()
