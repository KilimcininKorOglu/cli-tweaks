-- pg-payload-offload.scan.sql — find TOAST-heavy tables and columns, autovacuum pressure, partitioning.
-- Run: psql "$DATABASE_URL" -f pg-payload-offload.scan.sql

\echo '== 1. Tables by TOAST size (main vs toast) =='
SELECT c.relname                                   AS table_name,
       pg_size_pretty(pg_relation_size(c.oid))     AS heap,
       pg_size_pretty(pg_relation_size(t.oid))     AS toast,
       ROUND(100.0 * pg_relation_size(t.oid) /
             NULLIF(pg_total_relation_size(c.oid),0), 1) AS toast_pct,
       pg_size_pretty(pg_total_relation_size(c.oid)) AS total
FROM pg_class c
JOIN pg_class t ON t.oid = c.reltoastrelid
WHERE c.relkind IN ('r','p') AND t.oid IS NOT NULL
ORDER BY pg_relation_size(t.oid) DESC
LIMIT 20;

\echo '== 2. Large-value columns (jsonb/bytea/text) on those tables =='
SELECT a.attrelid::regclass AS table_name, a.attname, format_type(a.atttypid, a.atttypmod) AS type,
       CASE a.attstorage WHEN 'x' THEN 'EXTENDED' WHEN 'e' THEN 'EXTERNAL' WHEN 'm' THEN 'MAIN' ELSE 'PLAIN' END AS storage
FROM pg_attribute a
JOIN pg_class c ON c.oid = a.attrelid
WHERE c.relkind IN ('r','p') AND c.relnamespace NOT IN ('pg_catalog'::regnamespace,'information_schema'::regnamespace)
  AND a.attnum > 0 AND NOT a.attisdropped
  AND a.atttypid IN ('jsonb'::regtype,'json'::regtype,'bytea'::regtype,'text'::regtype)
  AND c.reltoastrelid <> 0
ORDER BY 1,2;

\echo '== 3. Autovacuum activity on TOAST tables (running now) =='
SELECT pid, now() - xact_start AS duration, query
FROM pg_stat_activity
WHERE query ILIKE '%autovacuum%pg_toast%'
ORDER BY duration DESC;

\echo '== 4. TOAST vacuum stats / dead tuples =='
SELECT c.relname AS parent, t.relname AS toast,
       s.n_live_tup, s.n_dead_tup, s.last_autovacuum, s.autovacuum_count
FROM pg_class c
JOIN pg_class t ON t.oid = c.reltoastrelid
JOIN pg_stat_all_tables s ON s.relid = t.oid
WHERE c.relkind IN ('r','p')
ORDER BY s.n_dead_tup DESC NULLS LAST
LIMIT 20;

\echo '== 5. Partitioned tables and partition count =='
SELECT parent.relname AS parent, count(child.oid) AS partitions,
       pg_get_partkeydef(parent.oid) AS partition_key
FROM pg_inherits i
JOIN pg_class parent ON parent.oid = i.inhparent
JOIN pg_class child  ON child.oid  = i.inhrelid
WHERE parent.relkind = 'p'
GROUP BY parent.relname, parent.oid
ORDER BY 2 DESC;

\echo '== 6. Transaction ID age (wraparound risk) top 10 =='
SELECT c.oid::regclass AS table_name, age(c.relfrozenxid) AS xid_age
FROM pg_class c WHERE c.relkind IN ('r','t','p')
ORDER BY 2 DESC LIMIT 10;
