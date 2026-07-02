-- Centralized logging schema (relational / SQL).
-- Three tables: request_logs (every API call), audit_logs (data-mutating operations),
-- and app_logs (general-purpose application logging, independent of HTTP context).
-- Written in ANSI-leaning SQL; dialect notes are called out inline.
-- Adjust types to the target database (PostgreSQL, MySQL, SQL Server, SQLite, ...).

-- ============================================================
-- request_logs: one row per inbound API request.
-- ============================================================
CREATE TABLE request_logs (
    id               BIGINT PRIMARY KEY,          -- BIGSERIAL/IDENTITY/AUTOINCREMENT per dialect
    request_id       CHAR(36)     NOT NULL UNIQUE, -- UUID; correlates with audit_logs.request_id and trace logs
    user_id          BIGINT       NULL,             -- FK -> users.id; NULL for anonymous/unauthenticated requests
    username         VARCHAR(255) NULL,             -- denormalized snapshot, survives user deletion/rename
    ip_address       VARCHAR(45)  NOT NULL,         -- IPv4/IPv6 textual form (use INET on PostgreSQL)
    user_agent       VARCHAR(512) NULL,
    http_method      VARCHAR(10)  NOT NULL,         -- GET/POST/PUT/PATCH/DELETE
    endpoint         VARCHAR(512) NOT NULL,         -- request path, e.g. /persons
    module           VARCHAR(100) NULL,             -- logical module/domain, e.g. Users
    action            VARCHAR(150) NULL,             -- logical action name, e.g. BulkInsertUser
    query_params     TEXT         NULL,             -- JSON-encoded query string
    request_body     TEXT         NULL,             -- JSON-encoded body, sensitive fields redacted before write
    response_status  SMALLINT     NULL,             -- HTTP status code (filled after handler returns)
    response_time_ms  INT          NULL,
    error_message     TEXT         NULL,             -- populated when response_status >= 400
    created_at        TIMESTAMP    NOT NULL DEFAULT CURRENT_TIMESTAMP,

    CONSTRAINT fk_request_logs_user FOREIGN KEY (user_id) REFERENCES users(id)
);

CREATE INDEX idx_request_logs_user_id    ON request_logs (user_id);
CREATE INDEX idx_request_logs_created_at ON request_logs (created_at);
CREATE INDEX idx_request_logs_endpoint   ON request_logs (endpoint);

-- ============================================================
-- audit_logs: one row per data-mutating operation (Insert/Update/Delete).
-- ============================================================
CREATE TABLE audit_logs (
    id              BIGINT PRIMARY KEY,
    request_id      CHAR(36)     NULL,             -- FK -> request_logs.request_id; NULL for non-HTTP triggers (jobs, migrations)
    user_id         BIGINT       NULL,
    username        VARCHAR(255) NULL,
    action_type     VARCHAR(20)  NOT NULL,          -- INSERT | UPDATE | DELETE | BULK_INSERT | BULK_UPDATE | BULK_DELETE
    table_name      VARCHAR(150) NOT NULL,          -- target table/collection name
    record_id       VARCHAR(100) NULL,              -- primary key of affected row; NULL for bulk operations
    affected_count  INT          NULL,              -- row count for bulk operations
    old_values      TEXT         NULL,              -- JSON-encoded pre-change state (UPDATE/DELETE)
    new_values      TEXT         NULL,              -- JSON-encoded post-change state (INSERT/UPDATE)
    ip_address      VARCHAR(45)  NULL,
    created_at      TIMESTAMP    NOT NULL DEFAULT CURRENT_TIMESTAMP,

    CONSTRAINT fk_audit_logs_request FOREIGN KEY (request_id) REFERENCES request_logs(request_id),
    CONSTRAINT fk_audit_logs_user    FOREIGN KEY (user_id)    REFERENCES users(id)
);

CREATE INDEX idx_audit_logs_table_record ON audit_logs (table_name, record_id);
CREATE INDEX idx_audit_logs_user_id      ON audit_logs (user_id);
CREATE INDEX idx_audit_logs_created_at   ON audit_logs (created_at);

-- ============================================================
-- app_logs: one row per general-purpose application log entry
-- (TRACE/DEBUG/INFO/WARN/ERROR/FATAL), independent of HTTP context.
-- Populated by a logging-library sink/handler/transport, not by middleware.
-- ============================================================
CREATE TABLE app_logs (
    id               BIGINT PRIMARY KEY,             -- BIGSERIAL/IDENTITY/AUTOINCREMENT per dialect
    level            VARCHAR(10)  NOT NULL,           -- TRACE | DEBUG | INFO | WARN | ERROR | FATAL
    message          TEXT         NOT NULL,
    logger_name      VARCHAR(150) NULL,               -- emitting module/service/class, e.g. "PersonService"
    source_location  VARCHAR(255) NULL,               -- file:line or function name, when the library exposes it
    context          TEXT         NULL,               -- JSON-encoded structured fields, sensitive fields redacted
    stack_trace      TEXT         NULL,                -- populated for ERROR/FATAL when an exception is attached
    request_id       CHAR(36)     NULL,                -- optional correlation only; this table works standalone
    environment      VARCHAR(50)  NULL,                -- e.g. production/staging/development
    hostname         VARCHAR(255) NULL,                -- emitting host/container/instance id
    created_at       TIMESTAMP    NOT NULL DEFAULT CURRENT_TIMESTAMP
);

CREATE INDEX idx_app_logs_level      ON app_logs (level);
CREATE INDEX idx_app_logs_created_at ON app_logs (created_at);
CREATE INDEX idx_app_logs_logger     ON app_logs (logger_name);

-- ============================================================
-- Dialect notes
-- ============================================================
-- PostgreSQL: use BIGSERIAL/IDENTITY for id, UUID type + gen_random_uuid() for request_id,
--             JSONB instead of TEXT for query_params/request_body/old_values/new_values/context, INET for ip_address.
-- MySQL:      use BIGINT AUTO_INCREMENT for id, CHAR(36) for request_id (UUID() at insert time),
--             JSON type for the JSON-encoded columns (MySQL 5.7.8+).
-- SQL Server: use BIGINT IDENTITY(1,1), UNIQUEIDENTIFIER for request_id, NVARCHAR(MAX) for JSON columns.
-- SQLite:     use INTEGER PRIMARY KEY AUTOINCREMENT, TEXT for request_id/JSON columns (no native JSON/UUID type).
--
-- app_logs is deliberately NOT foreign-keyed to request_logs/audit_logs (per design decision: it must
-- work standalone from background jobs, startup code, and any non-HTTP context). request_id is a soft
-- correlation column only; do not add a FK constraint on it.
