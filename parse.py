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

"""Parsing of HTML webpages."""

import math
import re

import requests
from lxml import html
from six.moves.urllib.parse import urljoin


MOLECULAR_FORMULA_RE = re.compile("([a-zA-Z]+)([0-9]*)")


def convert_formula(formula_string):
    """Returns a chemical formula using <sub> tags.

    :param str formula_string: representation of the formula using just letter
                               and numbers.
    :return: Returns a chemical formula using <sub> tags.
    :rtype: str
    """
    return "".join(["%s<sub>%s</sub>" % item if len(item[1]) else item[0]
                    for item in MOLECULAR_FORMULA_RE.findall(formula_string)])


def extract_product_data(url):
    """Extract product data from the specific product sheet URL.

    :param str url: URL for the product sheet webpage.
    :return: Returns a dictionary holding the extracted product data.
    :rtype: dict
    """
    product = {
        'pid': None,
        'name': None,
        'url': url,
        'packaging': {},
    }

    # Parse the webpage with the product details.
    tree = html.fromstring(requests.get(url, verify=False).content)

    # Extract misc product data from the `Product Detail` table.
    table = tree.xpath('//table[@class="ptable"][1]')[0]
    for useful_row in table.xpath('.//tr[td[@class="ptdataleft"]]'):
        label = useful_row.find('.//td[@class="ptdataleft"]').text
        value = useful_row.find('.//td[@class="ptdataright"]').text

        if label == "Glentham Code":
            product['pid'] = value
        elif label == "Product Name":
            product['name'] = value
        elif label == "CAS":
            product['CAS'] = value
        elif label == "Molecular Formula":
            product['structure'] = convert_formula(value)
        elif label == "Molecular Weight":
            if 'properties' not in product:
                product['properties'] = {}
            product['properties']['weight'] = value

    # Extract available preset packaging options and their prices, if any.
    prices_table = tree.xpath('//table[@class="pricetable"][1]')[0]
    for useful_row in prices_table.xpath('.//tr[@itemprop="offers"]'):
        size = useful_row.find('.//td[@class="pricetdmid"]').text
        price = float(useful_row.find(
            './/td[@class="pricetdmid"]/b/span[@itemprop="price"]').text)
        product['packaging'][size] = price

    # Set default if there are no specific packaging options.
    if not len(product['packaging']):
        product['packaging']['ne'] = 0.0

    # Extract product synonyms, if any.
    synonyms = tree.find('.//p[@itemprop="isRelatedTo"]/i')
    if synonyms is not None:
        product['synonyms'] = synonyms.text.split("; ")

    # Extract product's `Material Safety Data Sheet`, if any.
    msds_link = tree.find('.//a[@title="Download MSDS"]')
    if msds_link is not None:
        product['pdf_msds'] = msds_link.attrib['href']

    # Extract more product data from the `Product Specification` table.
    table = tree.xpath('//table[@class="ptable"]')[1]
    for useful_row in table.xpath('.//tr[td[@class="ptdataleft"]]'):
        label = useful_row.find('.//td[@class="ptdataleft"]').text
        value = useful_row.find('.//td[@class="ptdataright"]').text

        if label == "Purity":
            if 'properties' not in product:
                product['properties'] = {}
            product['properties']['purity'] = value

    return product


def get_last_page(url, count=None):
    """Return the last page to process in the product's list.

    :param str url: URL for the product list.
    :param int count: optional number of products to process. If not specified
            then all products in the product list will be processed.
    :return: Returns the number of the last product list page to process.
    :rtype: int
    """
    # First get the last available page.
    tree = html.fromstring(requests.get(url, verify=False).content)
    node = tree.xpath('//div[@class="pagenavbox"]')[0]
    last_page = int(node.text.strip().split("of ")[1])

    # If number of products is not specified then return last available page.
    if count is None:
        return last_page

    # Otherwise calculate and return last page to process based on the
    # specified number of products.
    products_per_page = 100. if "100" in url else 50.
    return min(int(math.ceil(count / products_per_page)), last_page)


def get_products(url, count=None):
    """Extract product data for a number of products from the specified URL.

    :param str url: URL for the product list.
    :param int count: optional number of products to process. If not specified
            then all products in the product list will be processed.
    :return: Returns a list of dictionaries holding each the extracted data for
            a product.
    :rtype: dict
    """
    product_urls = []
    i = 0

    all_urls = ["%s?page=%d" % (url, number)
                for number in range(1, get_last_page(url, count) + 1)]

    # Parse each page of the product list to get all product URLs.
    for current_url in all_urls:
        tree = html.fromstring(requests.get(current_url, verify=False).content)

        xpath = '//table[@class="prodtable"][1]/tr[td[@class="borderbtmfine"]]'
        for useful_row in tree.xpath(xpath):
            i += 1
            product_urls.append(urljoin(url, useful_row.find(
                './/td[@class="borderbtmfine"]/div/a').attrib['href']))

            # Process only the specified number of products.
            if count is not None and i == count:
                break

    return [extract_product_data(url) for url in product_urls]
