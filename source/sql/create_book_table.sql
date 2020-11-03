CREATE TABLE IF NOT EXISTS book
(
  id             INTEGER      NOT NULL
    CONSTRAINT book_pkey PRIMARY KEY,
  title          VARCHAR(255) NOT NULL,
  lang           VARCHAR(2)   NOT NULL,
  file_type      VARCHAR(4)   NOT NULL,
  uploaded       DATE         NOT NULL DEFAULT CURRENT_DATE,
  search_content tsvector     NOT NULL,
);
ALTER TABLE book
  OWNER TO {};
CREATE INDEX IF NOT EXISTS book_search_content2 ON book USING GIN (title gin_trgm_ops);
