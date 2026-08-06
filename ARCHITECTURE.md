# Architettura di RaceEngineer

## Stato del documento

Questa architettura descrive la direzione iniziale del progetto.

I formati dei file, il protocollo di telemetria reale e le librerie concrete
non sono ancora stati scelti.

Gran Turismo 7 è un candidato da sottoporre a verifica tecnica e non è ancora
una dipendenza dell'architettura.

## Tecnologia iniziale

Il linguaggio iniziale del progetto è Python.

Python è stato scelto per:

- rapidità di sviluppo;
- compatibilità con Raspberry Pi;
- integrazione con AI, Ollama, STT e TTS;
- disponibilità di un ampio ecosistema di librerie.

Questa scelta non costituisce un vincolo permanente.

I confini tra i moduli dovranno permettere di sostituire in futuro singole
implementazioni Python con moduli C++ o Rust, qualora le misure dimostrino
che ciò è necessario per rispettare i requisiti di prestazioni, stabilità o
reattività.

La sostituzione di un modulo non dovrà modificare il comportamento osservabile
del core né introdurre dipendenze da uno specifico simulatore.

## Obiettivi architetturali

L'architettura deve garantire:

- funzionamento locale senza servizi cloud obbligatori;
- indipendenza dal PC di sviluppo;
- esecuzione iniziale su Raspberry Pi 3B+;
- sviluppo e validazione del core senza un simulatore collegato;
- separazione tra simulatori e logica centrale;
- comportamento deterministico per le decisioni critiche;
- possibilità di testare tutto con telemetria sintetica o registrata;
- sostituibilità dei sistemi di input, output e persistenza;
- possibilità di sostituire singoli moduli Python con implementazioni C++ o
  Rust;
- degradazione controllata dei componenti opzionali;
- raccolta di dati diagnostici e misure prestazionali.

## Principi architetturali

### Performance first

Ogni componente e ogni nuova funzionalità devono essere valutati anche
rispetto alle risorse disponibili sull'hardware di riferimento.

Le priorità del sistema sono, nell'ordine:

1. stabilità;
2. affidabilità;
3. funzionalità aggiuntive.

La reattività del percorso principale non deve essere sacrificata per
aggiungere caratteristiche non essenziali.

Ottimizzazioni e sostituzioni tecnologiche devono essere guidate da misure
reali. Se un modulo Python non raggiunge le prestazioni necessarie, la sua
implementazione potrà essere sostituita con C++ o Rust mantenendone invariati
confini e responsabilità.

### Core indipendente dal simulatore

Il core non deve conoscere protocolli, pacchetti o comportamenti specifici
di un simulatore.

Telemetria sintetica, telemetria registrata e telemetria reale devono
raggiungere il core attraverso la stessa rappresentazione interna.

Questo permette di sviluppare, testare e validare completamente il core
prima di collegare una sorgente reale.

### Decisioni critiche deterministiche

Le decisioni critiche durante una sessione devono essere prodotte da regole
esplicite, verificabili e ripetibili.

Un eventuale LLM non appartiene al percorso critico.

## Fuori ambito per il primo prototipo

Non fanno parte del primo prototipo:

- riconoscimento vocale;
- conversazione tramite LLM;
- dipendenze cloud;
- strategie avanzate di gara;
- profilazione adattiva del pilota;
- dashboard completa;
- gestione musicale;
- supporto contemporaneo a più simulatori.

## Struttura logica

Il sistema è suddiviso nei seguenti livelli:

1. sorgenti di telemetria;
2. normalizzazione;
3. stato della sessione;
4. motore deterministico;
5. messaggi e priorità;
6. sistemi di output;
7. persistenza e diagnostica;
8. moduli opzionali.

Il flusso principale è:

Sorgente telemetria
→ adattatore
→ modello interno normalizzato
→ stato della sessione
→ motore di regole
→ evento o avviso
→ output locale e log

## Sorgenti di telemetria

Una sorgente produce campioni di telemetria senza conoscere le regole di
gara.

Le prime sorgenti previste sono:

### Telemetria sintetica

Genera scenari controllati per testare casi normali ed eccezioni.

Deve permettere di riprodurre più volte lo stesso scenario.

### Telemetria registrata

Legge una registrazione locale e la riproduce mantenendo o simulando la
sequenza temporale originale.

Deve supportare almeno:

- avvio;
- pausa;
- arresto;
- velocità di riproduzione controllabile;
- ripetibilità dello stesso test.

### Telemetria reale

Riceve dati via rete locale dal simulatore o dalla console.

Il primo possibile adattatore reale sarà valutato per Gran Turismo 7, ma
verrà implementato soltanto dopo:

1. lo sviluppo del core;
2. la validazione con telemetria sintetica;
3. la validazione con telemetria registrata;
4. la verifica dell'output vocale locale;
5. la validazione completa del core sul Raspberry Pi 3B+;
6. una verifica tecnica specifica del simulatore.

Ogni simulatore dovrà avere un adattatore separato.

## Modello interno normalizzato

Gli adattatori convertono i dati esterni in un formato interno indipendente
dal simulatore.

Il modello dovrà distinguere almeno:

- timestamp della sorgente, quando disponibile;
- timestamp di ricezione;
- identità o tipo della sorgente;
- stato della sessione;
- numero del giro;
- tempo sul giro, quando disponibile;
- carburante, quando disponibile;
- validità e qualità del campione;
- campi assenti o non supportati.

L'elenco definitivo dei campi verrà definito durante il prototipo.

Il core non deve interpretare direttamente pacchetti o formati specifici di
un simulatore.

## Stato della sessione

Questo componente costruisce una vista coerente della sessione a partire dai
campioni ricevuti.

Le sue responsabilità includono:

- identificare inizio e fine della sessione;
- mantenere l'ultimo stato valido;
- riconoscere transizioni di giro;
- gestire dati mancanti, duplicati o fuori ordine;
- esporre al motore di regole uno stato consistente.

## Motore deterministico

Il motore valuta regole esplicite sullo stato della sessione.

Ogni regola deve avere:

- input dichiarati;
- condizioni verificabili;
- risultato prevedibile;
- priorità;
- meccanismo per evitare avvisi ripetuti inutilmente;
- test costruibili con telemetria sintetica o registrata.

Il motore non dipende da un LLM.

Le decisioni critiche devono rimanere disponibili anche quando audio,
rete Internet o moduli opzionali non funzionano.

## Eventi, avvisi e priorità

Il risultato del motore non viene inviato direttamente al TTS.

Viene prima rappresentato come evento o avviso strutturato contenente almeno:

- tipo;
- timestamp;
- priorità;
- dati che hanno causato l'avviso;
- messaggio predefinito o identificatore del messaggio;
- stato di consegna.

Questa separazione permette di usare lo stesso avviso per log, testo, audio
o future interfacce.

## Output

Gli output sono adattatori indipendenti.

### Output testuale

È obbligatorio nel primo prototipo per debug e test automatici.

### Log locale

Registra eventi, avvisi, errori e metriche diagnostiche.

### TTS locale

Converte messaggi approvati in audio senza richiedere servizi cloud.

Il motore di TTS non è ancora stato scelto.

Un guasto del TTS non deve arrestare la ricezione o l'analisi della
telemetria.

## Persistenza

Nel primo prototipo la persistenza può essere basata su file locali.

Dovrà conservare almeno:

- log applicativi;
- eventi riconosciuti;
- avvisi prodotti;
- errori;
- metriche essenziali;
- informazioni necessarie a riprodurre un test.

La necessità di un database verrà valutata solo quando emergeranno requisiti
concreti per sessioni, setup e profili del pilota.

## Moduli LLM opzionali

Un LLM non fa parte del core e non si trova nel percorso critico.

Potrà ricevere copie di eventi o riepiloghi già prodotti dal sistema
deterministico, ma non sostituirà le regole responsabili degli avvisi
critici.

L'interfaccia LLM dovrà:

- essere disattivabile;
- non bloccare il core;
- tollerare indisponibilità ed errori;
- distinguere chiaramente contenuto deterministico e contenuto generato;
- non rendere obbligatoria una connessione cloud.

## Gestione degli errori

Il sistema deve degradare in modo controllato.

Esempi:

- perdita della telemetria: segnalazione e attesa della sorgente;
- pacchetto non valido: scarto controllato e log;
- campo assente: valore non disponibile, senza inventare dati;
- errore TTS: conservazione dell'avviso nel log e nell'output testuale;
- modulo opzionale non disponibile: continuazione del core;
- risorse hardware insufficienti: metrica e segnalazione diagnostica.

## Prestazioni

Il Raspberry Pi 3B+ è il banco di prova iniziale.

La validazione completa del core sul Raspberry Pi 3B+ deve avvenire prima
della scelta e dell'implementazione dell'adattatore per il primo simulatore
reale.

La validazione userà telemetria sintetica e registrata e dovrà misurare:

- uso della CPU;
- uso della memoria;
- latenza tra campione ed evento;
- latenza tra evento e avviso;
- perdita di campioni;
- stabilità durante esecuzioni prolungate;
- utilizzo dello spazio locale.

Le soglie di accettazione verranno definite dopo le prime misure, senza
assumerle in anticipo.

Se le prestazioni di un singolo modulo Python risultassero insufficienti,
sarà possibile valutarne la sostituzione con un'implementazione C++ o Rust
senza modificare l'architettura generale.

## Verifica tecnica di Gran Turismo 7

Prima di dichiarare il supporto a Gran Turismo 7 sarà necessario verificare:

- come viene trasmessa la telemetria;
- quali piattaforme e configurazioni sono supportate;
- quali campi sono disponibili;
- frequenza e latenza dei dati;
- comportamento in caso di perdita o riordinamento dei pacchetti;
- identificazione di sessione, giro e vettura;
- eventuali trasformazioni o decodifiche necessarie;
- stabilità tra aggiornamenti del gioco;
- compatibilità con Raspberry Pi 3B+;
- aspetti di licenza, distribuzione e documentazione.

Questa verifica avverrà dopo la validazione completa del core sul Raspberry
Pi 3B+.

Il risultato dovrà essere documentato prima di trasformare GT7 in un
requisito definitivo.

## Sicurezza e privacy

Il funzionamento base deve restare confinabile alla rete locale.

I dati delle sessioni devono essere conservati localmente per impostazione
predefinita.

Qualsiasi futura trasmissione a servizi esterni dovrà essere opzionale,
esplicita e documentata.

## Indipendenza dalla Companion AI

RaceEngineer e Companion AI sono progetti distinti.

Il core di RaceEngineer non deve importare direttamente il progetto privato
né dipendere dal suo ambiente di esecuzione.

Eventuali componenti condivisi dovranno avere:

- confini chiari;
- licenza compatibile;
- dipendenze documentate;
- possibilità di essere usati e testati autonomamente.
