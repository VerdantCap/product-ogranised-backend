from fastapi import APIRouter, Response
from prometheus_client import CollectorRegistry, Counter, generate_latest
import redis

router = APIRouter()

class MetricsService:
    def __init__(self):
        self.redis_client = redis.StrictRedis(host='127.0.0.1', port=6379, decode_responses=True)
        self.registry = CollectorRegistry()

    def add_counter(self, name, description, labels=None):
        if labels is None:
            labels = []
        return Counter(name, description, labelnames=labels, registry=self.registry)

    def render_metrics(self):
        return generate_latest(self.registry)

metrics_service = MetricsService()

@router.get("/metrics")
    metrics_content = metrics_service.render_metrics()
    return Response(content=metrics_content, media_type="text/plain")
