# Authentication Guide for YouTube Music Playlist Merger

## Why Authentication is Required

YouTube Music requires authentication to access your personal playlists and liked songs. This guide will walk you through creating the necessary authentication file.

## Prerequisites

- Firefox browser (recommended) or Chrome
- Active YouTube Music account

## Step-by-Step Instructions

### 1. Open YouTube Music
- Navigate to [music.youtube.com](https://music.youtube.com)
- Sign in with your Google account

### 2. Open Developer Tools
- Press `F12` or right-click → "Inspect Element"
- Click on the **Network** tab

### 3. Prepare to Capture Request
- Check the **Disable cache** checkbox in the Network tab
- Keep the Developer Tools open

### 4. Trigger the Request
- Click on **Library** in the YouTube Music sidebar
- **Reload the page** (F5 or Ctrl+R)

### 5. Find the Browse Request
- In the Network tab, click on **XHR** filter
- In the search box, type: `/browse`
- Look for a request named `browse?prettyPrint=false`
- Click on this request

### 6. Copy Request Headers
- In the request details, click on **Headers** tab
- Find **Request Headers** section
- Click on **Raw** button (switch from formatted view)
- Select all text (Ctrl+A) and copy (Ctrl+C)

### 7. Generate browser.json
Open terminal/command prompt and run:
```bash
ytmusicapi browser
```
When prompted:

1. Paste the copied headers
2. Press Enter
3. Press Ctrl+Z (Windows) or Ctrl+D (macOS/Linux)
4. Press Enter again
This creates a `browser.json` file in your current directory.

### 8. Use in Application
- Open YouTube Music Playlist Merger
- Click Browse button in Step 1
- Select your `browser.json` file
- Click **Test Authentication**

## Troubleshooting

### "Authentication Failed" Error
- Make sure you're logged into YouTube Music
- Try using a different browser
- Ensure you copied the complete raw headers
- Regenerate the browser.json file

### Headers Not Appearing
- Make sure Developer Tools is open before reloading
- Clear browser cache and try again
- Try using an incognito/private window

### Token Expiration
- Authentication tokens may expire after some time
- If you get authentication errors after previously working, regenerate browser.json

### Security Notes
- **Keep browser.json private** - it contains your authentication tokens
- Don't commit browser.json to version control
- Don't share your browser.json file with others
- Regenerate if you suspect it's been compromised