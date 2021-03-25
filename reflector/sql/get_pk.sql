-- VARIABLES
-- {0} $Schema$
-- {2} $Table$
SELECT
    kcu.column_name as "PRIMARY_KEY",
    c.data_type as "DATA_TYPE"
FROM 
    information_schema.key_column_usage AS kcu
    JOIN information_schema.table_constraints AS tc 
    ON tc.constraint_name = kcu.constraint_name
    AND tc.table_schema = kcu.table_schema
    JOIN information_schema.columns AS c
    ON c.table_schema = kcu.table_schema and c.table_name = kcu.table_name and c.column_name = kcu.column_name 
WHERE tc.constraint_type = 'PRIMARY KEY' and kcu.table_schema = '{0}' and kcu.table_name = '{1}';
