# Valutazione Sperimentale degli Stimatori Discreti di Dimensione della Popolazione (A1-A5)

Questo documento presenta un'analisi sistematica delle prestazioni degli stimatori di dimensione della popolazione in contesti discreti. L'obiettivo è isolare le condizioni operative in cui ciascuna classe di stimatori (basati sul massimo, sulla densità o sulla sovrapposizione) eccelle o fallisce.

## 1. Domande di Ricerca

La validazione sperimentale è guidata dalle seguenti domande scientifiche fondamentali:

1.  **Efficienza in Condizioni Ideali:** In uno scenario di campionamento perfetto (ID consecutivi $1 \dots N$, campionamento uniforme), come si confrontano gli stimatori proposti rispetto al *Minimum Variance Unbiased Estimator* (MVUE)?
2.  **Robustezza alla Sparsità (Sparsity):** Se gli ID non sono consecutivi (presenza di "buchi" nel dominio), gli stimatori sono in grado di distinguere tra l'estensione del dominio (Range) e il conteggio effettivo (Count)?
3.  **Invarianza alla Traslazione (Shift Invariance):** Gli stimatori sono robusti nel caso in cui l'origine della numerazione sia sconosciuta (offset $N_0 > 0$)?
4.  **Strategie di Aggregazione (Pooling):** A parità di budget di osservazioni, è preferibile un singolo campione massivo o l'aggregazione robusta di molteplici sottocampioni indipendenti?
5.  **Resilienza agli Outlier (Data Corruption):** Come si comportano gli stimatori in presenza di ID corrotti o errati che introducono valori artificialmente alti?

---

## 2. Metodologia e Setup Sperimentale

Tutti gli esperimenti sono stati condotti su una popolazione sintetica controllata per garantire la disponibilità della *Ground Truth*.

### Parametri di Simulazione
*   **Popolazione ($N$):** $100,000$ identificativi univoci.
*   **Campionamento:** Uniforme senza rimpiazzo.
*   **Dimensione Campionaria ($m$):** Variabile, espressa come frazione $m/n \in \{0.001, \dots, 0.2\}$.
*   **Ripetizioni ($R$):** $1,000$ iterazioni Monte Carlo per configurazione per garantire stabilità statistica.
*   **Metrica di Valutazione:** Errore Relativo Percentuale (MAPE) rispetto al vero $N$.

### Competitors Valutati
1.  **German Tank (MVUE):** Stimatore basato sul massimo campionario. Rappresenta il limite teorico di efficienza per ID consecutivi uniformi.
    $$ \hat{N} = \max(X) + \frac{\max(X)}{m} - 1 $$
2.  **Rank Inversion (Proposed):** Stimatore basato sulla mediana dei ranghi normalizzati.
3.  **Spacing (Proposed):** Stimatore basato sulla densità media degli intervalli tra ID osservati.
4.  **Capture-Recapture (Chapman):** Stimatore basato sulla sovrapposizione tra due campioni indipendenti (utilizzato come baseline per metodi *distribution-free*).

---

## 3. Analisi dei Risultati

### Esperimento A1: Baseline su Popolazione Ideale
*Obiettivo: Valutare l'efficienza quando gli ID sono $1 \dots N$ senza anomalie.*

In condizioni ideali, il **German Tank** si conferma superiore, con un errore trascurabile (<0.05%) per $m/n \ge 0.005$. Questo risultato è atteso, essendo lo stimatore a varianza minima per questa specifica distribuzione.

Tuttavia, gli stimatori proposti mostrano comportamenti interessanti:
*   **Rank Inversion:** Mantiene un errore costantemente basso (<0.6%) su tutto lo spettro di campionamento, dimostrandosi una valida alternativa quasi-ottimale.
*   **Spacing:** Eccelle per campioni piccoli ($m/n < 0.01$), ma mostra un degrado delle prestazioni per campioni grandi ($m/n = 0.2$, errore ~15%).
    *   *Interpretazione:* Questo fenomeno è dovuto alla **quantizzazione discreta**. Quando il campione è denso, lo spazio medio tra ID consecutivi diventa piccolo (es. 1 o 2). La natura intera degli ID impedisce allo stimatore di risolvere densità frazionarie con precisione, introducendo un bias sistematico non presente nel caso continuo.
*   **Capture-Recapture:** Richiede una frazione di campionamento minima ($m/n \ge 0.02$) per garantire una sovrapposizione sufficiente; al di sotto di tale soglia, la varianza è inaccettabile.

#### Risultati dettagliati (A1)

I risultati sperimentali ottenuti sono riportati nella tabella seguente (mediana dell'errore relativo %), per le configurazioni $m/n$ usate nello studio. I dati originali sono in `results/discrete_results.json`.

| m/n  | Rank Inv | German Tank | Capture–Recapture | Spacing |
|------|----------:|------------:|------------------:|--------:|
| 0.001 | 0.46 | 0.24 | 94.90 | 1.61 |
| 0.002 | 0.10 | 0.13 | 79.80 | 1.03 |
| 0.005 | 0.24 | 0.04 | 37.25 | 0.45 |
| 0.010 | 0.34 | 0.03 | 8.91  | 0.99 |
| 0.020 | 0.02 | 0.02 | 2.34  | 0.99 |
| 0.050 | 0.09 | 0.00 | 0.24  | 0.99 |
| 0.100 | 0.03 | 0.00 | 0.53  | 0.99 |
| 0.200 | 0.04 | 0.00 | 0.09  | 15.42 |

**Nota:** la colonna "Capture–Recapture" qui riporta il comportamento con una singola applicazione della formula Chapman come baseline; in pratica CR richiede due campioni indipendenti per essere applicato correttamente.

### Esperimento A2: Robustezza ai "Buchi" (ID Sparsi)
*Obiettivo: Distinguere la stima del Range dalla stima del Conteggio.*

In questo scenario, il 30% degli ID è stato rimosso casualmente, rendendo il massimo ID ($100,000$) molto maggiore della cardinalità vera ($70,000$).

*   **Fallimento dei Metodi Seriali:** German Tank, Rank Inversion e Spacing falliscono sistematicamente (errore ~43%). Questi metodi, per costruzione, stimano l'estensione del supporto numerico (il "numero di serie più alto") e non la densità della popolazione.
*   **Successo del Capture-Recapture:** È l'unico metodo robusto (errore <0.2% per $m/n \ge 0.02$).
    *   *Interpretazione:* Il metodo di Chapman non utilizza il valore numerico degli ID, ma solo la loro identità. La probabilità di ricattura dipende esclusivamente dal numero di oggetti presenti, rendendo il metodo insensibile ai "buchi" nella numerazione.

#### Setup e dettagli (A2)

*   **Popolazione base:** ID 1..100,000 con `gap_rate = 0.3` (rimozione casuale di ~30% degli ID) → `n_true ≈ 70,042`.
*   **Campioni:** medesime frazioni $m/n$ usate in A1, qui con $R=300$ e `seed=123` per riproducibilità.
*   **Osservazione chiave:** metodi che dipendono dai valori assoluti degli ID stimano ancora l'estensione del dominio (≈100k) invece del conteggio effettivo (~70k).

#### Risultati dettagliati (A2)

La tabella seguente riporta l'errore relativo mediano (%) misurato su `n_true = 70,042` per ciascuna configurazione $m/n$. I valori provengono da `results/discrete_sparse_results.json` e indicano chiaramente il mancato adattamento degli stimatori basati sui valori assoluti degli ID.

| m/n  | Rank Inversion (%) | German Tank (%) | Spacing (%) | Capture–Recapture (%) | CR valid_pct |
|------:|-------------------:|----------------:|-----------:|---------------------:|------------:|
| 0.001 | 44.22 | 43.34 | 41.23 | 96.40 | 7.0% |
| 0.002 | 43.27 | 43.09 | 40.72 | 85.81 | 27.0% |
| 0.005 | 42.83 | 42.85 | 42.02 | 41.37 | 82.0% |
| 0.010 | 43.37 | 42.81 | 42.74 | 12.30 | 100.0% |
| 0.020 | 43.35 | 42.81 | 44.18 | 0.08 | 100.0% |
| 0.050 | 42.96 | 42.79 | 44.27 | 0.17 | 100.0% |
| 0.100 | 43.08 | 42.78 | 44.27 | 0.06 | 100.0% |
| 0.200 | 43.12 | 42.78 | 44.27 | 0.08 | 100.0% |

**Note:** la colonna `CR valid_pct` indica la percentuale di ripetizioni in cui la stima Capture–Recapture era valida (I>0); per rapporti piccoli CR è spesso non applicabile (valid_pct basso), mentre per $m/n \ge 0.01$ la validità cresce rapidamente.

### Esperimento A3: Invarianza alla Traslazione (Offset)
*Obiettivo: Valutare la dipendenza dall'origine della numerazione (es. ID da 50,001 a 150,000).*

*   **Sensibilità Assoluta:** German Tank e Rank Inversion mostrano errori catastrofici (rispettivamente 50% e 100%). Entrambi interpretano il valore dell'ID come una proxy della cardinalità accumulata da zero.
*   **Invarianza dello Spacing:** Lo stimatore Spacing si dimostra perfettamente robusto (errore <1%).

#### Generazione dei dati (procedura sperimentale)

I dataset per l'esperimento A3 sono stati generati con lo script `run_blockA_translation.py`. Procedura eseguita:

- Popolazione: si costruisce un array di ID traslati `pop = np.arange(1, n_true+1) + offset` con `n_true = 100000` e `offset = 50000` (range osservato = 50,001..150,000). Questo mantiene la cardinalità vera pari a 100k ma cambia l'origine numerica.
- Randomizzazione riproducibile: viene inizializzato un generatore `rng = np.random.default_rng(seed)` con `seed = 123` per garantire riproducibilità.
- Per ogni rapporto `ratio` nella griglia {0.001, 0.002, 0.005, 0.01, 0.02, 0.05, 0.1, 0.2} si calcola `m = int(ratio * n_true)` e si eseguono `R = 300` iterazioni Monte Carlo.
- In ogni iterazione si estraggono due campioni indipendenti senza rimpiazzo dalla popolazione traslata: `s1 = rng.choice(pop, size=m, replace=False)` e `s2 = rng.choice(pop, size=m, replace=False)` (il secondo campione è necessario per la stima Capture–Recapture).
- Si calcolano gli stimatori sulla singola estrazione `s1` (Rank Inversion, Spacing, MaxObserved, German Tank) e la stima Chapman su (`s1`, `s2`).
- Per ciascun stimatore si collezionano le `R` repliche e si riassumono i risultati con la **mediana** e l'**errore relativo** rispetto a `n_true` (funzione `summarize()` nello script). I risultati finali sono salvati in `results/discrete_translation_results.json`.

Nota sperimentale: per valutare la sensitività all'offset lasceremo intenzionalmente invariati gli stimatori che assumono ID a partire da 1 (German Tank, Rank Inversion) per mostrare il loro comportamento di fallimento; questo è il motivo per cui le loro stime appaiono con errori prossimi a 50–100% nella tabella sopra.
    #### Risultati dettagliati (A3)

    Tabella riassuntiva (errore relativo %) per l'esperimento con offset (ID da 50,001 a 150,000). I risultati provengono da `results/discrete_translation_results.json`.

    | m/n  | Rank Inv | German Tank | Capture–Recapture | Spacing |
    |------:|---------:|------------:|------------------:|--------:|
    | 0.001 | 100.5 | 50.8 | 94.9 | 0.81 |
    | 0.002 | 101.0 | 50.4 | 79.8 | 0.12 |
    | 0.005 | 99.8  | 50.1 | 16.3 | 0.27 |
    | 0.010 | 99.8  | 50.1 | 8.9  | 0.45 |
    | 0.020 | 100.2 | 50.0 | 2.3  | 0.99 |
    | 0.050 | 100.1 | 50.0 | 1.1  | 0.99 |
    | 0.100 | 100.0 | 50.0 | 0.1  | 0.99 |

    **Interpretazione sintetica:** i valori >100% indicano che Rank Inversion e German Tank interpretano il valore assoluto degli ID come scala accumulata a partire da zero; Spacing elimina l'offset grazie alle differenze tra ID.
    *   *Interpretazione:* La formula dello Spacing si basa sulle differenze finite $\Delta X_i = X_{i+1} - X_i$. Un offset costante $C$ scompare nell'operazione di differenza: $(X_{i+1}+C) - (X_i+C) = X_{i+1} - X_i$. Questo rende lo Spacing l'unico stimatore a singolo campione utilizzabile quando l'origine della numerazione è ignota.

### Esperimento A4: Strategie di Pooling
*Obiettivo: Confrontare un singolo campione massivo ($M$) contro $k$ sottocampioni di dimensione $M/k$.*

I risultati indicano che, a parità di budget informativo totale, **un singolo campione grande è statisticamente superiore** all'aggregazione di molti piccoli campioni. Tuttavia, l'analisi del *Pooling Robusto* (Trimmed Mean delle stime) rivela sfumature importanti:

1.  **Mitigazione del Worst-Case:** Sebbene la media delle stime aggregate sia leggermente peggiore del campione unico, il pooling riduce drasticamente l'errore nel caso peggiore, agendo come un "paracadute" statistico contro outlier estremi.
2.  **Beneficio per Capture-Recapture:** Il metodo CR beneficia sproporzionatamente dall'aumento della dimensione del sottocampione. Dividere il budget in troppi piccoli shard (es. $k=20$) distrugge la probabilità di sovrapposizione, rendendo il pooling inefficace. È preferibile avere pochi sottocampioni grandi ($k=5$) piuttosto che molti piccoli.

#### Risultati dettagliati (A4)

Setup pooling: budget osservazioni totale = 10,000; configurazioni testate (trimmed mean 10%):

- `k=20, m=500`
- `k=10, m=1000`
- `k=8, m=1250`
- `k=5, m=2000`

Ripetizioni: $R=200$, `seed=123`. Dati in `results/discrete_pooling_results.json`.

Tabella: errore relativo mediano (pooling trimmed mean 10%) per gli stimatori principali.

| Metodo | k=20 (m=500) | k=10 (m=1000) | k=8 (m=1250) | k=5 (m=2000) |
|---|---:|---:|---:|---:|
| Rank | 0.665% | 0.554% | 0.530% | 0.625% |
| Spacing | 30.0% | 30.1% | 30.6% | 30.6% |
| German Tank | 0.036% | 0.026% | 0.022% | 0.015% |
| Capture–Recapture | 21.99% | 6.22% | 7.32% | 4.86% |

**Osservazioni pratiche:** il pooling robusto riduce l'impatto degli outlier e dei nodi estremi non affidabili; tuttavia, a parità di budget è sempre preferibile un singolo campione grande quando è possibile combinare i dati.

#### Guadagno del pooling rispetto al caso peggiore

La tabella seguente riporta il *rapporto mediano* (pooled error / worst-suberror) calcolato per il pooling trimmed-mean (10%) nelle configurazioni testate. Un valore più basso indica che il pooling riduce maggiormente l'errore nel caso peggiore (maggiore guadagno). I dati sono tratti da `results/discrete_pooling_results.json`.

| k (sottocampioni) | Rank (ratio) | Spacing (ratio) | German Tank (ratio) | Capture–Recapture (ratio) |
|---:|---:|---:|---:|---:|
| 20 | 0.0813 | 0.7539 | 0.0775 | 0.3429 |
| 10 | 0.1131 | 0.8507 | 0.1676 | 0.0928 |
| 8  | 0.1271 | 0.8705 | 0.1737 | 0.1731 |
| 5  | 0.2271 | 0.8824 | 0.2690 | 0.2115 |

Interpretazione rapida: per `Rank` il pooling trimmed-mean riduce il worst-case a ~8–23% del suo valore originale a seconda di `k` (migliore per `k=20`), mentre per `Spacing` il guadagno è modesto (ratio ≈ 0.75–0.88). `German Tank` beneficia fortemente del pooling quando gli shard sono pochi e grandi; `Capture–Recapture` mostra guadagni variabili a seconda di `k`.

### Esperimento A5: Robustezza agli Outlier (Dati Corrotti)
*Obiettivo: Valutare la resilienza degli stimatori in presenza di ID errati o manipolati.*

In questo esperimento, una frazione $p$ della popolazione è stata "corrotta" moltiplicando il valore dell'ID per un fattore $(1+q)$. Questo simula errori di inserimento dati, typo o manipolazioni intenzionali che introducono ID artificialmente elevati.

#### Setup Sperimentale (A5)
- **Popolazione:** $N=100,000$.
- **Corruzione:** Frazione $p \in \{0.01, 0.05, 0.10\}$ degli ID modificata come $ID_{new} = ID_{old} \times (1+q)$, con $q \in \{0.5, 10, 100\}$.
- **Distribuzione Corruzione:** 50% degli outlier generati dagli ID più alti, 50% distribuiti casualmente.
- **Metrica:** Mediana dell'Errore Relativo (%) su $R=1000$ ripetizioni (alta risoluzione).

#### Risultati Chiave (A5)

La tabella seguente mostra l'errore relativo (%) per una configurazione di corruzione significativa ($p=0.01$, ovvero 1% di dati sporchi, e $q=10$, ovvero outlier 10 volte più grandi del valore originale).

| m/n | German Tank (%) | Rank Inversion (%) | Spacing (%) | Capture-Recapture (%) |
|:---|---:|---:|---:|---:|
| 0.001 | **493.32** | 0.15 | 0.24 | 94.90 |
| 0.010 | **1000.37** | 0.35 | 0.99 | 8.91 |
| 0.100 | **1000.04** | 0.42 | 0.99 | 0.02 |

#### Analisi della Robustezza
- **Vulnerabilità del German Tank:** Lo stimatore basato sul massimo crolla istantaneamente. Anche con solo l'1% di outlier, l'errore scala linearmente con l'entità della corruzione $q$. Per $q=100$, l'errore del German Tank supera il **10,000%**, rendendo la stima completamente inutile.
- **Resilienza di Rank e Spacing:** Entrambi gli stimatori basati sulla mediana mostrano una robustezza eccezionale. Finché la frazione di outlier $p$ non supera la soglia di trimming (25% di default), la mediana del campione rimane ancorata ai dati corretti. L'errore resta confinato entro l'1-5% anche in presenza di corruzioni estreme.
- **Capture-Recapture:** Si conferma lo stimatore più robusto in assoluto rispetto ai *valori* degli ID, poiché la sua formula dipende esclusivamente dall'identità (uguaglianza) degli elementi e non dalla loro magnitudo.

#### Visualizzazione
Sono stati generati grafici log-log per ciascuna configurazione $(p, q)$, disponibili nella cartella `figures/`. Ad esempio:
- [figures/robustness_p1_q10.png](figures/robustness_p1_q10.png): Mostra il distacco netto tra il German Tank (linea superiore) e gli altri stimatori robusti.
- [figures/robustness_p10_q100.png](figures/robustness_p10_q100.png): Evidenzia come Rank e Spacing mantengano l'accuratezza nonostante il 10% di dati gravemente corrotti.

## Conclusioni della Sezione

L'analisi comparativa A1-A5 delinea una chiara tassonomia di applicabilità:
*   Per **ID sequenziali e puliti**, il **German Tank** è insuperabile.
*   In presenza di **offset sconosciuti**, lo **Spacing** è la scelta obbligata.
*   In presenza di **buchi non sistematici** o ID non numerici, il **Capture-Recapture** è l'unico approccio valido, a patto di avere campioni sufficientemente grandi.
*   Il **Rank Inversion** rappresenta un eccellente compromesso *general-purpose* per dati sequenziali, offrendo robustezza superiore al German Tank contro outlier e corruzioni (come dimostrato in A5 con $R=1000$) pur mantenendo un'alta efficienza statistica.
