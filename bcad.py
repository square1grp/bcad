import requests
from lxml import etree
import csv
import pdb

property_ids = [398470, 1173139, 503785, 1062992, 192404, 192380, 1172789,
                1185813, 718111, 1004921, 186394, 1144438, 673590, 479907, 479889]

FIELD_NAMES = []


def send_requests():
    session = requests.Session()
    response = session.get(
        'http://www.bcad.org/ClientDB/PropertySearch.aspx?cid=1')

    for property_id in property_ids:
        response = session.get(
            'http://www.bcad.org/ClientDB/Property.aspx?prop_id=%s' % property_id)

        if response.status_code != 200:
            pdb.set_trace()

        parse_property_page(response.text.encode('utf8'))


# Property
def parse_dropdown_property(page_tree):
    listing = dict()
    property_keys = ['Property ID', 'Legal Description', 'Geographic ID',
                     'Zoning', 'Type', 'Agent Code', 'Property Use Code',
                     'Property Use Description', 'Protest Status', 'Informal Date',
                     'Formal Date', 'Address', 'Mapsco', 'Neighborhood', 'Map ID',
                     'Neighborhood CD', 'Name', 'Owner ID', 'Mailing Address',
                     '% Ownership', 'Exemptions']

    for key in property_keys:
        if key == 'Exemptions':
            listing['Property - %s' % key] = '\n'.join([text.strip() for text in page_tree.xpath(
                '//div[@id="propertyDetails"]/table[@summary="Property Details"]//td[a/text()="%s:"]/following-sibling::td[1]/text()' % key)])
        else:
            listing['Property - %s' % key] = '\n'.join([text.strip() for text in page_tree.xpath(
                '//div[@id="propertyDetails"]/table[@summary="Property Details"]//td[text()="%s:"]/following-sibling::td[1]/text()' % key)])

    return listing


# Values
def parse_dropdown_values(page_tree):
    listing = dict()
    value_keys = ['Improvement Homesite Value', 'Improvement Non-Homesite Value', 'Land Homesite Value', 'Land Non-Homesite Value',
                  'Agricultural Market Valuation', 'Agricultural Use Valuation', 'Timber Market Valuation', 'Timber Use Valuation',
                  'Market Value', 'Ag or Timber Use Value Reduction', 'Appraised Value', 'HS Cap', 'Assessed Value']

    for key in value_keys:
        if key == 'Agricultural Use Valuation':
            listing['Values - %s' % key] = '\n'.join([text.strip() for text in page_tree.xpath(
                '//div[@id="valuesDetails"]/table[@summary="Property Values"]//td[contains(text(), "Agricultural Market Valuation")]/following-sibling::td[3]/text()')])
        elif key == 'Timber Use Valuation':
            listing['Values - %s' % key] = '\n'.join([text.strip() for text in page_tree.xpath(
                '//div[@id="valuesDetails"]/table[@summary="Property Values"]//td[contains(text(), "Timber Market Valuation")]/following-sibling::td[3]/text()')])
        else:
            listing['Values - %s' % key] = '\n'.join([text.strip() for text in page_tree.xpath(
                '//div[@id="valuesDetails"]/table[@summary="Property Values"]//td[contains(text(), "%s")]/following-sibling::td[2]/text()' % key)])

    return listing


# Taxing Jurisdiction
def parse_dropdown_tax(page_tree):
    listing = dict()
    tax_keys = ['Owner', '% Ownership', 'Total Value']

    for key in tax_keys:
        listing['Taxing Jurisdiction - %s' % key] = page_tree.xpath(
            '//div[@id="taxingJurisdictionDetails"]/table[1]//td[text()="%s:"]/following-sibling::td[1]/text()' % key)[0].strip()

    row_tree_list = page_tree.xpath('//div[@id="taxingJurisdictionDetails"]/table[2]//tr[not(contains(@class, "tableDataHeader")) and position() <= %s]' %
                                    (len(page_tree.xpath('//div[@id="taxingJurisdictionDetails"]/table[2]//tr')) - 3))
    tax_keys = ['Entity', 'Description', 'Tax Rate',
                'Appraised Value', 'Taxable Value', 'Estimated Tax']
    for index, row_tree in enumerate(row_tree_list):
        for key_index, key in enumerate(tax_keys):
            listing['Taxing Jurisdiction - %s #%s' % (key, index + 1)] = '\n'.join(
                [text.strip() for text in row_tree.xpath('./td[%s]/text()' % (key_index + 1))])

    tax_keys = ['Total Tax Rate',
                'Taxes w/Current Exemptions', 'Taxes w/o Exemptions']
    for key in tax_keys:
        listing['Taxing Jurisdiction - %s' % key] = '\n'.join([text.strip() for text in page_tree.xpath(
            '//div[@id="taxingJurisdictionDetails"]/table[2]//tr/td[text()="%s:"]/following-sibling::td[1]/text()' % key)])

    return listing


# Improvement / Building
def parse_dropdown_improvement(page_tree):
    listing = dict()
    row_tree_list = page_tree.xpath(
        '//div[@id="improvementBuildingDetails"]/table//tr/td[not(contains(text(), "No improvements exist for this property."))]')

    if len(row_tree_list):
        pass
        # pdb.set_trace()

    return listing


# Land
def parse_dropdown_land(page_tree):
    listing = dict()
    row_tree_list = page_tree.xpath(
        '//div[@id="landDetails"]/table//tr[not(contains(@class, "tableDataHeader"))]')
    land_keys = ['Type', 'Description', 'Acres', 'Sqft',
                 'Eff Front', 'Eff Depth', 'Market Value', 'Prod. Value']
    for index, row_tree in enumerate(row_tree_list):
        for key_index, key in enumerate(land_keys):
            listing['Land - %s #%s' % (key, index + 1)] = '\n'.join([text.strip()
                                                                     for text in row_tree.xpath('./td[%s]/text()' % (key_index + 2))])

    return listing


# Roll Value History
def parse_dropdown_value_history(page_tree):
    listing = dict()
    row_tree_list = page_tree.xpath(
        '//div[@id="rollHistoryDetails"]/table//tr[not(contains(@class, "tableDataHeader"))]')
    value_history_keys = ['Year', 'Improvements', 'Land Market', 'Ag Valuation',
                          'Appraised', 'HS Cap', 'Assessed']
    for index, row_tree in enumerate(row_tree_list):
        for key_index, key in enumerate(value_history_keys):
            listing['Roll Value History - %s #%s' % (key, index + 1)] = '\n'.join(
                [text.strip() for text in row_tree.xpath('./td[%s]/text()' % (key_index + 1))])

    return listing


# Deed History - (Last 3 Deed Transactions)
def parse_dropdown_deed_history(page_tree):
    listing = dict()
    row_tree_list = page_tree.xpath(
        '//div[@id="deedHistoryDetails"]/table//tr[not(contains(@class, "tableDataHeader"))]')
    deed_history_keys = ['Deed Date', 'Type', 'Description', 'Grantor',
                         'Grantee', 'Volume', 'Page', 'Deed Number']
    for index, row_tree in enumerate(row_tree_list):
        for key_index, key in enumerate(deed_history_keys):
            listing['Deed History - %s #%s' % (key, index + 1)] = '\n'.join(
                [text.strip() for text in row_tree.xpath('./td[%s]//text()' % (key_index + 2))])

    return listing


def parse_property_page(page_text):
    page_tree = etree.HTML(page_text)

    listing = {
        **parse_dropdown_property(page_tree),
        **parse_dropdown_values(page_tree),
        **parse_dropdown_tax(page_tree),
        **parse_dropdown_improvement(page_tree),
        **parse_dropdown_land(page_tree),
        **parse_dropdown_value_history(page_tree),
        **parse_dropdown_deed_history(page_tree)
    }

    for key in [key for key in listing.keys() if key not in FIELD_NAMES]:
        FIELD_NAMES.append(key)

    print(listing)
    return listing


parsed_listing = []
for property_id in property_ids:
    listing = None

    with open('%s.html' % property_id, 'r') as f:
        print('=============== %s ==============' % property_id)
        listing = parse_property_page(f.read())

    if listing:
        parsed_listing.append(listing)

with open('results.csv', 'w') as results_file:
    csv_writer = csv.DictWriter(results_file, fieldnames=FIELD_NAMES)
    csv_writer.writeheader()

    csv_writer.writerows(parsed_listing)
