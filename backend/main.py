"""
MediaImovel — API (FastAPI)
Fase 1: endpoints /neighborhoods e /valuate sobre o PostgreSQL (Supabase).

Regras freemium (sem login ainda — controlado pelo parametro ?plan=):
  free    -> top 3 bairros, 3 comparaveis por consulta
  premium -> todos os bairros, 10 comparaveis

Auth/JWT/Stripe entram na fase de monetizacao.
"""
from typing import Optional, Literal

from fastapi import FastAPI, Query, HTTPException
from fastapi.middleware.cors import CORSMiddleware
from pydantic import BaseModel

from db import query

app = FastAPI(title="MediaImovel API", version="0.1.0")

# Libera o frontend React (Vite) em dev e o GitHub Pages em produção.
app.add_middleware(
    CORSMiddleware,
    allow_origins=[
        "http://localhost:5173",
        "http://localhost:3000",
        "https://younobody.github.io",
    ],
    allow_methods=["*"],
    allow_headers=["*"],
)

FREE_NEIGHBORHOODS = 3
COMPARABLES = {"free": 3, "premium": 10}
MIN_SAMPLE = 3  # n minimo para considerar uma mediana confiavel

# Faixa sa de R$/m2 — exclui erro de extracao de preco/area (ex.: imovel com
# price_brl=1,00, ou area capturada errada tipo "6 alqueires" virar 100m2).
# Baseado nos percentis reais dos dados (p1=~R$17, p99=~R$18.450): so corta
# lixo grosseiro, nao mexe na faixa legitima de terrenos rurais (baixo R$/m2
# por serem grandes) nem no topo urbano.
PM2_MIN, PM2_MAX = 10, 20000
PM2_SANE = f"price_per_m2 BETWEEN {PM2_MIN} AND {PM2_MAX}"

Plan = Literal["free", "premium"]
Purpose = Literal["venda", "locacao"]


def _purpose_clause(purpose: str) -> tuple[str, tuple]:
    """venda inclui tambem 'venda-e-locacao'."""
    if purpose == "venda":
        return "purpose IN ('venda','venda-e-locacao')", ()
    return "purpose = %s", (purpose,)


# ------------------------------------------------------------------ #
@app.get("/health")
def health():
    rows = query("SELECT COUNT(*) AS n FROM properties")
    return {"status": "ok", "total_properties": rows[0]["n"]}


@app.get("/municipalities")
def municipalities():
    return query(
        """
        SELECT m.id, m.name, m.state, m.region,
               m.landmark_name, m.landmark_lat, m.landmark_lng,
               COUNT(p.id) AS property_count,
               COUNT(DISTINCT p.neighborhood_normalized) AS neighborhood_count
        FROM municipalities m
        LEFT JOIN properties p ON p.municipality_id = m.id
        GROUP BY m.id
        ORDER BY m.name
        """
    )


# ------------------------------------------------------------------ #
@app.get("/neighborhoods")
def neighborhoods(
    municipality_id: int = Query(...),
    property_type: Optional[str] = Query(None),
    purpose: Purpose = Query("venda"),
    plan: Plan = Query("free"),
):
    """Estatisticas de R$/m2 por bairro + comparaveis."""
    pclause, pparams = _purpose_clause(purpose)
    filters = f"municipality_id = %s AND {pclause}"
    params: tuple = (municipality_id, *pparams)
    if property_type:
        filters += " AND property_type = %s"
        params += (property_type,)

    stats = query(
        f"""
        SELECT
            neighborhood_normalized AS neighborhood,
            COUNT(*) AS total,
            COUNT(price_per_m2) FILTER (WHERE {PM2_SANE}) AS n_com_m2,
            ROUND(PERCENTILE_CONT(0.5) WITHIN GROUP (ORDER BY price_per_m2) FILTER (WHERE {PM2_SANE})::numeric, 2) AS median_pm2,
            ROUND(AVG(price_per_m2) FILTER (WHERE {PM2_SANE})::numeric, 2) AS mean_pm2,
            ROUND(MIN(price_per_m2) FILTER (WHERE {PM2_SANE})::numeric, 2) AS min_pm2,
            ROUND(MAX(price_per_m2) FILTER (WHERE {PM2_SANE})::numeric, 2) AS max_pm2,
            ROUND(PERCENTILE_CONT(0.5) WITHIN GROUP (ORDER BY area_m2)::numeric, 2) AS median_area
        FROM properties
        WHERE {filters} AND neighborhood_normalized IS NOT NULL
        GROUP BY neighborhood_normalized
        ORDER BY total DESC
        """,
        params,
    )

    total_neighborhoods = len(stats)
    limited = plan == "free"
    if limited:
        stats = stats[:FREE_NEIGHBORHOODS]

    # Comparaveis: top K por bairro (mais recentes), so para os bairros retornados.
    k = COMPARABLES[plan]
    names = [s["neighborhood"] for s in stats]
    comps_by_nbhd: dict = {n: [] for n in names}
    if names:
        comp_rows = query(
            f"""
            SELECT * FROM (
                SELECT
                    neighborhood_normalized AS neighborhood,
                    external_id, property_type, price_brl, area_m2, price_per_m2,
                    source_url, title, collected_at,
                    ROW_NUMBER() OVER (
                        PARTITION BY neighborhood_normalized
                        ORDER BY collected_at DESC, price_per_m2 DESC NULLS LAST
                    ) AS rn
                FROM properties
                WHERE {filters} AND neighborhood_normalized = ANY(%s)
                  AND (price_per_m2 IS NULL OR {PM2_SANE})
            ) t WHERE rn <= %s
            """,
            params + (names, k),
        )
        for r in comp_rows:
            r.pop("rn", None)
            comps_by_nbhd.setdefault(r["neighborhood"], []).append(r)

    for s in stats:
        s["comparables"] = comps_by_nbhd.get(s["neighborhood"], [])

    return {
        "municipality_id": municipality_id,
        "property_type": property_type,
        "purpose": purpose,
        "plan": plan,
        "neighborhoods_returned": len(stats),
        "neighborhoods_total": total_neighborhoods,
        "limited": limited,
        "comparables_per_neighborhood": k,
        "neighborhoods": stats,
    }


# ------------------------------------------------------------------ #
class ValuationRequest(BaseModel):
    municipality_id: int
    property_type: str
    neighborhood: Optional[str] = None
    area_m2: float
    plan: Plan = "free"


@app.post("/valuate")
def valuate(req: ValuationRequest):
    """Estima preco de um imovel a partir da mediana de R$/m2 de comparaveis."""
    if req.area_m2 <= 0:
        raise HTTPException(400, "area_m2 deve ser maior que zero")

    base_filter = f"municipality_id = %s AND property_type = %s AND {PM2_SANE}"
    base_params: tuple = (req.municipality_id, req.property_type)

    # 1) Tenta no bairro; se amostra pequena, cai para o tipo no municipio inteiro.
    basis = "bairro"
    where = base_filter
    params = base_params
    if req.neighborhood:
        where = base_filter + " AND neighborhood_normalized = %s"
        params = base_params + (req.neighborhood,)

    agg = query(
        f"""
        SELECT
            COUNT(*) AS n,
            ROUND(PERCENTILE_CONT(0.5) WITHIN GROUP (ORDER BY price_per_m2)::numeric, 2) AS median_pm2,
            ROUND(PERCENTILE_CONT(0.25) WITHIN GROUP (ORDER BY price_per_m2)::numeric, 2) AS p25_pm2,
            ROUND(PERCENTILE_CONT(0.75) WITHIN GROUP (ORDER BY price_per_m2)::numeric, 2) AS p75_pm2
        FROM properties WHERE {where}
        """,
        params,
    )[0]

    if (agg["n"] or 0) < MIN_SAMPLE and req.neighborhood:
        basis = "tipo no municipio (bairro tinha amostra pequena)"
        where, params = base_filter, base_params
        agg = query(
            f"""
            SELECT
                COUNT(*) AS n,
                ROUND(PERCENTILE_CONT(0.5) WITHIN GROUP (ORDER BY price_per_m2)::numeric, 2) AS median_pm2,
                ROUND(PERCENTILE_CONT(0.25) WITHIN GROUP (ORDER BY price_per_m2)::numeric, 2) AS p25_pm2,
                ROUND(PERCENTILE_CONT(0.75) WITHIN GROUP (ORDER BY price_per_m2)::numeric, 2) AS p75_pm2
            FROM properties WHERE {where}
            """,
            params,
        )[0]

    n = agg["n"] or 0
    if n == 0 or agg["median_pm2"] is None:
        raise HTTPException(
            404,
            f"Sem comparaveis com R$/m2 para tipo '{req.property_type}' "
            f"no municipio {req.municipality_id}.",
        )

    median = float(agg["median_pm2"])
    p25 = float(agg["p25_pm2"])
    p75 = float(agg["p75_pm2"])
    area = req.area_m2

    # 2) Comparaveis: mesmo tipo, priorizando o bairro, mais proximos em area.
    k = COMPARABLES[req.plan]
    comp_params = base_params + (req.neighborhood or "", area, k)
    comps = query(
        f"""
        SELECT
            neighborhood_normalized AS neighborhood,
            external_id, property_type, price_brl, area_m2, price_per_m2,
            source_url, title, collected_at
        FROM properties
        WHERE {base_filter}
        ORDER BY (neighborhood_normalized = %s) DESC,
                 ABS(COALESCE(area_m2, 0) - %s) ASC
        LIMIT %s
        """,
        comp_params,
    )

    return {
        "input": req.model_dump(),
        "basis": basis,
        "sample_size": n,
        "reliable": n >= MIN_SAMPLE,
        "price_per_m2_median": median,
        "estimated_price": round(median * area, 2),
        "confidence_band": {
            "low": round(p25 * area, 2),
            "high": round(p75 * area, 2),
        },
        "comparables_returned": len(comps),
        "comparables": comps,
    }
