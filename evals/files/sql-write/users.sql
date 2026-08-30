-- users(id text PK, email text UNIQUE, active boolean)
-- Writes in this file always filter on a key.

UPDATE users SET last_seen = now() WHERE id = $1;
