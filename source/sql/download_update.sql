INSERT INTO download (book_id, user_id, last) VALUES ($1, $2, $3) 
ON CONFLICT (book_id, user_id) DO UPDATE SET last = EXCLUDED.last;