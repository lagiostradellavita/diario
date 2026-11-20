-- Documenti della rendicontazione, caricati e scaricati dagli operatori (dopo la registrazione)
-- e dall'ufficio: Allegato G, fatture ricevute, relazioni, registri firma, ecc.
-- Il file sta dentro l'archivio (bytea), come gli allegati della app contabilita'.

create table if not exists documenti (
  id            serial primary key,
  tipo          text,            -- 'Allegato G' | 'Fattura ricevuta' | 'Relazione' | 'Registro firma' | 'Altro'
  titolo        text,
  attivita_id   integer references attivita(id) on delete set null,
  operatore_id  integer references operatori(id) on delete set null,
  minore_id     integer references minori(id) on delete set null,
  periodo       text,            -- mese/periodo di competenza, se serve
  importo       numeric(12,2),   -- se e' una fattura/spesa: l'importo (alimenta il ponte verso la contabilita')
  nome_file     text not null,
  mime          text,
  dimensione    integer,
  contenuto     bytea,           -- il file dentro l'archivio
  caricato_da   integer references utenti(id),
  caricato_il   timestamptz not null default now()
);

create index if not exists ix_documenti_attivita on documenti(attivita_id);
create index if not exists ix_documenti_operatore on documenti(operatore_id);

-- Accesso (nel backend, per ruolo):
--  - operatore: vede e carica i documenti delle SUE attivita';
--  - ufficio/admin: tutto;
--  - genitore: non vede i documenti.
-- L'importo delle fatture ricevute e i compensi (ore x tariffa, vedi importi.py) sono i numeri
-- che vanno nella app contabilita', sezione progetti -> APAYAYE.
