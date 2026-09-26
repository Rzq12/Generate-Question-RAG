CREATE TABLE IF NOT EXISTS documents (
    document_id TEXT PRIMARY KEY,
    filename TEXT NOT NULL,
    file_hash CHAR(64) NOT NULL UNIQUE,
    created_at TIMESTAMPTZ NOT NULL DEFAULT now()
);

CREATE TABLE IF NOT EXISTS pages (
    document_id TEXT NOT NULL REFERENCES documents(document_id) ON DELETE CASCADE,
    page_number INTEGER NOT NULL CHECK (page_number > 0),
    text_content TEXT NOT NULL,
    source_hash CHAR(64) NOT NULL,
    PRIMARY KEY (document_id, page_number)
);

CREATE TABLE IF NOT EXISTS image_contents (
    document_id TEXT NOT NULL,
    page_number INTEGER NOT NULL,
    image_id TEXT NOT NULL,
    meaningful BOOLEAN NOT NULL,
    extracted_text TEXT NOT NULL,
    description TEXT,
    confidence DOUBLE PRECISION NOT NULL CHECK (confidence BETWEEN 0 AND 1),
    provider TEXT NOT NULL,
    model TEXT NOT NULL,
    PRIMARY KEY (document_id, image_id),
    FOREIGN KEY (document_id, page_number) REFERENCES pages(document_id, page_number) ON DELETE CASCADE
);

CREATE TABLE IF NOT EXISTS chunks (
    chunk_id TEXT PRIMARY KEY,
    document_id TEXT NOT NULL REFERENCES documents(document_id) ON DELETE CASCADE,
    page_number INTEGER NOT NULL,
    text_content TEXT NOT NULL,
    source_hash CHAR(64) NOT NULL,
    UNIQUE (document_id, chunk_id)
);
