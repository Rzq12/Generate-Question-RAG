ALTER TABLE documents ADD COLUMN IF NOT EXISTS status TEXT NOT NULL DEFAULT 'completed';
ALTER TABLE documents ADD COLUMN IF NOT EXISTS error_message TEXT;

ALTER TABLE documents DROP CONSTRAINT IF EXISTS documents_status_check;
ALTER TABLE documents ADD CONSTRAINT documents_status_check
    CHECK (status IN ('processing', 'completed', 'failed'));

CREATE TABLE IF NOT EXISTS chunks (
    chunk_id TEXT PRIMARY KEY,
    document_id TEXT NOT NULL REFERENCES documents(document_id) ON DELETE CASCADE,
    page_number INTEGER NOT NULL,
    text_content TEXT NOT NULL,
    source_hash CHAR(64) NOT NULL,
    UNIQUE (document_id, chunk_id)
);