# Deploy no Railway com dados

## 1. Publicar o código no GitHub

Na pasta do projeto:

```powershell
cd "c:\Users\fabri\cofluhab\cofluhab"
git init
git add .
git commit -m "Prepare Railway deployment"
git branch -M main
git remote add origin https://github.com/SEU_USUARIO/SEU_REPO.git
git push -u origin main
```

## 2. Criar o projeto no Railway

1. Crie um projeto novo a partir do repositório do GitHub.
2. Adicione um serviço PostgreSQL no mesmo projeto.
3. No serviço web, configure estas variáveis:

```env
SECRET_KEY=<gere uma chave longa e aleatória>
DEBUG=False
ALLOWED_HOSTS=<seu-dominio>.up.railway.app
CSRF_TRUSTED_ORIGINS=https://<seu-dominio>.up.railway.app
SECURE_SSL_REDIRECT=True
SECURE_HSTS_SECONDS=31536000
SECURE_HSTS_INCLUDE_SUBDOMAINS=True
SECURE_HSTS_PRELOAD=True
```

O `DATABASE_URL` deve vir do PostgreSQL do Railway.

## 3. Subir os dados atuais do SQLite

Não envie o `db.sqlite3` para o GitHub. O fluxo correto é exportar localmente e importar para o PostgreSQL do Railway.

Execute no PowerShell local:

```powershell
cd "c:\Users\fabri\cofluhab\cofluhab"
.\scripts\migrar_sqlite_para_railway.ps1 -DatabaseUrl "postgresql://USUARIO:SENHA@HOST:PORTA/BANCO"
```

O script faz quatro passos:

1. exporta os dados atuais do SQLite para `exports/railway-bootstrap.json.gz`
2. conecta no PostgreSQL do Railway usando `DATABASE_URL`
3. executa `migrate`
4. executa `loaddata`

## 4. Verificação final

Depois do deploy e da carga:

```powershell
cd "c:\Users\fabri\cofluhab\cofluhab"
$env:DATABASE_URL="postgresql://USUARIO:SENHA@HOST:PORTA/BANCO"
.\.venv\Scripts\python.exe manage.py shell -c "from principal.models import Contrato, Mutuario, ParcelaContrato, Movimentacao; print({'Contrato': Contrato.objects.count(), 'Mutuario': Mutuario.objects.count(), 'ParcelaContrato': ParcelaContrato.objects.count(), 'Movimentacao': Movimentacao.objects.count()})"
```

Contagens atuais do banco local:

```text
Contrato: 3159
Mutuario: 3163
ParcelaContrato: 915486
Movimentacao: 3126
```