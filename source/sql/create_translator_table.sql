CREATE TABLE IF NOT EXISTS translator (
    book_id INTEGER NOT NULL
        CONSTRAINT translator_book_id_fkey REFERENCES book,
    translator_id INTEGER NOT NULL
        CONSTRAINT translator_author_id_fkey REFERENCES author,
    pos INTEGER NOT NULL,
    PRIMARY KEY (book_id, translator_id)
);
ALTER TABLE translator
    OWNER TO {};
CREATE INDEX IF NOT EXISTS translator_book_id ON translator (book_id);