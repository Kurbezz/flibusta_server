WITH filtered_books AS ( 
  SELECT *, similarity(title, $2) as sml FROM book
  WHERE lang = ANY ($1::text[]) AND book.title % $2
)
SELECT json_build_object(
    'count', ( SELECT COUNT(*) FROM filtered_books), 
    'result', ( SELECT array_to_json(array_agg(j.json_build_object))
      FROM (
       SELECT json_build_object(
                  'id', book.id,
                  'title', book.title,
                  'lang', book.lang,
                  'file_type', book.file_type,
                  'annotation_exists', EXISTS(
                    SELECT * FROM book_annotation WHERE book_annotation.book_id = book.id
                  ),
                  'authors', (
                    SELECT array_to_json(array_agg(row_to_json(author)))
                    FROM (SELECT id, first_name, last_name, middle_name FROM author) author
                           LEFT JOIN bookauthor ba ON author.id = ba.author_id
                    WHERE ba.book_id = book.id),
                  'translators', (
                    SELECT array_to_json(array_agg(row_to_json(translator)))
                    FROM (
                          SELECT author.id, first_name, last_name, middle_name
                          FROM author
                                  LEFT JOIN translator tr on author.id = tr.translator_id
                          WHERE tr.book_id = book.id ORDER BY tr.pos) translator 
                  ))
       FROM filtered_books AS book
       ORDER BY book.sml DESC, book.title
       LIMIT $3 OFFSET $4) j
    )
) as json;