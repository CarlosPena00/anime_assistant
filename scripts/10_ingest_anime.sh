#!/bin/bash
# Usage: ./10_ingest_anime.sh "Anime Search Query"

if [ -z "$1" ]; then
  echo "Usage: $0 'Anime Search Query'"
  exit 1
fi

QUERY="$1"

python -c "from src.ingest import ingest_anime_metadata; ingest_anime_metadata(\"$QUERY\")"
