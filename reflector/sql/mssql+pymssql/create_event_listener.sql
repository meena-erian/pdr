-- VARIABLES
-- {0} $pdr_prefix$
-- {1} $Schema$
-- {2} $Table$
-- {3} $Pk$
CREATE OR ALTER TRIGGER {1}.on_{2}_change ON {2}
AFTER
INSERT, UPDATE, DELETE 
AS 
BEGIN
DECLARE @Action as char(6);
SET @Action = (
            CASE
                  WHEN EXISTS(
                        SELECT *
                        FROM INSERTED
                  )
                  AND EXISTS(
                        SELECT *
                        FROM DELETED
                  ) THEN 'UPDATE'
                  WHEN EXISTS(
                        SELECT *
                        FROM INSERTED
                  ) THEN 'INSERT'
                  WHEN EXISTS(
                        SELECT *
                        FROM DELETED
                  ) THEN 'DELETE'
                  ELSE NULL
            END
      );
INSERT INTO 
      "{0}_o_{1}_o_{2}"(
            c_action,
            c_record,
            c_time
      )
      SELECT
          @Action,
          {3},
          CURRENT_TIMESTAMP
      FROM 
          INSERTED 
      UNION 
          SELECT
            @Action,
            {3},
            CURRENT_TIMESTAMP
          FROM 
            DELETED
      GROUP BY {3};
END