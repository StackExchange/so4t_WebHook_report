'''
This Python script is offered with no formal support. 
If you run into difficulties, reach out to the person who provided you with this script.
'''

# Standard libraries
import argparse
import csv
import re
import time

# Third-party libraries
import requests
from selenium import webdriver
from bs4 import BeautifulSoup


def main():

    args = get_args()
    validate_args(args)

    s = create_session(args.url)
    validate_admin(s, args.url)

    webhooks = get_webhooks(s, args.url)
    export_webhooks_to_csv(webhooks)


def get_args():

    parser = argparse.ArgumentParser(
        prog='soe_webhooks.py',
        formatter_class=argparse.RawDescriptionHelpFormatter,
        description='Gathers webhook data from Stack Overflow Enterprise and exports it to a CSV file.',
        epilog = 'Example usage:\n'
                'python3 so4t_tag_report.py --url "https://SUBDOMAIN.stackenterprise.co"')
    parser.add_argument('--url', 
                        type=str,
                        help='[REQUIRED] Base URL for your Stack Overflow for Teams instance')

    return parser.parse_args()


def validate_args(args):

    if not args.url:
        print("Missing required argument: --url")
        print("See --help for more information")
        raise SystemExit
    if "stackoverflowteams.com" in args.url:
        print("This script only works for Stack Overflow Enterprise. Sorry.")
        raise SystemExit


def create_session(base_url):

    options = webdriver.ChromeOptions()
    options.add_argument("--window-size=500,800")
    options.add_experimental_option("excludeSwitches", ['enable-automation'])
    driver = webdriver.Chrome(options=options)
    driver.get(base_url)

    while True:
        try:
            driver.find_element("class name", "s-user-card")
            break
        except:
            time.sleep(1)
    
    # pass cookies to requests
    cookies = driver.get_cookies()
    s = requests.Session()
    for cookie in cookies:
        s.cookies.set(cookie['name'], cookie['value'])
    driver.close()
    driver.quit()
    
    return s


def validate_admin(s, base_url):

    admin_url = base_url + '/enterprise/admin-settings'

    response = get_page_response(s, admin_url)
    if response.status_code != 200:
        print("Error: Unable to access admin settings page. Please check your URL and permissions.")
        exit()


def get_page_response(s, url):

    response = s.get(url)
    if response.status_code == 200:
        return response
    else:
        print(f'Error getting page {url}')
        print(f'Response code: {response.status_code}')
        return None


def get_webhooks(s, base_url):

    webhooks_url = base_url + '/enterprise/webhooks'
    page_count = get_page_count(s, webhooks_url + '?page=1&pagesize=50')

    # get the webhook urls from each page
    webhooks = []
    for page in range(1, page_count + 1):
        print(f'Getting webhooks from page {page} of {page_count}')
        page_url = webhooks_url + f'?page={page}&pagesize=50'
        response = get_page_response(s, page_url)
        soup = BeautifulSoup(response.text, 'html.parser')
        webhook_rows = soup.find_all('tr')
        webhooks += process_webhooks(webhook_rows)

    return webhooks


def get_page_count(s, url):

    response = get_page_response(s, url)
    soup = BeautifulSoup(response.text, 'html.parser')
    pagination = soup.find_all('a', {'class': 's-pagination--item js-pagination-item'})
    try:
        page_count = int(pagination[-2].text)
    except IndexError: # only one page
        page_count = 1

    return page_count


def process_webhooks(webhook_rows):

    # A webhook description has three parts: tags, activity type, and channel
    # Examples to process:
        # All post activity to Private Channel > Private Channel
        # Any aws kubernetes github amazon-web-services (added via synonyms) kube 
            # (added via synonyms) posts to Engineering > Platform Engineering
        # Any admiral python aws amazon-web-services (added via synonyms) questions, 
            # answers to #admiral
        # Any questions, answers to #help-desk
        # Any machine-learning posts to #mits-demo

    activity_types = ['edited questions', 'updated answers', 'accepted answers', 'questions', 
                      'answers', 'comments']
    webhooks = []
    for row in webhook_rows:
        if row.find('th'): # skip header row
            continue

        columns = row.find_all('td')

        # Description always starts with "Any" unless it's "All post activity to..."
            # Which means all tags and activity types
        # In the description string, the space-delimited words after "Any" are tags
            # unless the notifications trigger for all tags, in which case it skips to activity type
            # some tags have suffixes like "(added via synonyms)"
        # The word "posts" is used to denote all activity types
        # Activity types are comma-delimited; everything else is space-delimited
        # The words after "to" are the channel; also, surrounded by <b></b> tags
        description = strip_html(columns[2].text).replace(
            '(added via synonyms) ', '').replace(',', '')

        if description.startswith('All post activity to'):
            tags = ['all']
            activities = activity_types
            channel = description.split('All post activity to ')[1]
        else:
            description = description.split('Any ')[1] # strip "Any"
            channel = description.split(' to ')[1]
            if 'posts to' in description: # all activity types
                activities = activity_types
                tags = description.split(' posts to ')[0].split(' ')
            else: # activity types are specified, but tags may or may not be
                # of the remaining words, find which are tags and activity types
                # activity types are comma-delimited
                # tags are space-delimited
                # tags are always first
                # tags are always followed by activity types
                description = description.split(' to ')[0] # strip off channel
                activities = []
                for activity_type in activity_types:
                    if activity_type in description:
                        activities.append(activity_type)
                        description = description.replace(activity_type, '').strip()
                if description:
                    tags = description.split(' ')
                else:
                    tags = ['all']
        
        webhook = {
            'type': strip_html(columns[0].text),
            'channel': channel,
            'tags': tags,
            'activities': activities,
            'creator': columns[3].text,
            'creation_date': columns[4].text
        }
        webhooks.append(webhook)

    return webhooks


def strip_html(text):

    return re.sub('<[^<]+?>', '', text).replace('\n', '').replace(
        '\r', '').strip()


def export_webhooks_to_csv(webhooks):

    file_name = 'webhooks.csv'

    csv_header = list(webhooks[0].keys())
    with open(file_name, 'w', encoding='UTF8', newline='') as f:
        writer = csv.writer(f)
        writer.writerow(csv_header)
        for webhook in webhooks:
            row_data = []
            for name, attribute in webhook.items():
                if name == 'tags':
                    tag_row = ''
                    for tag in attribute:
                        tag_row += tag + ', '
                    row_data.append(tag_row.strip(', '))
                elif name == 'activities':
                    activity_row = ''
                    for activity in attribute:
                        activity_row += activity + ', '
                    row_data.append(activity_row.strip(', '))
                else:
                    row_data.append(attribute)
            writer.writerow(row_data)

    print(f'CSV file created: {file_name}')


if __name__ == '__main__':

    main()