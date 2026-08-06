# AGENTS.md

## Inizio della sessione

Prima di svolgere qualsiasi lavoro, leggere i documenti nel seguente ordine:

1. `PROJECT_CONTEXT.md`;
2. `PROJECT_JOURNAL.md`;
3. `README.md`;
4. `ARCHITECTURE.md`;
5. `ROADMAP.md`;
6. `AGENTS.md`.

Questo ordine permette di comprendere prima lo stato operativo corrente, poi
le motivazioni storiche, il prodotto, l'architettura, la roadmap e infine le
regole operative.

## Regole del progetto

1. Trattare `PROJECT_JOURNAL.md` come fonte di verità per l'intento e le
   decisioni del progetto.
2. Non modificare file finché l'utente non ha approvato il piano proposto.
3. Non inventare requisiti.
4. Mantenere RaceEngineer indipendente dal progetto privato Companion AI.
5. Conservare in `PROJECT_CONTEXT.md` esclusivamente lo stato operativo
   corrente, senza trasformarlo in un diario o in un changelog cumulativo.
6. Non inserire in `PROJECT_JOURNAL.md` il dettaglio delle modifiche ai file,
   perché la cronologia tecnica è conservata da Git.

## Fine della sessione

Alla fine di ogni sessione di sviluppo l'agente deve:

1. aggiornare `PROJECT_CONTEXT.md`, sostituendo le informazioni non più
   attuali;
2. aggiornare la data dell'ultimo aggiornamento in `PROJECT_CONTEXT.md`;
3. se durante la sessione sono emerse nuove decisioni progettuali, nuove idee
   importanti o cambi di direzione, proporre anche un aggiornamento di
   `PROJECT_JOURNAL.md`;
4. non aggiornare `PROJECT_JOURNAL.md` se sono cambiati solamente file di
   codice, refactoring, bugfix o implementazioni tecniche;
5. attendere sempre l'approvazione dell'utente prima di modificare
   `PROJECT_JOURNAL.md`.
