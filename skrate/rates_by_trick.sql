-- Get recent success rate of a user for each trick, over last X attempts of that trick (minus most
-- recent, for in current game of SKATE). FYI the table name in attempt.user is important here - see
-- https://dba.stackexchange.com/questions/75551/returning-rows-in-postgresql-with-a-table-called-user


-- First get all attempts by user, indexed by how many times user has tried that trick since 
WITH attempts_indexed AS 
( 
         SELECT   trick_id, 
                  Row_number() OVER (partition BY trick_id ORDER BY time_of_attempt DESC) AS tries_ago,
                  landed 
         FROM     attempt 
         WHERE    attempt.USER = :username ) 
-- Limit at most to only the last _ times we tried each trick, minus most recent
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
         WHERE    tries_ago <= :nlimit and tries_ago > :nmin
         GROUP BY trick_id ) 
-- If above data set doesn't provide insight on a trick, fallback any trick is 0.0 
, all_tricks_zeros AS 
( 
       SELECT id as trick_id, 
              0.0 AS land_rate_recent 
       FROM   trick ) 
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
SELECT all_tricks_zeros.trick_id,
       coalesce(unordered.land_rate_recent, all_tricks_zeros.land_rate_recent) as land_rate_recent
FROM   unordered
RIGHT OUTER JOIN all_tricks_zeros
              ON unordered.trick_id = all_tricks_zeros.trick_id
ORDER BY 2 DESC
