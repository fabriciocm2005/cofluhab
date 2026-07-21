# cofluhab

## Preparar para deploy Railway

- Substitua **todas** as ocorrências de `your-username` pelo seu usuário real do GitHub.
- Se você já clonou o repositório, pule `git init` e `git remote add origin ...` (o `origin` já existe).
- Execute `git add .` e `git commit ...` apenas se houver mudanças para versionar.

```bash
git init
git add .
git commit -m "Preparar para deploy Railway"
git remote add origin https://github.com/your-username/cofluhab.git
git push -u origin main
```

Opcional (SSH, recomendado para uso frequente):

```bash
git remote set-url origin git@github.com:your-username/cofluhab.git
```
