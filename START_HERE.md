# 📖 Guida di Inizio - Esperimenti A1-A5

## ⚡ Sommario Veloce (2 min)

Questo repository contiene gli **esperimenti A1-A5** per la validazione di stimatori discreti della dimensione della popolazione basati su ID sequenziali univoci.

- **A1:** Baseline con ID sequenziali puri (1..N)
- **A2:** ID sparsi con buchi casuali
- **A3:** ID con offset sconosciuto (invarianza alla traslazione)
- **A4:** Pooling robusto con aggregazione trimmed mean
- **A5:** Robustezza a corruzione dei dati e outlier

---

## 📂 Cosa Trovare Nel Repo

```
discrete_estimators.py         # Base per tutti gli stimatori (German Tank, Spacing, Rank, CR)
run_blockA_pooling.py          # Esperimento A4: Pooling
run_blockA_sparse.py           # Esperimento A2: ID Sparsi
run_blockA_translation.py      # Esperimento A3: Offset
run_robustness_outliers.py     # Esperimento A5: Outlier

results/
├── discrete_results.json              # A1: Baseline
├── discrete_sparse_results.json       # A2: ID Sparsi
├── discrete_translation_results.json  # A3: Offset
├── discrete_pooling_results.json      # A4: Pooling
├── robustness_outliers_results.json   # A5: Outlier

experiments.md                  # Documentazione completa A1-A5
START_HERE.md                   # Questo file
README.md                       # Descrizione generale
```

---

## 🚀 Come Eseguire gli Esperimenti

### A1 - Baseline
```bash
python run_blockA_pooling.py
```

### A2 - ID Sparsi (Gaps)
```bash
python run_blockA_sparse.py
```

### A3 - Offset/Traslazione
```bash
python run_blockA_translation.py
```

### A4 - Pooling
```bash
python run_blockA_pooling.py  # stesso script di A1 con flag diverso
```

### A5 - Robustezza a Outlier
```bash
python run_robustness_outliers.py
```

---

## 📊 Risultati Principali

| Esperimento | Scenario | Stimatore Migliore | Accuratezza |
|-------------|----------|-------------------|-------------|
| **A1** | ID Sequenziali Puri | German Tank | < 0.1% errore |
| **A2** | ID Sparsi | Capture-Recapture | < 0.2% errore |
| **A3** | Offset Sconosciuto | Spacing | < 1% errore |
| **A4** | Pooling Budget Fisso | Rank + Trimmed Mean | Stabilizza worst-case |
| **A5** | Dati Corrotti | Rank Inversion | Robusto fino a 50% corruzione |

---

## 📖 Per Approfondire

Leggi `experiments.md` per:
- Descrizione matematica completa di ogni esperimento
- Tabelle dettagliate dei risultati
- Analisi interpretative e lezioni pratiche
- Quando scegliere quale stimatore

---

## 🎯 Takeaway Finale

- **German Tank è ottimale** per ID puliti e sequenziali (A1)
- **Spacing è robusto** a offset e dati sporchi (A3, A5)
- **Capture-Recapture vince** quando gli ID hanno buchi (A2)
- **Rank Inversion è il più affidabile** in scenari reali (A5)

**Per collaborare con il team:** condividere i risultati dai JSON e discutere le implicazioni per il vostro caso d'uso specifico.

