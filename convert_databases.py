"""
In version 0.3 the structure of the database table changed.

This script will convert the databases created in version < 0.3
to be compatible with version 0.3 of pr-omega-logger.

Update the value of log_dir below to be the value of the <log_dir>
XML element in the configuration file and then run this script.

After running this script you will also need to update MSL-Equipment
in the Python environment:

pip install -U https://github.com/MSLNZ/msl-equipment/archive/main.zip

"""
import os
import sys
import shutil
import sqlite3
from contextlib import closing

# Update to be the directory where the *.sqlite3 databases are located
log_dir = 'UPDATE!'


db_files = []
for filename in os.listdir(log_dir):
    if not (filename.startswith('iTHX') and filename.endswith('.sqlite3')):
        continue

    if filename.endswith('-new.sqlite3'):
        os.remove(os.path.join(log_dir, filename))
        continue

    db_files.append(filename)

if not db_files:
    sys.exit(f'There are no databases in {log_dir}')

for filename in db_files:
    print(filename)

    # make a backup of the original
    original_database = os.path.join(log_dir, filename)
    backup_database = os.path.join(log_dir, 'original-backup', filename)
    os.makedirs(os.path.join(log_dir, 'original-backup'), exist_ok=True)
    shutil.copy2(original_database, backup_database)

    # create the new database
    new_database = original_database.replace('.sqlite3', '-new.sqlite3')
    with closing(sqlite3.connect(original_database)) as orig:
        with closing(sqlite3.connect(new_database)) as new:
            cursor = orig.cursor()
            cursor.execute('SELECT * from data;')
            row = cursor.fetchone()
            if len(row) == 4:
                new.execute(
                    'CREATE TABLE data ('
                    'pid INTEGER PRIMARY KEY AUTOINCREMENT, '
                    'datetime DATETIME, '
                    'temperature FLOAT, '
                    'humidity FLOAT, '
                    'dewpoint FLOAT);'
                )
            else:
                new.execute(
                    'CREATE TABLE data ('
                    'pid INTEGER PRIMARY KEY AUTOINCREMENT, '
                    'datetime DATETIME, '
                    'temperature1 FLOAT, '
                    'humidity1 FLOAT, '
                    'dewpoint1 FLOAT, '
                    'temperature2 FLOAT, '
                    'humidity2 FLOAT, '
                    'dewpoint2 FLOAT);'
                )
            new.commit()

    # insert the data into the new database
    print('  inserting data...')
    with closing(sqlite3.connect(original_database)) as orig:
        with closing(sqlite3.connect(new_database)) as new:
            cursor = orig.cursor()
            cursor.execute('SELECT * from data;')
            for i, row in enumerate(cursor.fetchall()):
                date_time = row[0][:10]+'T'+row[0][11:19]
                assert len(date_time) == 19
                values = (date_time, *row[1:])
                if len(values) == 4:
                    new.execute('INSERT INTO data VALUES (NULL, ?, ?, ?, ?);', values)
                else:
                    new.execute('INSERT INTO data VALUES (NULL, ?, ?, ?, ?, ?, ?, ?);', values)
                if i % 10000 == 0:
                    print(f'  at row {i} -- INSERTED', values)
            new.commit()

    # verify the data was inserted correctly
    print('  loading databases to verify...')
    with closing(sqlite3.connect(original_database)) as orig:
        cursor_orig = orig.cursor()
        cursor_orig.execute('SELECT * from data;')
        data_orig = cursor_orig.fetchall()
    with closing(sqlite3.connect(new_database)) as new:
        cursor_new = new.cursor()
        cursor_new.execute('SELECT * from data;')
        data_new = cursor_new.fetchall()
    assert len(data_orig) == len(data_new)
    for i, (row_orig, row_new) in enumerate(zip(data_orig, data_new)):
        assert row_new[0] == i+1, f'{row_new[0]} != {i+1}'
        assert row_orig[0].replace(' ', 'T')[:19] == row_new[1], f'{row_orig[0]} != {row_new[1]}'
        assert row_orig[1:] == row_new[2:], f'{row_orig[1:]} != {row_new[2:]}'
        if i % 10000 == 0:
            print(f'  at row {i} -- VERIFIED!')

    # conversion successful, replace original database
    os.remove(original_database)
    os.rename(new_database, original_database)


print('The databases have been converted. The original databases have been moved to:')
print(os.path.join(log_dir, 'original-backup'))
