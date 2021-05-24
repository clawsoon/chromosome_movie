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

        elif self.cfg.order == 'traveller_roundtrip_19e_39s_max480':
            column_name = self.cfg.order
            description = 'Travelling salesman heuristic from south of South Africa and back with max route length of 480.'
            self.create_order_description(column_name, description)
            self.traveller((19, -39), (19, -39), column_name, 480)

        elif self.cfg.order == 'traveller_roundtrip_19e_39s_max1000':
            column_name = self.cfg.order
            description = 'Travelling salesman heuristic from south of South Africa and back with max route length of 1000.'
            self.create_order_description(column_name, description)
            self.traveller((19, -39), (19, -39), column_name, 1000)

        elif self.cfg.order == 'traveller_roundtrip_19e_39s_max1000_byspread':
            column_name = self.cfg.order
            description = 'Travelling salesman heuristic from south of South Africa and back with max route length of 1000, subsorted by total distance from average location.'
            self.create_order_description(column_name, description)
            self.traveller((19, -39), (19, -39), column_name, 1000, True)

        elif self.cfg.order == 'traveller_roundtrip_19e_39s_max480_byspread':
            column_name = self.cfg.order
            description = 'Travelling salesman heuristic from south of South Africa and back with max route length of 480, subsorted by total distance from average location.'
            self.create_order_description(column_name, description)
            self.traveller((19, -39), (19, -39), column_name, 480, True)

        elif self.cfg.order == 'two_world_30w_65s_169w_65n_max480':
            column_name = self.cfg.order
            description = 'Travelling salesman heuristic from south of South Africa to Bering Strait, then to south of South America, with max route length of 480, splitting hemispheres at longitudes -30 and -169.'
            self.create_order_description(column_name, description)
            self.traveller((-30, -65), (-169, 65), column_name, max_route_length=480, two_world=True)


        elif self.cfg.order == 'two_world_30w_0s_169w_65n_max480':
            column_name = self.cfg.order
            description = 'Travelling salesman heuristic from south Atlantic to Bering Strait across Africa and Asia, then back to south Atlantic across North and South America, with max route length of 480.'
            self.create_order_description(column_name, description)
            self.traveller((-30, 0), (-169, 65), column_name, max_route_length=480, two_world=True)


        else:
            raise Exception('Order "%s" not implemented.' % self.cfg.order)

    def traveller(self, start_location, end_location, column_name, max_route_length=0, order_by_spread=False, two_world=False):

        # TODO: Split this into multiple, reasonable functions, instead
        # of this big mess.

        update_template = '''
            UPDATE
                variant
            SET
                %s=?
            WHERE
                id=?
        ''' % column_name
            
        select = '''
            SELECT
                id,
                average_longitude,
                average_latitude
            FROM
                variant
            WHERE
                time=?
        '''
        if order_by_spread:
            select += ' ORDER BY total_distance_to_average_location'

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
            sys.stderr.write('\nTime... %s\n' % time)

            read_cursor.execute(select, (time,))

            rows = read_cursor.fetchall()

            if two_world:
                start = start_location[0] % 360
                end = end_location[0] % 360
                #sys.stderr.write(f'start: {start} end: {end}\n')
                random.shuffle(rows)
                if max_route_length and len(rows) > max_route_length:
                    route_count = len(rows) // max_route_length + 1
                    prelims = [rows[i::route_count] for i in range(route_count)]
                else:
                    prelims = [rows]
                chunks = []
                for prelim in prelims:
                    hemisphere_a = []
                    hemisphere_b = []
                    for variant in prelim:
                        middle = variant['average_longitude'] % 360
                        if (start < end):
                            if start < middle < end:
                                hemisphere = hemisphere_a
                            else:
                                hemisphere = hemisphere_b
                        else:
                            if end < middle < start:
                                hemisphere = hemisphere_b
                            else:
                                hemisphere = hemisphere_a
                        hemisphere.append(variant)

                    chunks.append({
                        'start': start_location,
                        'end': end_location,
                        'variants': hemisphere_a,
                    })

                    chunks.append({
                        'start': end_location,
                        'end': start_location,
                        'variants': hemisphere_b,
                    })

            elif max_route_length and len(rows) > max_route_length:

                # We should probably turn these into iterators or sumtin'.

                if order_by_spread:

                    # Try to spread the remainder around evenly so that we
                    # don't have one leftover short route.
                    count, remainder = divmod(len(rows), max_route_length)
                    route_count = count + bool(remainder)
                    route_length, remainder = divmod(len(rows), route_count)
                    route_lengths = [route_length + (1 if i < remainder else 0) for i in range(route_count)]

                    # Small-big-small spread.
                    intro = rows[::2]
                    outro = rows[1::2]
                    outro.reverse()
                    new_rows = intro + outro

                    variants = []
                    position = 0
                    for route_length in route_lengths:
                        variants.append(new_rows[position:position+route_length])
                        position += route_length

                else:
                    random.shuffle(rows)
                    route_count = len(rows) // max_route_length + 1
                    variants = [rows[i::route_count] for i in range(route_count)]

                chunks = [{
                    'start': start_location,
                    'end': end_location,
                    'variants': variant,
                } for variant in variants]

            else:
                chunks = [{
                    'start': start_location,
                    'end': end_location,
                    'variants': rows,
                }]

            sys.stderr.write(f'Route lengths: {[len(chunk["variants"]) for chunk in chunks]}\n')

            for chunk in chunks:
                for variant_id in self.traveller_sort(chunk['start'], chunk['end'], chunk['variants']):
                    write_cursor.execute(update_template, (order, variant_id))
                    order += 1


        database.commit()
        database.close()

    def traveller_sort(self, start_location, end_location, rows):

        # Start isn't a real location.  It's an arbitrary point we picked...
        locations = [start_location]
        variant_ids = [-1]
        for row in rows:
            locations.append((row['average_longitude'], row['average_latitude']))
            variant_ids.append(row['id'])
        # ...end isn't a real location.  It's an arbitrary point we picked...
        locations.append(end_location)
        variant_ids.append(-1)

        route = travelling_genome.main(locations)
        #route = travelling_genome.nearest_neighbour_only(locations)

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

