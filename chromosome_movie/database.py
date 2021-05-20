#!/usr/bin/env python3

# Using a database ignores the advantages of the tree sequence format,
# but makes random access for arbitrary ordering, and the collection of
# calculated data, easier.  IOW, I'm using what I know.

import sys
import collections
import math

import sqlite3
import numpy

import tskit


class Database():

    def __init__(self, cfg):

        self.cfg = cfg

        self.treeseq = tskit.load(self.cfg.treeseq_path)

        #self.chromosome_id = -1


    def write_db(self):
        self.create_tables()
        self.write_data()
        self.create_indexes()


    def write_data(self):

        self.add_chromosome()
        self.add_variants()


    def create_tables(self):

        database = sqlite3.connect(self.cfg.database_path)
        cursor = database.cursor()

        cursor.execute('''
            CREATE TABLE IF NOT EXISTS chromosome (
                id INTEGER PRIMARY KEY,
                name TEXT,
                first_site INTEGER,
                last_site INTEGER,
                map_rate REAL,
                map_offset INTEGER,
                length INTEGER
            );
        ''')

        # We use "INT PRIMARY KEY" instead of "INTEGER PRIMARY KEY"
        # so that the ID field is not an alias for rowid and we can use
        # the treeseq variant ID.
        # See:
        # https://www.sqlite.org/lang_createtable.html#rowid
        # This allows us to be a little lazier, since the variant ID
        # (and the frame numbers it's used for) will remain consistent
        # even if we regenerate the whole database instead of modifying
        # it in place.
        cursor.execute('''
            CREATE TABLE IF NOT EXISTS variant (
                id INT PRIMARY KEY,
                chromosome TEXT,
                time REAL,
                worldwide_frequency REAL,
                ancestral_state TEXT,
                derived_state TEXT,
                chromosome_position INTEGER,
                average_longitude REAL,
                average_latitude REAL,
                local_counts_match_variant_id INTEGER
            );
        ''')

        cursor.execute('''
            CREATE TABLE IF NOT EXISTS variant_location (
                variant_id INTEGER,
                longitude REAL,
                latitude REAL,
                local_frequency REAL
            );
        ''')

        database.commit()
        database.close()

    def create_indexes(self):

        sys.stderr.write('Creating indexes...\n')
        sys.stderr.flush()

        database = sqlite3.connect(self.cfg.database_path)
        cursor = database.cursor()

        cursor.execute('''
            CREATE INDEX IF NOT EXISTS time_idx
                ON variant (time);
        ''')

        cursor.execute('''
            CREATE INDEX IF NOT EXISTS local_counts_match_variant_id_idx
                ON variant (local_counts_match_variant_id);
        ''')

        # We're going to be doing a SELECT DISTINCT on ancestral/derived.
        cursor.execute('''
            CREATE INDEX IF NOT EXISTS variant_type_idx
                ON variant (ancestral_state, derived_state);
        ''')


        # Turn any of these commented-out indexes back on if we find that
        # we're querying on any of these fields.

        #cursor.execute('''
        #    CREATE INDEX IF NOT EXISTS chromosome_id_idx
        #        ON variant (chromosome_id);
        #''')

        #cursor.execute('''
        #    CREATE INDEX IF NOT EXISTS worldwide_frequency_idx
        #        ON variant (worldwide_frequency);
        #''')

        #cursor.execute('''
        #    CREATE INDEX IF NOT EXISTS chromosome_position_idx
        #        ON variant (chromosome_position);
        #''')

        #cursor.execute('''
        #    CREATE INDEX IF NOT EXISTS average_longitude_idx
        #        ON variant (average_longitude);
        #''')

        #cursor.execute('''
        #    CREATE INDEX IF NOT EXISTS average_latitude_idx
        #        ON variant (average_latitude);
        #''')

        cursor.execute('''
            CREATE INDEX IF NOT EXISTS average_location_idx
                ON variant (average_longitude, average_latitude);
        ''')

        cursor.execute('''
            CREATE INDEX IF NOT EXISTS variant_id_idx
                ON variant_location (variant_id);
        ''')

        # We're doing SELECT DISTINCT to get our list of locations, so
        # we should probably index this.
        cursor.execute('''
            CREATE INDEX IF NOT EXISTS location_idx
                ON variant_location (longitude, latitude);
        ''')

        # We look for conflicts on this combination.
        cursor.execute('''
            CREATE INDEX IF NOT EXISTS variant_location_idx
                ON variant_location (variant_id, longitude, latitude);
        ''')

        database.commit()
        database.close()


    def add_chromosome(self):

        database = sqlite3.connect(self.cfg.database_path)
        cursor = database.cursor()

        entry = (
            self.cfg.chromosome,
            # Feels wrong to iterate twice, but it only takes a couple of
            # seconds and it's simpler than any of these ideas:
            # https://discuss.python.org/t/minmax-function-alongside-min-and-max
            min(site.position for site in self.treeseq.sites()),
            max(site.position for site in self.treeseq.sites()),
            int(self.treeseq.sequence_length),
        )
        cursor.execute('''
            INSERT INTO chromosome
                (
                    name,
                    first_site,
                    last_site,
                    length
                )
            VALUES
                (?, ?, ?, ?)
            ON CONFLICT
                (name)
            DO UPDATE SET
                first_site=?,
                last_site=?,
                length=?
            ''', entry + entry[1:])
        #self.chromosome_id = cursor.lastrowid

        database.commit()
        database.close()


    def average_location(self, locations):
        # This could be weighted by local frequency, but... nah.
        # 
        # Loosely based on:
        # https://gis.stackexchange.com/a/7566
        # ...but with a bunch of things reversed to give the right answers.

        longitudes = numpy.radians(numpy.array([loc[0] for loc in locations]))
        latitudes = numpy.radians(numpy.array([loc[1] for loc in locations]))

        x = numpy.average(numpy.cos(latitudes) * numpy.cos(longitudes))
        y = numpy.average(numpy.cos(latitudes) * numpy.sin(longitudes))
        z = numpy.average(numpy.sin(latitudes))

        average_longitude = math.degrees(math.atan2(y, x))
        average_latitude = math.degrees(math.atan2(z, (x**2 + y**2)**0.5))

        return average_longitude, average_latitude


    def add_variants(self):

        # Bit of an omnibus function, I guess?  Should it be broken up?

        database = sqlite3.connect(self.cfg.database_path)
        cursor = database.cursor()

        # Get sample totals for each location.
        location_node_counts = collections.Counter()
        for sample in self.treeseq.samples():
            location = self.get_location(sample)
            location_node_counts[location] += 1

        # Only record the first variant ID for which a given combination
        # of local counts occurs, and have the other variants refer back
        # to it.  This cuts down the number of images we have to create
        # by about half, which is significant given that converting all of
        # them is a 20-24 hour process on my machine.
        # I'm guessing that this is the memory hog in this script.  This,
        # or not committing the database until everything is done.
        seen_local_counts = {}

        num = 0
        variants = []
        for tree in self.treeseq.trees():
            for variant in tree.mutations():

                if num % 1000 == 0:
                    sys.stderr.write('Loading### %s\n' % num)
                    sys.stderr.flush()

                node = self.treeseq.node(variant.node)


                # Get sample totals for each location for this variant.
                # (And, useful for average_location, all the locations where
                # the variant is found.)
                local_counts = collections.Counter()
                for leaf in tree.leaves(node.id):
                    location = self.get_location(leaf)
                    local_counts[location] += 1

                average_location = self.average_location(local_counts.keys())

                local_counts = frozenset(local_counts.items())

                # Setdefault does exactly what we want (returns the first
                # value that we set for this key in the dictionary, or sets
                # the new value and returns it if the key isn't already in
                # the dictionary), but it took me longer to write out this
                # comment than it would've taken to write this as a clearer
                # to understand if-else.
                local_counts_match_variant_id = seen_local_counts.setdefault(local_counts, variant.id)

                entry = (
                    variant.id,
                    self.cfg.chromosome,
                    node.time,
                    tree.get_num_leaves(node.id)/self.treeseq.num_samples,
                    self.treeseq.site(variant.site).ancestral_state,
                    variant.derived_state,
                    int(variant.position),
                    average_location[0],
                    average_location[1],
                    local_counts_match_variant_id,
                )

                # FIXME: if a variant is deleted, this won't remove it.
                cursor.execute('''
                    INSERT INTO variant
                        (
                            id,
                            chromosome,
                            time,
                            worldwide_frequency,
                            ancestral_state,
                            derived_state,
                            chromosome_position,
                            average_longitude,
                            average_latitude,
                            local_counts_match_variant_id
                        )
                    VALUES
                        (?, ?, ?, ?, ?, ?, ?, ?, ?, ?)
                    ON CONFLICT
                        (id)
                    DO UPDATE SET
                            chromosome=?,
                            time=?,
                            worldwide_frequency=?,
                            ancestral_state=?,
                            derived_state=?,
                            chromosome_position=?,
                            average_longitude=?,
                            average_latitude=?,
                            local_counts_match_variant_id=?
                    ''', entry + entry[1:])

                entries = [(variant.id, location[0], location[1], count/location_node_counts[location], count/location_node_counts[location]) for location, count in local_counts]
                # FIXME: If a local frequency changes to 0, this won't
                # actually fix it.
                cursor.executemany('''
                    INSERT INTO variant_location
                        (
                            variant_id,
                            longitude,
                            latitude,
                            local_frequency
                        )
                    VALUES
                        (?, ?, ?, ?)
                    ON CONFLICT
                        (variant_id, longitude, latitude)
                    DO UPDATE SET
                        local_frequency=?
                ''', entries)

                num += 1

        database.commit()
        database.close()


    def get_location(self, node_id):
        if self.cfg.treeseq_type == 'sgdp':
            # Not sure why all the treeseqs don't store the location
            # with the individual.  SGDP does, though.
            latitude, longitude = self.treeseq.individual(self.treeseq.node(node_id).individual).location
        else:
            raise Exception(f'Unknown treeseq type "{self.cfg.treeseq_type}".')

        # I am using (longitude, latitude) ordering everywhere in this code.
        return (longitude, latitude)


