import requests

API_KEY = "pub_f47ac10d3f6444429248ff3afa6d8408"

def fetch_real_time_news(query):
    try:
        url = f"https://newsdata.io/api/1/news?apikey={API_KEY}&q={query}&language=en"
        res = requests.get(url).json()

        articles = []
        for article in res.get("results", [])[:3]:
            articles.append(article.get("title", ""))

        return articles

    except Exception as e:
        print("News API Error:", e)
        return []

FACT_CHECK_API_KEY = "AIzaSyD3mVpT-gXHoGluVFWxi9c-SjAwMbWdGXE"

def fetch_fact_check(query):
    try:
        url = f"https://factchecktools.googleapis.com/v1alpha1/claims:search?query={query}&key={FACT_CHECK_API_KEY}"
        res = requests.get(url).json()

        claims = []

        for item in res.get("claims", [])[:3]:
            claim_text = item.get("text", "")
            reviews = item.get("claimReview", [])

            if reviews:
                rating = reviews[0].get("textualRating", "Unknown")
                claims.append(f"{claim_text} → {rating}")

        return claims

    except Exception as e:
        print("FactCheck API Error:", e)
        return []