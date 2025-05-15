import os
from datetime import datetime, timezone
from feedgen.feed import FeedGenerator

def generate_test_hashtag_rss():
    """Generate a test RSS feed for a hashtag to verify link formatting"""
    
    # Create feed generator
    fg = FeedGenerator()
    
    # Set up feed metadata for a hashtag
    hashtag = "veganfood"
    feed_id = f'https://www.tiktok.com/tag/{hashtag}'
    feed_title = f'#{hashtag} TikTok Hashtag'
    feed_subtitle = f'All the latest TikToks with hashtag #{hashtag}'
    file_name = f'hashtag_{hashtag}'
    
    fg.id(feed_id)
    fg.title(feed_title)
    fg.author({'name':'Test Author','email':'test@example.com'})
    fg.link(href='http://tiktok.com', rel='alternate')
    fg.subtitle(feed_subtitle)
    fg.link(href=f'rss/{file_name}.xml', rel='self')
    fg.language('en')
    
    # Add some test entries with properly formatted links
    test_videos = [
        {
            'id': '1234567890123456789',
            'author': 'user1',
            'title': 'Test Video 1',
            'desc': 'This is a test video for hashtag #veganfood',
            'createTime': int(datetime.now().timestamp())
        },
        {
            'id': '9876543210987654321',
            'author': 'user2',
            'title': 'Test Video 2',
            'desc': 'Another test video for hashtag #veganfood',
            'createTime': int(datetime.now().timestamp()) - 3600
        }
    ]
    
    for video in test_videos:
        fe = fg.add_entry()
        
        # Create the direct link to the TikTok video
        link = f"https://tiktok.com/@{video['author']}/video/{video['id']}"
        print(f"Adding video link: {link}")
        
        # Set the link as both the ID and the link for the RSS entry
        fe.id(link)
        ts = datetime.fromtimestamp(video['createTime'], timezone.utc)
        fe.published(ts)
        fe.updated(ts)
        
        fe.title(video['title'])
        
        # Explicitly set the link for the RSS entry
        fe.link(href=link)
        print(f"Set link in RSS entry: {link}")
        
        content = f"By @{video['author']}: {video['desc']}"
        fe.content(content)
    
    # Ensure the rss directory exists
    os.makedirs('rss', exist_ok=True)
    
    # Write the RSS feed to a file
    fg.rss_file(f'rss/{file_name}.xml', pretty=True)
    print(f"Generated test RSS feed: rss/{file_name}.xml")

if __name__ == "__main__":
    generate_test_hashtag_rss()
