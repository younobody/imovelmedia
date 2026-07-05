"""
Atribuicao final de coordenadas + validacao de bairro para os 1.988 imoveis
(imoveis.db). SEM geocoding externo — Nominatim e Photon foram testados e
nao cobrem Dois Vizinhos (Nominatim: 0 resultados; Photon: falsos positivos
de rua/bairro). Estrategia 100% dado proprio:

  1. Chave de bairro "limpa" (bairro_key): agrupa grafias diferentes do
     mesmo bairro. Regra descoberta nos dados: quando o campo bairro_norm
     tem virgula, o nome do bairro vem DEPOIS da ultima virgula (formato
     "RUA X 123, BAIRRO"). Sem virgula, tira sufixo ", DOIS VIZINHOS - PR"
     e prefixos genericos (LOTEAMENTO/BAIRRO/RESIDENCIAL/CONJUNTO). Se
     sobrar so um endereco de rua puro (sem bairro identificavel), a
     chave fica None (nao da pra saber o bairro).

  2. Centroide de cada bairro_key = MEDIANA das coordenadas REAIS (as 121
     que ja existiam + as 729 aplicadas por aplicar_coords.py) dos imoveis
     daquele bairro. Zero dependencia de API externa.

  3. Atribuicao final por imovel, em ordem de prioridade:
       a) coordenada real propria (extraida da pagina do anuncio)
          -> precision_level = "address_original"
       b) centroide do bairro_key (>=1 imovel real no bairro)
          -> precision_level = "neighborhood_centroid"
       c) nada disponivel -> precision_level = "none"

  4. bairro_confere: so calculavel para quem tem coordenada propria (a).
     Compara a distancia dessa coordenada ao centroide do bairro
     CALCULADO SEM incluir o proprio imovel (evita circularidade).
     NAO se > 5 km.

Uso:
  python geocode_imoveis.py
Saida:
  E:\\Claude Cowork\\Claude code Imoveis\\imoveis_geocodificado_2026-06.csv
"""
import csv
import math
import re
import sqlite3
import statistics

DB_PATH = r"E:\Claude Cowork\Claude code Imoveis\imoveis.db"
OUT_CSV = r"E:\Claude Cowork\Claude code Imoveis\imoveis_geocodificado_2026-06.csv"

PARQUE_LAT = -25.7322852
PARQUE_LNG = -53.0776012
DIVERGENCIA_THRESHOLD_M = 5000  # acima disso, bairro_confere = NAO

SUFFIX_RE = re.compile(r"\s*-\s*DOIS VIZINHOS\s*-\s*PR\s*$", re.IGNORECASE)
LEADING_DASH_RE = re.compile(r"^-\s*")
BARE_STREET_RE = re.compile(r"^(RUA:?|AV\.?|AVENIDA|PR\s*-?\s*\d|LINHA)\b", re.IGNORECASE)
GENERIC_PREFIX_RE = re.compile(
    r"^(LOTEAMENTO|BAIRRO|RESIDENCIAL|CONJUNTO|CONJ\.?)\s+", re.IGNORECASE
)


def bairro_key(bairro_norm: str):
    """Extrai uma chave de bairro que agrupa grafias diferentes do mesmo lugar."""
    if not bairro_norm:
        return None
    s = bairro_norm.strip()
    has_comma = "," in s
    core = s.rsplit(",", 1)[-1].strip() if has_comma else s

    core = SUFFIX_RE.sub("", core).strip()
    core = LEADING_DASH_RE.sub("", core).strip()
    if not core:
        return None

    # Sem virgula E ainda parece um endereco de rua puro -> nao da pra saber o bairro
    if not has_comma and BARE_STREET_RE.match(core):
        return None

    core = GENERIC_PREFIX_RE.sub("", core).strip()
    core = re.sub(r"\s+", " ", core).upper()
    return core or None


def norm_lat_lng(lat, lng):
    """Corrige escala de coordenadas antigas sem ponto decimal (ex.: -257357044 -> -25.7357044).
    So mexe em quem ja tinha lat preenchido ANTES desta sessao — as 729 aplicadas por
    aplicar_coords.py ja vem em escala correta (extraidas direto do HTML)."""
    if lat is None or lng is None or lat == 0 or lng == 0:
        return None, None
    lat, lng = float(lat), float(lng)
    while abs(lat) >= 90:
        lat /= 10
    while abs(lng) >= 180:
        lng /= 10
    return round(lat, 7), round(lng, 7)


def haversine_m(lat1, lng1, lat2, lng2):
    R = 6371000.0
    p1, p2 = math.radians(lat1), math.radians(lat2)
    dphi = math.radians(lat2 - lat1)
    dlmb = math.radians(lng2 - lng1)
    a = math.sin(dphi / 2) ** 2 + math.cos(p1) * math.cos(p2) * math.sin(dlmb / 2) ** 2
    return 2 * R * math.asin(math.sqrt(a))


def main():
    conn = sqlite3.connect(DB_PATH)
    conn.row_factory = sqlite3.Row
    rows = conn.execute(
        """SELECT id, tipo, finalidade, bairro, bairro_norm, preco, area, preco_m2,
                  quartos, fonte, url, data_coleta, titulo, lat, lng
           FROM imoveis"""
    ).fetchall()
    conn.close()
    print(f"Lidas {len(rows)} linhas do SQLite")

    def _prep(r):
        lat, lng = norm_lat_lng(r["lat"], r["lng"])
        return dict(r, lat=lat, lng=lng, key=bairro_key(r["bairro_norm"]))

    rows = [_prep(r) for r in rows]

    # 1) Reune coordenadas reais por bairro_key (para mediana)
    coords_por_key: dict = {}
    for r in rows:
        if r["lat"] is not None and r["key"] is not None:
            coords_por_key.setdefault(r["key"], []).append((r["id"], r["lat"], r["lng"]))

    def centroide(key, excluir_id=None):
        pts = coords_por_key.get(key, [])
        if excluir_id is not None:
            pts = [p for p in pts if p[0] != excluir_id]
        if not pts:
            return None, None
        return statistics.median(p[1] for p in pts), statistics.median(p[2] for p in pts)

    n_bairros_com_dado = len(coords_por_key)
    n_bairros_distintos = len({r["key"] for r in rows if r["key"]})
    print(f"Bairros distintos (chave limpa): {n_bairros_distintos}")
    print(f"Bairros com >=1 coordenada real: {n_bairros_com_dado}")

    # 2) Atribuicao final por imovel
    out_rows = []
    for r in rows:
        if r["lat"] is not None:
            final_lat, final_lng = r["lat"], r["lng"]
            precision = "address_original"
        else:
            c_lat, c_lng = centroide(r["key"]) if r["key"] else (None, None)
            if c_lat is not None:
                final_lat, final_lng = c_lat, c_lng
                precision = "neighborhood_centroid"
            else:
                final_lat = final_lng = None
                precision = "none"

        bairro_confere = "NA"
        dist_bairro_m = None
        if precision == "address_original" and r["key"]:
            c_lat, c_lng = centroide(r["key"], excluir_id=r["id"])
            if c_lat is not None:
                dist_bairro_m = round(haversine_m(final_lat, final_lng, c_lat, c_lng))
                bairro_confere = "SIM" if dist_bairro_m <= DIVERGENCIA_THRESHOLD_M else "NAO"

        dist_parque_m = (
            round(haversine_m(final_lat, final_lng, PARQUE_LAT, PARQUE_LNG))
            if final_lat is not None
            else None
        )

        out_rows.append(
            {
                "id": r["id"],
                "tipo": r["tipo"],
                "finalidade": r["finalidade"],
                "bairro_original": r["bairro"],
                "bairro_norm": r["bairro_norm"],
                "bairro_key": r["key"],
                "preco": r["preco"],
                "area": r["area"],
                "preco_m2": r["preco_m2"],
                "quartos": r["quartos"],
                "fonte": r["fonte"],
                "url": r["url"],
                "data_coleta": r["data_coleta"],
                "titulo": r["titulo"],
                "lat": final_lat,
                "lng": final_lng,
                "precision_level": precision,
                "dist_bairro_centroide_m": dist_bairro_m,
                "bairro_confere": bairro_confere,
                "dist_parque_m": dist_parque_m,
            }
        )

    fieldnames = list(out_rows[0].keys())
    with open(OUT_CSV, "w", newline="", encoding="utf-8-sig") as f:
        w = csv.DictWriter(f, fieldnames=fieldnames, delimiter=";")
        w.writeheader()
        w.writerows(out_rows)

    # Resumo
    n_total = len(out_rows)
    n_com_coord = sum(1 for r in out_rows if r["lat"] is not None)
    n_confere_nao = sum(1 for r in out_rows if r["bairro_confere"] == "NAO")
    by_prec = {}
    for r in out_rows:
        by_prec[r["precision_level"]] = by_prec.get(r["precision_level"], 0) + 1

    print("\n=== RESUMO ===")
    print(f"Total processado: {n_total}")
    print(f"Com coordenada: {n_com_coord} ({100*n_com_coord/n_total:.1f}%)")
    print(f"Por precisao: {by_prec}")
    print(f"bairro_confere = NAO: {n_confere_nao}")
    print(f"CSV salvo em: {OUT_CSV}")


if __name__ == "__main__":
    main()
