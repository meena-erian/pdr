-- {0} prefix
-- {1} Schema
-- {2} table
DROP TRIGGER IF EXISTS {2}_insert ON {1}.{2};
DROP TRIGGER IF EXISTS {2}_update ON {1}.{2};
DROP TRIGGER IF EXISTS {2}_delete ON {1}.{2};


DROP FUNCTION IF EXISTS {1}.on_{2}_insert();
DROP FUNCTION IF EXISTS {1}.on_{2}_update();
DROP FUNCTION IF EXISTS {1}.on_{2}_delete();


DROP TABLE IF EXISTS "{0}_o_{1}_o_{2}" CASCADE;