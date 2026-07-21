# cofluhab

## Preparar para deploy Railway

Substitua `your-username` pelo seu usuário real do GitHub antes de executar os comandos.
Se você já clonou o repositório, pule o `git init` e o `git remote add origin ...` (o `origin` já existe).

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
