SELECT json_build_object(
               'id', seqname.seq_id,
               'name', name,
               'authors', (
                   SELECT array_to_json(array_agg(row_to_json(author)))
                   FROM (select a.id, a.first_name, a.last_name, a.middle_name
                         from seq
                                  inner join book b on seq.book_id = b.id
                                  inner join bookauthor b2 on b.id = b2.book_id
                                  inner join author a on b2.author_id = a.id
                         where seq.seq_id = seqname.seq_id
                           and b.lang = any ($1::text[])
                         group by a.id
                         order by (select count(*)
                                   from seq
                                            inner join book b on seq.book_id = b.id
                                            inner join bookauthor b2 on b.id = b2.book_id and b2.author_id = a.id
                                   where seq.seq_id = seqname.seq_id) desc
                         ) author
               ))
FROM seqname
WHERE (SELECT count(*) FROM seq INNER JOIN book b ON b.id = seq.book_id WHERE b.lang = ANY($1::text[])) <> 0 
  AND random() < 0.2
ORDER BY random() LIMIT 1;
