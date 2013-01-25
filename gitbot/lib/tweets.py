from datetime import datetime
import json
import re
import urllib2


API_BASE = 'http://api.twitter.com/1'
TWEETER_LINK_TEMPLATE = 'http://twitter.com/%s'
TWEET_LINK_TEMPLATE = TWEETER_LINK_TEMPLATE + '/status/%s'


def twokenize(text):
    user = '(?<=^|(?<=[^a-zA-Z0-9-_\.]))(@[A-Za-z]+[A-Za-z0-9]+)'
    hashtag = '(?<=^|(?<=[^a-zA-Z0-9-_\.]))(\#[A-Za-z]+[A-Za-z0-9]+)'
    link = '(https?://\S+)'
    char = '(.+?)'
    tokens = [user, hashtag, link, char]
    # USER = 1
    # HASHTAG = 2
    # LINK = 3
    CHAR = 4
    types = ['user', 'hashtag', 'link', 'text']

    tokenizer = re.compile('|'.join(tokens))
    tokens = []
    current_match_type = CHAR
    current_token = ''
    for match in tokenizer.finditer(text):
        match_type = match.lastindex
        value = repr(match.group(match_type)).strip(u'\"\'')
        if current_match_type == CHAR and match_type == CHAR:
            current_token = current_token + value
            continue
        elif match_type == CHAR:
            current_token = value
            current_match_type = CHAR
            continue
        elif current_match_type == CHAR:
            current_token = current_token.strip()
            if len(current_token):
                new_token = dict(type=types[current_match_type - 1],
                                    value=current_token)
                tokens.append(new_token)

        new_token = dict(type=types[match_type - 1], value=value)
        tokens.append(new_token)
        current_token = ''
        current_match_type = CHAR
    return tokens


class Tweet(object):

    @staticmethod
    def parse(data):
        sender = {}
        user = data["user"]
        sender["id"] = user["id_str"]
        sender["username"] = user["screen_name"]
        sender["profile_image"] = user["profile_image_url"]
        sender["profile_image_secure"] = user["profile_image_url_https"]
        sender["link"] = TWEETER_LINK_TEMPLATE % sender["username"]

        tweet = {}
        tweet["id"] = data['id_str']
        tweet["link"] = TWEET_LINK_TEMPLATE % (sender["username"], tweet["id"])
        tweet["time"] = datetime.strptime(data['created_at'],
                                            '%a %b %d %H:%M:%S +0000 %Y')
        tweet['text'] = data["text"]
        tweet["tokens"] = twokenize(str(tweet["text"]))
        return {"sender": sender, "tweet": tweet}


class Tweeter(object):

    def __init__(self, username):
        if not username:
            raise Exception('User name is required')
        self.username = username

    def lookup_user(self):
        url = '%s/users/lookup.json?screen_name=%s' % (API_BASE, self.username)
        try:
            data = urllib2.urlopen(url).read()
        except urllib2.HTTPError, e:
            if e.code == 404:
                return False
            raise Exception("HTTP error: %d" % e.code)
        except urllib2.URLError, e:
            raise Exception("Network error: %s" % e.reason.args[1])

        return "errors" not in data

    def get_favorites(self):
        if not self.lookup_user():
            return []
        url = '%s/favorites/%s.json' % (API_BASE, self.username)
        try:
            data = urllib2.urlopen(url).read()
        except urllib2.HTTPError, e:
            raise Exception("HTTP error: %d" % e.code)
        except urllib2.URLError, e:
            raise Exception("Network error: %s" % e.reason.args[1])

        return [Tweet.parse(tweet) for tweet in json.loads(data)]
