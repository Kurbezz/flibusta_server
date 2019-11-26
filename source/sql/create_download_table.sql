CREATE TABLE IF NOT EXISTS download
(
    book_id INTEGER NOT NULL,
    user_id INTEGER NOT NULL,
    last DATE NOT NULL,
    PRIMARY KEY (book_id, user_id)
);
ALTER TABLE download OWNER TO {};