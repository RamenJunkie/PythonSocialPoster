#!/usr/bin/env python3
"""
Bluesky & Mastodon Auto-Poster Script with Link Embeds and Featured Images

This script reads the first line from "topost.txt", posts it to both Bluesky and Mastodon
with proper link embedding and featured images, removes it from the file, 
and appends it to "posted.txt".

Requirements:
- pip install atproto requests beautifulsoup4 pillow Mastodon.py
- Set your Bluesky and Mastodon credentials in environment variables
"""

import os
import sys
import requests
from datetime import datetime
from urllib.parse import urljoin, urlparse
from io import BytesIO
from PIL import Image
import tempfile

from atproto import Client, models
from mastodon import Mastodon
from bs4 import BeautifulSoup

# Bluesky Configuration
BLUESKY_HANDLE = os.getenv('BLUESKY_HANDLE', 'your-handle.bsky.social')
BLUESKY_PASSWORD = os.getenv('BLUESKY_PASSWORD', 'your-app-password')

# Mastodon Configuration
MASTODON_INSTANCE_URL = os.getenv('MASTODON_INSTANCE_URL', 'https://mastodon.social')
MASTODON_ACCESS_TOKEN = os.getenv('MASTODON_ACCESS_TOKEN', 'your-access-token')

# File Configuration
TOPOST_FILE = 'topost.txt'
POSTED_FILE = 'posted.txt'

# User agent for web scraping
USER_AGENT = 'Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/91.0.4472.124 Safari/537.36'

def read_first_line():
    """Read and return the first line from topost.txt"""
    try:
        with open(TOPOST_FILE, 'r', encoding='utf-8') as f:
            lines = f.readlines()
        
        if not lines:
            print("No content to post - topost.txt is empty")
            return None, []
        
        first_line = lines[0].strip()
        remaining_lines = lines[1:]
        
        return first_line, remaining_lines
    
    except FileNotFoundError:
        print(f"Error: {TOPOST_FILE} not found")
        return None, []
    except Exception as e:
        print(f"Error reading {TOPOST_FILE}: {e}")
        return None, []

def create_bluesky_post_with_embed(client, url, comment, metadata):
    """Create a Bluesky post with embedded link card"""
    try:
        # Create external embed
        external_embed = models.AppBskyEmbedExternal.External(
            uri=url,
            title=metadata['title'][:300],  # Bluesky has title limits
            description=metadata['description'][:1000] if metadata['description'] else ''
        )
        
        # Handle image if available
        if metadata['image_url']:
            print(f"Downloading featured image: {metadata['image_url']}")
            image_data = download_and_process_image(metadata['image_url'])
            
            if image_data:
                print("Uploading image to Bluesky...")
                blob = upload_image_to_bluesky(client, image_data)
                if blob:
                    external_embed.thumb = blob.blob
                    print("✓ Image uploaded successfully")
                else:
                    print("⚠️  Failed to upload image, posting without it")
            else:
                print("⚠️  Failed to download image, posting without it")
        
        # Create the embed
        embed = models.AppBskyEmbedExternal.Main(external=external_embed)
        
        # Create the post
        response = client.send_post(text=comment, embed=embed)
        return response
    
    except Exception as e:
        print(f"Error creating post with embed: {e}")
        return None
        with open(TOPOST_FILE, 'r', encoding='utf-8') as f:
            lines = f.readlines()
        
        if not lines:
            print("No content to post - topost.txt is empty")
            return None, []
        
        first_line = lines[0].strip()
        remaining_lines = lines[1:]
        
        return first_line, remaining_lines
    
    except FileNotFoundError:
        print(f"Error: {TOPOST_FILE} not found")
        return None, []
    except Exception as e:
        print(f"Error reading {TOPOST_FILE}: {e}")
        return None, []
    pass

def parse_line(line):
    """Parse a line into URL/image and comment, or just text for simple status"""
    if '|' not in line:
        # No separator found - treat entire line as simple text status
        return {'type': 'text', 'content': line.strip()}
    
    parts = line.split('|', 1)
    first_part = parts[0].strip()
    comment = parts[1].strip()
    
    # Check if the first part is a URL
    if first_part.startswith(('http://', 'https://', 'www.')):
        return {'type': 'url', 'url': first_part, 'comment': comment}
    
    # Check if the first part is an image file
    image_extensions = ('.jpg', '.jpeg', '.png', '.gif', '.webp', '.bmp', '.tiff')
    if any(first_part.lower().endswith(ext) for ext in image_extensions):
        return {'type': 'image', 'filename': first_part, 'caption': comment}
    
    # First part doesn't look like a URL or image, treat whole line as text
    return {'type': 'text', 'content': line.strip()}

def fetch_page_metadata(url):
    """Fetch page title, description, and featured image from URL"""
    try:
        headers = {'User-Agent': USER_AGENT}
        response = requests.get(url, headers=headers, timeout=10)
        response.raise_for_status()
        
        soup = BeautifulSoup(response.content, 'html.parser')
        
        # Get title
        title = None
        title_tag = soup.find('title')
        if title_tag:
            title = title_tag.get_text().strip()
        
        # Try Open Graph title first
        og_title = soup.find('meta', property='og:title')
        if og_title and og_title.get('content'):
            title = og_title.get('content').strip()
        
        # Get description
        description = None
        # Try Open Graph description first
        og_desc = soup.find('meta', property='og:description')
        if og_desc and og_desc.get('content'):
            description = og_desc.get('content').strip()
        else:
            # Try meta description
            meta_desc = soup.find('meta', attrs={'name': 'description'})
            if meta_desc and meta_desc.get('content'):
                description = meta_desc.get('content').strip()
        
        # Get featured image URL
        image_url = None
        # Try Open Graph image first
        og_image = soup.find('meta', property='og:image')
        if og_image and og_image.get('content'):
            image_url = og_image.get('content').strip()
            # Make sure it's an absolute URL
            image_url = urljoin(url, image_url)
        
        # If no OG image, try Twitter card image
        if not image_url:
            twitter_image = soup.find('meta', attrs={'name': 'twitter:image'})
            if twitter_image and twitter_image.get('content'):
                image_url = twitter_image.get('content').strip()
                image_url = urljoin(url, image_url)
        
        return {
            'title': title or url,
            'description': description or '',
            'image_url': image_url
        }
    
    except Exception as e:
        print(f"Error fetching metadata for {url}: {e}")
        return {
            'title': url,
            'description': '',
            'image_url': None
        }

def load_local_image(filename):
    """Load and process a local image file from the images subfolder"""
    try:
        image_path = os.path.join('images', filename)
        
        if not os.path.exists(image_path):
            print(f"Error: Image file not found: {image_path}")
            return None
        
        with open(image_path, 'rb') as f:
            image_data = f.read()
        
        # Process the image with PIL (resize if needed, convert format, etc.)
        img = Image.open(BytesIO(image_data))
        
        # Convert to RGB if necessary
        if img.mode in ('RGBA', 'LA', 'P'):
            img = img.convert('RGB')
        
        # Resize if too large (both platforms have size limits)
        max_size = (1200, 1200)
        if img.size[0] > max_size[0] or img.size[1] > max_size[1]:
            img.thumbnail(max_size, Image.Resampling.LANCZOS)
        
        # Save to bytes as JPEG
        img_bytes = BytesIO()
        img.save(img_bytes, format='JPEG', quality=85)
        img_bytes.seek(0)
        
        return img_bytes.getvalue()
    
    except Exception as e:
        print(f"Error loading local image {filename}: {e}")
        return None
    """Download image and process it for social media upload"""
    try:
        headers = {'User-Agent': USER_AGENT}
        response = requests.get(image_url, headers=headers, timeout=15)
        response.raise_for_status()
        
        # Open image with PIL
        img = Image.open(BytesIO(response.content))
        
        # Convert to RGB if necessary
        if img.mode in ('RGBA', 'LA', 'P'):
            img = img.convert('RGB')
        
        # Resize if too large (both platforms have size limits)
        max_size = (1200, 1200)
        if img.size[0] > max_size[0] or img.size[1] > max_size[1]:
            img.thumbnail(max_size, Image.Resampling.LANCZOS)
        
        # Save to bytes
        img_bytes = BytesIO()
        img.save(img_bytes, format='JPEG', quality=85)
        img_bytes.seek(0)
        
        return img_bytes.getvalue()
    
    except Exception as e:
        print(f"Error downloading/processing image {image_url}: {e}")
        return None

def download_and_process_image(image_url):
    """Download image and process it for Bluesky upload"""
    try:
        headers = {'User-Agent': USER_AGENT}
        response = requests.get(image_url, headers=headers, timeout=15)
        response.raise_for_status()
        
        # Open image with PIL
        img = Image.open(BytesIO(response.content))
        
        # Convert to RGB if necessary
        if img.mode in ('RGBA', 'LA', 'P'):
            img = img.convert('RGB')
        
        # Resize if too large (Bluesky has size limits)
        max_size = (1200, 1200)
        if img.size[0] > max_size[0] or img.size[1] > max_size[1]:
            img.thumbnail(max_size, Image.Resampling.LANCZOS)
        
        # Save to bytes
        img_bytes = BytesIO()
        img.save(img_bytes, format='JPEG', quality=85)
        img_bytes.seek(0)
        
        return img_bytes.getvalue()
    
    except Exception as e:
        print(f"Error downloading/processing image {image_url}: {e}")
        return None


def upload_image_to_bluesky(client, image_data):
    """Upload image to Bluesky and return blob reference"""
    try:
        blob = client.upload_blob(image_data)
        return blob
    except Exception as e:
        print(f"Error uploading image to Bluesky: {e}")
        return None

def create_bluesky_image_post(client, image_data, caption):
    """Create a Bluesky post with an image"""
    try:
        print("Uploading image to Bluesky...")
        blob = upload_image_to_bluesky(client, image_data)
        
        if not blob:
            print("Failed to upload image to Bluesky")
            return None
        
        # Create image embed
        image_embed = models.AppBskyEmbedImages.Image(
            alt="",  # You could add alt text here if needed
            image=blob.blob
        )
        
        embed = models.AppBskyEmbedImages.Main(images=[image_embed])
        
        # Create the post
        response = client.send_post(text=caption, embed=embed)
        print("✓ Image uploaded to Bluesky successfully")
        return response
    
    except Exception as e:
        print(f"Error creating Bluesky image post: {e}")
        return None
    """Create a simple text-only Bluesky post"""
    try:
        response = client.send_post(text=text)
        return response
    except Exception as e:
        print(f"Error creating simple Bluesky post: {e}")
        return None

def create_simple_bluesky_post(client, text):
    """Create a simple text-only Bluesky post"""
    try:
        response = client.send_post(text=text)
        return response
    except Exception as e:
        print(f"Error creating simple Bluesky post: {e}")
        return None

def create_mastodon_image_post(mastodon_client, image_data, caption):
    """Create a Mastodon post with an image"""
    try:
        print("Uploading image to Mastodon...")
        media_dict = mastodon_client.media_post(image_data, mime_type='image/jpeg')
        media_id = media_dict['id']
        
        response = mastodon_client.status_post(caption, media_ids=[media_id])
        print("✓ Image uploaded to Mastodon successfully")
        return response
    
    except Exception as e:
        print(f"Error creating Mastodon image post: {e}")
        return None
    """Create a Bluesky post with embedded link card"""
    try:
        # Create external embed
        external_embed = models.AppBskyEmbedExternal.External(
            uri=url,
            title=metadata['title'][:300],  # Bluesky has title limits
            description=metadata['description'][:1000] if metadata['description'] else ''
        )
        
        # Handle image if available
        if metadata['image_url']:
            print(f"Downloading featured image: {metadata['image_url']}")
            image_data = download_and_process_image(metadata['image_url'])
            
            if image_data:
                print("Uploading image to Bluesky...")
                blob = upload_image_to_bluesky(client, image_data)
                if blob:
                    external_embed.thumb = blob.blob
                    print("✓ Image uploaded successfully")
                else:
                    print("⚠️  Failed to upload image, posting without it")
            else:
                print("⚠️  Failed to download image, posting without it")
        
        # Create the embed
        embed = models.AppBskyEmbedExternal.Main(external=external_embed)
        
        # Create the post
        response = client.send_post(text=comment, embed=embed)
        return response
    
    except Exception as e:
        print(f"Error creating post with embed: {e}")
        return None

def create_mastodon_post(mastodon_client, text, url=None, image_data=None):
    """Create a Mastodon post with optional image and URL"""
    try:
        media_id = None
        
        # Upload image if available
        if image_data:
            print("Uploading image to Mastodon...")
            media_dict = mastodon_client.media_post(image_data, mime_type='image/jpeg')
            media_id = media_dict['id']
            print("✓ Image uploaded to Mastodon successfully")
        
        # Create post text
        if url:
            post_text = f"{text}\n\n{url}"
        else:
            post_text = text
        
        # Create the toot
        if media_id:
            response = mastodon_client.status_post(post_text, media_ids=[media_id])
        else:
            response = mastodon_client.status_post(post_text)
        
        return response
    
    except Exception as e:
        print(f"Error creating Mastodon post: {e}")
        return None

def create_simple_mastodon_post(mastodon_client, text):
    """Create a simple text-only Mastodon post"""
    try:
        response = mastodon_client.status_post(text)
        return response
    except Exception as e:
        print(f"Error creating simple Mastodon post: {e}")
        return None

def update_files(posted_line, remaining_lines):
    """Update topost.txt and append to posted.txt"""
    try:
        # Write remaining lines back to topost.txt
        with open(TOPOST_FILE, 'w', encoding='utf-8') as f:
            f.writelines(remaining_lines)
        
        # Append posted line to posted.txt with timestamp
        timestamp = datetime.now().strftime('%Y-%m-%d %H:%M:%S')
        with open(POSTED_FILE, 'a', encoding='utf-8') as f:
            f.write(f"[{timestamp}] {posted_line}\n")
        
        print(f"✓ Files updated successfully")
        
    except Exception as e:
        print(f"Error updating files: {e}")
        return False
    
    return True

def main():
    """Main function"""
    print("Bluesky & Mastodon Auto-Poster with Link Embeds Starting...")
    
    # Check Bluesky credentials
    if BLUESKY_HANDLE == 'your-handle.bsky.social' or BLUESKY_PASSWORD == 'your-app-password':
        print("\n⚠️  Please set your Bluesky credentials:")
        print("   Set environment variables BLUESKY_HANDLE and BLUESKY_PASSWORD")
        print("   export BLUESKY_HANDLE='yourname.bsky.social'")
        print("   export BLUESKY_PASSWORD='your-app-password'")
        sys.exit(1)
    
    # Check Mastodon credentials
    if MASTODON_ACCESS_TOKEN == 'your-access-token':
        print("\n⚠️  Please set your Mastodon credentials:")
        print("   Set environment variables MASTODON_INSTANCE_URL and MASTODON_ACCESS_TOKEN")
        print("   export MASTODON_INSTANCE_URL='https://your-instance.social'")
        print("   export MASTODON_ACCESS_TOKEN='your-access-token'")
        print("\n   To get a Mastodon access token:")
        print("   1. Go to your Mastodon instance Settings -> Development")
        print("   2. Create a new application with 'write' permissions")
        print("   3. Copy the access token")
        sys.exit(1)
    
    # Read first line from topost.txt
    line_to_post, remaining_lines = read_first_line()
    if not line_to_post:
        return
    
    print(f"Content to post: {line_to_post}")
    
    # Parse the line
    parsed_content = parse_line(line_to_post)
    
    image_data = None  # Will store image data
    
    if parsed_content['type'] == 'url':
        url = parsed_content['url']
        text_content = parsed_content['comment']
        
        print(f"URL: {url}")
        print(f"Comment: {text_content}")
        
        # Fetch page metadata
        print("Fetching page metadata...")
        metadata = fetch_page_metadata(url)
        print(f"✓ Page title: {metadata['title']}")
        print(f"✓ Description: {metadata['description'][:100]}..." if metadata['description'] else "✓ No description found")
        print(f"✓ Featured image: {metadata['image_url']}" if metadata['image_url'] else "✓ No featured image found")
        
        # Download image if available (we'll use it for both platforms)
        if metadata['image_url']:
            print(f"Downloading featured image: {metadata['image_url']}")
            image_data = download_and_process_image(metadata['image_url'])
            if image_data:
                print("✓ Image downloaded successfully")
            else:
                print("⚠️  Failed to download image")
    
    elif parsed_content['type'] == 'image':
        filename = parsed_content['filename']
        text_content = parsed_content['caption']
        
        print(f"Local image: {filename}")
        print(f"Caption: {text_content}")
        
        # Load local image
        print("Loading local image...")
        image_data = load_local_image(filename)
        if image_data:
            print("✓ Local image loaded successfully")
        else:
            print("❌ Failed to load local image")
            return
        
        metadata = None
    
    else:  # text post
        text_content = parsed_content['content']
        print(f"Simple text post: {text_content}")
        metadata = None
    
    try:
        # Initialize clients
        print("Connecting to Bluesky...")
        bluesky_client = Client()
        bluesky_client.login(BLUESKY_HANDLE, BLUESKY_PASSWORD)
        print("✓ Successfully logged in to Bluesky")
        
        print("Connecting to Mastodon...")
        mastodon_client = Mastodon(
            access_token=MASTODON_ACCESS_TOKEN,
            api_base_url=MASTODON_INSTANCE_URL
        )
        # Test the connection
        mastodon_client.account_verify_credentials()
        print("✓ Successfully connected to Mastodon")
        
        # Post to both platforms
        bluesky_success = False
        mastodon_success = False
        
        # Post to Bluesky
        if parsed_content['type'] == 'url' and metadata:
            print("Creating Bluesky post with embedded link...")
            bluesky_response = create_bluesky_post_with_embed(bluesky_client, parsed_content['url'], text_content, metadata)
        elif parsed_content['type'] == 'image' and image_data:
            print("Creating Bluesky post with image...")
            bluesky_response = create_bluesky_image_post(bluesky_client, image_data, text_content)
        else:
            print("Creating simple Bluesky text post...")
            bluesky_response = create_simple_bluesky_post(bluesky_client, text_content)
        
        if bluesky_response:
            print("✓ Bluesky post created successfully!")
            print(f"Bluesky Post URI: {bluesky_response.uri}")
            bluesky_success = True
        else:
            print("❌ Failed to create Bluesky post")
        
        # Post to Mastodon
        if parsed_content['type'] == 'url':
            print("Creating Mastodon post with link...")
            mastodon_response = create_mastodon_post(mastodon_client, text_content, parsed_content['url'], image_data)
        elif parsed_content['type'] == 'image' and image_data:
            print("Creating Mastodon post with image...")
            mastodon_response = create_mastodon_image_post(mastodon_client, image_data, text_content)
        else:
            print("Creating simple Mastodon text post...")
            mastodon_response = create_simple_mastodon_post(mastodon_client, text_content)
        
        if mastodon_response:
            print("✓ Mastodon post created successfully!")
            print(f"Mastodon Post URL: {mastodon_response['url']}")
            mastodon_success = True
        else:
            print("❌ Failed to create Mastodon post")
        
        # Update files only if at least one post was successful
        if bluesky_success or mastodon_success:
            success_platforms = []
            if bluesky_success:
                success_platforms.append("Bluesky")
            if mastodon_success:
                success_platforms.append("Mastodon")
            
            if update_files(line_to_post, remaining_lines):
                print(f"✓ Process completed successfully! Posted to: {', '.join(success_platforms)}")
            else:
                print(f"⚠️  Posts were created on {', '.join(success_platforms)} but file update failed")
        else:
            print("❌ Failed to post to both platforms")
    
    except Exception as e:
        print(f"❌ Error: {e}")
        sys.exit(1)

if __name__ == "__main__":
    main()
