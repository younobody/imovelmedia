# Explicação dos Termos — Linguagem Simples

## 1. O que é "Pipeline de Coleta"?

**Pipeline** = um **tubo por onde passa água** (ou neste caso, dados)

**Coleta** = ir e trazer dados

Então **"pipeline de coleta"** é um **processo automático que faz várias etapas de forma sequencial** (uma depois da outra).

### Analogia do dia a dia:

Imagina que você quer montar uma casa:

```
Pedreiro vem → faz alicerce → encanador vem → faz encanação → eletricista vem → faz fiação
```

Não pode fazer tudo de uma vez. Tem que fazer em ordem.

No nosso caso:

```
PowerShell coleta dados → Python extrai coordenadas → normaliza bairros → sincroniza com banco
```

---

## 2. O Pipeline Coleta — COLETA OU SÓ CONFERE?

### Resposta: **COLETA novos anúncios + CONFERE os dados**

Ele faz **duas coisas diferentes**:

### Parte 1: COLETA (PowerShell)
```
Você roda: .\coleta_imoveis.ps1

O que faz:
  1. Acessa as 5 imobiliárias (NIDV, DoceLar, Tonietto, Cabredo, Realize)
  2. Baixa TODOS os anúncios de cada uma
  3. Guarda em arquivo "imoveis.db" (banco de dados local)

Resultado: 1.988 imóveis (dados BRUTOS, desorganizados)
Tempo: ~30 minutos
```

**Isso traz dados NOVOS** — qualquer imóvel que entrou ou saiu das imobiliárias desde a última coleta.

---

### Parte 2: CONFERE E ORGANIZA (Python)
```
Você roda: python pipeline_coleta.py

O que faz:
  1. Lê os 1.988 imóveis brutos
  2. EXTRAI as coordenadas (lat/lng) das páginas de detalhe
     → Descobre onde cada imóvel fica no mapa
  3. NORMALIZA os bairros
     → "Rua X", "Rua Y", "Loteamento Z" do mesmo bairro viram um só
  4. CALCULA preço/m²
     → Divide preço pela área
  5. SINCRONIZA com o banco na nuvem (Supabase)
     → Manda tudo pra lá pra website buscar
  6. VALIDA a qualidade
     → Procura por erros (preço R$1, área errada, etc.)

Resultado: Dados LIMPOS e ORGANIZADOS no banco
Tempo: ~30 minutos
```

---

## 3. Fluxo Completo (do ponto de vista seu)

```
MÊS 1
├─ Você roda: .\coleta_imoveis.ps1 (coleta)
│  └─ Resultado: 1.988 imóveis em arquivo imoveis.db
│
└─ Você roda: python pipeline_coleta.py (processa)
   └─ Resultado: Dados LIMPOS no Supabase
      └─ Website mostra: "308 bairros, 1.643 com coordenadas"

MÊS 2
├─ Você roda: .\coleta_imoveis.ps1 (coleta NOVAMENTE)
│  └─ Resultado: 1.988 imóveis (pode ter 50 imóveis novos, 20 saíram)
│
└─ Você roda: python pipeline_coleta.py (processa NOVAMENTE)
   └─ Resultado: Dados NOVOS no Supabase
      └─ Website mostra dados atualizados

E assim por diante todo mês...
```

---

## 4. O que o Pipeline NÃO Faz?

- ❌ Não publica no Google / Facebook / redes sociais
- ❌ Não envia emails / mensagens
- ❌ Não deleta dados antigos (guarda histórico)
- ❌ Não compra / vende imóvel (só coleta informação)

---

## 5. O que é "Build para Produção"?

**Build** = montar, construir

**Produção** = quando está pronto pra usar de verdade (não mais teste)

### Analogia:

Imagina que você faz um bolo pra testar a receita na sua cozinha. Depois, a receita fica boa e você quer vender esse bolo num restaurante.

```
Teste em casa        →  Build pra produção  →  Restaurante vendendo
(seu computador)     →  (prepara pra vender) →  (pessoas usando)
```

### No nosso caso:

```
Desenvolvimento                Build Produção              Produção
(localhost:5173)              (empacota app)              (online)
   ↓                            ↓                          ↓
Você testa em casa     →  Cria arquivo.html      →  Website ao vivo
React roda local           pronto pra servir        http://mediaimovel.com
npm run dev                em servidor                nginx / Railway

Banco local (SQLite)  →  Supabase Cloud      →  Usuarios aceitando
imoveis.db               (banco na nuvem)       pagamentos / usando
```

---

## 6. Por que fazer "Build pra Produção"?

Seu computador (desenvolvimento):
- ✓ React só para você
- ✓ Backend roda local
- ✓ Ninguém mais pode usar

Build para produção:
- ✓ React em um servidor (Railway, Vercel, etc.)
- ✓ Qualquer pessoa no mundo acessa
- ✓ Está sempre ligado (não precisa do seu PC)
- ✓ É rápido (otimizado)

### Exemplo:

**Desenvolvimento (agora):**
```
Você abre http://localhost:5173
  ↓
Seu PC roda o React
  ↓
Só você consegue ver
```

**Produção (depois):**
```
Qualquer pessoa abre http://mediaimovel.com
  ↓
Servidor Vercel roda o React
  ↓
Todos conseguem ver
  ↓
Cobra R$99/mês de quem quer Premium
```

---

## 7. Resumo Visual

```
┌─────────────────────────────────────────────────────────────┐
│         CICLO MENSAL DE COLETA (você roda tudo)            │
├─────────────────────────────────────────────────────────────┤
│                                                             │
│  Dia 1 do mês:                                              │
│  ┌──────────────────────────────────────────────────────┐  │
│  │ PowerShell: .\coleta_imoveis.ps1                      │  │
│  │ (baixa anúncios novos das 5 imobiliárias)            │  │
│  │ Tempo: 30 min                                         │  │
│  └──────────────────────────────────────────────────────┘  │
│                                                             │
│  ↓                                                          │
│                                                             │
│  ┌──────────────────────────────────────────────────────┐  │
│  │ Python: python pipeline_coleta.py                     │  │
│  │ (extrai coords, normaliza, sincroniza, valida)       │  │
│  │ Tempo: 30 min                                         │  │
│  └──────────────────────────────────────────────────────┘  │
│                                                             │
│  ↓                                                          │
│                                                             │
│  ✓ Website atualizado com dados novos                      │
│    (1.988 imóveis, 308 bairros, preços recentes)          │
│                                                             │
└─────────────────────────────────────────────────────────────┘
```

---

## 8. Próximos Passos (Opções)

### Opção A: Ficar Testando Assim
- Você roda pipeline todo mês manualmente
- Website só funciona quando seu PC está ligado
- Não cobra ninguém

### Opção B: Deploy (Colocar Online)
- Contrata servidor (Railway, Vercel, AWS)
- Website fica 24/7 online
- Qualquer pessoa acessa
- Pode cobrar assinatura (R$99/mês Premium)

---

## 9. Dúvidas Comuns

### "O pipeline coleta dados das imobiliárias ou de um banco que já tenho?"

**Resposta:** Das imobiliárias. Toda vez que você roda PowerShell, ele acessa:
- nidv.com.br
- realizeagora.com.br
- camposimoveisdv.com.br
- etc.

E baixa os anúncios que estão lá NAQUELE DIA.

---

### "Se eu rodar pipeline de novo, não vai duplicar os dados?"

**Resposta:** Não. Porque:
- URL do anúncio é ÚNICA
- Se o mesmo anúncio aparece 2 meses seguidos, o sistema reconhece como o "mesmo"
- Só atualiza o preço/status, não duplica

---

### "Posso rodá-lo 2 vezes no mesmo dia?"

**Resposta:** Sim, mas não faz diferença.
- Primeira vez: coleta os dados
- Segunda vez: mesmos dados (nada mudou em 1 hora)

Não prejudica, só perde tempo.

---

### "E se cair no meio da coleta?"

**Resposta:** Retoma do ponto que parou.
- PowerShell: guarda checkpoint a cada 50 imóveis
- Python: sabe qual bairro já processou

Você pode rodar de novo sem preocupação.

---

## 10. Checklist: O Que Você Precisa Saber

- [ ] Pipeline = processo automático em etapas (PowerShell + Python)
- [ ] Coleta = traz dados NOVOS das imobiliárias (PowerShell)
- [ ] Processa = organiza dados e coloca no banco (Python)
- [ ] Build = prepara app pra estar online 24/7
- [ ] Produção = quando está online e pessoas podem acessar
- [ ] Você roda pipeline uma vez por mês (automático depois)
- [ ] Dados nunca duplicam (reconhece URL repetida)

---

**Dúvida específica? Mande!**

Última atualização: 5 de julho de 2026
