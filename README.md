# Population Size Estimators - Esperimenti A1-A5

Validazione di stimatori statistici per la stima della dimensione di una popolazione basata su ID sequenziali univoci. Questo repository contiene i **5 esperimenti chiave** (A1-A5) per valutare la robustezza e l'applicabilità di metodi classici come il German Tank, lo Spacing Estimator, il Rank Inversion e il Capture-Recapture.

## 📂 Struttura del Progetto

```
population_size_estimation/
├── README.md                          # Questo file
├── START_HERE.md                      # Guida rapida di inizio
├── experiments.md                     # Documentazione dettagliata A1-A5
├── requirements.txt                   # Dipendenze Python
│
├── discrete_estimators.py             # Base: Stimatori (German Tank, Spacing, Rank, CR)
├── run_blockA_pooling.py              # Esperimento A4: Pooling con budget fisso
├── run_blockA_sparse.py               # Esperimento A2: ID Sparsi (Gaps)
├── run_blockA_translation.py          # Esperimento A3: Offset/Traslazione
├── run_robustness_outliers.py         # Esperimento A5: Corruzione e Outlier
│
├── results/                           # Output JSON degli esperimenti
│   ├── discrete_results.json          # A1: Baseline
│   ├── discrete_sparse_results.json   # A2: ID Sparsi
│   ├── discrete_translation_results.json # A3: Offset
│   ├── discrete_pooling_results.json  # A4: Pooling
│   └── robustness_outliers_results.json # A5: Outlier
│
└── figures/                           # Grafici generati
    └── *.png
```

## 📚 Gli Esperimenti A1-A5

| Esperimento | Scenario | Stimatore Migliore | Risultato |
|-------------|----------|-------------------|-----------|
| **A1** | ID Sequenziali Puri (1..N) | German Tank | < 0.1% errore |
| **A2** | ID Sparsi con Buchi Casuali | Capture-Recapture | < 0.2% errore (m/n ≥ 0.02) |
| **A3** | ID con Offset Sconosciuto | Spacing | < 1% errore (translation-invariant) |
| **A4** | Pooling con Budget Fisso | Rank Inversion + Trimmed Mean | Stabilizza worst-case |
| **A5** | Dati Corrotti / Outlier | Rank Inversion | Robusto fino a 50% corruzione |

## 🎯 Stimatori Discreti (`discrete_estimators.py`)

Per stimare il numero totale di entità con identificatori univoci:

- **German Tank Problem (MVUE)** - Ottimale per ID sequenziali puliti partendo da 1.
  - Formula: $\hat{N} = \max(\text{sample}) + \frac{\max(\text{sample})}{m} - 1$
  - Quando usare: A1 (ID puri e sequenziali)
  - Quando evitare: A3, A5 (offset o outlier)

- **Spacing Estimator** - Translation-invariant, robusto a offset sconosciuto.
  - Formula: $\hat{N} = m \times \text{mediana}(\text{gap tra ID ordinati})$
  - Quando usare: A3, A5 (offset o dati sporchi)
  - Quando evitare: ID con buchi sistematici

- **Rank Inversion** - Basato sulla mediana, altamente robusto.
  - Quando usare: A5 (outlier), A4 (pooling)
  - Quando evitare: Sample size molto piccolo

- **Capture-Recapture (Chapman)** - Unico metodo non basato sui valori degli ID.
  - Formula: $\hat{N} = \frac{(m_1+1)(m_2+1)}{I+1} - 1$
  - Quando usare: A2 (ID sparsi con buchi)
  - Richiede: Due campioni indipendenti

## 🚀 Guida Rapida

### Prerequisiti

- Python 3.8+
- pip

### Installazione

```bash
# 1. Clone o scarica il repository

# 2. (Opzionale) Crea virtual environment
python -m venv venv
venv\Scripts\activate

# 3. Installa dipendenze
pip install -r requirements.txt
```

### Eseguire gli Esperimenti

```bash
# A1 - Baseline (ID Sequenziali Puri)
python run_blockA_pooling.py --baseline

# A2 - ID Sparsi (Gaps)
python run_blockA_sparse.py

# A3 - Offset/Traslazione
python run_blockA_translation.py

# A4 - Pooling
python run_blockA_pooling.py --pooling

# A5 - Robustezza a Outlier
python run_robustness_outliers.py
```

I risultati sono salvati in `results/*.json` come:
```
results/discrete_results.json
results/discrete_sparse_results.json
results/discrete_translation_results.json
results/discrete_pooling_results.json
results/robustness_outliers_results.json
```

## 📖 Documentazione

- **START_HERE.md** - Guida di inizio (2 min)
- **experiments.md** - Documentazione completa A1-A5 con tabelle e analisi (20+ min)

## 🔑 Takeaway Principale

1. **German Tank è MVUE** per ID sequenziali puliti (A1: <0.1% errore)
2. **Spacing è translation-invariant** e robusto a offset (A3: <1% errore)
3. **Capture-Recapture non dipende dai valori** degli ID, solo dall'overlap (A2)
4. **Rank Inversion è il più affidabile** in scenari reali con outlier (A5)
5. **Il metodo migliore dipende dallo scenario** - vedi la tabella decisionale in experiments.md

## 💬 Per il Team

Condividete i risultati dai file JSON in `results/` e discutete le implicazioni per il vostro caso d'uso specifico. Ogni esperimento viene documentato con statistiche complete:
- Mediana della stima
- Errore relativo percentuale
- Intervallo di confidenza (95%)
- Bias e varianza
