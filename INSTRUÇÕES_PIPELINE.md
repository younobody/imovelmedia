# Instruções: Pipeline Mensal de Coleta

**Para:** Marcos (proprietário)  
**Objetivo:** Coletar imóveis de Dois Vizinhos e atualizar o banco de dados  
**Frequência:** Mensalmente (1º do mês ou conforme necessário)  
**Tempo total:** ~1 hora (30 min PowerShell + 30 min Python)

---

## O Que Acontece?

Você tem dois passos:

1. **PowerShell** (coleta) → lista todos os imóveis das 5 imobiliárias
2. **Python** (processamento) → extrai coordenadas, normaliza bairros, atualiza banco

No final, o banco Supabase fica atualizado e o site/app do MediaImovel mostra os dados novos.

---

## Passo 1: Coleta PowerShell

**Abra PowerShell:**
```
Win + X → Windows PowerShell (Administrador)
```

**Navegue pra pasta do projeto:**
```powershell
cd "E:\Claude Cowork\Claude code Imoveis"
```

**Rode a coleta:**
```powershell
.\coleta_imoveis.ps1
```

**O que esperar:**
- Script baixa ~950 anúncios de 5 imobiliárias (NIDV, DoceLar, Tonietto, Cabredo, Realize)
- Demora ~30 minutos (respeita rate limiting pra não sobrecarregar os servidores)
- Gera arquivo `imoveis.db` com os dados
- Se cair no meio, pode rodar de novo — retoma do ponto em que parou
- Quando terminar, deve mostrar algo como: `✓ Coleta completa: 1988 imóveis`

---

## Passo 2: Processamento Python

**Mesmo PowerShell, mesma pasta. Agora:**

```powershell
cd backend
```

**Ative o ambiente Python:**
```powershell
.\.venv\Scripts\Activate.ps1
```

**Rode o pipeline:**
```powershell
python pipeline_coleta.py
```

**O que acontece automaticamente:**

| Passo | O que faz | Tempo |
|-------|----------|-------|
| **Extração** | Baixa ~950 páginas de detalhe, tira coordenadas do mapa (lat/lng) | 20 min |
| **Geocoding** | Normaliza 590 variações de bairro pra 308 nomes limpos; calcula centroide de cada bairro | 2 min |
| **Sync Coords** | Manda lat/lng pra base Supabase | 1 min |
| **Sync Bairros** | Manda nomes de bairro limpo pra base Supabase | 1 min |
| **Limpeza** | Valida dados, identifica 8 imóveis com erro (preço/área inconsistentes) | 1 min |

**Quando terminar, você vê:**
```
Total de imóveis: 1988
  [OK] Com coordenadas: 1643 (82%)
  [OK] Com bairro: 1748 (87%)
    -> 308 bairros distintos
  [OK] Com price/m² saudável: 787 (39%)
  [OK] Com distância ao Parque: 1643 (82%)

Log salvo em: E:\Claude Cowork\Claude code Imoveis\logs\pipeline_20260705_102210.log

✓ Pipeline completado com sucesso!
```

---

## Checklist Pós-Coleta

Depois que o pipeline termina:

- [ ] Pipeline mostrou "completado com sucesso"?
- [ ] Total de imóveis é próximo de 1.988 (pode variar ±50)?
- [ ] Abra o site/app no navegador: http://localhost:5173
- [ ] Vá em "Explorar bairros" e escolha "Premium"
- [ ] Vê os bairros listados? (deve ter ~300 opções)
- [ ] Clica em um bairro → mostra preço/m²?
- [ ] Vá em "Avaliar imóvel", preenche dados, clica "Avaliar"?
- [ ] Mostra preço estimado + banda de confiança?

Se tudo funcionou, os dados novos estão live no banco. 🎉

---

## Se Algo Der Errado

### PowerShell falhou (Passo 1)

**Erro: "Script desabilitado"**
```powershell
Set-ExecutionPolicy -ExecutionPolicy RemoteSigned -Scope CurrentUser
```
Depois rode de novo: `.\coleta_imoveis.ps1`

**Erro: "imoveis.db não encontrado" ou "Arquivo em uso"**
- Feche qualquer Excel com `imoveis.db` aberto
- Rode de novo: `.\coleta_imoveis.ps1`

---

### Python falhou (Passo 2)

**Erro: "Script não encontrado" ou "Permissão negada"**
- Verifique que está em `E:\Claude Cowork\Claude code Imoveis\backend`
- Rode: `ls -Name` (PowerShell)
- Deve listar `pipeline_coleta.py`

**Erro: "Database connection failed"**
- Verifique arquivo `.env` existe em `backend/`
- Deve ter uma linha: `DATABASE_URL=postgres://...`
- Se não existir, peça a Claude Code pra criar

**Erro: "coords_extraidas_*.csv não encontrado"**
- Significa o passo de extração falhou silenciosamente
- Olhe o arquivo de log em `logs/` pra ver o erro
- Rode só a extração de novo:
  ```powershell
  python pipeline_coleta.py --step extrair
  ```

---

## Relatório Sem Rodar Nada

Quer só ver os números atuais sem coletar?

```powershell
cd backend
python pipeline_coleta.py --report
```

Mostra quantos imóveis têm coordenada, bairro, etc. — **SEM fazer coleta**.

---

## Rodando Um Passo Específico

Se algo falhou no meio, pode rodar só aquela etapa:

```powershell
# Só geocoding (após coleta, antes de sync)
python pipeline_coleta.py --step geocode

# Só sincronização (após geocoding)
python pipeline_coleta.py --step sync_coords
python pipeline_coleta.py --step sync_bairros

# Só validação
python pipeline_coleta.py --step limpeza
```

---

## Logs & Histórico

Cada rodada cria um log em:
```
E:\Claude Cowork\Claude code Imoveis\logs\pipeline_YYYYMMDD_HHMMSS.log
```

Exemplo:
```
logs/
├── pipeline_20260705_102210.log  ← última rodada
├── pipeline_20260605_105500.log  ← rodada de junho
└── pipeline_20260505_110000.log  ← rodada de maio
```

Guarda esses logs pra auditoria (se algo estranho acontecer, tenho histórico).

---

## Proximos Passos (Futuro)

- **Automação:** agendar pra rodar todo dia 1º do mês automaticamente
- **Alertas:** se falhar, envio email ou mensagem Slack
- **Múltiplos municípios:** expandir pra outras cidades além de Dois Vizinhos

---

## Dúvidas?

Se algo der errado que não está aqui:
- Mande print do erro
- Mande o arquivo `.log` (pasta `logs/`)
- Descreva o passo exato (Power Shell completou? Trava em "Extração"? etc.)

---

**Última atualização:** 2026-07-05  
**Versão:** 1.0 — Para rodar manualmente  
**Próxima versão:** 2.0 — Automação agendada
