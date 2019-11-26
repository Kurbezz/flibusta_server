// TODO

SELECT json_build_object(
    'count', ( SELECT count(*) FROM updated_books ),
    'result', (
        SELECT array_to_json(array_agg(j.json_build_object))
        FROM (
            SELECT json_build_object(
                'id', book.id,
                'title', book.title,
                'lang', book.lang,
                'file_type', book.file_type,
                'annotation_exists', EXISTS(
                    SELECT * FROM book_annotation WHERE book_annotation.book_id = book.id ),
                'authors', (
                    SELECT array_to_json(array_agg(row_to_json(author)))
                    FROM (SELECT id, first_name, last_name, middle_name FROM author) author
                        LEFT JOIN bookauthor ba ON author.id = ba.author_id
                    WHERE ba.book_id = book.id))
            FROM updated_books as book
            ORDER BY book.id
            LIMIT $4 OFFSET $5) j)
) as json;