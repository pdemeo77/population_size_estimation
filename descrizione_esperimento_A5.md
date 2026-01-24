# Esperimento A5: Robustezza agli Outlier e Corruzione dei Dati

L'esperimento **A5** rappresenta il test di stress finale del framework di valutazione, volto a misurare la resilienza degli stimatori in presenza di identificativi "sporchi", manipolati o errati.

---

## 1. Motivazioni Scientifiche
Il presupposto fondamentale degli stimatori seriali classici (come il *German Tank*) è l'integrità dei dati: si assume che ogni identificativo osservato rifletta fedelmente lo stato della popolazione. Tuttavia, nei sistemi reali, la presenza di identificativi "anomali" (outlier) è frequente a causa di:
*   **Errori tecnici:** Bug software che generano ID fuori scala o duplicati.
*   **Manipolazioni intenzionali:** Attori che iniettano ID artificialmente elevati per mascherare la reale dimensione di un servizio.
*   **Errori umani:** Errori di battitura (typos) o incongruenze durante le migrazioni di database.

L'obiettivo di A5 è determinare il **breakdown point** statistico: quanta corruzione può sopportare un metodo prima di fornire risultati privi di significato economico o operativo.

---

## 2. Metodologia Sperimentale (Setup di Simulazione)
L'esperimento è stato condotto tramite lo script `run_robustness_outliers.py` seguendo una procedura rigorosa:

### A. Generazione della Popolazione Corrotta
Partendo da una popolazione di $N = 100.000$ identificativi ($1, 2, \dots, N$), viene applicata una corruzione governata da due parametri:
1.  **Parametro $p$ (Frazione di Corruzione):** La percentuale di ID alterati. Testati valori $p \in \{0.01, 0.05, 0.10\}$ (da 1% a 10% di dati sporchi).
2.  **Parametro $q$ (Fattore di Magnitudo):** L'intensità della corruzione. Ogni ID selezionato viene ricalcolato come: 
    $$ID_{new} = \text{round}(ID_{old} \times (1 + q))$$
    Per $q=10$, l'ID diventa circa 11 volte più grande del valore originale. Testati $q \in \{0.5, 10, 100\}$.

### B. Distribuzione degli Outlier
Per simulare scenari reali, la corruzione è stata divisa equamente (50/50) tra:
*   **Top-Heavy Outliers:** ID corrotti scelti tra i valori più alti (vicini a $N$). Simula errori che estendono il range superiore in modo ingannevole.
*   **Random Outliers:** ID corrotti scelti casualmente nell'intera popolazione.

### C. Procedura Monte Carlo
Per ogni configurazione $(p, q)$ e frazione di campionamento $m/n$:
1.  Vengono estratti campioni indipendenti.
2.  Vengono calcolate le stime di tutti i competitor.
3.  La procedura viene ripetuta per **$R = 1.000$ iterazioni** per garantire stabilità statistica.
4.  La metrica principale è la **Mediana dell'Errore Relativo Percentuale (MAPE)**.

---

## 3. Risultati e Commento Dettagliato
I risultati ottenuti (configurazione $p=1\%$, $q=10$) evidenziano differenze fondamentali tra le classi di stimatori:

| Rapporto Campionario ($m/n$) | German Tank (%) | Rank Inversion (%) | Spacing (%) | Capture-Recapture (%) |
| :--- | :---: | :---: | :---: | :---: |
| **0.001 (0.1%)** | **493.32%** | 0.15% | 0.24% | 94.90% |
| **0.010 (1.0%)** | **1000.37%** | 0.35% | 0.99% | 8.91% |
| **0.100 (10.0%)** | **1000.04%** | 0.42% | 0.99% | 0.02% |

### Analisi Tecnica:
1.  **Vulnerabilità del German Tank:** Lo stimatore basato sul massimo crolla istantaneamente. Anche con solo l'1% di dati sporchi, l'errore scala linearmente con $q$, rendendo la stima del tutto inaffidabile.
2.  **Effetto Median-Filtering:** Gli stimatori **Rank Inversion** e **Spacing** dimostrano una robustezza eccezionale. Finché la corruzione non supera il 50% (breakdown point della mediana), questi metodi ignorano gli outlier e rimangono ancorati alla densità reale della popolazione.
3.  **Immunità del Capture-Recapture:** Questo metodo si conferma il più robusto rispetto ai *valori* degli ID, poiché si basa esclusivamente sull'identità (matching) degli elementi e non sulla loro magnitudo numerica.

---

## 3.1 Visualizzazione dei Risultati (Analisi delle Figure)
L'esperimento produce **9 figure** (corrispondenti alle combinazioni della matrice $p \times q$), che permettono di osservare visivamente le dinamiche di fallimento e successo:

*   **Scala Log-Log:** L'uso di scale logaritmiche su entrambi gli assi è necessario per apprezzare il distacco tra gli stimatori. Spesso il *German Tank* si colloca ordini di grandezza sopra gli altri.
*   **Divergenza Lineare:** Nelle figure con $q$ elevato (10x, 100x), la curva del *German Tank* appare come una retta orizzontale o leggermente crescente ad altissimo errore, indicando che la stima è dominata esclusivamente dal valore degli outlier e non beneficia minimamente dell'aumento del campione.
*   **Convergenza Robusta:** Le curve di *Rank Inversion* e *Spacing* mantengono invece un trend decrescente coerente con quello degli esperimenti in condizioni ideali, dimostrando che i metodi basati sulla mediana riescono a "filtrare" il rumore e convergere verso il valore vero all'aumentare delle osservazioni.
*   **Incrocio delle Prestazioni:** I grafici evidenziano il punto di incrocio dove il *Capture-Recapture* (inizialmente affetto da alta varianza per campioni piccoli) diventa più preciso del *Rank Inversion*, fornendo una guida visiva per la scelta dello stimatore in base al budget di campionamento disponibile.

---

## 4. Conclusioni
L'esperimento A5 chiarisce che, mentre il *German Tank* è lo stimatore ottimale in condizioni teoriche perfette, il **Rank Inversion** rappresenta la scelta più sicura e affidabile per applicazioni di ingegneria dei dati reale, offrendo una protezione nativa contro la corruzione dei dati senza perdite significative di precisione.
