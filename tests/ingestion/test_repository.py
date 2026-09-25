from app.ingestion.contracts import ImageContent, PageContent, ParsedDocument
from app.ingestion.repository import IngestionRepository


class Cursor:
    def __init__(self, rows=(), rowcount=1):
        self.rows = list(rows)
        self.rowcount = rowcount
        self.queries = []

    def __enter__(self):
        return self

    def __exit__(self, *_):
        return False

    def execute(self, query, params):
        self.queries.append((query, params))

    def fetchone(self):
        return self.rows.pop(0)

    def fetchall(self):
        return self.rows.pop(0)


class Connection:
    def __init__(self, cursors):
        self.cursors = iter(cursors)
        self.commits = 0

    def cursor(self):
        return next(self.cursors)

    def commit(self):
        self.commits += 1


def document():
    return ParsedDocument(
        document_id="doc-1",
        filename="source.pdf",
        file_hash="a" * 64,
        pages=(PageContent(
            document_id="doc-1", page_number=1, text="plain text", source_hash="b" * 64,
            images=(ImageContent(image_id="p1-i1", page_number=1, meaningful=True, extracted_text="image evidence", confidence=1, provider="test", model="fixture"),),
        ),),
    )


def test_get_by_hash_reconstructs_pages_and_images():
    connection = Connection([
        Cursor(rows=[("doc-1", "source.pdf", "a" * 64), [(1, "plain text", "b" * 64)], [(1, "p1-i1", True, "image evidence", None, 1, "test", "fixture")]]),
    ])

    result = IngestionRepository(connection).get_by_hash("a" * 64)

    assert result == document()


def test_save_duplicate_hash_is_noop():
    connection = Connection([Cursor(rows=[], rowcount=0)])

    IngestionRepository(connection).save(document())

    assert connection.commits == 1
