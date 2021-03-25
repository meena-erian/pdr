# Reflector

The reflector app is the main app of the Pantograph Database Replicator.
 It contains all the computer instructions and models for handling 
 and managing the replication processes.

If you would like to contribute to Pantograph Database Replicator or 
understaing how it works internally, Then this README file is where you should start.

<br />

## How it works

1. Both source and destination databases need to be added in the [pdr server](#pdr-server) with read and write access in order to perform replications.
2. Once a database table is defined as a [SourceTable](#SourceTable), a notification channel table is created AKA [pdr table](#pdr-table). And trigger functions are installed in the database to add [pdr event](#pdr-event) records to the [pdr table](#pdr-table) for any change occurring in any record in the specified table.
3. Once any record in a [SourceTable](#SourceTable) is inserted, updated, or deleted, all information regarding such change is stacked in a [pdr event](#pdr-event) record in the [pdr table](#pdr-table) associated with the specified [SourceTable](#SourceTable).
4. After declaring a table as a [SourceTable](#SourceTable), a [Reflection](#Reflection) can be created for such table in any database connected to the [pdr server](#pdr-server), 
5. The [pdr server](#pdr-server) listens for [pdr event](#pdr-event)s for each active reflection. 
6. Once new [pdr event](#pdr-event)s are added for any [SourceTable](#SourceTable), the [pdr server](#pdr-server) replicates the changes to the remote table defined as a [Reflection](#Reflection) and saves the id of the last replicated event in order to mark the [pdr event](#pdr-event) as read.

<br />

## Important items in this directory

1. **[js](/reflector/js) folder:** This folder contains JavaScript templetes for adding some interactivity to the client side.
2. **[sql](/reflector/js) folder:** This folder contains SQL templates used to run advanced database commands that cannot be otherwise performed using SQLAlchemy.
3. **[admin.py](/reflector/admin.py):** This file defines how users can manage PDR from the Django admin portal
4. **[methods.py](/reflector/methods.py):** This file defines some functions for general use such as ```make_query``` and ```make_script``` which are used to load code templates from the folders [sql](/reflector/js) and [js](/reflector/js).
5. **[models.py](/reflector/models.py):** This is basically the core of PDR. it defines not only all data models stored in the pdr server as the server settings but also all methods associated with each.
6. **[views.py](/reflector/views.py):** This file defines server-side APIs used to perform some client-server communication.

<br />
<br />

## Definitions

<br />

### SourceTable

A table defined as a SourceTable is a table meant to be a source of data in a replication process. It informs all of its reflections when any changes occur in any of its records.

<br />

### pdr table

A pdr_table is a table created for each [SourceTable](#SourceTable) in the same database of the [source table](#SourceTable). Each pdr_table functions as a notification channel for a specific [source table](#SourceTable) to update [reflection](#Reflection)s with any changes occurring in any records in the [SourceTable](#SourceTable) by appending pdr_event records for each affected record.

<br />

### pdr event

A pdr_event is a record in a pdr_table which describes a change that has occurred in a specific record in a [source table](#SourceTable) by identifying the record, the kind of change (INSERT, UPDATE or DELETE) and the exact timestamp at which the change has occurred.

<br />

### pdr server

The pdr server is the running instance of the Django python framework running the PDR app. It’s responsible for keeping all [reflection](#Reflection)s up to date and providing a web-based GUI for managing [reflection](#Reflection)s, database connections, and user authentication.

<br />

### Reflection

A Reflections describes how data is supposed to be replicated from [SourceTable](#SourceTable)s to any other tables in any database whenever any changes occur in any records in the [SourceTable](#SourceTable). A [SourceTable](#SourceTable) might have one or more Reflections, and multiple Reflections from multiple different [SourceTable](#SourceTable)s might be reflecting data to different fields in the same table; The structure of a reflection doesn’t has to be the same as that of the [source table](#SourceTable), as it can be customized by customizing the configurations of the reflection. (destination fields and reflection statement)