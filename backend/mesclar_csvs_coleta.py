#!/usr/bin/env python3
"""
Mescla CSVs de diferentes coletas (PowerShell original + imobiliárias locais).

Cria um CSV único pra passar pro extrair_coords_detalhe.py

Uso: python mesclar_csvs_coleta.py
"""

import csv
from pathlib import Path
from datetime import datetime

def mesclar_csvs():
    """Mescla os CSVs de coleta."""
    print("Mesclando CSVs de coleta...\n")

    # Caminhos
    projeto_root = Path(__file__).parent.parent
    csv_original = projeto_root / "coords_extraidas_2026-06.csv"
    csv_locais = projeto_root / "coords_extraidas_locais_2026-06.csv"
    csv_mesclado = projeto_root / "coords_extraidas_mesclado_2026-06.csv"

    if not csv_original.exists():
        print(f"[FAIL] Não encontrei {csv_original}")
        print("      Rode primeiro: python coleta_imoveis.ps1")
        return False

    if not csv_locais.exists():
        print(f"[FAIL] Não encontrei {csv_locais}")
        print("      Rode primeiro: python coleta_imobiliarias_locais.py")
        return False

    # Lê CSVs
    linhas_original = []
    linhas_locais = []
    urls_vistas = set()

    print(f"Lendo {csv_original}...")
    with open(csv_original, encoding='utf-8-sig') as f:
        reader = csv.DictReader(f, delimiter=';')
        for row in reader:
            linhas_original.append(row)
            urls_vistas.add(row['url'])
        print(f"  [OK] {len(linhas_original)} linhas")

    print(f"Lendo {csv_locais}...")
    with open(csv_locais, encoding='utf-8-sig') as f:
        reader = csv.DictReader(f)
        for row in reader:
            # Evita duplicatas
            if row['url'] not in urls_vistas:
                linhas_locais.append(row)
                urls_vistas.add(row['url'])
        print(f"  [OK] {len(linhas_locais)} linhas (únicas)")

    # Mescla
    todas_linhas = linhas_original + linhas_locais

    print(f"\nMesclando...")
    print(f"  Original: {len(linhas_original)}")
    print(f"  Locais:   {len(linhas_locais)}")
    print(f"  Total:    {len(todas_linhas)}")

    # Escreve mesclado
    with open(csv_mesclado, 'w', newline='', encoding='utf-8-sig') as f:
        # Detecta campos comuns
        campos_original = set(linhas_original[0].keys()) if linhas_original else set()
        campos_locais = set(linhas_locais[0].keys()) if linhas_locais else set()
        todos_campos = sorted(list(campos_original | campos_locais))

        writer = csv.DictWriter(f, fieldnames=todos_campos, delimiter=';')
        writer.writeheader()

        for linha in todas_linhas:
            # Preenche campos faltantes com vazio
            linha_completa = {campo: linha.get(campo, '') for campo in todos_campos}
            writer.writerow(linha_completa)

    print(f"\n[OK] Salvo em {csv_mesclado}")
    print(f"     Pronto para extrair coordenadas!")

    return True

if __name__ == "__main__":
    mesclar_csvs()
