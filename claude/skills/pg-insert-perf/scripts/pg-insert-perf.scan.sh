#!/usr/bin/env bash
# pg-insert-perf.scan.sh — grep-based heuristics for Postgres insert anti-patterns.
# Usage: scripts/pg-insert-perf.scan.sh [dir]   (default: .)
set -u
ROOT="${1:-.}"
EXCL='--exclude-dir=vendor --exclude-dir=node_modules --exclude-dir=.git --exclude-dir=testdata --exclude-dir=dist --exclude-dir=target'
G="grep -rnIE $EXCL"

section() { printf '\n== %s ==\n' "$1"; }

section "Single-row INSERT statements (check whether called in a loop)"
$G 'INSERT[[:space:]]+INTO[^;]*VALUES[[:space:]]*\(\$1|INSERT[[:space:]]+INTO[^;]*VALUES[[:space:]]*\(\?' "$ROOT" \
  --include='*.go' --include='*.sql' --include='*.py' --include='*.js' --include='*.ts' --include='*.rs' || echo "  none"

section "Exec/Query calls that look like inserts inside loops (Go: within 6 lines of for/range)"
for f in $(grep -rlIE $EXCL 'INSERT[[:space:]]+INTO' "$ROOT" --include='*.go' 2>/dev/null); do
  awk -v F="$f" '
    /for[[:space:]].*(range|;|\{)/ { loop=NR }
    /\.(Exec|Query|QueryRow|Insert|Create)\(/ && loop && NR-loop<=6 { printf "  %s:%d  %s\n", F, NR, $0 }
  ' "$f"
done

section "Already batched / COPY (leave alone, check batch size)"
$G 'SendBatch|CopyFrom|copy_records_to_table|copy_from|cursor\.copy|copy_in|pg-copy-streams|UNNEST\(|executemany|execute_values' "$ROOT" || echo "  none"

section "RETURNING * (drop if unused — blocks COPY)"
$G 'RETURNING[[:space:]]+\*' "$ROOT" --include='*.go' --include='*.sql' --include='*.py' --include='*.js' --include='*.ts' --include='*.rs' || echo "  none"

section "Pool size configuration (flag >20 per instance or unbounded)"
$G 'MaxConns|MaxOpenConns|SetMaxOpenConns|pool_size|max_size|maxPoolSize|max:[[:space:]]*[0-9]+|POOL_SIZE|MAX_CONNS|max_connections|pool_max_conns' "$ROOT" || echo "  none"

section "Driver detection"
$G 'jackc/pgx|lib/pq|database/sql|psycopg|asyncpg|sqlalchemy|require\(.pg.\)|from .pg.|postgres\.js|tokio-postgres|sqlx' "$ROOT" \
  --include='go.mod' --include='*.go' --include='requirements*.txt' --include='pyproject.toml' --include='package.json' --include='Cargo.toml' | cut -d: -f1 | sort -u || echo "  none"

printf '\nHeuristic only — confirm each hit manually and classify per SKILL.md Phase 1.\n'
