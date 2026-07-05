#!/usr/bin/env python3
"""
Investiga estrutura HTML de cada imobiliária.
Descobre: onde ficam os imóveis, como extrai preço/área/bairro/link.

Uso: python investigar_sites.py
"""

import requests
from bs4 import BeautifulSoup
from urllib.parse import urljoin
import json
from datetime import datetime

# Lista de imobiliárias para investigar
SITES = {
    "Cecatto + Dal Pra": "https://www.ceccattoedalpraimob.com.br/",
    "Flora": "https://www.floraocorretoradeimoveis.com.br/",
    "Tombini": "https://www.tombiniimoveis.com.br/",
    "Casarili": "https://www.casarilimoveisdoisvizinhos.com.br/",
    "Martini": "https://www.imobiliariamartini.com.br/",
    "Silva": "https://www.silvacorretoradeimoveis.com.br/",
    "Romani": "https://www.romanicorretordeimoveis.com.br/",
}

HEADERS = {
    "User-Agent": "Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36"
}

def investigar_site(nome, url):
    """Acessa site e tira info sobre estrutura."""
    print(f"\n{'='*70}")
    print(f"Investigando: {nome}")
    print(f"URL: {url}")
    print(f"{'='*70}")

    try:
        resp = requests.get(url, headers=HEADERS, timeout=10)
        resp.encoding = 'utf-8'

        if resp.status_code != 200:
            print(f"[FAIL] Status {resp.status_code}")
            return None

        soup = BeautifulSoup(resp.text, 'html.parser')

        # Procura por padrões comuns
        resultado = {
            "nome": nome,
            "url": url,
            "status": "OK",
            "tamanho_html": len(resp.text),
            "titulo": soup.title.string if soup.title else "?",
        }

        # Procura por divs/sections de imóvel (padrões comuns)
        imovel_divs = soup.find_all(
            ["div", "section", "article"],
            class_=lambda x: x and any(
                termo in x.lower()
                for termo in ["imovel", "property", "card", "listing", "anuncio", "imóvel"]
            )
        )

        # Procura por links pra listagem
        links_imovel = [
            a.get('href')
            for a in soup.find_all('a')
            if a.get('href') and any(
                termo in a.get('href', '').lower()
                for termo in ["imovel", "property", "anuncio", "listagem", "detalhes", "properties"]
            )
        ]
        links_imovel = list(set(links_imovel))[:5]  # Top 5 únicos

        # Procura por formas de acesso (busca, filtro)
        formularios = soup.find_all(['form', 'select', 'input'])

        # Info coletada
        resultado["imovel_divs_encontradas"] = len(imovel_divs)
        resultado["links_imovel_encontrados"] = len(links_imovel)
        resultado["formularios_encontrados"] = len(formularios)
        resultado["exemplos_links"] = links_imovel

        # Tenta encontrar endpoint de API (comum em sites modernos)
        scripts = soup.find_all('script')
        apis = set()
        for script in scripts:
            if script.string:
                # Procura por chamadas fetch/ajax
                if 'fetch' in script.string or 'api' in script.string.lower():
                    apis.add("Possível API JavaScript")

        resultado["apis_js"] = list(apis)[:3]

        # Status de facilidade
        if imovel_divs or links_imovel:
            resultado["facilidade"] = " Fácil (estrutura clara)"
        elif formularios:
            resultado["facilidade"] = " Médio (precisa navegação)"
        else:
            resultado["facilidade"] = " Difícil (estrutura não clara)"

        return resultado

    except Exception as e:
        print(f"[FAIL] Erro: {e}")
        return {"nome": nome, "url": url, "status": f"ERRO: {e}"}

def main():
    print("\n" + "="*70)
    print("INVESTIGAÇÃO DE SITES DE IMOBILIÁRIAS")
    print("="*70)

    resultados = []
    for nome, url in SITES.items():
        try:
            resultado = investigar_site(nome, url)
            if resultado:
                resultados.append(resultado)

                # Print resumido
                print(f"\n[OK] {resultado['nome']}")
                print(f"  Título: {resultado.get('titulo', '?')}")
                print(f"  Facilidade: {resultado.get('facilidade', '?')}")
                print(f"  Divs de imóvel encontradas: {resultado.get('imovel_divs_encontradas', 0)}")
                print(f"  Links de imóvel encontrados: {resultado.get('links_imovel_encontrados', 0)}")
                if resultado.get('exemplos_links'):
                    print(f"  Exemplos: {resultado['exemplos_links'][0]}")
        except Exception as e:
            print(f"[FAIL] ERRO em {nome}: {e}")

    # Relatório final
    print("\n" + "="*70)
    print("RESUMO FINAL")
    print("="*70)

    facil = sum(1 for r in resultados if " " in r.get('facilidade', ''))
    medio = sum(1 for r in resultados if " " in r.get('facilidade', ''))
    dificil = sum(1 for r in resultados if "" in r.get('facilidade', ''))

    print(f"\nFáceis (): {facil}")
    print(f"Médios (): {medio}")
    print(f"Difíceis (): {dificil}")

    print("\nResultados detalhados:")
    for r in resultados:
        print(f"\n{r['nome']}: {r.get('facilidade', '?')}")
        if r.get('status') == "OK":
            print(f"  [OK] Divs: {r.get('imovel_divs_encontradas', 0)}")
            print(f"  [OK] Links: {r.get('links_imovel_encontrados', 0)}")
            print(f"  [OK] Forms: {r.get('formularios_encontrados', 0)}")

if __name__ == "__main__":
    main()
