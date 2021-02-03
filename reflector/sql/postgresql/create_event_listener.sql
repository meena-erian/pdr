-- VARIABLES
-- {0} $pdr_prefix$
-- {1} $Schema$
-- {2} $Table$
-- {3} $Pk$
CREATE OR REPLACE FUNCTION {1}.on_{2}_insert() RETURNS TRIGGER LANGUAGE plpgsql
AS $$
   BEGIN 
      INSERT INTO 
        "{0}_o_{1}_o_{2}"(
            c_action,
            c_record,
            c_time
      ) VALUES (
          'INSERT',
          new.{3},
          CURRENT_TIMESTAMP
      );
      RETURN NEW;
   END;
$$;


CREATE OR REPLACE FUNCTION {1}.on_{2}_update() RETURNS TRIGGER LANGUAGE plpgsql
AS $$
   BEGIN 
      INSERT INTO 
        "{0}_o_{1}_o_{2}"(
            c_action,
            c_record,
            c_time
      ) VALUES (
          'UPDATE',
          new.{3},
          CURRENT_TIMESTAMP 
      );
      RETURN NEW;
   END;
$$;


CREATE OR REPLACE FUNCTION {1}.on_{2}_delete() RETURNS TRIGGER LANGUAGE plpgsql
AS $$
   BEGIN 
      INSERT INTO 
        "{0}_o_{1}_o_{2}"(
            c_action,
            c_record,
            c_time
      ) VALUES (
          'DELETE',
          old.{3},
          CURRENT_TIMESTAMP 
      );
      RETURN OLD;
   END;
$$;


DROP TRIGGER IF EXISTS {2}_insert
  ON {1}.{2};
CREATE TRIGGER {2}_insert
  AFTER INSERT ON {1}.{2}
  FOR EACH ROW
  EXECUTE PROCEDURE {1}.on_{2}_insert();


DROP TRIGGER IF EXISTS {2}_update
  ON {1}.{2};
CREATE TRIGGER {2}_update
  AFTER UPDATE ON {1}.{2}
  FOR EACH ROW
  EXECUTE PROCEDURE {1}.on_{2}_update();


DROP TRIGGER IF EXISTS {2}_delete
  ON {1}.{2};
CREATE TRIGGER {2}_delete
  AFTER DELETE ON {1}.{2}
  FOR EACH ROW
  EXECUTE PROCEDURE {1}.on_{2}_delete();