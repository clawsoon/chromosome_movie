#!/usr/bin/env python3

from chromosome_movie import config
import chromosome_movie

if __name__ == '__main__':

    import argparse

    parser = argparse.ArgumentParser()

    parser.add_argument('-o', '--order', default=config.order)
    parser.add_argument('-d', '--force-database-rebuild', action='store_true')
    parser.add_argument('-a', '--force-audio-rebuild', action='store_true')
    parser.add_argument('-c', '--force-concat-rebuild', action='store_true')

    args = parser.parse_args()

    config.order = args.order

    reordered = False

    order = chromosome_movie.order.Order(config)
    if not order.in_database or args.force_database_rebuild:
        order.write_db()
        reordered = True

    if args.force_audio_rebuild or reordered:
        audio = chromosome_movie.audio.Audio(config)
        audio.write_midi()
        audio.write_wav()

    movie = chromosome_movie.movie.Movie(config)
    if args.force_concat_rebuild or reordered:
        movie.write_concat()
    movie.write_mp4()


