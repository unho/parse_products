# -*- coding: utf-8 -*-
#
# Copyright © 2017 Leandro Regueiro Iglesias.
#
# This code is free software: you can redistribute it and/or modify
# it under the terms of the GNU General Public License as published by
# the Free Software Foundation, either version 3 of the License, or
# (at your option) any later version.
#
# This code is distributed in the hope that it will be useful,
# but WITHOUT ANY WARRANTY; without even the implied warranty of
# MERCHANTABILITY or FITNESS FOR A PARTICULAR PURPOSE.  See the
# GNU General Public License for more details.
#
# You should have received a copy of the GNU General Public License
# along with this code.  If not, see <http://www.gnu.org/licenses/>.

"""Sample script to test getting product's data from webpage."""

import argparse
import json
import os
import sys

from parse import get_products


def main():
    """Sample script to test the parsing of product list."""
    parser = argparse.ArgumentParser()
    parser.add_argument(
        "--url",
        required=True,
        metavar="URL",
        help="the URL to parse the products from")
    parser.add_argument(
        "--output",
        metavar="FILENAME",
        dest="filename",
        default=os.path.join(os.getcwd(), "output.json"),
        help="filename for the JSON output file (default: %(default)s). It "
             "will be overwritten if it already exists")
    parser.add_argument(
        "--count",
        metavar="COUNT",
        type=int,
        help="the (optional) number of products to parse")

    args = parser.parse_args()

    # Validate the inputs.
    if args.count is not None and args.count <= 0:
        print("\033[91m\033[1mERROR: The number of products must be a "
              "positive integer.\033[0m\033[0m")
        sys.exit(1)

    filename = args.filename
    if not os.path.isabs(filename):
        filename = os.path.join(os.getcwd(), filename)
    if os.path.isfile(filename):
        print("\033[93mWARNING: The specified file already exists. It will be "
              "overwritten.\033[0m")

    # Get the data and output.
    with open(filename, "w") as f:
        json.dump(get_products(args.url, args.count), f, indent=4)


if __name__ == '__main__':
    main()
