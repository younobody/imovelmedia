#!/usr/bin/env python3
"""
Pipeline completo MediaImovel: Scraping  -> Geocoding  -> Sincronização  -> Limpeza
Orquestra os passos de coleta e prepara os dados para a API.

Uso:
  python pipeline_coleta.py                 # Modo automático (full pipeline)
  python pipeline_coleta.py --step geocode # Só geocoding
  python pipeline_coleta.py --step sync    # Só sincronização
  python pipeline_coleta.py --report       # Relatório final sem rodar nada

Estrutura:
  1. [SCRAPING] — rodado externamente (PowerShell), dados em imoveis.db
  2. [GEOCODING] — extrai_coords_detalhe.py  -> geocode_imoveis.py
  3. [SINCRONIZAÇÃO] — sync_coords_supabase.py + sync_bairro_supabase.py
  4. [LIMPEZA] — aplica filtros de outliers no banco (automático no main.py)
  5. [RELATÓRIO] — valida estado final

Pré-requisitos:
  - Python 3.12+
  - venv ativado (backend/.venv)
  - .env com DATABASE_URL (Supabase)
  - imoveis.db com dados da última coleta via PowerShell
"""

import argparse
import sys
import subprocess
from datetime import datetime
from pathlib import Path
from typing import Optional

from db import query, get_cursor


# ============================================================================
# CONFIGURAÇÃO
# ============================================================================

PROJECT_ROOT = Path(__file__).parent.parent
BACKEND_DIR = PROJECT_ROOT / "backend"

# Scripts que orquestramos
SCRIPT_COLETA_LOCAIS = BACKEND_DIR / "coleta_imobiliarias_locais.py"
SCRIPT_MESCLAR_CSVS = BACKEND_DIR / "mesclar_csvs_coleta.py"
SCRIPT_EXTRAIR_COORDS = BACKEND_DIR / "extrair_coords_detalhe.py"
SCRIPT_GEOCODE = BACKEND_DIR / "geocode_imoveis.py"
SCRIPT_SYNC_COORDS = BACKEND_DIR / "sync_coords_supabase.py"
SCRIPT_SYNC_BAIRROS = BACKEND_DIR / "sync_bairro_supabase.py"

# Logs
LOG_DIR = PROJECT_ROOT / "logs"
LOG_DIR.mkdir(exist_ok=True)
LOG_FILE = LOG_DIR / f"pipeline_{datetime.now().strftime('%Y%m%d_%H%M%S')}.log"


# ============================================================================
# LOGGING & UTILS
# ============================================================================

def log_msg(msg: str, level: str = "INFO"):
    """Escreve mensagem com timestamp."""
    ts = datetime.now().strftime("%Y-%m-%d %H:%M:%S")
    formatted = f"[{ts}] [{level}] {msg}"
    try:
        print(formatted)
    except UnicodeEncodeError:
        # Windows cp1252 fallback
        print(formatted.encode('ascii', 'ignore').decode('ascii'))
    with open(LOG_FILE, "a", encoding="utf-8") as f:
        f.write(formatted + "\n")


def run_step(description: str, script_path: Path, args: list = None) -> bool:
    """Executa um script Python e captura saída."""
    if not script_path.exists():
        log_msg(f"Script não encontrado: {script_path}", "ERROR")
        return False

    log_msg(f" -> {description}...", "INFO")
    try:
        cmd = [sys.executable, str(script_path)] + (args or [])
        result = subprocess.run(cmd, cwd=BACKEND_DIR, capture_output=True, text=True, timeout=3600)

        if result.returncode == 0:
            log_msg(f"[OK] {description} concluido", "OK")
            if result.stdout.strip():
                for line in result.stdout.strip().split("\n"):
                    log_msg(f"  {line}", "OUTPUT")
            return True
        else:
            log_msg(f"[FAIL] {description} falhou com codigo {result.returncode}", "ERROR")
            if result.stderr.strip():
                for line in result.stderr.strip().split("\n"):
                    log_msg(f"  {line}", "ERROR")
            return False
    except subprocess.TimeoutExpired:
        log_msg(f"[TIMEOUT] {description} timeout (>1h)", "ERROR")
        return False
    except Exception as e:
        log_msg(f" [FAIL] {description} erro: {e}", "ERROR")
        return False


# ============================================================================
# PASSOS DO PIPELINE
# ============================================================================

def step_coleta_locais() -> bool:
    """Coleta imobiliárias locais (7 novas)."""
    return run_step(
        "Coleta de imobiliarias locais",
        SCRIPT_COLETA_LOCAIS,
    )


def step_mesclar_csvs() -> bool:
    """Mescla CSVs de coleta original + locais."""
    return run_step(
        "Mesclagem de CSVs",
        SCRIPT_MESCLAR_CSVS,
    )


def step_extrair_coords() -> bool:
    """Extrai coordenadas das páginas de detalhe."""
    return run_step(
        "Extracao de coordenadas",
        SCRIPT_EXTRAIR_COORDS,
    )


def step_geocode() -> bool:
    """Normaliza bairros e calcula centroides."""
    return run_step(
        "Geocoding + normalização de bairros",
        SCRIPT_GEOCODE,
    )


def step_sync_coords() -> bool:
    """Sincroniza lat/lng/distance ao Supabase."""
    return run_step(
        "Sincronização de coordenadas",
        SCRIPT_SYNC_COORDS,
    )


def step_sync_bairros() -> bool:
    """Sincroniza bairros normalizados ao Supabase."""
    return run_step(
        "Sincronização de bairros",
        SCRIPT_SYNC_BAIRROS,
    )


def step_limpeza() -> bool:
    """
    No MediaImovel, a limpeza é automática na API (via FILTER em main.py).
    Este passo apenas valida que os dados estão limpos.
    """
    log_msg(" -> Validação de outliers...", "INFO")
    try:
        # Conta imóveis com price_per_m2 fora da faixa sã
        outliers = query(
            "SELECT COUNT(*) as n FROM properties WHERE price_per_m2 < 10 OR price_per_m2 > 20000"
        )
        n_outliers = outliers[0]["n"] if outliers else 0

        if n_outliers > 0:
            log_msg(
                f" [WARN] Detectados {n_outliers} imóveis com price/m² suspeito "
                f"(< R$10 ou > R$20.000). Dados brutos preservados; "
                f"filtro FILTER(WHERE...) aplica-se às agregações da API.",
                "WARN"
            )
        else:
            log_msg(" [OK] Nenhum outlier detectado (ou todos já filtrados)", "OK")
        return True
    except Exception as e:
        log_msg(f" [FAIL] Validação falhou: {e}", "ERROR")
        return False


# ============================================================================
# RELATÓRIO FINAL
# ============================================================================

def relatorio_final():
    """Imprime estatísticas finais do banco Supabase."""
    log_msg("", "INFO")
    log_msg("=" * 70, "INFO")
    log_msg("RELATÓRIO FINAL", "INFO")
    log_msg("=" * 70, "INFO")

    try:
        # Total de imóveis
        total = query("SELECT COUNT(*) as n FROM properties")
        n_total = total[0]["n"] if total else 0

        # Com coordenadas
        com_coords = query(
            "SELECT COUNT(*) as n FROM properties WHERE latitude IS NOT NULL AND longitude IS NOT NULL"
        )
        n_coords = com_coords[0]["n"] if com_coords else 0

        # Com bairro normalizado
        com_bairro = query(
            "SELECT COUNT(*) as n FROM properties WHERE neighborhood_normalized IS NOT NULL"
        )
        n_bairro = com_bairro[0]["n"] if com_bairro else 0

        # Bairros distintos
        distinct_bairros = query(
            "SELECT COUNT(DISTINCT neighborhood_normalized) as n FROM properties WHERE neighborhood_normalized IS NOT NULL"
        )
        n_distinct = distinct_bairros[0]["n"] if distinct_bairros else 0

        # Price/m² saudável
        com_m2_saudavel = query(
            "SELECT COUNT(*) as n FROM properties WHERE price_per_m2 BETWEEN 10 AND 20000"
        )
        n_m2 = com_m2_saudavel[0]["n"] if com_m2_saudavel else 0

        # Distância ao Parque
        com_dist = query(
            "SELECT COUNT(*) as n FROM properties WHERE distance_to_landmark_m IS NOT NULL"
        )
        n_dist = com_dist[0]["n"] if com_dist else 0

        # Print formatado
        log_msg(f"Total de imóveis: {n_total}", "STAT")
        log_msg(f"   [OK] Com coordenadas: {n_coords} ({100*n_coords//n_total if n_total else 0}%)", "STAT")
        log_msg(f"   [OK] Com bairro: {n_bairro} ({100*n_bairro//n_total if n_total else 0}%)", "STAT")
        log_msg(f"     -> {n_distinct} bairros distintos", "STAT")
        log_msg(f"   [OK] Com price/m² saudável: {n_m2} ({100*n_m2//n_total if n_total else 0}%)", "STAT")
        log_msg(f"   [OK] Com distância ao Parque: {n_dist} ({100*n_dist//n_total if n_total else 0}%)", "STAT")
        log_msg("", "INFO")
        log_msg(f"Log salvo em: {LOG_FILE}", "INFO")

    except Exception as e:
        log_msg(f" [FAIL] Relatório falhou: {e}", "ERROR")


# ============================================================================
# ORQUESTRAÇÃO
# ============================================================================

def pipeline_completo():
    """Executa o pipeline inteiro."""
    log_msg("", "INFO")
    log_msg("=" * 70, "INFO")
    log_msg("INICIANDO PIPELINE COMPLETO", "INFO")
    log_msg("=" * 70, "INFO")

    steps = [
        ("COLETA LOCAIS", step_coleta_locais),
        ("MESCLAGEM CSVS", step_mesclar_csvs),
        ("EXTRAÇÃO", step_extrair_coords),
        ("GEOCODING", step_geocode),
        ("SINCRONIZAÇÃO COORDS", step_sync_coords),
        ("SINCRONIZAÇÃO BAIRROS", step_sync_bairros),
        ("LIMPEZA/VALIDAÇÃO", step_limpeza),
    ]

    resultados = []
    for nome, func in steps:
        log_msg(f"\n[{nome}]", "INFO")
        sucesso = func()
        resultados.append((nome, sucesso))
        if not sucesso:
            log_msg(f" [WARN] Pipeline interrompido em {nome}", "WARN")
            break

    # Relatório final
    log_msg("", "INFO")
    relatorio_final()

    # Resumo
    log_msg("", "INFO")
    log_msg("RESUMO", "INFO")
    for nome, sucesso in resultados:
        status = " [OK]" if sucesso else " [FAIL]"
        log_msg(f"  {status} {nome}", "STAT")

    todos_ok = all(s for _, s in resultados)
    if todos_ok:
        log_msg("\n [OK] Pipeline completado com sucesso!", "OK")
        return 0
    else:
        log_msg("\n [FAIL] Pipeline falhou em algumas etapas", "ERROR")
        return 1


def pipeline_step(step_name: str):
    """Executa um passo específico."""
    steps = {
        "extrair": ("Extração de coordenadas", step_extrair_coords),
        "geocode": ("Geocoding", step_geocode),
        "sync_coords": ("Sincronização de coordenadas", step_sync_coords),
        "sync_bairros": ("Sincronização de bairros", step_sync_bairros),
        "limpeza": ("Limpeza", step_limpeza),
    }

    if step_name not in steps:
        print(f"Passo desconhecido: {step_name}")
        print(f"Opções: {', '.join(steps.keys())}")
        return 1

    log_msg("", "INFO")
    log_msg("=" * 70, "INFO")
    log_msg(f"EXECUTANDO: {steps[step_name][0]}", "INFO")
    log_msg("=" * 70, "INFO")

    sucesso = steps[step_name][1]()
    relatorio_final()

    return 0 if sucesso else 1


def report_only():
    """Apenas imprime relatório sem executar nada."""
    log_msg("", "INFO")
    log_msg("=" * 70, "INFO")
    log_msg("RELATÓRIO (sem executar)", "INFO")
    log_msg("=" * 70, "INFO")
    relatorio_final()
    return 0


# ============================================================================
# CLI
# ============================================================================

def main():
    parser = argparse.ArgumentParser(
        description="Pipeline de coleta MediaImovel: scraping  -> geocoding  -> sync  -> limpeza"
    )
    parser.add_argument(
        "--step",
        choices=["extrair", "geocode", "sync_coords", "sync_bairros", "limpeza"],
        help="Executa apenas um passo (padrão: pipeline completo)",
    )
    parser.add_argument(
        "--report",
        action="store_true",
        help="Apenas imprime relatório (sem executar)",
    )

    args = parser.parse_args()

    if args.report:
        return report_only()
    elif args.step:
        return pipeline_step(args.step)
    else:
        return pipeline_completo()


if __name__ == "__main__":
    sys.exit(main())
