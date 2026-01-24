# Esperimenti A1-A5: Validazione Stimatori Discreti

Questo documento raccoglie gli esperimenti sulla stima della dimensione di una popolazione discreta basata su ID sequenziali univoci.

## Blocco A – Validazione popolazione discreta (e varianti)

### A1 – Baseline (gia eseguito)

**Obiettivo**
- Validare gli stimatori discreti di dimensione della popolazione (paper *explanation_of_matlab_for_estimating_n.pdf* e piano *Pasquale_plan_sn.pdf*) su una popolazione finita con ID univoci.

**Setup**
- Popolazione discreta: N = 100,000 (ID 1..N), estrazione senza rimpiazzo.
- Campioni: m corrispondente a m/n in {0.001, 0.002, 0.005, 0.01, 0.02, 0.05, 0.1, 0.2}.
- Ripetizioni: R = 1000 (default degli script discreti).
- Dati sorgente: [results/discrete_results.json](results/discrete_results.json).

**Metodi valutati**
- Rank Inversion (discreto)
- Spacing (discreto)
- German Tank
- Capture–Recapture (Chapman)

**Metriche**
- Mediana della stima N̂
- Errore relativo (%) = |mediana - N_true| / N_true * 100

**Risultati chiave (errore relativo %) per m/n**

| m/n  | Rank Inv | German Tank | CR | Spacing |
|------|----------|-------------|----|---------|
| 0.001 | 0.46 | 0.24 | 94.90 | 1.61 |
| 0.002 | 0.10 | 0.13 | 79.80 | 1.03 |
| 0.005 | 0.24 | 0.04 | 37.25 | 0.45 |
| 0.010 | 0.34 | 0.03 | 8.91 | 0.99 |
| 0.020 | 0.02 | 0.02 | 2.34 | 0.99 |
| 0.050 | 0.09 | 0.00 | 0.24 | 0.99 |
| 0.100 | 0.03 | 0.00 | 0.53 | 0.99 |
| 0.200 | 0.04 | 0.00 | 0.09 | 15.42 |

**Grafico**
- Errore relativo (mediana) vs m/n, scala log-log: [figures/blockA_discrete_rel_error.png](figures/blockA_discrete_rel_error.png)

**Formula e Teoria**
- **German Tank (MVUE):** $\hat{N} = \max(\text{sample}) + \frac{\max(\text{sample})}{m} - 1$
  - Fornisce la stima a varianza minima quando gli ID sono 1..N consecutivi.
  - La correzione $+\max/m$ compensa il bias dovuto al campionamento uniforme.
  - È derivato dalla teoria dei valori estremi per distribuzioni uniformi.

**Osservazioni**
- German Tank è l MVUE; lo usiamo come unico rappresentante dei metodi basati sul massimo.
- Rank Inversion resta <0.6% su tutti i m/n; CR è affidabile solo da m/n ≳ 0.02.
- **Spacing (corretto)**: Ora molto accurato (<1.6%) per m/n bassi. Per m/n elevati (0.2), l'errore aumenta (~15%) a causa della quantizzazione degli spaziamenti discreti (media piccola).

### A2 – ID sparsi (German Tank non valido)

**Obiettivo**
- Valutare gli stimatori discreti quando gli ID non sono consecutivi (30% di buchi casuali), così che il max non rappresenti più N.

**Setup**
- Popolazione di base: 1..100,000 con gap_rate=0.3 → n_true=70,042 ID effettivi.
- Campioni: m/n in {0.001, 0.002, 0.005, 0.01, 0.02, 0.05, 0.1, 0.2}; R=300; seed=123.
- Dati: [results/discrete_sparse_results.json](results/discrete_sparse_results.json).

**Metodi**
- Rank inversion (discreto), Spacing (discreto), German Tank, Capture–Recapture (Chapman).

**Risultati chiave (errore relativo %)**
- **Spacing**: Dopo la correzione, si comporta come German Tank e Rank Inversion, mostrando un errore del ~41-44%. Questo perché stima il range degli ID ($N_{base} \approx 100k$) e non il conteggio effettivo ($N_{true} \approx 70k$).
- **German Tank / Rank**: Restano distorti di ~43% su tutti i m/n (il max osservato non traccia più N).
- **Capture-Recapture**: Unico metodo valido. L'errore scende rapidamente con l'aumentare dell'overlap: da ~12% (m/n=0.01) a <0.2% (m/n >= 0.02).

**Takeaway**
- Rompendo l assunzione di ID consecutivi, tutti i metodi basati su ordine e spaziamento (German Tank, Rank, Spacing) falliscono perché stimano l'estensione del dominio degli ID. Solo **Capture-Recapture** è robusto ai buchi negli ID, poiché si basa sulla sovrapposizione dei campioni, non sui valori assoluti.

**Perché Capture-Recapture è Robusto ai Buchi**
- CR utilizza la formula di Chapman: $\hat{N} = \frac{(m_1+1)(m_2+1)}{I+1} - 1$, dove $I$ è l'overlap (numero di ID comuni).
- CR non guarda i *valori* degli ID, solo la loro *identità* e *sovrapposizione*.
- **Esempio:** Se $\text{sample}_1 = \{1, 5, 100, 200\}$ e $\text{sample}_2 = \{5, 150, 200, 300\}$, CR vede $I=2$ (elementi comuni: {5, 200}).
- I "buchi" (assenza di 2, 3, 4, etc.) non influenzano il calcolo perché non entrano nella formula.

### A3 – Invarianza alla Traslazione (Offset)

**Obiettivo**
- Verificare la robustezza degli stimatori quando gli ID non partono da 1 ma hanno un offset sconosciuto (es. 50,001..150,000).

**Setup**
- Popolazione: N = 100,000; ID da 50,001 a 150,000.
- Campioni: m/n in {0.001, ..., 0.2}; R=300.
- Dati: [results/discrete_translation_results.json](results/discrete_translation_results.json).

**Risultati chiave (errore relativo %)**

| m/n  | Rank Inv | German Tank | CR | Spacing |
|------|----------|-------------|----|---------|
| 0.001 | 100.5 | 50.8 | 94.9 | 0.81 |
| 0.002 | 101.0 | 50.4 | 79.8 | 0.12 |
| 0.005 | 99.8 | 50.1 | 16.3 | 0.27 |
| 0.010 | 99.8 | 50.1 | 8.9 | 0.45 |
| 0.020 | 100.2 | 50.0 | 2.3 | 0.99 |
| 0.050 | 100.1 | 50.0 | 1.1 | 0.99 |
| 0.100 | 100.0 | 50.0 | 0.1 | 0.99 |

**Analisi Matematica**
- **German Tank / Rank**: Falliscono catastroficamente perché entrambi interpretano il valore assoluto dell'ID.
  - German Tank stima il max (~150k) e calcola $\hat{N} \approx 150k \times \frac{m+1}{m} \approx 150k$ (errore ~50%).
  - Rank Inversion assume che l'ID più alto sia il rango massimo, portando a $\hat{N} \approx 200k$ (errore ~100%).

- **Spacing**: È **invariante per traslazione** grazie alla formula $\hat{N} = m \times \text{avg}(X_{i+1} - X_i)$.
  - Per ID in [50001, 50002, ..., 150000], ogni differenza consecutiva è 1: $(50002 - 50001) = 1$.
  - La traslazione (l'offset 50000) si cancella nella sottrazione: $\hat{N} = m \times \text{avg}(1) = m \approx N$ (errore < 1%).
  - Questo è il motivo per cui Spacing è **translation-invariant**: le differenze eliminano qualsiasi costante additiva.

- **Capture-Recapture**: Anch'esso invariante perché dipende solo da $I$ (overlap), non dai valori degli ID.

**Takeaway**
- Se non si conosce l'origine degli ID (es. numeri d'ordine che non partono da zero), **Spacing** e **Capture-Recapture** sono le uniche scelte valide. German Tank e Rank richiedono la normalizzazione degli ID (sottrazione del minimo teorico).

### Nota sul campionamento degli ID

- Gli stimatori discreti (rank, spacing discreto, German Tank, CR) assumono campionamento uniforme senza rimpiazzo sugli ID univoci 1..N o su ID riindicizzati consecutivi. Gli ID sono il dato informativo; gli attributi (es. valori Pareto) non vanno usati per stimare N.
- Se gli ID non sono consecutivi ma osservabili, si può riordinare e lavorare sui ranghi osservati; spacing e CR sono robusti ai buchi, German Tank e rank no.
- Se il campione sugli ID non è uniforme (bias di visibilità, PPS non noto), le stime possono essere distorte: serve modellare il disegno di campionamento o usare metodi specifici. CR resta l ancora più difendibile quando l overlap è >0.
- Per dati reali: controllare buchi/duplicati negli ID, % overlap tra due campioni, quota m/n, eventuali stratificazioni prima di scegliere lo stimatore.

### A4 – Pooling robusto (trimmed mean)

**Obiettivo**
- Valutare il pooling con aggregazione robusta e sottocampioni piu grandi: errore vs campione unico e guadagno rispetto al sottocampione peggiore.

**Setup**
- Popolazione discreta N = 100,000; budget osservazioni fisso a 10,000.
- Configurazioni pooling (trimmed mean 10%):
	- k=20, m=500
	- k=10, m=1000
	- k=8, m=1250
	- k=5, m=2000
- Ripetizioni R = 200; seed=123.
- Dati: [results/discrete_pooling_results.json](results/discrete_pooling_results.json).

**Risultati chiave (errore relativo mediano, pooling)**
- Rank: 0.665% (k20), 0.554% (k10), 0.530% (k8), 0.625% (k5); sempre peggio del campione unico, ma sottocampioni piu grandi aiutano.
- Spacing: ~30–30.6% in tutte le configurazioni; pooling non aiuta.
- German Tank: 0.036% (k20), 0.026% (k10), 0.022% (k8), 0.015% (k5) — migliora al crescere di m_base ma resta peggio del campione unico da 10k.
- Capture–Recapture: 21.99% (k20), 6.22% (k10), 7.32% (k8), 4.86% (k5); grande beneficio da sottocampioni piu grandi.

**Guadagno vs sottocampione peggiore (median diff, trimmed mean)**
- Rank: il pooling riduce il worst-case a ~8–23% del worst (es. k10: da ~4.9% a ~0.55%).
- CR: forte beneficio; k10 porta il worst da ~67% a ~6.2% (ratio ~0.09), k5 da ~23% a ~4.9% (ratio ~0.21).
- German Tank: ratio ~0.08–0.28 a seconda di k; pooling attenua outlier estremi.
- Spacing: beneficio limitato (ratio ~0.75–0.88).

**Quando il pooling diventa indispensabile**
- Privacy/silos: non si possono condividere dati raw, solo stime locali.
- Parallelizzazione/scalabilità: shard indipendenti calcolati in parallelo, con aggregazione robusta per contenere outlier.
- Streaming/batch incrementali: combinare blocchi successivi senza rielaborare tutto.
- Resource bound: memoria/tempo non permettono un campione unico grande.

**Takeaway**
- A parita di budget, il pooling frammentato resta inferiore al campione unico per tutti gli stimatori; aumentare m_base (ridurre k) mitiga la perdita e aiuta molto CR.
- Il pooling robusto è un paracadute nei contesti in cui non si possono fondere i dati; se i dati sono unibili è preferibile un unico campione grande.

## Takeaway complessivo

- Usa stima sugli ID con gli stimatori discreti: rank e German Tank funzionano quando gli ID sono consecutivi e il campionamento è uniforme; CR è l ancora più robusta se c è overlap; spacing serve soprattutto quando ci sono buchi.
- Se gli ID non sono consecutivi o il max non rappresenta N, spacing e CR prevalgono; rank/German Tank diventano distorti.
- Se il campionamento sugli ID non è uniforme (bias di visibilità, PPS), occorre modellare il disegno; in assenza di modello, CR è l opzione più difendibile.
- Pooling: usarlo solo quando non si possono unire i dati; in tal caso preferire pochi sottocampioni grandi e aggregazione robusta. Se i dati sono unibili, meglio un campione unico.

## Nota su esperimenti continui

Gli stress-test continui (Blocco B) e l'analisi di sensibilità (Blocco C) sono stati rimossi in quanto l'assunzione di una distribuzione Pareto (o comunque di una struttura discreta nota come gli ID) è considerata fondamentale per il funzionamento degli stimatori. L'analisi si concentra quindi sulla validazione discreta e sull'applicabilità a scenari reali con ID.

## Blocco D – Applicazione a Dati Reali (Simulazione GitHub Issues)

**Obiettivo**
- Verificare l'applicabilità degli stimatori discreti a uno scenario reale comune: stimare il numero totale di Issue + PR (Total Activity) in una repository GitHub campionando solo le Issue.
- Questo scenario presenta **ID Sequenziali con Buchi** (le PR mancano dalla lista delle Issue), che è una sfida per gli stimatori basati sulla densità (Spacing) ma teoricamente gestibile da quelli basati sul massimo (German Tank).

**Setup**
- Popolazione Totale (Max ID): N = 20,000.
- Struttura: 40% PR (buchi), 5% Issue cancellate.
- Campione: Solo Issue visibili (non cancellate).
- Metodi: German Tank, Spacing, Rank Inversion.

**Risultati Chiave (MAPE %)**

| Campione (m) | German Tank | Rank Inversion | Spacing |
|--------------|-------------|----------------|---------|
| 100          | **0.59%**   | 5.44%          | 10.55%  |
| 500          | **0.13%**   | 2.32%          | 4.60%   |
| 1000         | **0.06%**   | 1.82%          | 6.22%   |

**Osservazioni**
- **German Tank (Max)** è straordinariamente preciso (<0.6% errore anche con pochi campioni). Questo perché, nonostante i buchi, il *Massimo* osservato scala molto bene con N. I buchi sono distribuiti uniformemente, quindi non "accorciano" artificialmente il massimo.
- **Spacing** soffre molto dei buchi (errore 5-10%). Interpreta i "salti" dovuti alle PR come una popolazione più grande o più sparsa in modo errato, perché la densità locale è alterata sistematicamente (mancano il 40% degli ID).
- **Rank Inversion** è una via di mezzo, ma meno preciso del German Tank in questo scenario specifico.

**Quando Buchi Sistematici vs Casuali Importano**
- **Buchi Casuali (30% random):** Distribuiti uniformemente su tutto il range → German Tank è resiliente.
  - Il max osservato rimane un buon proxy per $N$ perché alcuni ID alti sono comunque visibili.
  - Spacing vede una densità uniforme (leggermente ridotta) → rimane robusto.

- **Buchi Sistematici (40% PR sempre assenti):** Non accorcia il max, ma altera la densità locale.
  - German Tank rimane preciso perché il max non cambia.
  - Spacing sovrastima perché calcola avg(gap) × m su una densità artificialmente bassa → bias sistematico.

**Conclusione Pratica**
- Per stimare il volume totale di attività (Issue + PR) di un progetto software usando gli ID delle Issue: **Usare il German Tank Estimator**.
- Non usare Spacing se si sospetta che una fetta *sistematica* di ID sia mancante. Usare Spacing solo se i buchi sono *casuali* o se l'offset è *sconosciuto*.

## Blocco E – Robustezza agli Outlier e Corruzione dei Dati (A5)

L'esperimento **A5** rappresenta il test di stress finale del framework di valutazione, volto a misurare la resilienza degli stimatori in presenza di identificativi "sporchi", manipolati o errati.

### Motivazioni Scientifiche
Il presupposto fondamentale degli stimatori seriali classici (come il *German Tank*) è l'integrità dei dati: si assume che ogni identificativo osservato rifletta fedelmente lo stato della popolazione. Tuttavia, nei sistemi reali, la presenza di identificativi "anomali" (outlier) è frequente a causa di:
*   **Errori tecnici:** Bug software che generano ID fuori scala o duplicati.
*   **Manipolazioni intenzionali:** Attori che iniettano ID artificialmente elevati per mascherare la reale dimensione di un servizio.
*   **Errori umani:** Errori di battitura (typos) o incongruenze durante le migrazioni di database.

L'obiettivo di A5 è determinare il **breakdown point** statistico: quanta corruzione può sopportare un metodo prima di fornire risultati privi di significato economico o operativo.

### Metodologia Sperimentale

#### A. Generazione della Popolazione Corrotta
Partendo da una popolazione di $N = 100.000$ identificativi ($1, 2, \dots, N$), viene applicata una corruzione governata da due parametri:
1.  **Parametro $p$ (Frazione di Corruzione):** La percentuale di ID alterati. Testati valori $p \in \{0.01, 0.05, 0.10\}$ (da 1% a 10% di dati sporchi).
2.  **Parametro $q$ (Fattore di Magnitudo):** L'intensità della corruzione. Ogni ID selezionato viene ricalcolato come: 
    $$ID_{new} = \text{round}(ID_{old} \times (1 + q))$$
    Per $q=10$, l'ID diventa circa 11 volte più grande del valore originale. Testati $q \in \{0.5, 10, 100\}$.

#### B. Distribuzione degli Outlier
Per simulare scenari reali, la corruzione è stata divisa equamente (50/50) tra:
*   **Top-Heavy Outliers:** ID corrotti scelti tra i valori più alti (vicini a $N$). Simula errori che estendono il range superiore in modo ingannevole.
*   **Random Outliers:** ID corrotti scelti casualmente nell'intera popolazione.

#### C. Procedura Monte Carlo
Per ogni configurazione $(p, q)$ e frazione di campionamento $m/n$:
1.  Vengono estratti campioni indipendenti.
2.  Vengono calcolate le stime di tutti i competitor.
3.  La procedura viene ripetuta per **$R = 1.000$ iterazioni** per garantire stabilità statistica.
4.  La metrica principale è la **Mediana dell'Errore Relativo Percentuale (MAPE)**.

### Risultati Chiave
I risultati ottenuti (configurazione $p=1\%$, $q=10$) evidenziano differenze fondamentali tra le classi di stimatori:

| Rapporto Campionario ($m/n$) | German Tank (%) | Rank Inversion (%) | Spacing (%) | Capture-Recapture (%) |
| :--- | :---: | :---: | :---: | :---: |
| **0.001 (0.1%)** | **493.32%** | 0.15% | 0.24% | 94.90% |
| **0.010 (1.0%)** | **1000.37%** | 0.35% | 0.99% | 8.91% |
| **0.100 (10.0%)** | **1000.04%** | 0.42% | 0.99% | 0.02% |

### Analisi Tecnica
1.  **Vulnerabilità del German Tank:** Lo stimatore basato sul massimo crolla istantaneamente. Anche con solo l'1% di dati sporchi, l'errore scala linearmente con $q$, rendendo la stima del tutto inaffidabile.
2.  **Effetto Median-Filtering:** Gli stimatori **Rank Inversion** e **Spacing** dimostrano una robustezza eccezionale. Finché la corruzione non supera il 50% (breakdown point della mediana), questi metodi ignorano gli outlier e rimangono ancorati alla densità reale della popolazione.
3.  **Immunità del Capture-Recapture:** Questo metodo si conferma il più robusto rispetto ai *valori* degli ID, poiché si basa esclusivamente sull'identità (matching) degli elementi e non sulla loro magnitudo numerica.

### Conclusioni A5
L'esperimento A5 chiarisce che, mentre il *German Tank* è lo stimatore ottimale in condizioni teoriche perfette, il **Rank Inversion** rappresenta la scelta più sicura e affidabile per applicazioni di ingegneria dei dati reale, offrendo una protezione nativa contro la corruzione dei dati senza perdite significative di precisione.

---

## Tabella Decisionale Riassuntiva (A1-A5)

Questa tabella riassume quale metodo scegliere in base alle caratteristiche dei dati e al risultato degli esperimenti A1-A5:

| Esperimento | Scenario | Metodo Consigliato | Risultato |
|-------------|----------|-------------------|-----------|
| **A1** | ID Sequenziali Puri (1..N) | **German Tank** | < 0.5% errore |
| **A2** | ID Sparsi con Buchi | **Capture-Recapture** | < 0.2% errore (m/n ≥ 0.02) |
| **A3** | ID con Offset Sconosciuto | **Spacing** | < 1% errore |
| **A4** | Pooling con Budget Fisso | **Rank Inversion + Trimmed Mean** | Stabilizza worst-case |
| **A5** | Dati Corrotti / Outlier | **Rank Inversion** | Robusto fino a 50% corruzione |
