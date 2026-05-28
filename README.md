# semantic_memory_hri

## How to play

Navigare nella cartella **app** ed eseguire il comando:
```sh
py app.py 1 0
```
Dove 1 è l'ID del giocatore, e 0..4 sono le condizioni:
+ 0) CC: Both robot are competent(correct card - correct curiosity)
+ 1) CS0: One robot is competent, the other one is semi-competent (correct card - wrong curiosity)
+ 2) CS1: One robot is competent, the other one is semi-competent (wrong card - correct curiosity)
+ 3) CI: One robot is competent, the other one is incompetent (wrong card - wrong curiosity)
+ 4) II: Both robot are incompetent (wrong card - wrong curiosity)

Si aprirà automaticamente la schermata del gioco.

Successivamente, aprire un'altra scheda del terminale e navigare nella cartella **semantic_memory** ed eseguire il comando:
```sh
py mixed_team.py
```

Infine, ritornare sulla schermata del gioco e andare avanti nel tutorial, per poi giocare.

## Training
Per più informazioni: https://github.com/rikifunt/tya-associative-memory/tree/main
