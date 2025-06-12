# Bluesky & Mastodon Auto-Poster

A Python script that automatically posts content to both Bluesky and Mastodon social networks. Supports text posts, URL links with rich previews, and local image uploads with captions.

## Features

- 📝 **Text Posts**: Simple status updates
- 🔗 **Rich Link Previews**: Automatically extracts titles, descriptions, and featured images from URLs
- 🖼️ **Local Image Uploads**: Post images from your local `images/` folder with captions
- 🤖 **Dual Platform**: Posts to both Bluesky and Mastodon simultaneously
- 📁 **File Management**: Automatically moves posted content from queue to archive
- 🛡️ **Error Handling**: Continues working even if one platform fails
- 🔄 **Batch Processing**: Processes one item at a time from your queue file

## Installation

### 1. Install Python Dependencies

```bash
pip install atproto requests beautifulsoup4 pillow Mastodon.py
```

### 2. Set Up Environment Variables

#### For Bluesky:
```bash
export BLUESKY_HANDLE='yourname.bsky.social'
export BLUESKY_PASSWORD='your-app-password'
```

#### For Mastodon:
```bash
export MASTODON_INSTANCE_URL='https://your-instance.social'
export MASTODON_ACCESS_TOKEN='your-access-token'
```

### 3. Get Your Credentials

#### Bluesky App Password:
1. Go to [Bluesky Settings](https://bsky.app/settings)
2. Navigate to "Privacy and Security" → "App Passwords"
3. Create a new app password
4. Use this password, NOT your regular login password

#### Mastodon Access Token:
1. Go to your Mastodon instance
2. Settings → Development → New Application
3. Give it a name and select "write" permissions
4. Copy the access token from the created application

## File Structure

```
your-project-folder/
├── autoposter.py          # The main script
├── topost.txt            # Queue of content to post
├── posted.txt            # Archive of posted content
└── images/               # Folder for local images
    ├── photo1.jpg
    ├── meme.png
    └── screenshot.gif
```

## Usage

### Input Format

Create a `topost.txt` file with one item per line:

#### Text Posts
```
Just had the best coffee ever!
Working on some Python code today.
```

#### URL Posts with Comments
```
https://example.com/article | Check out this fascinating article about AI
https://blog.example.com/post | This blog post changed my perspective
```

#### Local Image Posts
```
vacation.jpg | Beautiful sunset from my trip to Hawaii
funny-meme.png | This made me laugh so hard 😂
screenshot.gif | Demo of my latest project
```

### Running the Script

```bash
python autoposter.py
```

### What Happens

1. **Reads** the first line from `topost.txt`
2. **Processes** the content based on type (text/URL/image)
3. **Posts** to both Bluesky and Mastodon
4. **Removes** the posted line from `topost.txt`
5. **Archives** it in `posted.txt` with timestamp

## Content Types

### 1. Simple Text Posts
- Just write your status update
- Posted as-is to both platforms

### 2. URL Posts
- Format: `URL | Your comment`
- Automatically extracts page title, description, and featured image
- Creates rich link previews on both platforms
- Your comment appears above the link card

### 3. Local Image Posts
- Format: `filename.ext | Your caption`
- Loads image from `images/` subfolder
- Supports: `.jpg`, `.jpeg`, `.png`, `.gif`, `.webp`, `.bmp`, `.tiff`
- Automatically resizes and optimizes images
- Posts image with your caption on both platforms

## Error Handling

- **Platform Failures**: If one platform fails, the other will still post
- **Image Issues**: If image download/upload fails, posts without image
- **Network Problems**: Detailed error messages help troubleshoot
- **File Issues**: Handles missing files gracefully
- **Credential Problems**: Clear setup instructions if credentials are missing

## Automation

### Run Periodically with Cron

Add to your crontab to run every hour:
```bash
# Edit crontab
crontab -e

# Add this line to run every hour
0 * * * * cd /path/to/your/script && python autoposter.py
```

### Run Periodically with systemd (Linux)

Create a service file and timer for more advanced scheduling.

## Limitations

- **Rate Limits**: Respects platform rate limits (posts one item per run)
- **Image Size**: Automatically resizes large images to platform limits
- **File Formats**: Images converted to JPEG for compatibility
- **Sequential Processing**: Processes one line at a time from the queue

## Troubleshooting

### Common Issues

1. **"Please set your credentials"**
   - Make sure environment variables are set correctly
   - For Bluesky, use app password, not your regular password

2. **"Image file not found"**
   - Make sure the `images/` folder exists
   - Check that image filename matches exactly (case-sensitive)

3. **"Failed to create post"**
   - Check your internet connection
   - Verify credentials are still valid
   - Check if you've hit platform rate limits

4. **"Error fetching metadata"**
   - Some websites block automated requests
   - Script will post the URL without rich preview

### Debug Mode

For more detailed output, you can modify the script to add debug logging or run with verbose error reporting.

## Contributing

Feel free to submit issues, feature requests, or pull requests to improve this script!

## License

This script is provided as-is for personal use. Please respect the terms of service of both platforms when using automated posting tools.
