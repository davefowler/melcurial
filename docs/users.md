## mel – quick guide (for non‑engineers)

Use these commands in your project folder:

```bash
mel start          # creates your branch (prompts for your name)
# edit files...
mel sync           # saves/stashes, updates with main, and pushes
mel status         # shows what's going on
mel publish        # runs checks and ships your changes to main
```

Tips:
- If mel asks what to do with local changes, choose Save or Stash.
- If mel offers to open a pull request, say yes and follow the link.
- If something goes wrong, run `mel status` and share the output with an engineer.


