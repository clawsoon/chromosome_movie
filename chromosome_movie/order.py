#!/usr/bin/env python3

import sys
import random

import sqlite3

from . import travelling_genome

class Order():

    def __init__(self, cfg):
        self.cfg = cfg
        random.seed(1234)

    def write_db(self):
        # There's probably a cleaner way to do this.

        # WARNING: Everything will go kablooie if you don't use a valid
        # column name, or if you re-use an existing column name that isn't
        # meant for ordering.  No guardrails here.
        if self.cfg.order == 'traveller_45e_30s_105w_40s':
            column_name = self.cfg.order
            description = 'Travelling salesman heuristic from Indian Ocean east of South Africa to southern Pacific west of South America.'
            self.create_order_description(column_name, description)
            self.traveller((45, -30), (-105, -40), column_name)

        elif self.cfg.order == 'traveller_19e_39s_99w_19n':
            column_name = self.cfg.order
            description = 'Travelling salesman heuristic from south of South Africa to Mexico City.'
            self.create_order_description(column_name, description)
            self.traveller((19, -39), (-99, 19), column_name)

        elif self.cfg.order == 'traveller_19e_39s_99w_19n_max1000':
            column_name = self.cfg.order
            description = 'Travelling salesman heuristic from south of South Africa to Mexico City with max route length of 1000.'
            self.create_order_description(column_name, description)
            self.traveller((19, -39), (-99, 19), column_name, 1000)

        elif self.cfg.order == 'traveller_roundtrip_19e_39s_max1000':
            column_name = self.cfg.order
            description = 'Travelling salesman heuristic from south of South Africa and back with max route length of 1000.'
            self.create_order_description(column_name, description)
            self.traveller((19, -39), (19, -39), column_name, 1000)

        else:
            raise Exception('Order "%s" not implemented.' % self.cfg.order)


    def traveller(self, start_location, end_location, column_name, max_route_length=0):

        # TODO: Move the database boilerplate into a separate function?

        update_template = '''
            UPDATE
                variant
            SET
                %s=?
            WHERE
                id=?
        ''' % column_name
            
        database = sqlite3.connect(self.cfg.database_path)
        database.row_factory = sqlite3.Row
        read_cursor = database.cursor()
        write_cursor = database.cursor()

        read_cursor.execute('SELECT DISTINCT time FROM variant')
        times = []
        for row in read_cursor:
            times.append(row['time'])
        times.sort(reverse=True)

        order = 0

        for time in times:
            sys.stderr.write('Time... %s\n' % time)
            sys.stderr.flush()

            read_cursor.execute('''
                SELECT
                    id,
                    average_longitude,
                    average_latitude
                FROM
                    variant
                WHERE
                    time=?
                ''', (time,))

            rows = read_cursor.fetchall()

            if max_route_length and len(rows) > max_route_length:
                random.shuffle(rows)
                route_count = len(rows) // max_route_length + 1
                chunks = [rows[i::route_count] for i in range(route_count)]
                for chunk in chunks:
                    for variant_id in self.traveller_sort(start_location, end_location, chunk):
                        write_cursor.execute(update_template, (order, variant_id))
                        order += 1
            else:
                for variant_id in self.traveller_sort(start_location, end_location, rows):
                    write_cursor.execute(update_template, (order, variant_id))
                    order += 1

        database.commit()
        database.close()

    def traveller_sort(self, start_location, end_location, rows):

        # Start isn't a real location.  It's an arbitrary point we picked.
        locations = [start_location]
        variant_ids = [-1]
        for row in rows:
            locations.append((row['average_longitude'], row['average_latitude']))
            variant_ids.append(row['id'])
        # End isn't a real location.  It's an arbitrary point we picked.
        locations.append(end_location)
        variant_ids.append(-1)

        route = travelling_genome.main(locations)
        # ...so we don't include start_location and end_location in the
        # final route.
        sorted_variant_ids = [variant_ids[i] for i in route[1:-1]]

        for variant_id in sorted_variant_ids:
            yield variant_id


    def create_order_description(self, column_name, description):

        # There's probably a better way to store column names and descriptions,
        # but this will do for now.

        database = sqlite3.connect(self.cfg.database_path)
        cursor = database.cursor()
        cursor.execute('''
            CREATE TABLE IF NOT EXISTS variant_order_description (
                id INTEGER PRIMARY KEY,
                column_name TEXT UNIQUE NOT NULL,
                description TEXT
            )
        ''')

        cursor.execute('''
            SELECT
                *
            FROM
                variant_order_description
            WHERE
                column_name=?
            ''', (column_name,))

        if not cursor.fetchone():
            cursor.execute('''
                INSERT INTO variant_order_description (
                    column_name,
                    description
                )
                VALUES
                    (?, ?)
                ''', (column_name, description))
            cursor.execute('''
                ALTER TABLE
                    variant
                ADD COLUMN
                    %s INTEGER
                ''' % column_name)
            cursor.execute('''
                CREATE INDEX %s_idx
                    ON variant (%s)
                ''' % (column_name, column_name))
        database.commit()
        database.close()

