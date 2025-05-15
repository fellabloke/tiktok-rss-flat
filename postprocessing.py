import os
import asyncio
import csv
import time
from datetime import datetime, timezone
from feedgen.feed import FeedGenerator
#from tiktokapipy.api import TikTokAPI
from TikTokApi import TikTokApi
import config
from playwright.async_api import async_playwright, Playwright
from pathlib import Path
from urllib.parse import urlparse


# Edit config.py to change your URLs
ghRawURL = config.ghRawURL

api = TikTokApi()

ms_token = os.environ.get(
    "MS_TOKEN", None
)

async def runscreenshot(playwright: Playwright, url, screenshotpath):
    chromium = playwright.chromium # or "firefox" or "webkit".
    browser = await chromium.launch()
    page = await browser.new_page()
    await page.goto(url)
    # Save the screenshot
    await page.screenshot(path=screenshotpath, quality = 20, type = 'jpeg')
    await browser.close()

async def process_videos(api, identifier, is_hashtag=False):
    """Process videos for a user or hashtag and return a list of video data"""
    videos_data = []
    
    try:
        if is_hashtag:
            # For hashtags, use the hashtag search method
            challenge = api.challenge(identifier)
            challenge_info = await challenge.info()
            async for video in challenge.videos(count=10):
                videos_data.append(video)
        else:
            # For users, use the existing user method
            ttuser = api.user(identifier)
            user_data = await ttuser.info()
            async for video in ttuser.videos(count=10):
                videos_data.append(video)
        
        return videos_data
    except Exception as e:
        print(f"Error processing {('hashtag' if is_hashtag else 'user')} '{identifier}': {e}")
        return []

async def user_videos():
    with open('subscriptions.csv') as f:
        cf = csv.DictReader(f, fieldnames=['identifier', 'type'])
        for row in cf:
            identifier = row['identifier']
            # Default to 'user' if type is not specified
            entry_type = row.get('type', 'user').lower()
            is_hashtag = entry_type == 'hashtag'
            
            # Remove # from hashtag if present
            if is_hashtag and identifier.startswith('#'):
                identifier = identifier[1:]
            
            print(f'Running for {entry_type} \'{identifier}\'')
            
            # Create feed generator
            fg = FeedGenerator()
            
            if is_hashtag:
                feed_id = f'https://www.tiktok.com/tag/{identifier}'
                feed_title = f'#{identifier} TikTok Hashtag'
                feed_subtitle = f'All the latest TikToks with hashtag #{identifier}'
                file_name = f'hashtag_{identifier}'
            else:
                feed_id = f'https://www.tiktok.com/@{identifier}'
                feed_title = f'{identifier} TikTok'
                feed_subtitle = f'All the latest TikToks from {identifier}'
                file_name = identifier
            
            fg.id(feed_id)
            fg.title(feed_title)
            fg.author({'name':'Conor ONeill','email':'conor@conoroneill.com'})
            fg.link(href='http://tiktok.com', rel='alternate')
            fg.logo(ghRawURL + 'tiktok-rss.png')
            fg.subtitle(feed_subtitle)
            fg.link(href=ghRawURL + 'rss/' + file_name + '.xml', rel='self')
            fg.language('en')
            
            # Set the last modification time for the feed to be the most recent post, else now.
            updated = None
            
            async with TikTokApi() as api:
                await api.create_sessions(ms_tokens=[ms_token], num_sessions=1, sleep_after=3, headless=False)
                
                videos = await process_videos(api, identifier, is_hashtag)
                
                for video in videos:
                    fe = fg.add_entry()
                    
                    # Get author username for hashtag videos
                    author_username = video.as_dict['author']['uniqueId'] if is_hashtag else identifier
                    
                    link = f"https://tiktok.com/@{author_username}/video/{video.id}"
                    fe.id(link)
                    ts = datetime.fromtimestamp(video.as_dict['createTime'], timezone.utc)
                    fe.published(ts)
                    fe.updated(ts)
                    updated = max(ts, updated) if updated else ts
                    
                    if video.as_dict['desc']:
                        fe.title(video.as_dict['desc'][0:255])
                    else:
                        fe.title("No Title")
                    
                    fe.link(href=link)
                    
                    if video.as_dict['desc']:
                        content = video.as_dict['desc'][0:255]
                    else:
                        content = "No Description"
                    
                    if is_hashtag:
                        content = f"By @{author_username}: {content}"
                    
                    if video.as_dict['video']['cover']:
                        videourl = video.as_dict['video']['cover']
                        parsed_url = urlparse(videourl)
                        path_segments = parsed_url.path.split('/')
                        last_segment = [seg for seg in path_segments if seg][-1]
                        
                        # Use different folder structure for hashtags
                        folder_name = f"hashtag_{identifier}" if is_hashtag else identifier
                        screenshotsubpath = f"thumbnails/{folder_name}/screenshot_{last_segment}.jpg"
                        screenshotpath = os.path.dirname(os.path.realpath(__file__)) + "/" + screenshotsubpath
                        
                        # Create directory if it doesn't exist
                        os.makedirs(os.path.dirname(screenshotpath), exist_ok=True)
                        
                        if not os.path.isfile(screenshotpath):
                            async with async_playwright() as playwright:
                                await runscreenshot(playwright, videourl, screenshotpath)
                        
                        screenshoturl = ghRawURL + screenshotsubpath
                        content = f'<img src="{screenshoturl}" /> {content}'
                    
                    fe.content(content)
                
                if updated:
                    fg.updated(updated)
                
                # Ensure the rss directory exists
                os.makedirs('rss', exist_ok=True)
                
                # Write the RSS feed to a file
                fg.rss_file(f'rss/{file_name}.xml', pretty=True)


if __name__ == "__main__":
    asyncio.run(user_videos())
