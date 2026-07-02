# Centralized Logging Schema (NoSQL / Document Store)

Same three-collection split as the SQL schema (`reference/log-schema-sql.sql`): `requestLogs`,
`auditLogs`, and `appLogs`. Field names below use camelCase, the common convention for document
stores (MongoDB, DynamoDB, Firestore). Adjust casing to match the target project's existing
convention.

## Collection: `requestLogs`

```json
{
  "_id": "ObjectId/UUID",
  "requestId": "uuid-v4",
  "userId": "string|null",
  "username": "string|null",
  "ipAddress": "string",
  "userAgent": "string|null",
  "httpMethod": "POST",
  "endpoint": "/persons",
  "module": "Users",
  "action": "BulkInsertUser",
  "queryParams": { "...": "..." },
  "requestBody": { "...": "redacted of sensitive fields" },
  "responseStatus": 200,
  "responseTimeMs": 42,
  "errorMessage": "string|null",
  "createdAt": "ISODate"
}
```

## Collection: `auditLogs`

```json
{
  "_id": "ObjectId/UUID",
  "requestId": "uuid-v4|null",
  "userId": "string|null",
  "username": "string|null",
  "actionType": "INSERT | UPDATE | DELETE | BULK_INSERT | BULK_UPDATE | BULK_DELETE",
  "tableName": "GoUsers",
  "recordId": "string|null",
  "affectedCount": "number|null",
  "oldValues": { "...": "..." },
  "newValues": { "...": "..." },
  "ipAddress": "string|null",
  "createdAt": "ISODate"
}
```

## Collection: `appLogs`

General-purpose application logging (TRACE/DEBUG/INFO/WARN/ERROR/FATAL), independent of HTTP
context. Populated by a logging-library sink/handler/transport, not by request middleware.

```json
{
  "_id": "ObjectId/UUID",
  "level": "TRACE | DEBUG | INFO | WARN | ERROR | FATAL",
  "message": "string",
  "loggerName": "string|null",
  "sourceLocation": "string|null",
  "context": { "...": "redacted of sensitive fields" },
  "stackTrace": "string|null",
  "requestId": "uuid-v4|null",
  "environment": "string|null",
  "hostname": "string|null",
  "createdAt": "ISODate"
}
```

`requestId` is a soft correlation field only (this collection must keep working standalone for
background jobs, startup code, and any other non-HTTP context); do not require it.

## Indexes (MongoDB example)

```js
db.requestLogs.createIndex({ userId: 1 });
db.requestLogs.createIndex({ createdAt: -1 });
db.requestLogs.createIndex({ endpoint: 1 });
db.requestLogs.createIndex({ requestId: 1 }, { unique: true });

db.auditLogs.createIndex({ tableName: 1, recordId: 1 });
db.auditLogs.createIndex({ userId: 1 });
db.auditLogs.createIndex({ createdAt: -1 });
db.auditLogs.createIndex({ requestId: 1 });

db.appLogs.createIndex({ level: 1 });
db.appLogs.createIndex({ createdAt: -1 });
db.appLogs.createIndex({ loggerName: 1 });
```

## Notes

- Document stores have no native foreign keys; `requestId` is the correlation key linking an
  `auditLogs`/`appLogs` entry back to the `requestLogs` entry that triggered it. Enforce the link in
  application code, not the database.
- Consider a TTL index (`createdAt`) on `requestLogs` and `appLogs` if those only need
  short-to-medium retention, while keeping `auditLogs` indefinitely for compliance.
- For very high write volume, write logs to an append-only/time-series collection or a separate
  logging-specific database instance so log writes never contend with primary OLTP traffic. This
  matters most for `appLogs`, since DEBUG/TRACE volume can be orders of magnitude higher than
  request or audit volume.
