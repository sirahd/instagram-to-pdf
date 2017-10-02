import argparse
import errno
import json
import logging.config
import os
import re
import time
import warnings

import concurrent.futures
import requests
import tqdm

from const import *

class InstagramScraper(object):
    # epoch seconds of 1st November, 2016
    startDate = 1488268800
    # epoch seconds of 28th February, 2017
    endDate = 1477983600


    """InstagramScraper scrapes and downloads an instagram user's photos and videos"""

    def __init__(self, usernames, dst=None, quiet=False, max=0, retain_username=False):
        self.usernames = usernames if isinstance(usernames, list) else [usernames]
        self.max = max
        self.retain_username = retain_username
        self.dst = './' if dst is None else dst

        # Controls the graphical output of tqdm
        self.quiet = quiet

        self.session = requests.Session()
        self.cookies = None
        self.logged_in = False

    def make_dst_dir(self, username):
        """Creates the destination directory"""
        if self.dst == './':
            dst = './' + username
        else:
            dst = self.dst + '/' + username

        try:
            os.makedirs(dst)
        except OSError as err:
            if err.errno == errno.EEXIST and os.path.isdir(dst):
                # Directory already exists
                pass
            else:
                # Target dir exists as a file, or a different error
                raise

        return dst

    def scrape(self):
        """Crawls through and downloads user's media"""
        executor = concurrent.futures.ThreadPoolExecutor(max_workers=10)
        for username in self.usernames:

            # Make the destination dir.
            dst = self.make_dst_dir(username)

            # Crawls the media and sends it to the executor.
            iter = 0
            count = 1
            for item in self.media_gen(username):
                iter = iter + 1
                if ( self.max != 0 and iter >= self.max ):
                    break
                else:
                    executor.submit(self.download, item, username, count, dst)
                    self.parse_comment(username, item, count, dst)
                    count = count + 1

    def parse_comment(self, username, item, count, save_dir='./'):
        """Parses the returned JSON to extract details from each post"""
        base_name = username + "_" + str(count).zfill(3) + ".txt"
        file_path = os.path.join(save_dir, base_name)

        if not os.path.isfile(file_path):
            data = dict()

            time_second = time.localtime(int(item['created_time']))
            data['date'] = time.strftime('%b. %d, %Y', time_second)

            data['likes'] = str(item['likes']['count'])
            if (item['location'] and item['location']['name'] is not None):
                data['location'] = item['location']['name']
            else:
                data['location'] = ""
            data['caption'] = item['caption']['text'] if item['caption'] is not None else ""

            commentsList = []
            for comment in item['comments']['data']:
                commentsList.append({'person': comment['from']['username'], 'text': comment['text']})
            data['comments'] = commentsList

            with open(file_path, 'w') as text_file:
                json.dump(data, text_file)

    def media_gen(self, username):
        """Generator of all user's media"""
        media = self.fetch_media_json(username, max_id=None)

        while True:
            for item in media['items']:
                #
                if (int(item['created_time']) > self.startDate):
                    continue
                elif (int(item['created_time']) < self.endDate):
                    break
                else:
                    yield item
            if media.get('more_available') and media['items']:
                max_id = media['items'][-1]['id']
                media = self.fetch_media_json(username, max_id)
            else:
                return

    def fetch_media_json(self, username, max_id):
        """Fetches the user's media metadata"""
        url = MEDIA_URL.format(username)

        if max_id is not None:
            url += '?&max_id=' + max_id

        resp = self.session.get(url)

        if resp.status_code == 200:
            media = json.loads(resp.text)

            if not media['items']:
                raise ValueError('User {0} is private'.format(username))

            media['items'] = [self.set_media_url(item) for item in media['items']]
            return media
        else:
            raise ValueError('User {0} does not exist'.format(username))

    def set_media_url(self, item):
        """Sets the media url"""
        item['url'] = item[item['type'] + 's']['standard_resolution']['url'].split('?')[0]
        # remove dimensions to get largest image
        item['url'] = re.sub(r'/s\d{3,}x\d{3,}/', '/', item['url'])
        # get non-square image if one exists
        item['url'] = re.sub(r'/c\d{1,}.\d{1,}.\d{1,}.\d{1,}/', '/', item['url'])
        return item

    def download(self, item, username, count, save_dir='./'):
        """Downloads the media file"""
        extension = base_name = item['url'].split('/')[-1].split('.')[-1]
        base_name = username + "_" + str(count).zfill(3) + "." + extension
        file_path = os.path.join(save_dir, base_name)

        if not os.path.isfile(file_path):
            with open(file_path, 'wb') as media_file:
                try:
                    content = self.session.get(item['url']).content
                except requests.exceptions.ConnectionError:
                    time.sleep(5)
                    content = requests.get(item['url']).content

                media_file.write(content)

def main():
    people = ['tiffanyzhang96', 'lunanananalu',
              'premiere.palm', 'lightskineats', 'jenniewang_', 'amthystngyn',
              'freshlysnapped', 'andy_taing', 'jinas_eats', 'suetinysue',
              'foodjourneybynap', 'feastingseattle', 'raziyasworld', 'varihungry',
              'mikisophomorelyfe']
    scraper = InstagramScraper(people, 'data')
    scraper.scrape()

if __name__ == '__main__':
    main()
