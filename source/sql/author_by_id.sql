WITH author_books AS (
  SELECT * FROM book
  LEFT JOIN bookauthor ba ON book.id = ba.book_id
  WHERE ba.author_id = $2 AND book.lang = ANY ($1::text[])
)
SELECT json_build_object(
  'count', ( SELECT COUNT(*) FROM author_books ),
  'result', (SELECT json_build_object(
              'id', author.id,
              'first_name', author.first_name,
              'last_name', author.last_name,
              'middle_name', author.middle_name,
              'annotation_exists', EXISTS(
                  SELECT * FROM author_annotation WHERE author_annotation.author_id = author.id
                ),
              'books', (
                SELECT array_to_json(array_agg(row_to_json(book)))
                FROM (
                        SELECT tbook.book_id as id, tbook.title, tbook.lang, tbook.file_type,
                        EXISTS(SELECT * FROM book_annotation 
                               WHERE book_annotation.book_id = tbook.book_id) as annotation_exists,
                        (SELECT array_to_json(array_agg(row_to_json(translator)))
                          FROM (
                            SELECT author.id, first_name, last_name, middle_name
                            FROM author
                                    LEFT JOIN translator tr on author.id = tr.translator_id
                            WHERE tr.book_id = tbook.book_id ORDER BY tr.pos) translator 
                        ) as translators
                        FROM author_books as tbook
                        ORDER BY title
                        LIMIT $3 OFFSET $4) book))
 FROM author WHERE author.id = $2 )
) as json;