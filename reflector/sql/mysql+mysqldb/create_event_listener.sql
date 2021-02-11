-- VARIABLES
-- {0} $pdr_prefix$
-- {1} $Schema$
-- {2} $Table$
-- {3} $Pk$
DROP TRIGGER IF EXISTS {1}.on_{2}_insert;


DROP TRIGGER IF EXISTS {1}.on_{2}_update;


DROP TRIGGER IF EXISTS {1}.on_{2}_delete;


CREATE TRIGGER on_{2}_insert
AFTER
INSERT
ON {1}.{2} FOR EACH ROW 
INSERT INTO 
      {0}_o_{1}_o_{2}(
            c_action,
            c_record,
            c_time
      )
      VALUES (
          'INSERT',
          NEW.{3},
          CURRENT_TIMESTAMP
	);


CREATE TRIGGER on_{2}_update
AFTER
UPDATE
ON {1}.{2} FOR EACH ROW 
INSERT INTO 
      {0}_o_{1}_o_{2}(
            c_action,
            c_record,
            c_time
      )
      VALUES (
          'UPDATE',
          NEW.{3},
          CURRENT_TIMESTAMP
	);


CREATE TRIGGER on_{2}_delete
AFTER
DELETE
ON {1}.{2} FOR EACH ROW 
INSERT INTO 
      {0}_o_{1}_o_{2}(
            c_action,
            c_record,
            c_time
      )
      VALUES (
          'DELETE',
          OLD.{3},
          CURRENT_TIMESTAMP
	);