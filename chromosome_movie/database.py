#!/usr/bin/env python3

# Using a database ignores the advantages of the tree sequence format,
# but makes random access for arbitrary ordering, and the collection of
# calculated data, easier.  IOW, I'm using what I know.

import sys
import collections
import math
import json

import sqlite3
import numpy

import tskit


class Database():

    def __init__(self, cfg):

        self.cfg = cfg

        self.treeseq = tskit.load(self.cfg.treeseq_path)

        #self.chromosome_id = -1

        #if self.cfg.treeseq_type == '1kg':
        with open(self.cfg.code/'data'/'igsr_populations.tsv') as tsv:
            self.population_info = {}
            for num, line in enumerate(tsv):
                # TODO: Use csv module instead?
                columns = line.split('\t')
                if not num:
                    headers = columns
                else:
                    values = columns
                    population_info = dict(zip(headers, values))
                    self.population_info[population_info['Population elastic ID']] = population_info

    def write_db(self):
        self.create_tables()
        self.write_data()
        self.create_indexes()


    def write_data(self):

        self.add_chromosome()
        self.add_populations()
        self.add_variants()


    def create_tables(self):

        database = sqlite3.connect(self.cfg.database_path)
        cursor = database.cursor()

        cursor.execute('''
            CREATE TABLE IF NOT EXISTS chromosome (
                id INTEGER PRIMARY KEY,
                name TEXT UNIQUE,
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
                average_distance_to_average_location REAL,
                population_counts_match_variant_id INTEGER
            );
        ''')

        #cursor.execute('''
        #    CREATE TABLE IF NOT EXISTS variant_location (
        #        variant_id INTEGER,
        #        longitude REAL,
        #        latitude REAL,
        #        local_frequency REAL,
        #        PRIMARY KEY (variant_id, longitude, latitude)
        #    );
        #''')

        cursor.execute('''
            CREATE TABLE IF NOT EXISTS population (
                id INT PRIMARY KEY,
                source TEXT,
                name TEXT,
                node_count INTEGER,
                longitude REAL,
                latitude REAL
            );
        ''')

        cursor.execute('''
            CREATE TABLE IF NOT EXISTS variant_population (
                variant_id INTEGER,
                population_id INTEGER,
                node_count INTEGER,
                PRIMARY KEY (variant_id, population_id)
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
            CREATE INDEX IF NOT EXISTS population_counts_match_variant_id_idx
                ON variant (population_counts_match_variant_id);
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
            CREATE INDEX IF NOT EXISTS average_distance_to_average_location_idx
                ON variant (average_distance_to_average_location);
        ''')

        cursor.execute('''
            CREATE INDEX IF NOT EXISTS variant_id_idx
                ON variant_population (variant_id);
        ''')

        ## We're doing SELECT DISTINCT to get our list of locations, so
        ## we should probably index this.
        #cursor.execute('''
        #    CREATE INDEX IF NOT EXISTS location_idx
        #        ON variant_location (longitude, latitude);
        #''')

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


    def add_populations(self):
        database = sqlite3.connect(self.cfg.database_path)
        cursor = database.cursor()

        # FIXME: This is a hack which is likely to break.  To figure out which
        # sources the populations came from, we look through all the
        # individuals and look for keywords in their metadata.

        entries = set()

        node_counts = collections.Counter()
        populations = {}

        for individual in self.treeseq.individuals():

            if not individual.metadata:
                continue

            individual_meta = json.loads(individual.metadata)

            if 'sgdp_id' in individual_meta:
                source = 'SGDP'
            elif 'sample' in individual_meta:
                source = 'HGDP'
            elif 'individual_id' in individual_meta:
                source = '1KG'
            else:
                continue

            for node_id in individual.nodes:
                node = self.treeseq.node(node_id)
                population = self.treeseq.population(node.population)
                population_meta = json.loads(population.metadata)
                longitude, latitude = self.get_location(population, individual)

                # Note that this will set info about individuals
                # to that of the last listed individual in their population.
                # Hopefully that's not a problem.  We do know that
                # locations of SGDP individuals are slightly different
                # within populations.
                populations[population.id] = (source, population_meta['name'], longitude, latitude)
                node_counts[population.id] += 1

        for population_id, (source, name, longitude, latitude) in populations.items():

            entries.add((

                population_id,

                source,
                name,
                node_counts[population_id],
                longitude,
                latitude,

                source,
                name,
                node_counts[population_id],
                longitude,
                latitude,
            ))

            #population = self.treeseq.population(self.treeseq.node(individual.nodes[0]).population)
            #population_meta = json.loads(population.metadata)

            #populations[source][

            #entries.add((
            #    population.id,
            #    source,
            #    population_meta['name'],
            #    source,
            #    population_meta['name'],
            #))

        cursor.executemany('''
            INSERT INTO population
                (id, source, name, node_count, longitude, latitude)
            VALUES
                (?, ?, ?, ?, ?, ?)
            ON CONFLICT
                (id)
            DO UPDATE SET
                source=?,
                name=?,
                node_count=?,
                longitude=?,
                latitude=?
            ''', entries)

        database.commit()
        database.close()


    def average_location(self, local_frequencies):
        # Loosely based on:
        # https://gis.stackexchange.com/a/7566
        # ...but with a bunch of things reversed to give the right answers.

        longitudes = numpy.radians(numpy.array([lf[0][0] for lf in local_frequencies]))
        latitudes = numpy.radians(numpy.array([lf[0][1] for lf in local_frequencies]))
        if self.cfg.weighted_average_locations:
            weights = numpy.array([lf[1] for lf in local_frequencies])
        else:
            weights = 1

        x = numpy.average(numpy.cos(latitudes) * numpy.cos(longitudes) * weights)
        y = numpy.average(numpy.cos(latitudes) * numpy.sin(longitudes) * weights)
        z = numpy.average(numpy.sin(latitudes) * weights)

        average_longitude = math.atan2(y, x)
        average_latitude = math.atan2(z, (x**2 + y**2)**0.5)

        average_distance_to_average_location = numpy.sum(numpy.arccos(numpy.clip(
            numpy.sin(latitudes) * numpy.sin(average_latitude)
            + numpy.cos(latitudes) * numpy.cos(average_latitude)
            * numpy.cos(numpy.absolute(longitudes - average_longitude)),
            -1, 1)
        )) / len(local_frequencies)

        return math.degrees(average_longitude), math.degrees(average_latitude), math.degrees(average_distance_to_average_location)


    def add_variants(self):

        # Bit of an omnibus function, I guess?  Should it be broken up?

        database = sqlite3.connect(self.cfg.database_path)
        cursor = database.cursor()

        ## Get sample totals for each location.
        #location_node_counts = collections.Counter()
        #for sample in self.treeseq.samples():
        #    location = self.get_location(sample)
        #    if location:
        #        location_node_counts[location] += 1

        populations = {}

        cursor.execute('SELECT id, source, name, node_count, longitude, latitude FROM population')

        for row in cursor:
            population_id, source, name, node_count, longitude, latitude = row
            populations[population_id] = {
                'source': source,
                'name': name,
                'node_count': node_count,
                'longitude': longitude,
                'latitude': latitude,
                'location': (longitude, latitude),
            }

        # Only record the first variant ID for which a given combination
        # of local counts occurs, and have the other variants refer back
        # to it.  This cuts down the number of images we have to create
        # by about half, which is significant given that converting all of
        # them is a 20-24 hour process on my machine.
        # I'm guessing that this is the memory hog in this script.  This,
        # or not committing the database until everything is done.
        #local_counts_seen = {}
        #populations_seen = {}
        node_counts_in_populations_seen = {}

        num_all = 0
        num_used = 0

        skipped = collections.Counter()

        for tree in self.treeseq.trees():
            for variant in tree.mutations():


                if num_all % 1000 == 0:
                    sys.stderr.write(f'Loading### {num_used}/{num_all}\n')
                    sys.stderr.write(f'Skipped: {skipped}\n')
                    sys.stderr.flush()

                num_all += 1

                node = self.treeseq.node(variant.node)
                site = self.treeseq.site(variant.site)

                if site.ancestral_state == variant.derived_state:
                    # I'm not sure why some mutations are equal to the
                    # original state - change and change back, I guess?
                    # - but whatever the reason, we're not including
                    # them.
                    skipped['no mutation'] += 1
                    continue

                node_counts_in_populations = collections.Counter()
                individual_ids = set()
                leaf_count = 0
                for leaf in tree.leaves(node.id):
                    leaf_node = self.treeseq.node(leaf)
                    if leaf_node.population not in populations:
                        continue
                    leaf_count += 1
                    node_counts_in_populations[leaf_node.population] += 1
                    individual_ids.add(leaf_node.individual)

                if len(individual_ids) < 2:
                    # If a variant only shows up in one individual, we choose
                    # to ignore it.
                    skipped['one individual'] += 1
                    continue

                node_counts_in_populations = frozenset((population_id, node_count) for population_id, node_count in node_counts_in_populations.items())

                node_frequencies_in_populations = []
                for population_id, node_count in node_counts_in_populations:
                    population = populations[population_id]
                    node_frequencies_in_populations.append((population['location'], node_count/population['node_count']))

                average_longitude, average_latitude, average_distance_to_average_location = self.average_location(node_frequencies_in_populations)

                if node_counts_in_populations in node_counts_in_populations_seen:
                    population_counts_match_variant_id = node_counts_in_populations_seen[node_counts_in_populations]
                else:
                    population_counts_match_variant_id = variant.id
                    node_counts_in_populations_seen[node_counts_in_populations] = variant.id
                    # FIXME: If a population count changes to 0, this won't
                    # delete it from the database.
                    entries = [(variant.id, population_id, node_count, node_count) for population_id, node_count in node_counts_in_populations]
                    cursor.executemany('''
                        INSERT INTO variant_population
                            (
                                variant_id,
                                population_id,
                                node_count
                            )
                        VALUES
                            (?, ?, ?)
                        ON CONFLICT
                            (variant_id, population_id)
                        DO UPDATE SET
                            node_count=?
                    ''', entries)

                ##num_individuals = len(set(self.treeseq.node(leaf).individual for leaf in tree.leaves(node.id)))
                ##if num_individuals < 2:
                ##    continue

                ## Get sample totals for each location for this variant.
                #local_counts = collections.Counter()
                #population_ids = set()
                #individual_ids = set()
                #for leaf in tree.leaves(node.id):
                #    location = self.get_location(leaf)
                #    if location:
                #        local_counts[location] += 1
                #        leaf_node = self.treeseq.node(leaf)
                #        population_ids.add(leaf_node.population)
                #        individual_ids.add(leaf_node.individual)
                #if len(individual_ids) < 2:
                #    # If a variant only shows up in one individual, we're
                #    # choosing to ignore it.
                #    skipped['one individual'] += 1
                #    continue

                #local_frequencies = frozenset((location, count/location_node_counts[location]) for location, count in local_counts.items())
                #population_ids = frozenset(population_ids)

                #if local_frequencies in local_counts_seen:
                #    local_counts_match_variant_id = local_counts_seen[local_frequencies]
                #else:
                #    local_counts_match_variant_id = variant.id
                #    local_counts_seen[local_frequencies] = variant.id
                #    entries = [(variant.id, location[0], location[1], frequency, frequency) for location, frequency in local_frequencies]

                #    # FIXME: If a local frequency changes to 0, this won't
                #    # delete it from the database.
                #    cursor.executemany('''
                #        INSERT INTO variant_location
                #            (
                #                variant_id,
                #                longitude,
                #                latitude,
                #                local_frequency
                #            )
                #        VALUES
                #            (?, ?, ?, ?)
                #        ON CONFLICT
                #            (variant_id, longitude, latitude)
                #        DO UPDATE SET
                #            local_frequency=?
                #    ''', entries)

                #if population_ids in populations_seen:
                #    populations_match_variant_id = populations_seen[population_ids]
                #else:
                #    populations_match_variant_id = variant.id
                #    populations_seen[population_ids] = variant.id
                #    entries = [(variant.id, population_id) for population_id in population_ids]

                #    cursor.executemany('''
                #        INSERT OR REPLACE INTO variant_population
                #            (
                #                variant_id,
                #                population_id
                #            )
                #        VALUES
                #            (?, ?)
                #    ''', entries)

                ## Is this going to blow up 
                #entries = [(variant.id, population_id) for population_id in population_ids]

                #average_longitude, average_latitude, average_distance_to_average_location = self.average_location(local_frequencies)

                ##average_location = self.average_location(local_counts.keys())
                ##local_counts = frozenset(local_counts.items())

                ### Setdefault does exactly what we want (returns the first
                ### value that we set for this key in the dictionary, or sets
                ### the new value and returns it if the key isn't already in
                ### the dictionary), but it took me longer to write out this
                ### comment than it would've taken to write this as a clearer
                ### to understand if-else.
                ##local_counts_match_variant_id = seen_local_counts.setdefault(local_counts, variant.id)

                ###
                ### TODO: Continue modifying from local to population from here.
                ###

                entry = (
                    variant.id,
                    self.cfg.chromosome,
                    node.time,
                    leaf_count/self.treeseq.num_samples,
                    site.ancestral_state,
                    variant.derived_state,
                    site.position,
                    average_longitude,
                    average_latitude,
                    average_distance_to_average_location,
                    population_counts_match_variant_id,
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
                            average_distance_to_average_location,
                            population_counts_match_variant_id
                        )
                    VALUES
                        (?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?)
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
                            average_distance_to_average_location=?,
                            population_counts_match_variant_id=?
                    ''', entry + entry[1:])

                num_used += 1

        database.commit()
        database.close()

        sys.stderr.write(f'Loaded### {num_used}/{num_all}\n')
        sys.stderr.flush()


    #def get_location(self, node_id, notfound=set()):
    def get_location(self, population, individual, notfound=set()):
        #individual = self.treeseq.individual(self.treeseq.node(node_id).individual)
        #if self.cfg.treeseq_type == 'sgdp':
        if any(individual.location):
            # Not sure why all the treeseqs don't store the location
            # with the individual.  SGDP does, though.
            latitude, longitude = individual.location
        #elif self.cfg.treeseq_type == '1kg':
        else:
            #population_name = json.loads(self.treeseq.population(self.treeseq.node(node_id).population).metadata)['name']
            population_name = json.loads(population.metadata)['name']
            if population_name not in self.population_info:
                # This seems to successfully rule out ancients.
                if population_name not in notfound:
                    print('No location for population "%s", not including.' % population_name)
                    notfound.add(population_name)
                return None
            else:
                population_info = self.population_info[population_name]
                latitude = float(population_info['Population latitude'])
                longitude = float(population_info['Population longitude'])


        #else:
        #    raise Exception(f'Unknown treeseq type "{self.cfg.treeseq_type}".')

        # I am using (longitude, latitude) ordering everywhere in this code.
        return (longitude, latitude)


