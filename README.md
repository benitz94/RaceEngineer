# RaceEngineer

RaceEngineer nasce dall'idea di portare un vero ingegnere di pista personale
accanto al pilota, privilegiando affidabilità, replicabilità e funzionamento
locale rispetto alla complessità tecnologica.

Lo scopo del progetto non è dimostrare l'uso dell'intelligenza artificiale,
ma costruire uno strumento realmente utile durante una sessione di guida.

RaceEngineer è un progetto locale e open source per il sim racing.

Il suo obiettivo è ricevere la telemetria di un simulatore, analizzarla con
logica deterministica e fornire al pilota informazioni utili durante e dopo
la sessione.

Il progetto è pensato come una piattaforma autonoma e replicabile, eseguibile
inizialmente su Raspberry Pi 3B+.

## Stato del progetto

RaceEngineer è attualmente in fase di progettazione e prototipazione.

Non esiste ancora una prima versione utilizzabile.

Gran Turismo 7 è il simulatore iniziale candidato, ma il suo supporto non è
ancora un requisito definitivo. Prima sarà necessario verificare
tecnicamente disponibilità, formato, stabilità e condizioni d'uso della
telemetria.

Il core sarà sviluppato, testato e validato inizialmente usando telemetria
sintetica o registrata, senza richiedere un collegamento a un simulatore
reale.

## Tecnologia iniziale

Il linguaggio iniziale del progetto è Python.

La scelta è motivata da:

- rapidità di sviluppo;
- compatibilità con Raspberry Pi;
- integrazione con AI, Ollama, STT e TTS;
- disponibilità di un ampio ecosistema di librerie.

Python è la tecnologia iniziale del progetto, non un vincolo permanente.

L'architettura dovrà permettere di sostituire in futuro singoli moduli con
implementazioni in C++ o Rust, qualora misure reali dimostrino che le
prestazioni lo rendono necessario.

## Obiettivi

RaceEngineer dovrà poter:

- funzionare senza dipendere dal PC utilizzato per lo sviluppo;
- funzionare senza servizi cloud obbligatori;
- ricevere telemetria via rete locale da una console o da un simulatore;
- analizzare la telemetria completamente in locale;
- generare avvisi tramite regole deterministiche e verificabili;
- riprodurre avvisi vocali locali;
- conservare dati utili delle sessioni;
- essere esteso in futuro a più simulatori e piattaforme hardware;
- essere installato e replicato seguendo la documentazione ufficiale.

## Principi del progetto

### Utilità prima della complessità

RaceEngineer deve essere prima di tutto uno strumento utile durante una
sessione di guida.

Tecnologie, AI e funzionalità aggiuntive hanno valore soltanto quando
migliorano concretamente l'esperienza del pilota senza compromettere il
funzionamento del sistema.

### Locale prima di tutto

Il core deve continuare a funzionare senza connessione Internet.

Eventuali integrazioni online dovranno essere facoltative e non dovranno
essere necessarie per le funzioni principali.

### Nessun LLM nel percorso critico

RaceEngineer non richiede un LLM per analizzare la telemetria o prendere
decisioni critiche durante la gara.

Un eventuale LLM potrà essere aggiunto come modulo opzionale per funzioni
come:

- riformulazione naturale dei messaggi;
- spiegazioni dopo la sessione;
- conversazione;
- consultazione assistita dei dati.

L'assenza o il malfunzionamento dell'LLM non dovrà impedire al core di
funzionare.

### Performance first

Ogni nuova funzionalità deve essere valutata anche rispetto alle risorse
disponibili sull'hardware di riferimento.

L'ordine delle priorità è:

1. stabilità;
2. affidabilità;
3. funzionalità aggiuntive.

RaceEngineer non deve sacrificare la reattività del sistema per aggiungere
caratteristiche non essenziali.

### Indipendenza dal simulatore

Il core deve poter essere sviluppato, testato e validato completamente senza
un simulatore collegato.

Le integrazioni con i simulatori devono essere realizzate tramite adattatori
separati e non devono introdurre logica specifica nel core.

### Indipendenza dall'hardware

La piattaforma iniziale è Raspberry Pi 3B+, ma l'architettura non deve
dipendere da uno specifico modello di computer.

L'hardware potrà evolvere sulla base di misure reali di prestazioni e
necessità.

Allo stesso modo, singoli moduli Python potranno essere sostituiti in futuro
da implementazioni C++ o Rust senza richiedere la riscrittura dell'intero
sistema.

### Modularità

Le sorgenti di telemetria, il core di analisi, la persistenza e i sistemi di
output devono essere separati.

Aggiungere un nuovo simulatore, cambiare il sistema audio o sostituire
l'implementazione di un modulo non dovrebbe richiedere la riscrittura della
logica principale.

### Replicabilità

Il progetto non distribuirà soltanto codice.

Hardware, sistema operativo, installazione, configurazione e problemi noti
dovranno essere documentati in modo che un altro utente possa costruire un
sistema funzionante senza assistenza diretta.

## Primo prototipo

Il primo prototipo sarà una pipeline locale minima:

1. caricare o generare telemetria;
2. riprodurla con tempi controllati;
3. convertirla in un formato interno comune;
4. aggiornare lo stato della sessione;
5. riconoscere almeno un evento tramite una regola deterministica;
6. produrre un avviso testuale;
7. quando disponibile, riprodurre lo stesso avviso tramite TTS locale;
8. registrare eventi, avvisi e dati diagnostici.

Il prototipo non includerà inizialmente:

- riconoscimento vocale;
- LLM;
- servizi cloud obbligatori;
- dashboard completa;
- strategie avanzate;
- memoria adattiva del pilota;
- gestione musicale;
- supporto simultaneo a più simulatori.

## Hardware iniziale previsto

Banco di prova iniziale:

- Raspberry Pi 3B+;
- alimentatore;
- microSD, capacità e classe da definire;
- connessione Ethernet o Wi-Fi;
- microfono USB lavalier, non necessario per il primo prototipo;
- DAC USB verso mixer;
- mixer audio;
- cuffie;
- eventuale dissipatore o ventola.

Modelli, alternative, obbligatorietà e configurazione dei componenti saranno
documentati durante lo sviluppo.

## Documentazione

- `PROJECT_JOURNAL.md`: origine, intenzioni e motivazioni delle decisioni;
- `ARCHITECTURE.md`: componenti, confini e flussi del sistema;
- `ROADMAP.md`: fasi di sviluppo e criteri di completamento;
- `AGENTS.md`: regole operative per chi lavora nel repository.

`PROJECT_JOURNAL.md` è la fonte principale per l'intento e la storia delle
decisioni.

## Progetti separati

RaceEngineer non è la Companion AI nata dagli esperimenti con
Open-LLM-VTuber.

I due progetti devono rimanere indipendenti. Eventuale codice riutilizzato
dovrà essere importato in modo esplicito, documentato e compatibile con la
licenza scelta per RaceEngineer.

## Licenza

Il repository è destinato a essere open source.

La licenza non è ancora stata scelta.
