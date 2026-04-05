# Reddit Personal Profile Updater

A lightweight, automated script designed to publish updates strictly to my personal Reddit user profile (`u/forLyf`).

---

## 🎯 Purpose

The sole purpose of this script is to act as a personal automation tool. It synchronizes updates, project releases, and announcements from my external platforms and pushes them directly to my own Reddit profile page.

**Scope & Limitations:**
* **Profile Only:** This script is hardcoded to submit posts *only* to the authenticated user's personal profile.
* **No Subreddit Interaction:** It does not, and will not, interact with, post to, or comment on any public subreddits.
* **No Spam/Scraping:** It does not scrape Reddit data, send direct messages, or perform automated upvoting/downvoting.

---

## 🛠️ Tech Stack

* **Language:** Python 3.x
* **Library:** PRAW (Python Reddit API Wrapper)
* **Authentication:** OAuth2 (via Reddit API)

---

## ⚙️ Setup & Installation

1. **Clone the repository:**
   ```bash
   git clone https://github.com/yourusername/reddit-profile-updater.git
   cd reddit-profile-updater
   ```

2. **Install dependencies:**
   ```bash
   pip install praw python-dotenv
   ```

3. **Configure Environment Variables:**
   Create a `.env` file in the root directory and add your Reddit API credentials:

   ```env
   REDDIT_CLIENT_ID=your_client_id
   REDDIT_CLIENT_SECRET=your_client_secret
   REDDIT_USERNAME=forLyf
   REDDIT_PASSWORD=your_password
   REDDIT_USER_AGENT=profile_updater:v1.0 (by u/forLyf)
   ```

---

## 🚀 Usage

Once configured and authorized, the script can be triggered manually or via a cron job to push a new text or link post to the profile:

```bash
python run_updater.py
```

---

## 📜 Compliance

This script is built to strictly adhere to Reddit's API Terms of Service and Developer Guidelines. It operates exclusively within the bounds of a single user's personal profile to prevent any disruption to the wider Reddit community.

---

Created by Abhishek Choudhary