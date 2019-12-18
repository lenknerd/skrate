-- Get recent success rate of a user for each trick, over last X attempts of that trick
-- Incidentally, the table name in attempt.user is important here - see
-- https://dba.stackexchange.com/questions/75551/returning-rows-in-postgresql-with-a-table-called-user


-- First get all attempts by user, indexed by how many times user has tried that trick since 
WITH attempts_indexed AS 
( 
         SELECT   trick_id, 
                  Row_number() OVER (partition BY trick_id ORDER BY time_of_attempt DESC) AS tries_ago,
                  landed 
         FROM     attempt 
         WHERE    attempt.USER = :username ) 
-- Limit at most to only the last _ times we tried each trick 
, attempts_recent AS 
( 
         SELECT   trick_id, 
                  Sum( 
                  CASE 
                           WHEN landed THEN 1 
                           ELSE 0 
                  END) AS n_landed, 
                  Sum( 
                  CASE 
                           WHEN landed THEN 0 
                           ELSE 1 
                  END) AS n_missed 
         FROM     attempts_indexed 
         WHERE    tries_ago <= :nlimit 
         GROUP BY trick_id ) 
-- If we've used up all the tricks tried before, try one we haven't tried (with 0% chance) 
, tricks_not_tried AS 
( 
       SELECT id, 
              0.0 AS land_rate_recent 
       FROM   trick 
       WHERE  id NOT IN 
              ( 
                     SELECT trick_id 
                     FROM   attempt 
                     WHERE  attempt.USER = :username) ) 
-- Divide out for success rate, handle div by 0 error 
, unordered AS 
( 
       SELECT trick_id, 
              CASE 
                     WHEN n_landed          + n_missed = 0 THEN 0.0 
                     ELSE n_landed::decimal / (n_landed + n_missed)::decimal 
              END AS land_rate_recent 
       FROM   attempts_recent ) 
-- Lastly combined tried and not tried, and sort for best success rates first 
SELECT * 
FROM     unordered 
UNION ALL
SELECT *
FROM     tricks_not_tried
ORDER BY land_rate_recent DESC
