"""
OpenTelemetry setup for the capstone API.

Exports OTLP/gRPC to whatever collector is at OTEL_EXPORTER_OTLP_ENDPOINT
(docker-compose points it at Jaeger). Falls back to console output if no
endpoint is configured — great for `uv run` local dev.

Span naming follows OTel GenAI semantic conventions:
  https://opentelemetry.io/docs/specs/semconv/gen-ai/
"""

from __future__ import annotations

import os

from opentelemetry import trace
from opentelemetry.exporter.otlp.proto.grpc.trace_exporter import OTLPSpanExporter
from opentelemetry.sdk.resources import SERVICE_NAME, Resource
from opentelemetry.sdk.trace import TracerProvider
from opentelemetry.sdk.trace.export import BatchSpanProcessor, ConsoleSpanExporter

SERVICE = "building-ops-assistant"


def configure_tracing() -> trace.Tracer:
    """Install a global tracer provider; return our tracer."""
    provider = TracerProvider(resource=Resource.create({SERVICE_NAME: SERVICE}))

    endpoint = os.environ.get("OTEL_EXPORTER_OTLP_ENDPOINT")
    if endpoint:
        provider.add_span_processor(
            BatchSpanProcessor(OTLPSpanExporter(endpoint=endpoint, insecure=True))
        )
    else:
        # local dev — print spans to stdout so you can see them without a backend
        provider.add_span_processor(BatchSpanProcessor(ConsoleSpanExporter()))

    trace.set_tracer_provider(provider)
    return trace.get_tracer(SERVICE)


tracer = configure_tracing()
