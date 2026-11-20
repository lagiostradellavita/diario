-- Modello dati della GESTIONE Apayaye (minori, iscrizioni, attivita', ore).
-- Database Neon (PostgreSQL), in UE. Dati personali di minori: accesso solo con login e per ruolo.
-- Questo file descrive lo schema; in produzione diventera' una migrazione (alembic), come negli altri progetti.

-- ---- Accessi ----
create table if not exists utenti (
  id              serial primary key,
  email           text not null unique,
  password_hash   text not null,
  ruolo           text not null check (ruolo in ('admin','ufficio','operatore','genitore')),
  attivo          boolean not null default true,
  deve_cambiare_password boolean not null default true,
  operatore_id    integer,          -- se ruolo 'operatore': a quale operatore e' legato
  genitore_id     integer,          -- se ruolo 'genitore': a quale genitore e' legato
  creato_il       timestamptz not null default now()
);

-- ---- Progetto (una riga di configurazione) ----
create table if not exists progetto (
  id                    serial primary key,
  soggetto              text,
  titolo                text,
  cup                   text,
  clp                   text,       -- es. 2024-PE4-00024
  data_avvio            date,
  destinatari_previsti  integer,
  fascia_eta            text,       -- es. '11-17 anni'
  fase                  text
);

-- ---- Minori destinatari (campi del template ministeriale) ----
create table if not exists minori (
  id              serial primary key,
  cognome         text not null,
  nome            text not null,
  codice_fiscale  text not null unique,     -- 16 caratteri; eta' nella fascia; niente doppioni
  stato_nascita   text,
  comune_nascita  text,
  provincia       text,
  genere          text check (genere in ('M','F')),
  data_nascita    date,
  clp             text,
  scuola          text,                      -- utile per l'organizzazione (non va al Ministero)
  ore_previste    numeric(7,2),              -- monte ore ex art. 17.1
  stato           text check (stato in ('Nuovo inserimento','Concluso','Rinunciatario')),
  modulo_iscrizione boolean not null default false,  -- modulo d'iscrizione presente?
  note            text,
  creato_il       timestamptz not null default now()
);

-- ---- Genitori / tutori (dati d'iscrizione e consensi; NON vanno al Ministero) ----
create table if not exists genitori (
  id              serial primary key,
  cognome         text not null,
  nome            text not null,
  codice_fiscale  text,
  telefono        text,
  email           text,
  creato_il       timestamptz not null default now()
);

create table if not exists minore_genitore (
  minore_id           integer not null references minori(id) on delete cascade,
  genitore_id         integer not null references genitori(id) on delete cascade,
  rapporto            text,                  -- madre, padre, tutore...
  consenso_privacy    boolean not null default false,
  consenso_immagini   boolean not null default false,
  data_consenso       date,
  primary key (minore_id, genitore_id)
);

-- ---- Operatori (animatori / tutor) ----
create table if not exists operatori (
  id              serial primary key,
  cognome         text not null,
  nome            text not null,
  codice_fiscale  text,
  voce            text,                      -- A01 animatore, A02 tutor, ...
  email           text,
  telefono        text
);

-- ---- Attivita' e sessioni ----
create table if not exists attivita (
  id              serial primary key,
  nome            text not null,             -- Doposcuola, Scacchi, Affettivita', Uscita Orto botanico...
  tipo            text,                       -- doposcuola, laboratorio, uscita...
  descrizione     text,
  attiva          boolean not null default true
);

create table if not exists sessioni (
  id              serial primary key,
  attivita_id     integer not null references attivita(id) on delete cascade,
  data            date not null,
  ore             numeric(6,2) not null default 0,  -- durata della sessione
  operatore_id    integer references operatori(id),
  note            text,
  creato_il       timestamptz not null default now()
);

-- Presenza del minore a una sessione: ore accreditate (default = ore della sessione).
create table if not exists presenze (
  id              serial primary key,
  sessione_id     integer not null references sessioni(id) on delete cascade,
  minore_id       integer not null references minori(id) on delete cascade,
  ore             numeric(6,2) not null default 0,
  unique (sessione_id, minore_id)
);

-- Ore degli operatori per sessione (per il consulente e la rendicontazione).
create table if not exists operatore_ore (
  id              serial primary key,
  sessione_id     integer not null references sessioni(id) on delete cascade,
  operatore_id    integer not null references operatori(id) on delete cascade,
  ore             numeric(6,2) not null default 0,
  unique (sessione_id, operatore_id)
);

create index if not exists ix_minori_cf on minori(codice_fiscale);
create index if not exists ix_presenze_minore on presenze(minore_id);
create index if not exists ix_sessioni_attivita on sessioni(attivita_id);

-- La "Sommatoria ore erogate" del Ministero = somma di presenze.ore per minore.
-- La regola sta in ore.py (ore_per_minore), un posto solo, cosi' schermata ed export concordano.
