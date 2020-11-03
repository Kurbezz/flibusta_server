WITH filtered_authors AS (
  SELECT *, 
    similarity((last_name || ' ' || first_name || ' ' || middle_name), $1) as sml 
  FROM author
  WHERE EXISTS (SELECT *
    FROM bookauthor
            RIGHT JOIN book ON bookauthor.book_id = book.id
    WHERE book.lang = ANY ($2::text[])
      AND bookauthor.author_id = author.id) 
    AND (last_name || ' ' || first_name || ' ' || middle_name) % $1
)
SELECT json_build_object(
  'count', (SELECT COUNT(*) FROM filtered_authors),
  'result', (SELECT array_to_json(array_agg(j.json_build_object))
    FROM (
        select json_build_object(
                    'id', author.id,
                    'first_name', author.first_name,
                    'last_name', author.last_name,
                    'middle_name', author.middle_name,
                    'annotation_exists', EXISTS(
                      SELECT * FROM author_annotation WHERE author_annotation.author_id = author.id
                    )
        )
        FROM filtered_authors AS author
        ORDER BY author.sml DESC,
                  (SELECT count(*)
                   FROM bookauthor
                   WHERE bookauthor.author_id = author.id) DESC, author.id
        LIMIT $3 OFFSET $4) j
  )
) AS json;
