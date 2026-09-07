# Validation scope

The CI workflow has read-only repository permissions and no deployment credentials. It validates vendored artifact checksums, exact committed rendering, strict standard Kubernetes schemas, upstream custom-resource schemas and configuration guardrails. It also checks that deliberately excessive HPA limits and disabled aggregation TLS verification are rejected. VPA validates both recommendation and update-component installation variants.

Where a demo application is included, `make smoke` starts a local loopback HTTP server, exercises health and concurrent CPU-work requests, verifies the Prometheus counter and stops the server. This proves the application contract, not a working Kubernetes metrics pipeline or autoscaler.

The schema target is Kubernetes 1.35.0. Upstream compatibility must be checked for the selected controller and actual cluster; schema acceptance is not compatibility certification. JSON-schema validation does not execute Kubernetes CEL, admission webhooks, scheduler simulation, provider API calls or disruption behavior.

Before promotion, verify APIService and certificate readiness, actual metrics, controller permissions, scaling up/down under bounded load, scale-to-zero activation where applicable, PodDisruptionBudgets, capacity limits and rollback in a staging environment. Record the actual cluster version and results separately. No such live deployment was executed while publishing this package.
