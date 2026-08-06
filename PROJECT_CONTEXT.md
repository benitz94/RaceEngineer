# PROJECT_CONTEXT.md

Ultimo aggiornamento:
2026-08-06

## Fase attuale

Fase 0 — Documentazione e fondamenta del progetto.

Il progetto è ancora in fase di progettazione. Non è stato scritto codice e
non esiste ancora un prototipo eseguibile.

## Risultato dell'ultima sessione

Sono stati definiti e approvati i contenuti di:

- `README.md`;
- `ARCHITECTURE.md`;
- `ROADMAP.md`;
- `PROJECT_CONTEXT.md`;
- `AGENTS.md`.

Sono state confermate le seguenti decisioni:

- funzionamento locale senza servizi cloud obbligatori;
- core deterministico, indipendente da LLM e simulatori;
- Python come tecnologia iniziale, con possibilità futura di sostituire
  singoli moduli con C++ o Rust;
- Raspberry Pi 3B+ come hardware iniziale di riferimento;
- sviluppo iniziale con telemetria sintetica e registrata;
- stabilità, affidabilità e reattività prima delle funzionalità aggiuntive;
- Gran Turismo 7 come candidato da verificare, non ancora come requisito.

Non è stato scritto codice.

## Sessione successiva

Completare le decisioni ancora necessarie per chiudere la Fase 0.

## Decisioni ancora aperte

- Licenza open source.
- Ambiente di esecuzione Python.
- Sistema operativo iniziale.
- Struttura iniziale del progetto.
- Librerie iniziali.
- Schema interno della telemetria.
- Formato delle registrazioni.
- Prima regola deterministica del prototipo.
- Motore TTS locale.
- Criteri quantitativi di prestazione.
- Simulatore iniziale, dopo la verifica tecnica.
- Modalità finale di distribuzione: immagine pronta oppure installer.

## Problemi o blocchi

- Gran Turismo 7 non è ancora stato verificato tecnicamente.
- Le prestazioni effettive del core sul Raspberry Pi 3B+ non sono ancora
  misurate.
- L'implementazione non deve iniziare prima del completamento della
  documentazione prevista per la Fase 0.
- Non risultano attualmente altri blocchi tecnici noti.

## Documenti essenziali da leggere

1. `PROJECT_CONTEXT.md` — stato operativo corrente.
2. `PROJECT_JOURNAL.md` — intento, decisioni e motivazioni storiche.
3. `README.md` — visione, obiettivi e principi del progetto.
4. `ARCHITECTURE.md` — componenti, confini e flussi del sistema.
5. `ROADMAP.md` — fasi e criteri di completamento.
6. `AGENTS.md` — regole operative del repository.
