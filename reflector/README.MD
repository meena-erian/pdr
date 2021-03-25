# Reflector

The reflector app is the main app of the Pantograph Database Replicator.
 It contains all the computer instructions and models for handling 
 and managing the replication processes.

If you would like to contribute to Pantograph Database Replicator or 
understaing how it works internally, Then this README file is where you should start.


## How it works

1. Both source and destination databases need to be added in the pdr server with read and write access in order to perform replications.
2. Once a database table is defined as a SourceTable, a notification channel table is created AKA pdr table. And trigger functions are installed in the database to add pdr event records to the pdr table for any change occurring in any record in the specified table.
3. Once any record in a SourceTable is inserted, updated, or deleted, all information regarding such change is stacked in a pdr event record in the pdr table associated with the specified SourceTable.
4. After declaring a table as a SourceTable, a Reflection can be created for such table in any database connected to the pdr server, 
5. The pdr server listens for pdr events for each active reflection. 
6. Once new pdr events are added for any SourceTable, the pdr server replicates the changes to the remote table defined as a Reflection and saves the id of the last replicated event in order to mark the pdr event as read.

## Definitions

<br />

### SourceTable

A table defined as a SourceTable is a table meant to be a source of data in a replication process. It informs all of its reflections when any changes occur in any of its records.

<br />

### pdr table

A pdr_table is a table created for each SourceTable in the same database of the source table. Each pdr_table functions as a notification channel for a specific source table to update reflections with any changes occurring in any records in the SourceTable by appending pdr_event records for each affected record.

<br />

### pdr event

A pdr_event is a record in a pdr_table which describes a change that has occurred in a specific record in a source table by identifying the record, the kind of change (INSERT, UPDATE or DELETE) and the exact timestamp at which the change has occurred.

<br />

### pdr server

The pdr server is the running instance of the Django python framework running the PDR app. It’s responsible for keeping all reflections up to date and providing a web-based GUI for managing reflections, database connections, and user authentication.

<br />

### Reflection

A Reflections describes how data is supposed to be replicated from SourceTables to any other tables in any database whenever any changes occur in any records in the SourceTable. A SourceTable might have one or more Reflections, and multiple Reflections from multiple different SourceTables might be reflecting data to different fields in the same table; The structure of a reflection doesn’t has to be the same as that of the source table, as it can be customized by customizing the configurations of the reflection. (destination fields and reflection statement)