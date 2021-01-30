SELECT 
    CONCAT(table_schema, '.', table_name) AS "Table" 
FROM 
    information_schema.tables;