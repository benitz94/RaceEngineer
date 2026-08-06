# PROJECT_JOURNAL.md

# RaceEngineer - Diario di Progettazione

> Documento vivo. Non cancellare le idee: commentarle con `//`
> aggiungendo sempre il motivo. Questo documento racconta COME è nato il
> progetto.

------------------------------------------------------------------------

# Origine del progetto

L'idea iniziale non era RaceEngineer.

Le prime prove sono nate installando Open-LLM-VTuber con Ollama per
capire se fosse possibile avere una companion AI completamente locale.

Durante questi test è nata una domanda:

"Se invece di una semplice waifu costruissimo un vero assistente?"

Da quel momento il progetto ha iniziato a cambiare.

------------------------------------------------------------------------

# Companion AI

La Companion AI NON è RaceEngineer.

È un progetto separato.

Motivo:

-   può essere usata anche fuori dal sim racing;
-   permette di sperimentare STT, TTS e LLM;
-   parte del codice potrà essere riutilizzata da RaceEngineer.

Decisione: Mantenere i due progetti separati.

------------------------------------------------------------------------

# Open-LLM-VTuber

Attività svolte:

-   installazione Git
-   configurazione GitHub
-   installazione Python
-   installazione uv
-   installazione FFmpeg
-   configurazione Ollama
-   installazione Open-LLM-VTuber
-   configurazione del modello Qwen
-   problemi iniziali con MCP
-   disattivazione MCP per far partire il sistema
-   personalizzazione del prompt di Mao
-   traduzione in italiano
-   prove con Edge TTS

Problemi riscontrati:

-   voce inglese
-   TTS italiano non soddisfacente
-   errori casuali durante la conversazione
-   microfono webcam poco affidabile

Decisione:

Acquistare un microfono lavalier USB dedicato.

------------------------------------------------------------------------

# Microfono

Idea iniziale ChatGPT:

Microfono USB da tavolo.

Commento Benito:

// Preferisco un lavalier. Non voglio un microfono davanti mentre
programmo o mentre gioco.

Decisione finale:

Acquistato un lavalier USB MillSO.

Da verificare all'arrivo.

------------------------------------------------------------------------

# Nascita di RaceEngineer

Durante la discussione è nata l'idea di costruire un ingegnere di pista
personale.

Prima ipotesi:

Usare il PC principale.

Decisione successiva proposta da Benito:

Il PC dovrà servire SOLO per sviluppare.

La piattaforma inizale dovrà essere Raspberry Pi, successivamente
valutare l'utilizzo di un mini-pc o altro hardware a seconda delle
performance necessarie e alle esigenze.

Questa è diventata una delle decisioni più importanti dell'intero
progetto.

------------------------------------------------------------------------

# Raspberry Pi

Banco di prova.

Il software dovrà funzionare in maniera standalone.

Nessuna dipendenza dal PC.

Il PC servirà solo per:

-   sviluppo
-   test
-   debug

Questa decisione influenza tutta l'architettura.

------------------------------------------------------------------------

# Filosofia

Ogni nuova funzione dovrà essere progettata pensando:

"Gira sull'hardware?"

Se la risposta è NO:

capire se:

-   è davvero necessaria;
-   può essere riscritta;
-   occorre potenziare l'hardware?

------------------------------------------------------------------------

# AI

Discussione importante.

Obiezione:

"Bisogna addestrare un modello."

Conclusione:

NO.

RaceEngineer non dovrà creare un nuovo LLM.

Dovrà usare modelli esistenti.

Il valore del progetto sarà:

-   logica
-   telemetria
-   memoria
-   esperienza utente
-   integrazione

NON l'addestramento del modello.

------------------------------------------------------------------------

# Codex

Usare Codex direttamente dentro VS Code.

ChatGPT:

favorevole.

Ruoli decisi:

Benito: Product Owner.

Codex:

-   implementazione
-   codice
-   refactoring
-   test

ChatGPT:

-   architettura
-   progettazione
-   revisione
-   documentazione
-   decisioni tecniche

------------------------------------------------------------------------

# GitHub

Decisione:

Repository pubblico.

Motivo:

-   cronologia
-   collaborazione
-   progetto open source

------------------------------------------------------------------------

# Documentazione

Decisione importante.

Scrivere la documentazione PRIMA del codice.

Documenti previsti:

README.md PROJECT_CONTEXT.md ARCHITECTURE.md ROADMAP.md AGENTS.md
CHANGELOG.md PROJECT_JOURNAL.md

------------------------------------------------------------------------

# Idee annotate

-   Companion desktop ai waifu per facilitare il coding con commenti e
    suggerimenti.
-   Apertura automatica di VS Code.
-   Apertura repository GitHub.
-   Controllo Git.
-   Memoria delle sessioni al simulatore.
-   Database setup GT7, F1, etc.
-   Strategie carburante.
-   Strategie gomme.
-   Srategie pit stop.
-   Dashboard web o app per test hardware sul telefono.
-   Controllo e gestione musica e playlist con comandi vocali.
-   Supporto futuro ad altri simulatori.
-   Sistema modulare.
-   Interagire con il race engineer con il microfono.
-   Creazione di vari profili di race engineer in base a lingua, tono,
    stile, etc.
-   Il race engineer deve adattarsi al pilota, dare suggerimenti, nel
    caso faccia fatica ad applicare i suggerimenti trovare altre
    soluzioni più semplici, e segnalare errori di guida sul giro.

Aggiungere qui TUTTE le nuove idee, anche se sembrano inutili.

Mai cancellarle.

Commentarle e spiegare il motivo.

------------------------------------------------------------------------

# Regola del progetto

Ogni decisione importante deve essere riportata qui.

L'obiettivo è permettere a chiunque (compreso noi stessi tra mesi) di
capire non solo COSA è stato deciso, ma soprattutto PERCHE' è stato
deciso.

------------------------------------------------------------------------

# Hardware e Replicabilità

Uno degli obiettivi principali del progetto è permettere ad altri utenti
di replicare RaceEngineer senza dover ricostruire da zero l'ambiente
hardware.

La documentazione dovrà essere sufficientemente dettagliata da
consentire ad un utente di acquistare i componenti necessari, prepararli
e ottenere un sistema funzionante seguendo una guida passo-passo.

## Filosofia

L'obiettivo NON è soltanto distribuire il codice.

L'obiettivo è distribuire un'intera piattaforma replicabile.

Ogni componente hardware dovrà essere documentato.

Per ogni componente dovranno essere indicati:

-   Modello
-   Produttore
-   Motivazione della scelta
-   Obbligatorio oppure opzionale
-   Eventuali alternative
-   Problemi riscontrati
-   Note di configurazione

## Hardware previsto

Questa sezione verrà aggiornata durante lo sviluppo.

Configurazione iniziale prevista:

-   Raspberry Pi 3B+ (piattaforma iniziale)
-   Alimentatore
-   microSD (capacità e classe da definire)
-   Collegamento Wi-Fi oppure Ethernet
-   Microfono USB Lavalier
-   DAC USB verso mixer
-   Mixer audio
-   Cuffie
-   Eventuale dissipatore o ventola
-   Chiavetta usb da verificare capacità massima per la raspberry pi con
    canzoni in FLAC o mp3

In futuro potranno essere aggiunti:

-   Raspberry Pi 5
-   Mini PC
-   Altre piattaforme compatibili

L'architettura del software NON dovrà dipendere dall'hardware scelto.

## Sistema operativo

Valutare due modalità di distribuzione.

Modalità A

Distribuire direttamente un'immagine pronta da flashare (es.
RaceEngineer OS).

L'utente dovrà solamente:

1.  Flashare la microSD.
2.  Inserirla nella Raspberry.
3.  Collegare l'hardware.
4.  Avviare il sistema.

Modalità B

Distribuire un installer automatico.

L'utente installerà Raspberry Pi OS e successivamente RaceEngineer
tramite uno script di installazione che configurerà automaticamente
dipendenze, servizi e impostazioni.

La soluzione definitiva verrà scelta durante lo sviluppo.

## Obiettivo finale

Chiunque dovrà essere in grado di replicare il progetto seguendo
esclusivamente la documentazione ufficiale, senza dover chiedere
informazioni aggiuntive agli sviluppatori.

------------------------------------------------------------------------

# Convenzioni del Journal

Per mantenere il documento semplice e leggibile non verranno utilizzati
campi come "Attiva", "In pausa" o "Scartata".

Le idee NON devono essere eliminate.

Convenzioni:

-   Un'idea valida rimane semplicemente nel documento.
-   `//` viene utilizzato per commenti personali, motivazioni, idee
    scartate, idee in pausa e promemoria futuri.
-   `#` e `##` sono riservati esclusivamente ai titoli e ai sottotitoli
    del documento.

L'obiettivo è preservare il ragionamento che ha portato alle decisioni,
non classificare ogni idea con uno stato.

------------------------------------------------------------------------

# Sessione del 2026-08-06

Durante questa sessione sono state definite e approvate le seguenti decisioni progettuali.

## Core locale e deterministico

Decisione:

Il core funzionerà localmente, senza dipendere dal PC di sviluppo, da servizi
cloud obbligatori o da un LLM. La rete locale potrà essere usata per ricevere
la telemetria.

Motivazione:

Durante una sessione di guida, continuità di funzionamento e prevedibilità
sono più importanti della complessità tecnologica. Un eventuale LLM potrà
arricchire l'esperienza, ma non dovrà diventare un punto di errore per le
decisioni critiche.

## Python come tecnologia iniziale

Decisione:

Lo sviluppo inizierà in Python, mantenendo la possibilità di sostituire in
futuro singoli moduli con C++ o Rust.

Motivazione:

Python permette di sviluppare rapidamente, funziona su Raspberry Pi e offre
un ecosistema adatto alle future integrazioni audio e AI. Non deve però
diventare un vincolo se misure reali evidenzieranno limiti prestazionali.

## Performance first

Decisione:

Stabilità, affidabilità e reattività avranno priorità sulle funzionalità
aggiuntive.

Motivazione:

Il Raspberry Pi 3B+ dispone di risorse limitate e RaceEngineer deve essere
utile durante la guida. Una funzione non essenziale non giustifica la perdita
di reattività o affidabilità del sistema.

## Core indipendente dal simulatore

Decisione:

Il core verrà sviluppato e validato con telemetria sintetica e registrata
prima di integrare un simulatore reale. Gran Turismo 7 rimane un candidato da
verificare tecnicamente.

Motivazione:

Separare il core dalla sorgente reale permette di procedere anche senza un
simulatore collegato, creare test ripetibili e verificare prima la
compatibilità con il Raspberry Pi 3B+.

## Introduzione di PROJECT_CONTEXT.md

Decisione:

PROJECT_CONTEXT.md rappresenterà soltanto lo stato operativo corrente e verrà
riscritto alla fine di ogni sessione eliminando le informazioni superate.

Motivazione:

Il Journal conserva la memoria e le ragioni del progetto, ma non è adatto a
comunicare rapidamente dove si trova il lavoro in questo momento. Un
documento operativo breve evita di trasformare il Journal in un changelog o
in una copia degli altri documenti.

## Cambiamento del workflow

Decisione:

Ogni sessione inizierà dallo stato corrente, proseguirà con la memoria
storica e con la documentazione di progetto, e terminerà aggiornando
PROJECT_CONTEXT.md.

PROJECT_JOURNAL.md verrà aggiornato soltanto quando emergono decisioni,
motivazioni, idee importanti o cambi di direzione, e sempre dopo
l'approvazione dell'utente.

Motivazione:

Separare stato operativo, memoria progettuale, documentazione tecnica e
cronologia Git riduce le duplicazioni e rende più immediato comprendere sia
il presente sia le ragioni delle decisioni passate.
