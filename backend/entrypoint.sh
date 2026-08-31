#!/bin/sh
set -e

echo "Applico le migrazioni al database..."
n=0
until alembic upgrade head; do
  n=$((n + 1))
  if [ "$n" -ge 30 ]; then
    echo "Database non raggiungibile. Interrompo."
    exit 1
  fi
  echo "Database non ancora pronto, riprovo tra 2s ($n/30)..."
  sleep 2
done

echo "Avvio l'API del Diario Salute ..."
exec uvicorn app.main:app --host 0.0.0.0 --port "${PORT:-8000}"
