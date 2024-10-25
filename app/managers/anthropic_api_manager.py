import logging
import os
import time
from functools import wraps

import anthropic
from logger import configure_logger

logger = configure_logger(log_level=logging.DEBUG, log_file="logs/anthropic.log")


class AnthropicAPIManager:
    def __init__(self, app=None):
        self.app = app
        if app is not None:
            self.init_app(app)

    def init_app(self, app):
        app.config.setdefault("ANTHROPIC_API_KEY", os.environ.get("ANTHROPIC_API_KEY"))
        app.config.setdefault("ANTHROPIC_RATE_LIMIT", 10)
        app.config.setdefault("ANTHROPIC_RETRY_ATTEMPTS", 3)

        if not app.config["ANTHROPIC_API_KEY"]:
            raise ValueError("ANTHROPIC_API_KEY must be set")

        self.client = anthropic.Anthropic(api_key=app.config["ANTHROPIC_API_KEY"], max_retries=3)
        self.rate_limit = app.config["ANTHROPIC_RATE_LIMIT"]
        self.last_request_time = 0

    def get_anthropic_client(self):
        if self.client is None:
            raise RuntimeError("Anthropic API client not initialized")
        return self.client

    def rate_limited(func):
        @wraps(func)
        def wrapper(self, *args, **kwargs):
            while True:
                current_time = time.time()
                time_passed = current_time - self.last_request_time
                time_left = (60 / self.rate_limit) - time_passed

                if time_left > 0:
                    time.sleep(time_left)

                self.last_request_time = time.time()

                try:
                    return func(self, *args, **kwargs)
                except Exception as e:
                    logger.warning(f"Rate limit exceeded: {e}")
                    time.sleep(60 / self.rate_limit)
                except Exception as e:
                    logger.error(f"Error in Anthropic API call: {e}")
                    raise

        return wrapper

    @rate_limited
    def generate_text(
        self, prompt, model="claude-3-opus-20240229", max_tokens_to_sample=1000, temperature=0.7, top_p=None
    ):
        try:
            params = {
                key: value
                for key, value in {
                    "model": model,
                    "prompt": prompt,
                    "max_tokens_to_sample": max_tokens_to_sample,
                    "temperature": temperature,
                    "top_p": top_p,
                }.items()
                if value is not None
            }

            response = self.client.completions.create(**params)
            return response.completion
        except anthropic.APIConnectionError as e:
            print("The server could not be reached")
            print(e.__cause__)
        except anthropic.RateLimitError:
            print("A 429 status code was received; we should back off a bit.")
        except anthropic.APIStatusError as e:
            print("Another non-200-range status code was received")
            print(e.status_code)
            print(e.response)
        except Exception as e:
            logger.error(f"Error in generate_text: {e}")

    @rate_limited
    def generate_chat(
        self, context=None, content=None, model="claude-3-opus-20240229", max_tokens=1000, temperature=0.7, top_p=None
    ):
        try:
            params = {
                key: value
                for key, value in {
                    "model": model,
                    "max_tokens": max_tokens,
                    "temperature": temperature,
                    "system": context,
                    "messages": [{"role": "user", "content": [{"type": "text", "text": content}]}],
                    "top_p": top_p,
                }.items()
                if value is not None
            }

            response = self.client.messages.create(**params)
            return response.content[0].text
        except anthropic.APIConnectionError as e:
            print("The server could not be reached")
            print(e.__cause__)
        except anthropic.RateLimitError:
            print("A 429 status code was received; we should back off a bit.")
        except anthropic.APIStatusError as e:
            print("Another non-200-range status code was received")
            print(e.status_code)
            print(e.response)
        except Exception as e:
            logger.error(f"Error in generate_chat: {e}")
