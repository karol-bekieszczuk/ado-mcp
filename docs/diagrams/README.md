# Diagrams

Each diagram has a Mermaid source (`*.mmd`) and a rendered image (`*.png`) used by `ARCHITECTURE.md`.
Edit the `.mmd` file, then re-render:

```bash
npx -p @mermaid-js/mermaid-cli mmdc -i token-flow.mmd -o token-flow.png -s 2 -b white
```
