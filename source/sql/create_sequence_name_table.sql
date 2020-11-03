CREATE TABLE IF NOT EXISTS seqname
(
  seq_id         INTEGER      NOT NULL
    CONSTRAINT seqname_seq PRIMARY KEY,
  name           VARCHAR(255) NOT NULL,
  search_content tsvector     NOT NULL
);
ALTER TABLE seqname
  OWNER TO {};
CREATE INDEX IF NOT EXISTS seqname_search_content2 ON seqname USING GIN (name gin_trgm_ops);
