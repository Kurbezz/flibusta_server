SELECT json_build_object(
       'id', author.id,
       'first_name', author.first_name,
       'last_name', author.last_name,
       'middle_name', author.middle_name,
       'annotation_exists', EXISTS(
              SELECT * FROM author_annotation WHERE author_annotation.author_id = author.id
       )
) as json
FROM author
WHERE (SELECT count(*)
       FROM bookauthor
              RIGHT JOIN book ON bookauthor.book_id = book.id
       WHERE book.lang = ANY ($1::text[])
              AND bookauthor.author_id = author.id) <> 0 AND random() < 0.2
ORDER BY random() LIMIT 1;