import praw
import requests
from time import sleep

SUBREDDIT = 'longtail'
reddit = praw.Reddit('frontpagewatch')

nsfw_but_not_porn =[
  'ImGoingToHellForThis',
  'MorbidReality',
  'watchpeopledie',
  'GreatApes',
  'Gore',
  'DarkNetMarkets'
]

# Links that we have already posted to /r/undelete
posted_ids = []

def get_top_ids():
  return [submission.id for submission in reddit.subreddit('all').hot(limit=1000)]

# Initial fetch for the thread-IDs of top 100 posts of /r/all
ids = set(get_top_ids())

# Ugly hack to check if a post is removed
# - It checks if the thread has a meta-tag for robots to not index the page...
def is_removed(thread_id, subreddit):
  url = 'https://www.reddit.com/r/{}/comments/{}/'.format(subreddit, thread_id)
  user_agent = 'frontpagewatch by /u/Frontpage-Watch'
  response = requests.get(url, headers={'User-Agent': user_agent})
  return '<meta name="robots" content="noindex,nofollow' in response.text

def check_removals():
  global ids

  new_ids_list = get_top_ids()
  new_ids = set(new_ids_list)
  diff = ids - new_ids

  for thread_id in diff:
    submission = reddit.submission(id=thread_id)
    subreddit = submission.subreddit

    subreddit_name = subreddit.display_name
    over18 = subreddit.over18

    if over18 and subreddit_name.lower() not in nsfw_but_not_porn:
      continue

    if thread_id in posted_ids:
      continue

    if is_removed(thread_id, subreddit_name):
      posted_ids.append(thread_id)

      # For title of the post on /r/undelete
      index = new_ids_list.index(thread_id) + 1
      score = submission.score
      number_of_comments = submission.num_comments
      post_title = submission.title
      url = 'https://www.reddit.com{}'.format(submission.permalink)

      # A little ugly maybe...
      title = '[#{0}|+{1}|{2}] {4}  [/r/{3}]'.format(index, score, number_of_comments, subreddit.display_name, '{}')

      if len(title) - 2 + len(post_title) > 300:
        title = title.format(post_title[:300 - (len(title) - 2 + 3)] + '...')
      else:
        title = title.format(post_title)

      # Post to /r/undelete
      reddit.subreddit(SUBREDDIT).submit(title=title, url=url)
      print('----DELETED AND POSTED----', url)
  ids = new_ids


while True:
  sleep(60*10)
  check_removals()
