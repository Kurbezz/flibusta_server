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
             FROM (
                SELECT author.id, first_name, last_name, middle_name
                FROM author
                        LEFT JOIN bookauthor ba ON author.id = ba.author_id
                WHERE ba.book_id = book.id) author
           ),
           'translators', (
              SELECT array_to_json(array_agg(row_to_json(translator)))
              FROM (
                     SELECT author.id, first_name, last_name, middle_name
                     FROM author
                            LEFT JOIN translator tr on author.id = tr.translator_id
                     WHERE tr.book_id = book.id ORDER BY tr.pos) translator 
           )
         ) as json
FROM book WHERE lang = ANY($1::text[]) AND random() < 0.2 ORDER BY random() LIMIT 1;