-- Schema dell'archivio gestione Apayaye (Neon/PostgreSQL). Creato al primo avvio (init_db).
create table if not exists utenti (
  id              serial primary key,
  email           text not null unique,
  password_hash   text not null,
  ruolo           text not null check (ruolo in ('admin','ufficio','operatore','genitore')),
  attivo          boolean not null default true,
  deve_cambiare_password boolean not null default false,
  operatore_id    integer,
  genitore_id     integer,
  creato_il       timestamptz not null default now()
);

create table if not exists progetto (
  id                    serial primary key,
  soggetto              text,
  titolo                text,
  cup                   text,
  clp                   text,
  data_avvio            date,
  destinatari_previsti  integer,
  fascia_eta            text,
  fase                  text
);

create table if not exists minori (
  id              serial primary key,
  cognome         text not null,
  nome            text not null,
  codice_fiscale  text not null unique,
  stato_nascita   text,
  comune_nascita  text,
  provincia       text,
  genere          text check (genere in ('M','F')),
  data_nascita    date,
  clp             text,
  scuola          text,
  ore_previste    numeric(7,2),
  stato           text check (stato in ('Nuovo inserimento','Concluso','Rinunciatario')),
  modulo_iscrizione boolean not null default false,
  note            text,
  creato_il       timestamptz not null default now()
);

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
  rapporto            text,
  consenso_privacy    boolean not null default false,
  consenso_immagini   boolean not null default false,
  data_consenso       date,
  primary key (minore_id, genitore_id)
);

create table if not exists operatori (
  id              serial primary key,
  cognome         text not null,
  nome            text not null,
  codice_fiscale  text,
  voce            text,
  email           text,
  telefono        text
);

create table if not exists attivita (
  id              serial primary key,
  nome            text not null,
  tipo            text,
  descrizione     text,
  attiva          boolean not null default true
);

create table if not exists sessioni (
  id              serial primary key,
  attivita_id     integer not null references attivita(id) on delete cascade,
  data            date not null,
  ore             numeric(6,2) not null default 0,
  operatore_id    integer references operatori(id),
  note            text,
  creato_il       timestamptz not null default now()
);

create table if not exists presenze (
  id              serial primary key,
  sessione_id     integer not null references sessioni(id) on delete cascade,
  minore_id       integer not null references minori(id) on delete cascade,
  ore             numeric(6,2) not null default 0,
  unique (sessione_id, minore_id)
);

create table if not exists operatore_ore (
  id              serial primary key,
  sessione_id     integer not null references sessioni(id) on delete cascade,
  operatore_id    integer not null references operatori(id) on delete cascade,
  ore             numeric(6,2) not null default 0,
  unique (sessione_id, operatore_id)
);

create table if not exists documenti (
  id            serial primary key,
  tipo          text,
  titolo        text,
  attivita_id   integer references attivita(id) on delete set null,
  operatore_id  integer references operatori(id) on delete set null,
  minore_id     integer references minori(id) on delete set null,
  periodo       text,
  importo       numeric(12,2),
  nome_file     text not null,
  mime          text,
  dimensione    integer,
  contenuto     bytea,
  caricato_da   integer references utenti(id),
  caricato_il   timestamptz not null default now()
);

create index if not exists ix_minori_cf on minori(codice_fiscale);
create index if not exists ix_presenze_minore on presenze(minore_id);
create index if not exists ix_sessioni_attivita on sessioni(attivita_id);
create index if not exists ix_documenti_attivita on documenti(attivita_id);
create index if not exists ix_documenti_operatore on documenti(operatore_id);
