import os
import pandas as pd

def utenti_handover_dopo_shuffle(df):
    """
    Verifica se un utente ha iniziato a delegare le mosse ai robot 
    esclusivamente dopo aver subito almeno un reset del tabellone (shuffle).
    Ritorna una tupla (id_player, condition) se la condizione è verificata.
    """
    for player_id, group in df.groupby('id_player'):
        group = group.sort_values('turn_number')
        
        # Recupera la condizione dello studio per questo utente
        condition = group['experiment_condition'].iloc[0]
        
        # Individua i turni in cui è avvenuto uno shuffle
        shuffle_turns = group[group['board_changed'] == True]
        
        if not shuffle_turns.empty:
            first_shuffle_turn = shuffle_turns['turn_number'].iloc[0]
            before_first_shuffle = group[group['turn_number'] < first_shuffle_turn]
            tokens_before = before_first_shuffle['turn_token'].unique()

            print(f"Utente {player_id} in condizione {condition}:")
            print(f"  - Turni prima del primo shuffle: {list(tokens_before)}")
            print(f"  - Primo shuffle al turno: {first_shuffle_turn}")
            print(f"  - Turni totali: {len(group)}\n")
            
            # Se ha giocato ed è stato ESCLUSIVAMENTE 'human' prima del primo shuffle
            if len(tokens_before) > 0 and list(tokens_before) == ['human']:
                return player_id, condition

    return None

def main():
    path = r"..\data\\"
    
    # Dizionari per tracciare i dati per condizione
    totali_per_condizione = {}
    target_per_condizione = {}

    print("Inizio scansione file CSV...\n")

    for root, dirs, files in sorted(os.walk(path)):
        for file in files:
            if file.endswith(".csv"):
                filepath = os.path.join(root, file)
                df = pd.read_csv(filepath, sep=';')

                # Esclude il partecipante 2
                if df['id_player'].iloc[0] == 2:
                    continue

                cond = df['experiment_condition'].iloc[0]

                # Inizializza i contatori se è la prima volta che si incontra la condizione
                if cond not in totali_per_condizione:
                    totali_per_condizione[cond] = 0
                    target_per_condizione[cond] = []

                totali_per_condizione[cond] += 1

                # Applica l'analisi
                res = utenti_handover_dopo_shuffle(df)
                if res:
                    player_id, _ = res
                    target_per_condizione[cond].append(player_id)

    # --- STAMPA RISULTATI PER CONDIZIONE ---
    print("\n" + "="*55)
    print("   ANALISI HANDOVER DOPO SHUFFLE PER CONDIZIONE")
    print("="*55)
    
    totale_utenti_validi = sum(totali_per_condizione.values())
    totale_target = sum(len(ids) for ids in target_per_condizione.values())

    for cond in sorted(totali_per_condizione.keys()):
        tot = totali_per_condizione[cond]
        ids = target_per_condizione[cond]
        count = len(ids)
        pct = (count / tot) * 100 if tot > 0 else 0
        
        print(f"\n▶ Condizione {cond}:")
        print(f"  - Utenti totali: {tot}")
        print(f"  - Utenti target: {count} {ids}")
        print(f"  - Percentuale: {pct:.2f}%")

    print("\n" + "-"*55)
    print(f"TOTALE COMPLESSIVO: {totale_target}/{totale_utenti_validi} utenti "
          f"({(totale_target / totale_utenti_validi * 100):.2f}%)" if totale_utenti_validi > 0 else "")
    print("="*55)

if __name__ == "__main__":
    main()