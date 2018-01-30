from longtail_secret import *
import requests
import time
from lxml import etree
from io import StringIO
import html
from lxml.cssselect import CSSSelector

parser = etree.HTMLParser()

USER_AGENT = 'Python:{}:v{} (by /u/{})'.format(APP_NAME, VERSION, USERNAME)
TOKEN_URL = 'https://www.reddit.com/api/v1/access_token'
API_URL = 'https://oauth.reddit.com/'
REDDIT_THREAD = 'https://reddit.com/r/{}/comments/{}/'


token = None
top_posts = None
top_unique_ids = None

already_posted = []

def main():
	global token, top_posts, top_unique_ids, already_posted

	# Init token and current posts on frontpage
	token = get_token()
	top_posts = get_top_posts(token)
	top_unique_ids = get_unique_ids(top_posts)

	last_token_update = time.time()
	last_removals_check = time.time()
	last_already_posted_clear = time.time()

	current_time = 0

	while True:
		current_time = time.time()

		# update token every 50 minutes (token last 1 hour)
		if current_time - last_token_update >= 3000:
			token = get_token()
			last_token_update = current_time

		# Check frontpage every 40 seconds
		if current_time - last_removals_check >= 40:
			check_removals(token)
			last_removals_check = current_time

		# Clear the "already posted" array 1 time per day
		if current_time - last_already_posted_clear >= 86400:
			already_posted = []
			last_already_posted_clear = current_time

		time.sleep(1)

def get_token():
	client_auth = requests.auth.HTTPBasicAuth(CLIENT_ID, CLIENT_SECRET)
	post_data = {
		'grant_type': 'password',
		'username': USERNAME,
		'password': PASSWORD
	}
	headers = {"User-Agent": USER_AGENT}
	response = requests.post(TOKEN_URL, auth=client_auth, data=post_data, headers=headers)

	try:
		response.json()
	except:
		print('COULD NOT PARSE TOKEN', response.text, flush=True)
	return response.json()['access_token']


def check_removals(token):
	global top_posts, top_unique_ids

	# Get the current status of the frontpage
	new_top_posts = get_top_posts(token)
	new_top_unique_ids = get_unique_ids(new_top_posts)

	# Diff = was on frontpage 1 min ago but isn't currently
	potential_removals = top_unique_ids - new_top_unique_ids

	#print(potential_removals, flush=True)
	# Need to make sure that they were actually removed and not just moved down from frontpage
	verified_removals = []

	for post_id in potential_removals:
		if is_removed(post_id) and not is_porn(post_id, token):
			verified_removals.append(post_id)


	# Post removals to /r/undelete
	for removal in verified_removals:
		post_removal(removal, token)

	# Replace old top posts with new ones
	top_posts = new_top_posts
	top_unique_ids = new_top_unique_ids


def get_top_posts(token):
	headers = {'Authorization': 'bearer {}'.format(token), 'User-Agent': USER_AGENT}
	response = requests.get('{}r/all?limit=100'.format(API_URL), headers=headers)

	first_json = response.json()
	ids = first_json['data']['children']

	after = first_json['data']['after']
	
	for i in range(9):
		response = requests.get('{}r/all?limit=100&after={}'.format(API_URL, after), headers=headers)
		json = response.json()
		ids.extend(json['data']['children'])
		after = first_json['data']['after']
		
	return ids

def is_porn(post_id, token):
	subreddit = get_post_data(post_id)['subreddit']

	nsfw_but_not_porn = ['ImGoingToHellForThis','MorbidReality','watchpeopledie','GreatApes','Gore','DarkNetMarkets']

	if subreddit in nsfw_but_not_porn:
		return False

	headers = {'Authorization': 'bearer {}'.format(token), 'User-Agent': USER_AGENT}
	response = requests.get('{}r/{}/about'.format(API_URL, subreddit), headers=headers).json()

	if response['data']['over18']:
		print(subreddit, flush=True)

	return response['data']['over18']


def get_unique_ids(posts):
	ids = [post['data']['id'] for post in posts]
	return set(ids)


def is_removed(post_id):
	post = get_post_data(post_id)

	if post:
		url = REDDIT_THREAD.format(post['subreddit'], post_id)

		try:
			response = requests.get(url, headers={'User-Agent': USER_AGENT})
			# If the post has the tag <meta name="robots" content="noindex,nofollow" /> it counts as removed
			tree = etree.parse(StringIO(response.text), parser)
			#print(url)
			for meta_tag in tree.find('head').findall('meta'):
				if meta_tag.get('name') == 'robots':
					select_author = CSSSelector('.tagline .author')
					author_elements = select_author(tree.find('body'))

					if author_elements and len(author_elements) >= 1:
						if author_elements[0].text != '[deleted]':
							return True
					else:
						True
		except Error as e:
			print('error:', e, flush=True)
	return False


def post_removal(post_id, token):
	if post_id in already_posted:
		return

	post = get_post_data(post_id)
	index = get_post_index(post_id)

	if not post or not index:
		return

	post_title = html.unescape(post['title'])
	title = '[#{0}|+{1}|{2}] {4}  [/r/{3}]'.format(index, post['score'], post['num_comments'], post['subreddit'], '{}')

	if len(title) - 2 + len(post_title) > 299:
		title = title.format(post_title[:299 - (len(title) - 2 + 3)] + '...') 
	else:
		title = title.format(post_title)

	headers = {'Authorization': 'bearer {}'.format(token), 'User-Agent': USER_AGENT}
	post_data = {
		'api_type': 'json',
		'kind': 'link',
		'sr': SUBREDDIT,
		'title':title,
		'url': 'https://www.reddit.com' + post['permalink']
	}

	r = requests.post('{}api/submit'.format(API_URL), data=post_data, headers=headers)
	print(r.text, flush=True)
	already_posted.append(post_id)


def get_post_data(post_id):
	global top_posts

	for thread in top_posts:
		if thread['data']['id'] == post_id:
			return thread['data']
	return None


def get_post_index(post_id):
	global top_posts

	for i, post in enumerate(top_posts):
		if post['data']['id'] == post_id:
			return i + 1

	return 0


if __name__ == '__main__':
	main()
