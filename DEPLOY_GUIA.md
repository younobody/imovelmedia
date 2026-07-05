# Guia: Deploy GitHub Pages + Railway

**Data:** 5 de julho de 2026  
**Status:** Repositório local pronto, aguardando GitHub setup

---

## PASSO 1: Criar Repositório no GitHub

1. Abra https://github.com/new
2. **Nome:** `mediaimovel` (ou outro de sua preferência)
3. **Descrição:** "SaaS para análise de imóveis em Dois Vizinhos"
4. **Público** ou **Privado** (seu gosto)
5. **NÃO** inicialize com README (já tem repositório local)
6. Clique **Create repository**

Você verá uma página com comandos. Copie a URL do repositório (tipo: `https://github.com/seu-usuario/mediaimovel.git`)

---

## PASSO 2: Fazer Push para GitHub

**No PowerShell:**
```powershell
cd "E:\Claude Cowork\Claude code Imoveis"

# Adicione a origem remota (SUBSTITUA pela sua URL)
git remote add origin https://github.com/SEU-USUARIO/mediaimovel.git

# Renomeie branch (GitHub usa "main" não "master")
git branch -M main

# Faça push
git push -u origin main
```

Após isso, seu código estará no GitHub!

---

## PASSO 3: Configurar GitHub Pages (Frontend)

1. Vá para **Settings** do seu repositório
2. Menu esquerdo: **Pages**
3. **Build and deployment:**
   - Source: `Deploy from a branch`
   - Branch: `gh-pages` / `/ (root)`
4. Salve

Deixe configurado assim, vamos usar uma GitHub Action pra fazer build automático.

---

## PASSO 4: Criar GitHub Action (Build + Deploy Frontend)

Na raiz do seu projeto, crie a pasta `.github/workflows/` e um arquivo `deploy.yml`:

**Caminho:** `.github/workflows/deploy.yml`

**Conteúdo:**
```yaml
name: Deploy Frontend to GitHub Pages

on:
  push:
    branches: ["main"]
  workflow_dispatch:

permissions:
  contents: read
  pages: write
  id-token: write

concurrency:
  group: "pages"
  cancel-in-progress: false

jobs:
  build:
    runs-on: ubuntu-latest
    steps:
      - uses: actions/checkout@v3
      
      - uses: actions/setup-node@v3
        with:
          node-version: '20'
      
      - name: Install dependencies
        run: cd frontend && npm install
      
      - name: Build
        run: cd frontend && npm run build
      
      - name: Upload artifact
        uses: actions/upload-pages-artifact@v2
        with:
          path: 'frontend/dist'

  deploy:
    environment:
      name: github-pages
      url: ${{ steps.deployment.outputs.page_url }}
    runs-on: ubuntu-latest
    needs: build
    steps:
      - name: Deploy to GitHub Pages
        id: deployment
        uses: actions/deploy-pages@v2
```

**Como colocar esse arquivo:**

Abra PowerShell:
```powershell
# Crie a pasta
mkdir ".github\workflows"

# Crie o arquivo deploy.yml (copie o conteúdo acima e cole)
```

Depois:
```powershell
git add .github/
git commit -m "Add GitHub Pages deploy workflow"
git push
```

GitHub fará build e deploy automático! ✅

---

## PASSO 5: Configurar Railway (Backend)

1. Abra https://railway.app
2. **Sign Up** com GitHub (mais fácil)
3. Conecte seu repositório `mediaimovel`
4. Clique **New Project** → **Deploy from GitHub repo**
5. Selecione seu repositório

Railway detectará automaticamente que tem um `requirements.txt` (Python).

---

## PASSO 6: Configurar Variáveis Railway

No painel Railway:
1. Vá para **Variables** (ou **Environment**)
2. Adicione:
```
DATABASE_URL=sua_string_do_supabase
ENVIRONMENT=production
PORT=8000
```

Salve. Railway faz deploy automático!

---

## PASSO 7: Atualizar Frontend para Usar Railway

Depois que Railway der uma URL (tipo `https://mediaimovel-production.up.railway.app`):

**Arquivo:** `frontend/.env.production`

```
VITE_API_URL=https://mediaimovel-production.up.railway.app
```

Depois:
```powershell
git add frontend/.env.production
git commit -m "Update production API URL"
git push
```

GitHub Pages fará novo build com a URL correta! ✅

---

## RESULTADO FINAL

```
🌐 Frontend (React):  https://seu-usuario.github.io/mediaimovel/
🔧 Backend (FastAPI): https://mediaimovel-production.up.railway.app/
💾 Banco (Supabase):  Já está rodando
```

---

## Checklist

- [ ] Criei repositório no GitHub
- [ ] Fiz push do código
- [ ] Configurei GitHub Pages
- [ ] Criei workflow deploy.yml
- [ ] Fiz commit e push do workflow
- [ ] Assinei no Railway
- [ ] Conectei repositório no Railway
- [ ] Adicionei variáveis DATABASE_URL no Railway
- [ ] Atualizei .env.production no frontend
- [ ] Fiz push das mudanças

Pronto! Seu app está online!

---

**Tempo estimado:** 15-20 minutos

**Dúvidas?** Me chama que ajudo!
