#!/usr/bin/env python3

import sys
import random

import sqlite3

from . import travelling_genome

class Order():

    orders = {
        'traveller_45e_30s_105w_40s': {
            'description': 'Travelling salesman heuristic from Indian Ocean east of South Africa to southern Pacific west of South America.',
            'start_location': (45, -30),
            'end_location': (-105, -40),
        },

        'traveller_19e_39s_99w_19n': {
            'description': 'Travelling salesman heuristic from south of South Africa to Mexico City.',
            'start_location': (19, -39),
            'end_location': (-99, 19),
        },

        'traveller_19e_39s_99w_19n_max1000': {
            'description': 'Travelling salesman heuristic from south of South Africa to Mexico City with max route length of 1000.',
            'start_location': (19, -39),
            'end_location': (-99, 19),
            'max_route_length': 1000,
        },

        'traveller_roundtrip_19e_39s_max480': {
            'description': 'Travelling salesman heuristic from south of South Africa and back with max route length of 480.',
            'start_location': (19, -39),
            'end_location': (19, -39),
            'max_route_length': 480,
        },

        'traveller_roundtrip_19e_39s_max1000': {
            'description': 'Travelling salesman heuristic from south of South Africa and back with max route length of 1000.',
            'start_location': (19, -39),
            'end_location': (19, -39),
            'max_route_length': 1000,
        },

        'traveller_roundtrip_19e_39s_max1000_byspread': {
            'description': 'Travelling salesman heuristic from south of South Africa and back with max route length of 1000, subsorted by total distance from average location.',
            'start_location': (19, -39),
            'end_location': (19, -39),
            'max_route_length': 1000,
            'order_by_spread': True,
        },

        'traveller_roundtrip_19e_39s_max480_byspread': {
            'description': 'Travelling salesman heuristic from south of South Africa and back with max route length of 480, subsorted by total distance from average location.',
            'start_location': (19, -39),
            'end_location': (19, -39),
            'max_route_length': 480,
            'order_by_spread': True,
        },

        'two_world_30w_65s_169w_65n_max480': {
            'description': 'Travelling salesman heuristic from south of South Africa to Bering Strait, then to south of South America, with max route length of 480, splitting hemispheres at longitudes -30 and -169.',
            'start_location': (-30, -65),
            'end_location': (-169, 65),
            'max_route_length': 480,
            'two_world': True,
        },


        'two_world_30w_0s_169w_65n_max480': {
            'description': 'Travelling salesman heuristic from south Atlantic to Bering Strait across Africa and Asia, then back to south Atlantic across North and South America, with max route length of 480.',
            'start_location': (-30, 0),
            'end_location': (-169, 65),
            'max_route_length': 480,
            'two_world': True,
        },

        'two_world_jaccard5_30w_30s_169w_65n_max480': {
            'description': 'Travelling salesman heuristic from south Atlantic to Bering Strait across Africa and Asia, then back to south Atlantic across North and South America, with max route length of 480.  Use Jaccard distance offset of 5 degrees to make variants which share more locations closer to each other.',
            'start_location': (-30, -30),
            'end_location': (-169, 65),
            'max_route_length': 480,
            'two_world': True,
            'jaccard_offset': 5,
        },

        'two_world_jaccard20_30w_30s_169w_65n_max480': {
            'description': 'Travelling salesman heuristic from south Atlantic to Bering Strait across Africa and Asia, then back to south Atlantic across North and South America, with max route length of 480.  Use Jaccard distance offset of 20 degrees to make variants which share more locations closer to each other.',
            'start_location': (-30, -30),
            'end_location': (-169, 65),
            'max_route_length': 480,
            'two_world': True,
            'jaccard_offset': 20,
        },

        'two_world_jaccard20_30w_30s_169w_65n_max120': {
            'description': 'Travelling salesman heuristic from south Atlantic to Bering Strait across Africa and Asia, then back to south Atlantic across North and South America, with max route length of 120.  Use Jaccard distance offset of 20 degrees to make variants which share more locations closer to each other.',
            'start_location': (-30, -30),
            'end_location': (-169, 65),
            'max_route_length': 120,
            'two_world': True,
            'jaccard_offset': 20,
        },

        'two_world_jaccard20_30w_30s_169w_65n_max480_group_limit': {
            'description': 'Travelling salesman heuristic from south Atlantic to Bering Strait across Africa and Asia, then back to south Atlantic across North and South America, with max route length of 480.  Use Jaccard distance offset of 20 degrees to make variants which share more locations closer to each other.  Use fixed groups of 480, even if the times in the group do not all match.',
            'start_location': (-30, -30),
            'end_location': (-169, 65),
            'max_route_length': 480,
            'two_world': True,
            'jaccard_offset': 20,
            'route_group': 'limit',
        },

        'two_world_jaccard20_30w_30s_169w_65n_max480_round1': {
            'description': 'Travelling salesman heuristic from south Atlantic to Bering Strait across Africa and Asia, then back to south Atlantic across North and South America, with max route length of 480.  Use Jaccard distance offset of 20 degrees to make variants which share more locations closer to each other.  Round off dates to nearest 1 year.',
            'start_location': (-30, -30),
            'end_location': (-169, 65),
            'max_route_length': 480,
            'two_world': True,
            'jaccard_offset': 20,
            'route_group': 'round',
            'round_years': 1,
        },

        'two_world_jaccard20_30w_30s_169w_65n_max480_round5': {
            'description': 'Travelling salesman heuristic from south Atlantic to Bering Strait across Africa and Asia, then back to south Atlantic across North and South America, with max route length of 480.  Use Jaccard distance offset of 20 degrees to make variants which share more locations closer to each other.  Round off dates to nearest 5 years.',
            'start_location': (-30, -30),
            'end_location': (-169, 65),
            'max_route_length': 480,
            'two_world': True,
            'jaccard_offset': 20,
            'route_group': 'round',
            'round_years': 5,
        },

        'two_world_jaccard20_30w_30s_169w_65n_max120_round5': {
            'description': 'Travelling salesman heuristic from south Atlantic to Bering Strait across Africa and Asia, then back to south Atlantic across North and South America, with max route length of 120.  Use Jaccard distance offset of 20 degrees to make variants which share more locations closer to each other.  Round off dates to nearest 5 years.',
            'start_location': (-30, -30),
            'end_location': (-169, 65),
            'max_route_length': 120,
            'two_world': True,
            'jaccard_offset': 20,
            'route_group': 'round',
            'round_years': 5,
        },

        'two_world_jaccard20_30w_30s_169w_65n_max480_round10': {
            'description': 'Travelling salesman heuristic from south Atlantic to Bering Strait across Africa and Asia, then back to south Atlantic across North and South America, with max route length of 480.  Use Jaccard distance offset of 20 degrees to make variants which share more locations closer to each other.  Round off dates to nearest 10 years.',
            'start_location': (-30, -30),
            'end_location': (-169, 65),
            'max_route_length': 480,
            'two_world': True,
            'jaccard_offset': 20,
            'route_group': 'round',
            'round_years': 10,
        },

        'two_world_jaccard20_30w_30s_169w_65n_max360_round25': {
            'description': 'Travelling salesman heuristic from south Atlantic to Bering Strait across Africa and Asia, then back to south Atlantic across North and South America, with max route length of 360.  Use Jaccard distance offset of 20 degrees to make variants which share more locations closer to each other.  Round off dates to nearest 25 years.',
            'start_location': (-30, -30),
            'end_location': (-169, 65),
            'max_route_length': 360,
            'two_world': True,
            'jaccard_offset': 20,
            'route_group': 'round',
            'round_years': 25,
        },

        'two_world_jaccard20_30w_30s_169w_65n_max360_round5': {
            'description': 'Travelling salesman heuristic from south Atlantic to Bering Strait across Africa and Asia, then back to south Atlantic across North and South America, with max route length of 360.  Use Jaccard distance offset of 20 degrees to make variants which share more locations closer to each other.  Round off dates to nearest 5 years.',
            'start_location': (-30, -30),
            'end_location': (-169, 65),
            'max_route_length': 360,
            'two_world': True,
            'jaccard_offset': 20,
            'route_group': 'round',
            'round_years': 5,
        },

        'two_world_jaccard20_30w_30s_169w_65n_max240_group_limit_average_times': {
            'description': 'Travelling salesman heuristic from south Atlantic to Bering Strait across Africa and Asia, then back to south Atlantic across North and South America, with max route length of 240.  Use Jaccard distance offset of 20 degrees to make variants which share more locations closer to each other.  Use fixed groups of 240, even if the times in the group do not all match.  Display average time of variants in group.',
            'start_location': (-30, -30),
            'end_location': (-169, 65),
            'max_route_length': 240,
            'two_world': True,
            'jaccard_offset': 20,
            'route_group': 'limit',
            'average_times': True,
        },

    }

    def __init__(self, cfg):
        self.cfg = cfg
        random.seed(1234)

    def select(self):
        database = sqlite3.connect(self.cfg.database_readonly_uri, uri=True)
        database.row_factory = sqlite3.Row
        cursor = database.cursor()
        order_key = f'order_{self.cfg.order}'
        lap_key = f'lap_{self.cfg.order}'
        display_time_key = f'display_time_{self.cfg.order}'

        order = self.orders[self.cfg.order]

        # TODO: I'm sure all the repetition in here can be cleaned up.

        if self.cfg.movie_times['type'] == 'time_lap':
            index = 0
            for time, lap_count in self.cfg.movie_times['time_laps']:
                cursor.execute(f'SELECT * FROM variant WHERE time=? ORDER BY {order_key}', (time,))
                previous_lap = None
                counted_laps = 0
                for num, variant in enumerate(cursor):
                    if variant[lap_key] != previous_lap:
                        previous_lap = variant[lap_key]
                        counted_laps += 1
                    if counted_laps > lap_count:
                        break
                    variant_dict = dict(variant)
                    #variant_dict[order_key] = index
                    variant_dict['frame_number'] = index
                    if variant_dict[display_time_key]:
                        variant_dict['time'] = variant_dict[display_time_key]
                    elif order['route_group'] == 'round':
                        multiplier = self.cfg.years_per_generation/order['round_years']
                        variant_dict['time'] = round(variant_dict['time']*multiplier)/multiplier
                    yield variant_dict
                    index += 1

        elif self.cfg.movie_times['type'] == 'time_limit':
            index = 0
            for time, limit in self.cfg.movie_times['time_limits']:
                sql = f'SELECT * FROM variant WHERE time=? ORDER BY {order_key}'
                if limit:
                    sql += f' LIMIT {limit}'
                cursor.execute(sql, (time,))
                for variant in cursor:
                    variant_dict = dict(variant)
                    #variant_dict[order_key] = index
                    variant_dict['frame_number'] = index
                    if variant_dict[display_time_key]:
                        variant_dict['time'] = variant_dict[display_time_key]
                    elif order['route_group'] == 'round':
                        multiplier = self.cfg.years_per_generation/order['round_years']
                        variant_dict['time'] = round(variant_dict['time']*multiplier)/multiplier
                    yield variant_dict
                    index += 1

        elif self.cfg.movie_times['type'] == 'time_random':
            index = 0
            for time, limit in self.cfg.movie_times['time_limits']:
                sql = f'SELECT * FROM variant WHERE time=? ORDER BY RANDOM()'
                if limit:
                    sql += f' LIMIT {limit}'
                cursor.execute(sql, (time,))
                for variant in cursor:
                    variant_dict = dict(variant)
                    #variant_dict[order_key] = index
                    variant_dict['frame_number'] = index
                    if variant_dict[display_time_key]:
                        variant_dict['time'] = variant_dict[display_time_key]
                    elif order['route_group'] == 'round':
                        multiplier = self.cfg.years_per_generation/order['round_years']
                        variant_dict['time'] = round(variant_dict['time']*multiplier)/multiplier
                    yield variant_dict
                    index += 1

        elif self.cfg.movie_times['type'] == 'time_range':
            index = 0
            for start, end in self.cfg.movie_times['time_ranges']:
                small, large = sorted((start, end))
                sql = f'SELECT * FROM variant WHERE time >= ? AND time < ? ORDER BY {order_key}'
                cursor.execute(sql, (small, large))
                for variant in cursor:
                    variant_dict = dict(variant)
                    #variant_dict[order_key] = index
                    variant_dict['frame_number'] = index
                    if variant_dict[display_time_key]:
                        variant_dict['time'] = variant_dict[display_time_key]
                    elif order['route_group'] == 'round':
                        multiplier = self.cfg.years_per_generation/order['round_years']
                        variant_dict['time'] = round(variant_dict['time']*multiplier)/multiplier
                    yield variant_dict
                    index += 1

        elif self.cfg.movie_times['type'] == 'order_range':
            index = 0
            for start, end in self.cfg.movie_times['order_ranges']:
                small, large = sorted((start, end))
                sql = f'SELECT * FROM variant WHERE {order_key} >= ? AND {order_key} <= ? ORDER BY {order_key}'
                cursor.execute(sql, (small, large))
                for variant in cursor:
                    variant_dict = dict(variant)
                    #variant_dict[order_key] = index
                    variant_dict['frame_number'] = index
                    if variant_dict[display_time_key]:
                        variant_dict['time'] = variant_dict[display_time_key]
                    elif order['route_group'] == 'round':
                        multiplier = self.cfg.years_per_generation/order['round_years']
                        variant_dict['time'] = round(variant_dict['time']*multiplier)/multiplier
                    yield variant_dict
                    index += 1


        else:
            cursor.execute(f'SELECT * FROM variant ORDER BY {order_key}')
            for variant in cursor:
                yield variant


    def write_db(self):

        order = self.orders[self.cfg.order]
        self.create_order_column(self.cfg.order, order['description'])
        kwargs = {k: v for k, v in order.items() if k != 'description'}
        kwargs['column_name'] = self.cfg.order
        self.traveller(**kwargs)


    def traveller(self, start_location, end_location, column_name, max_route_length=0, order_by_spread=False, two_world=False, jaccard_offset=-1, route_group='time', round_years=0, average_times=False):

        # TODO: Split this into multiple, reasonable functions, instead
        # of this big mess.

        update_template = f'''
            UPDATE
                variant
            SET
                order_{column_name}=?,
                lap_{column_name}=?,
                display_time_{column_name}=?
            WHERE
                id=?
        '''
            
        database = sqlite3.connect(self.cfg.database_path)
        database.row_factory = sqlite3.Row
        read_cursor = database.cursor()
        write_cursor = database.cursor()

        #read_cursor.execute('SELECT DISTINCT time FROM variant')
        #times = []
        #for row in read_cursor:
        #    times.append(row['time'])
        #times.sort(reverse=True)

        if route_group == 'time':
            groups = read_cursor.execute('SELECT DISTINCT time FROM variant ORDER BY time DESC')
            groups = list(tuple(row) for row in read_cursor)
            select = '''
                SELECT
                    id,
                    local_counts_match_variant_id,
                    average_longitude,
                    average_latitude,
                    time
                FROM
                    variant
                WHERE
                    time=?
            '''
            if order_by_spread:
                select += ' ORDER BY total_distance_to_average_location'

        elif route_group == 'limit':
            read_cursor.execute('SELECT COUNT(*) FROM variant')
            variant_count = read_cursor.fetchone()[0]
            groups = [(offset, max_route_length) for offset in range(0, variant_count, max_route_length)]
            select = '''
                SELECT
                    id,
                    local_counts_match_variant_id,
                    average_longitude,
                    average_latitude,
                    time
                FROM
                    variant
                ORDER BY
                    time DESC
                LIMIT ?,?
            '''

        elif route_group == 'round':
            multiplier = self.cfg.years_per_generation/round_years
            read_cursor.execute('SELECT DISTINCT ROUND(time*?)/? AS rounded_time FROM variant ORDER BY time DESC', (multiplier, multiplier))
            groups = [(multiplier, multiplier, row['rounded_time']) for row in read_cursor]
            select = '''
                SELECT
                    id,
                    local_counts_match_variant_id,
                    average_longitude,
                    average_latitude,
                    time
                FROM
                    variant
                WHERE
                    ROUND(time*?)/?=?
            '''
            if order_by_spread:
                select += ' ORDER BY total_distance_to_average_location'

        order = 0
        lap = 0

        for group in groups:
            sys.stderr.write(f'\nGroup... {group}\n')

            read_cursor.execute(select, group)

            rows = read_cursor.fetchall()

            if average_times:
                display_time = sum(row['time'] for row in rows)/len(rows)
                sys.stderr.write(f'Display time... {display_time}\n')
            else:
                display_time = None

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

                    # If one of them is empty, do there-and-back-again.
                    if not hemisphere_b:
                        half = len(hemisphere_a) // 2
                        hemisphere_a, hemisphere_b = hemisphere_a[:half], hemisphere_a[half:]
                    elif not hemisphere_a:
                        half = len(hemisphere_b) // 2
                        hemisphere_a, hemisphere_b = hemisphere_b[:half], hemisphere_b[half:]

                    chunks.append({
                        'start': start_location,
                        'end': end_location,
                        'variants': hemisphere_a,
                        'lap': lap,
                    })

                    chunks.append({
                        'start': end_location,
                        'end': start_location,
                        'variants': hemisphere_b,
                        'lap': lap,
                    })
                    lap += 1

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

                chunks = []
                for variant in variants:
                    chunks.append({
                        'start': start_location,
                        'end': end_location,
                        'variants': variant,
                        'lap': lap,
                    })
                    lap += 1

            else:
                chunks = [{
                    'start': start_location,
                    'end': end_location,
                    'variants': rows,
                    'lap': lap,
                }]
                lap += 1

            sys.stderr.write(f'Route lengths: {[len(chunk["variants"]) for chunk in chunks]}\n')

            for chunk in chunks:
                for variant_id in self.traveller_sort(chunk['start'], chunk['end'], chunk['variants'], jaccard_offset, read_cursor):
                    write_cursor.execute(update_template, (order, chunk['lap'], display_time, variant_id))
                    order += 1


        database.commit()
        database.close()

    def traveller_sort(self, start_location, end_location, variants, jaccard_offset, read_cursor):

        # Start isn't a real location.  It's an arbitrary point we picked...
        average_locations = [start_location]
        all_locations = [set()]
        variant_ids = [-1]

        for variant in variants:
            average_locations.append((variant['average_longitude'], variant['average_latitude']))
            variant_ids.append(variant['id'])
            if jaccard_offset >= 0:
                read_cursor.execute('''
                    SELECT
                        longitude,
                        latitude
                    FROM
                        variant_location
                    WHERE
                        variant_id=?
                ''', (variant['local_counts_match_variant_id'],))
                all_locations.append(set((r[0], r[1]) for r in read_cursor))

        # ...end isn't a real location.  It's an arbitrary point we picked...
        average_locations.append(end_location)
        all_locations.append(set())
        variant_ids.append(-1)

        route = travelling_genome.main(average_locations, jaccard_offset=jaccard_offset, all_locations=all_locations)
        #route = travelling_genome.nearest_neighbour_only(average_locations)

        # ...so we don't include start_location and end_location in the
        # final route.
        sorted_variant_ids = [variant_ids[i] for i in route[1:-1]]

        for variant_id in sorted_variant_ids:
            yield variant_id


    def create_order_column(self, column_name, description):

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
                    order_%s INTEGER
                ''' % column_name)

            cursor.execute('''
                ALTER TABLE
                    variant
                ADD COLUMN
                    lap_%s INTEGER
                ''' % column_name)

            cursor.execute('''
                ALTER TABLE
                    variant
                ADD COLUMN
                    display_time_%s INTEGER
                ''' % column_name)

            cursor.execute('''
                CREATE INDEX order_%s_idx
                    ON variant (order_%s)
                ''' % (column_name, column_name))

            cursor.execute('''
                CREATE INDEX lap_%s_idx
                    ON variant (lap_%s)
                ''' % (column_name, column_name))

        database.commit()
        database.close()

