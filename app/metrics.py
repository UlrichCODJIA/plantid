from prometheus_client import Counter, Histogram, start_http_server

REQUEST_COUNT = Counter(
    "chatbot_request_count", "Number of requests received", ["endpoint"]
)
REQUEST_LATENCY = Histogram(
    "chatbot_request_latency", "Request latency in seconds", ["endpoint"]
)


def start_metrics_server(port=7000):
    start_http_server(port)


def log_request(endpoint):
    REQUEST_COUNT.labels(endpoint=endpoint).inc()


def log_latency(endpoint, latency):
    REQUEST_LATENCY.labels(endpoint=endpoint).observe(latency)
