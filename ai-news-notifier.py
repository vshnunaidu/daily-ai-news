from dotenv import load_dotenv
load_dotenv()
import feedparser
import requests
from groq import Groq  # Or use openai if preferred
import os
from datetime import datetime

# Your custom sources (add/remove anytime)
RSS_FEEDS = [
    'https://therundown.ai/rss',  # The Rundown AI
    'https://bensbites.beehiiv.com/feed',  # Ben's Bites
    'https://www.artificialintelligence-newsletter.com/feed',  # The Batch alternative
    'https://blog.practicalai.news/feed',  # Practical AI News
    'https://huggingface.co/blog/feed.xml',  # Hugging Face
    # Add more: e.g., Arxiv AI: 'https://arxiv.org/rss/cs.AI'
]

# Groq API key (free tier: sign up at console.groq.com, get key)
GROQ_API_KEY = os.getenv('GROQ_API_KEY')  # Store as env var for security

# ntfy topic (your custom one)
NTFY_TOPIC = 'daily-ai-news'
NTFY_URL = f'https://ntfy.sh/{NTFY_TOPIC}'

# Custom summary prompt (change this string anytime for different styles)
SUMMARY_PROMPT = """
You are a witty AI news curator with a dry, deadpan sense of humor—like a British comedian who actually knows what they're talking about. 
Summarize the latest AI developments from the provided articles into a concise daily digest (350–450 words max).

Rules:
- Prioritize the most important, novel, or impactful stories first.
- For each major item: Give a short, punchy headline-style title, then 1–3 sentences explaining what happened and why it matters.
- Weave in subtle, dry humor where it fits naturally (sarcastic understatement, ironic observation, or light self-awareness)—never forced, never memes, and never at the expense of clarity or usefulness.
- Cut all fluff: No "exciting times ahead" filler, no excessive hype.
- End with a clean numbered or bulleted list of all individual article titles with direct links (no extra commentary there).
- Tone: Informative first, quietly amusing second. The reader should feel smarter after reading, with maybe one or two raised eyebrows from the humor.

Articles to summarize:
{articles}
"""

def fetch_latest_articles():
    articles = []
    for feed_url in RSS_FEEDS:
        feed = feedparser.parse(feed_url)
        for entry in feed.entries[:5]:  # Top 5 per feed to avoid overload
            pub_date = entry.get('published', datetime.now().isoformat())
            articles.append({
                'title': entry.title,
                'link': entry.link,
                'summary': entry.get('summary', 'No summary available'),
                'date': pub_date
            })
    # Sort by date, newest first
    articles.sort(key=lambda x: x['date'], reverse=True)
    return articles[:15]  # Limit to top 15 overall

def generate_summary(articles):
    client = Groq(api_key=GROQ_API_KEY)
    article_str = '\n'.join([f"Title: {a['title']}\nLink: {a['link']}\nSummary: {a['summary']}" for a in articles])
    
    response = client.chat.completions.create(
        messages=[{"role": "user", "content": SUMMARY_PROMPT.format(articles=article_str)}],
        model="llama-3.3-70b-versatile",  # Fast and free-tier friendly
    )
    return response.choices[0].message.content

def send_notification(summary, articles):
    # Format notification: Summary + clickable links
    message = f"Daily AI News - {datetime.now().strftime('%Y-%m-%d')}\n\n{summary}\n\nIndividual Articles:\n"
    for a in articles:
        message += f"- {a['title']}: {a['link']}\n"
    
    # Send to ntfy (supports markdown for better formatting)
    requests.post(NTFY_URL, data=message.encode('utf-8'), headers={'Title': 'Daily AI News', 'Priority': 'default'})

if __name__ == '__main__':
    articles = fetch_latest_articles()
    if articles:
        summary = generate_summary(articles)
        send_notification(summary, articles)