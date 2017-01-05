#!/usr/bin/env python3

from __future__ import print_function

import curses
import argparse
import logging
import sys

from data import *
from config import *
from view import *

def get_view(window, datum, config, file_num, total_files, position):
    cursor = position[:]
    link = position[:] if config.annotation_type == AnnType.link else [-1, -1]
    return View(window, cursor, link, datum, config, file_num, total_files)

def annotate(window, config, filenames):
    out_filename = "files_still_to_do"
    overwrite = False
    for i in range(len(sys.argv)):
        if sys.argv[i] == '-log' and len(sys.argv) > i + 1:
            out_filename = sys.argv[i + 1]
        if sys.argv[i] == '-overwrite':
            overwrite = True
    out = open(out_filename, "w")

    # Set color combinations
    for num, fore, back in COLORS:
        curses.init_pair(num, fore, back)

    # No blinking cursor
    curses.curs_set(0)

    cfilename = 0
    filename, start_pos = filenames[cfilename]
    datum = Datum(filename, config)
    view = get_view(window, datum, config, cfilename, len(filenames), start_pos)

    at_end = None
    while True:
        if at_end is None:
            # Draw screen
            view.render()
            view.must_show_linking_pos = False
            # Get input
            user_input = window.getch()

            # Note - First two are SHIFT + DOWN and SHIFT + UP, determined by
            # hand on a Mac.
            if user_input == 337:
                if config.annotation_type == AnnType.link: view.move_up(True)
                else: view.move_to_top()
            elif user_input == 336:
                if config.annotation_type == AnnType.link: view.move_down(True)
                else: view.move_to_bottom() 
            elif user_input == curses.KEY_SLEFT:
                if config.annotation_type == AnnType.link: view.move_left(True)
                else: view.move_to_start()
            elif user_input == curses.KEY_SRIGHT:
                if config.annotation_type == AnnType.link: view.move_right(True)
                else: view.move_to_end()
            elif user_input == curses.KEY_UP: view.move_up()
            elif user_input == curses.KEY_DOWN: view.move_down()
            elif user_input == curses.KEY_LEFT: view.move_left()
            elif user_input == curses.KEY_RIGHT: view.move_right()
            elif user_input == ord("n"): view.next_number()
            elif user_input == ord("h"): view.toggle_help()
            elif user_input == ord("p"): view.next_number()
            elif user_input == ord("d"):
                datum.modify_annotation(view.cursor, view.linking_pos)
                if config.annotation_type == AnnType.link:
                    if config.annotation == AnnScope.line:
                        view.move_down(True)
                        view.cursor[0] = view.linking_pos[0]
                        view.cursor[1] = view.linking_pos[1]
                        view.move_up()
                    else:
                        view.move_right(True)
                        view.cursor[0] = view.linking_pos[0]
                        view.cursor[1] = view.linking_pos[1]
                        view.move_left()
                    view.must_show_linking_pos = True
            elif user_input == ord("D"):
                datum.modify_annotation(view.cursor, view.linking_pos)
            elif user_input == ord("u"):
                datum.remove_annotation(view.cursor, view.linking_pos)
            elif user_input in [ord('s'), ord('b'), ord('r')]:
                datum.modify_annotation(view.cursor, view.linking_pos,
                        chr(user_input))
            elif user_input == ord("/") or user_input == ord("\\"):
                # If we can get another file, do
                datum.write_out()
                filenames[cfilename] = (filename, view.cursor)
                direction = 1 if user_input == ord("/") else -1
                if 0 <= cfilename + direction < len(filenames):
                    cfilename += direction
                    filename, start_pos = filenames[cfilename]
                    datum = Datum(filename, config)
                    view = get_view(window, datum, config, cfilename,
                            len(filenames), start_pos)
                elif direction > 0:
                    at_end = 'end'
                else:
                    at_end = 'start'
            elif user_input == ord("q"):
                datum.write_out()
                filenames[cfilename] = (filename, view.cursor)
                break
        else:
            # Draw screen
            view.render_edgecase(at_end)
            # Get input
            user_input = window.getch()
            if at_end == 'start' and user_input == ord("/"):
                at_end = None
            elif at_end == 'end' and user_input == ord("\\"):
                at_end = None
            elif user_input == ord("q"): break

        window.clear()

    for filename, start_pos in filenames:
        print("{} {} {}".format(filename, start_pos[0], start_pos[1]), file=out)
    out.close()

if __name__ == '__main__':
    parser = argparse.ArgumentParser(description='A tool for annotating text data with extra information.')
    parser.add_argument('data', help='File containing a list of files to annotate')
    parser.add_argument('--output', help='File containing a list of files to annotate', choices=['overwrite', 'inline', 'standoff'], default="overwrite")
    parser.add_argument('--log_prefix', help='Prefix for logging files (otherwise none)')
    args = parser.parse_args()

    ### Start interface
    filenames = read_filenames(args.data)
    config = get_default_config(args)
    curses.wrapper(annotate, config, filenames)
