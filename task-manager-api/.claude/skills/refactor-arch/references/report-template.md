# Template do Relatório de Auditoria (Fase 2)

A saída da Fase 2 **deve** seguir exatamente esta estrutura — é o que será salvo em `reports/audit-project-N.md`. Não adicione seções extras; não remova nenhuma das seções abaixo.

```
================================
ARCHITECTURE AUDIT REPORT
================================
Project: <nome da pasta do projeto>
Stack:   <linguagem + framework>
Files:   <N> analyzed | ~<N> lines of code

## Summary
CRITICAL: <n> | HIGH: <n> | MEDIUM: <n> | LOW: <n>

## Findings

### [<SEVERIDADE>] <Nome do anti-pattern (do catálogo)>
File: <arquivo>:<linha ou faixa de linhas>
Description: <o que foi encontrado, 1-2 frases, sem jargão genérico — cite o trecho/padrão real>
Impact: <consequência concreta se não for corrigido>
Recommendation: <ação objetiva de correção, referenciando o playbook de refatoração quando aplicável>

### [<SEVERIDADE>] <próximo finding>
...

================================
Total: <N> findings
================================
```

## Regras de preenchimento

1. **Ordenação obrigatória**: findings ordenados por severidade, CRITICAL → HIGH → MEDIUM → LOW. Dentro da mesma severidade, ordene pela ordem em que o arquivo/linha aparece no código (top-down, arquivo a arquivo).
2. **Arquivo e linha exatos**: sempre `arquivo.ext:linha` ou `arquivo.ext:linha_inicial-linha_final`. Nunca "vários lugares" sem listar cada ocorrência (se houver muitas, liste todas separadas por vírgula no mesmo finding, ex.: `models.py:28, 48-50, 57-61`).
3. **Um finding por ocorrência relevante, não por categoria vaga**: se o mesmo anti-pattern aparece em módulos/domínios claramente diferentes (ex.: SQL injection em login vs. SQL injection em busca de produtos), prefira dois findings distintos e específicos a um finding genérico "SQL injection no projeto todo" — isso é o que permite auditar e corrigir item a item.
4. **Mínimo de 5 findings**, com pelo menos 1 CRITICAL ou HIGH. Se o projeto já tiver alguma organização (ex. projeto parcialmente estruturado), ainda assim procure os 13 itens do catálogo — a ausência de um anti-pattern óbvio não significa ausência de outros mais sutis (duplicação, dead code, N+1, etc.).
5. **Recommendation sempre acionável**: não escreva "melhorar a arquitetura"; escreva o que fazer de fato (ex.: "mover para `services/pedido_service.py` e injetar via import").
6. **Total no rodapé** deve bater exatamente com a soma do `## Summary`.

## Pausa obrigatória após o relatório

Depois de imprimir o relatório completo e salvá-lo em `reports/audit-project-N.md`, a skill **para** e pergunta ao usuário, literalmente:

```
Phase 2 complete. Proceed with refactoring (Phase 3)? [y/n]
```

Só prossiga para a Fase 3 após resposta afirmativa explícita. Nenhum arquivo do projeto-alvo pode ser modificado antes dessa confirmação.
