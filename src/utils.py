import os
import re
from urllib.parse import urlparse

from openai import OpenAI, OpenAIError

p = re.compile(r"^www\d*\.")


def get_domain(url):
    url = url.rstrip("/")

    if not url.startswith(("http://", "https://")):
        url = "http://" + url

    netloc = urlparse(url).netloc
    domain = p.sub("", netloc)
    return domain


api_key = os.environ.get("OPENAI_API_KEY")
client = OpenAI(api_key=api_key)


def search_website(prompt, url, model_name="gpt-5-nano"):
    try:
        response = client.responses.create(
            model=model_name,
            tools=[
                {
                    "type": "web_search",
                }
            ],
            # tools=[{"type": "web_search", "filters": {"allowed_domains": [domain]}}],
            # include=["web_search_call.action.sources"],
            input=prompt,
        )
        return response
    except OpenAIError as e:
        print("Error:", e)
        print(url)
        return None
