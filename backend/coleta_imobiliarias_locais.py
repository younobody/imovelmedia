#!/usr/bin/env python3
"""
Coleta imóveis de imobiliárias locais de Dois Vizinhos.

Scraper genérico que funciona pra: Cecatto, Flora, Tombini, Casarili,
Martini, Silva, Romani.

Usa padrão comum: /imovel/venda/tipo/cidade/bairro/nome/id

Uso:
  python coleta_imobiliarias_locais.py

Saída:
  coords_extraidas_2026-06.csv (mesmo formato do scraper original)
"""

import requests
from bs4 import BeautifulSoup
from urllib.parse import urljoin, urlparse
import csv
import re
from datetime import datetime
from pathlib import Path
import time

# Imobiliárias locais (template genérico)
IMOBILIARIAS = {
    "cecatto": {
        "nome": "Cecatto + Dal Pra",
        "urls": ["https://www.ceccattoedalpraimob.com.br/"],
        "padroes_imovel": [r"/imovel/venda/", r"/imovel/aluguel/", r"/imovel/locacao/"]
    },
    "flora": {
        "nome": "Flora",
        "urls": [
            "https://www.floraocorretoradeimoveis.com.br/",
            "https://www.floraocorretoradeimoveis.com.br/lancamentos",
        ],
        "padroes_imovel": [r"/imovel/venda/", r"/imovel/aluguel/", r"/imovel/locacao/"]
    },
    "tombini": {
        "nome": "Tombini",
        "urls": [
            "https://www.tombiniimoveis.com.br/",
            "https://www.tombiniimoveis.com.br/lancamentos",
        ],
        "padroes_imovel": [r"/imovel/venda/", r"/imovel/aluguel/", r"/imovel/locacao/"]
    },
    "casarili": {
        "nome": "Casarili",
        "urls": [
            "https://www.casarilimoveisdoisvizinhos.com.br/",
            "https://www.casarilimoveisdoisvizinhos.com.br/lancamentos",
        ],
        "padroes_imovel": [r"/imovel/venda/", r"/imovel/aluguel/", r"/imovel/locacao/"],
        "skip_ssl": True
    },
    "martini": {
        "nome": "Martini",
        "urls": [
            "https://www.imobiliariamartini.com.br/",
            "https://www.imobiliariamartini.com.br/lancamentos",
        ],
        "padroes_imovel": [r"/imovel/venda/", r"/imovel/aluguel/", r"/imovel/locacao/"]
    },
    "silva": {
        "nome": "Silva",
        "urls": [
            "https://www.silvacorretoradeimoveis.com.br/",
            "https://www.silvacorretoradeimoveis.com.br/lancamentos",
            "https://www.silvacorretoradeimoveis.com.br/lancamentos/1",
        ],
        "padroes_imovel": [r"/imovel/venda/", r"/imovel/aluguel/", r"/imovel/locacao/"]
    },
    "romani": {
        "nome": "Romani",
        "urls": [
            "https://www.romanicorretordeimoveis.com.br/",
            "https://www.romanicorretordeimoveis.com.br/lancamentos",
        ],
        "padroes_imovel": [r"/imovel/venda/", r"/imovel/aluguel/", r"/imovel/locacao/"]
    },
}

HEADERS = {
    "User-Agent": "Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36"
}

class ColectorImovelLocal:
    def __init__(self):
        self.imoveispor_url = {}  # URL -> dados do imóvel

    def coletar_imobiliaria(self, imob_key, imob_config):
        """Coleta imóveis de uma imobiliária (múltiplas URLs)."""
        print(f"\n[{imob_key.upper()}] Coletando {imob_config['nome']}...")

        try:
            verify_ssl = not imob_config.get('skip_ssl', False)
            links_imovel = set()
            n_urls_processadas = 0

            # Coleta de cada URL da imobiliária
            for url_base in imob_config.get('urls', [imob_config.get('url_base', '')]):
                try:
                    resp = requests.get(url_base, headers=HEADERS, timeout=10, verify=verify_ssl)

                    if resp.status_code != 200:
                        continue

                    soup = BeautifulSoup(resp.text, 'html.parser')
                    n_urls_processadas += 1

                    # Procura todos os links que parecem ser de imóvel
                    for a in soup.find_all('a', href=True):
                        href = a.get('href', '')
                        # Checa se match com padrão de imóvel
                        for padrao in imob_config.get('padroes_imovel', []):
                            if re.search(padrao, href, re.IGNORECASE):
                                # Converte pra URL absoluta
                                url_absoluta = urljoin(url_base, href)
                                # Apenas imóveis de Dois Vizinhos
                                if "dois-vizinhos" in url_absoluta.lower():
                                    links_imovel.add(url_absoluta)
                                break
                except Exception as e:
                    pass

            print(f"  Processadas {n_urls_processadas} URLs")
            print(f"  Encontrados {len(links_imovel)} imóveis")

            # Extrai dados de cada imóvel (SEM LIMITE de 100)
            n_processados = 0
            for url_imovel in links_imovel:
                try:
                    # Gera ID único a partir da URL
                    url_id = url_imovel.split('/')[-1].split('-')[-1]

                    if url_imovel not in self.imoveispor_url:
                        self.imoveispor_url[url_imovel] = {
                            'fonte': imob_config['nome'],
                            'url': url_imovel,
                            'id': url_id,
                            'extraido_em': datetime.now().isoformat()
                        }
                        n_processados += 1

                        # Mostra progresso
                        if n_processados % 10 == 0:
                            print(f"    {n_processados} processados...")
                except Exception as e:
                    pass

            print(f"  [OK] {n_processados} imóveis únicos capturados")
            return n_processados

        except Exception as e:
            print(f"  [FAIL] Erro: {e}")
            return 0

    def salvar_csv(self, arquivo_saida):
        """Salva URLs coletadas em CSV (formato compatível com etapa seguinte)."""
        print(f"\nSalvando em {arquivo_saida}...")

        with open(arquivo_saida, 'w', newline='', encoding='utf-8-sig') as f:
            writer = csv.DictWriter(f, fieldnames=['url', 'fonte', 'status', 'data_coleta'])
            writer.writeheader()

            for url, dados in self.imoveispor_url.items():
                writer.writerow({
                    'url': url,
                    'fonte': dados['fonte'],
                    'status': 'pendente_extracao',  # Próxima etapa vai extrair coords
                    'data_coleta': datetime.now().date(),
                })

        print(f"[OK] {len(self.imoveispor_url)} imóveis salvos")
        return len(self.imoveispor_url)

def main():
    print("="*70)
    print("COLETA: IMOBILIÁRIAS LOCAIS DE DOIS VIZINHOS")
    print("="*70)

    colector = ColectorImovelLocal()
    total = 0

    # Coleta de cada imobiliária
    for imob_key, imob_config in IMOBILIARIAS.items():
        n = colector.coletar_imobiliaria(imob_key, imob_config)
        total += n
        time.sleep(1)  # Rate limiting

    # Salva CSV
    arquivo_saida = Path(__file__).parent.parent / "coords_extraidas_locais_2026-06.csv"
    n_salvos = colector.salvar_csv(str(arquivo_saida))

    print("\n" + "="*70)
    print(f"RESUMO: {n_salvos} imóveis de {len(IMOBILIARIAS)} imobiliárias")
    print("="*70)
    print(f"\nPróximo passo: executar extração de coordenadas")
    print(f"  python extrair_coords_detalhe.py")

if __name__ == "__main__":
    main()
