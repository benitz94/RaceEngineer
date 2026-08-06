# Roadmap di RaceEngineer

## Principi

La roadmap procede per verifiche progressive.

Ogni fase deve produrre un risultato osservabile e documentato prima di
aggiungere complessità.

Il core deve essere sviluppato, testato e validato completamente senza
dipendere da un simulatore collegato.

Gran Turismo 7 rimane un candidato finché la verifica tecnica non ne
confermerà la fattibilità.

Il linguaggio iniziale del progetto è Python. Singoli moduli potranno essere
sostituiti in futuro con implementazioni C++ o Rust se misure reali ne
dimostreranno la necessità.

Durante tutte le fasi, le priorità sono:

1. stabilità;
2. affidabilità;
3. funzionalità aggiuntive.

La reattività non deve essere sacrificata per caratteristiche non essenziali.

## Fase 0 — Documentazione e fondamenta del progetto

Obiettivo: rendere espliciti scopo, vincoli e criteri decisionali prima
dell'implementazione.

Attività:

- completare README, ARCHITECTURE e ROADMAP;
- registrare nel PROJECT_JOURNAL le decisioni approvate;
- scegliere e aggiungere una licenza open source;
- definire il processo per documentare le decisioni;
- definire i requisiti minimi del primo prototipo;
- definire la struttura iniziale del progetto Python;
- scegliere le librerie iniziali solo dopo averne verificato la compatibilità
  con Raspberry Pi 3B+;
- documentare la configurazione hardware disponibile.

Criteri di completamento:

- scopo e fuori ambito del prototipo sono documentati;
- le assunzioni ancora aperte sono riconoscibili;
- Python è documentato come tecnologia iniziale e non come vincolo
  permanente;
- la licenza è stata scelta;
- l'ambiente di sviluppo iniziale è stato definito;
- nessuna libreria è obbligatoria senza motivazione documentata.

## Fase 1 — Pipeline deterministica con telemetria sintetica

Obiettivo: dimostrare il flusso completo senza simulatore reale.

Attività:

- definire la prima versione del modello interno di telemetria;
- creare una sorgente di telemetria sintetica;
- costruire lo stato minimo della sessione;
- implementare almeno una regola deterministica;
- produrre un avviso strutturato;
- fornire output testuale;
- registrare eventi ed errori localmente;
- creare scenari ripetibili per comportamento normale e dati non validi.

Criteri di completamento:

- lo stesso scenario produce sempre lo stesso risultato;
- il core funziona senza Internet e senza LLM;
- dati mancanti o non validi non causano decisioni inventate;
- gli eventi possono essere verificati automaticamente;
- la pipeline non contiene dipendenze da un simulatore specifico.

## Fase 2 — Replay di telemetria registrata

Obiettivo: testare il core con sequenze realistiche e riproducibili senza
collegare un simulatore.

Attività:

- definire un formato locale e versionato per le registrazioni;
- implementare avvio, pausa, arresto e velocità di replay;
- conservare timestamp e informazioni sulla sorgente;
- gestire campioni duplicati, mancanti o fuori ordine;
- misurare tempi di elaborazione e stabilità;
- preparare registrazioni di test prive di dati sensibili o non
  distribuibili.

Criteri di completamento:

- una registrazione può essere riprodotta più volte;
- i risultati sono ripetibili;
- il sistema gestisce interruzioni e dati imperfetti;
- il formato e il suo versionamento sono documentati;
- il replay utilizza lo stesso modello interno previsto per le future
  sorgenti reali.

## Fase 3 — Output vocale locale

Obiettivo: consegnare gli avvisi al pilota senza servizi cloud obbligatori.

Attività:

- valutare motori TTS locali compatibili con Raspberry Pi 3B+;
- scegliere una voce italiana iniziale;
- aggiungere un adattatore TTS separato dal core;
- gestire priorità, accodamento e soppressione degli avvisi duplicati;
- verificare l'uscita tramite DAC, mixer e cuffie;
- misurare la latenza tra evento e riproduzione.

Criteri di completamento:

- almeno un evento genera un avviso vocale locale;
- un guasto del TTS non blocca il core;
- l'avviso rimane disponibile tramite log e output testuale;
- consumo di risorse e latenza sono documentati.

## Fase 4 — Validazione completa sul Raspberry Pi 3B+

Obiettivo: verificare il funzionamento autonomo e continuativo del core
sull'hardware iniziale prima di integrare un simulatore reale.

La validazione userà telemetria sintetica e registrata.

Attività:

- installare il core sul Raspberry Pi 3B+;
- configurare l'avvio automatico;
- verificare la pipeline con telemetria sintetica;
- verificare il replay di telemetria registrata;
- verificare l'output testuale e vocale locale;
- eseguire test prolungati;
- misurare CPU, memoria, latenza, temperatura e spazio locale;
- verificare Wi-Fi ed Ethernet;
- verificare comportamento dopo riavvio e perdita della sorgente;
- verificare la degradazione in caso di errore TTS;
- documentare hardware obbligatorio e opzionale;
- identificare eventuali limiti che richiedano ottimizzazione;
- valutare la sostituzione di singoli moduli Python con C++ o Rust soltanto
  se giustificata dalle misure.

Criteri di completamento:

- il sistema parte senza il PC di sviluppo;
- non richiede Internet per il funzionamento base;
- il core funziona usando telemetria sintetica e registrata;
- recupera dagli errori previsti;
- un guasto dell'output vocale non blocca l'analisi;
- prestazioni e limiti del Raspberry Pi 3B+ sono documentati;
- eventuali ottimizzazioni sono motivate da misure reali;
- un altro utente può replicare il banco di prova seguendo la guida;
- il core è considerato validato prima del collegamento a un simulatore
  reale.

## Fase 5 — Verifica tecnica del primo simulatore reale

Obiettivo: decidere quale simulatore possa diventare il primo ufficialmente
supportato.

Il candidato attuale è Gran Turismo 7, ma non è ancora un requisito
definitivo.

Attività:

- verificare il meccanismo di trasmissione della telemetria;
- identificare piattaforme e configurazioni supportate;
- identificare campi, frequenza e formato disponibili;
- verificare la ricezione via rete locale;
- studiare perdita, duplicazione e ordine dei dati;
- verificare l'identificazione di sessione, giro e vettura;
- controllare stabilità rispetto agli aggiornamenti del gioco;
- verificare eventuali trasformazioni o decodifiche necessarie;
- verificare aspetti di licenza, distribuzione e documentazione;
- acquisire una breve registrazione tecnica, se legalmente e tecnicamente
  possibile;
- misurare la ricezione sul Raspberry Pi 3B+;
- documentare risultati, limiti e rischi.

Criteri di completamento:

- esiste un rapporto tecnico riproducibile;
- è noto quali dati utili siano realmente disponibili;
- sono documentati rischi tecnici e legali;
- la sorgente reale può essere ricondotta al modello interno senza
  introdurre logica specifica nel core;
- viene presa e registrata una decisione esplicita:

  - adottare GT7 come primo simulatore;
  - rimandarne il supporto;
  - scegliere un altro simulatore.

## Fase 6 — Adattatore del primo simulatore approvato

Obiettivo: collegare il primo simulatore reale senza modificare il core già
validato.

Attività:

- implementare l'adattatore del simulatore scelto;
- convertire i dati reali nel modello interno;
- gestire connessione, disconnessione e ripresa;
- gestire dati mancanti, duplicati o fuori ordine;
- confrontare dati reali e registrati;
- eseguire una sessione end-to-end;
- misurare latenza e utilizzo delle risorse sul Raspberry Pi 3B+;
- documentare configurazione di console o simulatore, rete e Raspberry Pi.

Criteri di completamento:

- il core non contiene parsing specifico del simulatore;
- l'adattatore utilizza la stessa interfaccia delle sorgenti sintetiche e
  registrate;
- la disconnessione non arresta il servizio;
- una sessione reale produce eventi e avvisi locali;
- prestazioni e latenza restano compatibili con i risultati della
  validazione;
- installazione e configurazione sono ripetibili.

## Fasi successive

Le fasi successive verranno dettagliate soltanto dopo la validazione del
prototipo e del primo adattatore reale.

Possibili direzioni:

- più regole e strategie;
- analisi post-sessione;
- memoria del pilota;
- gestione dei setup;
- profili vocali;
- riconoscimento vocale;
- dashboard web o applicazione;
- supporto ad altri simulatori;
- LLM locale o remoto opzionale;
- distribuzione tramite immagine pronta o installer;
- supporto a Raspberry Pi 5 e mini-PC.

Queste voci rappresentano possibilità future, non requisiti già approvati.

## Decisioni ancora necessarie

Prima o durante le prime fasi dovranno essere decisi:

- licenza open source;
- ambiente di esecuzione Python;
- sistema operativo iniziale;
- struttura iniziale del progetto;
- librerie iniziali;
- schema della telemetria interna;
- formato delle registrazioni;
- prima regola del prototipo;
- motore TTS locale;
- criteri quantitativi di prestazione;
- simulatore iniziale dopo la verifica tecnica;
- modalità finale di distribuzione.
