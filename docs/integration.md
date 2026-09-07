# Integration boundaries

| Component | Owns or supplies | Coordinate with |
| --- | --- | --- |
| HPA | Pod replica count | One replica owner per workload; metrics and resource requests |
| VPA | Resource recommendations; optional Pod resource updates | Avoid CPU/memory utilization feedback conflicts with HPA |
| KEDA | Event activation and its generated HPA | No independent HPA on the same target |
| Goldilocks | VPA creation and recommendation UI | A shared VPA recommender; opt-in namespace ownership |
| Metrics Server | metrics.k8s.io CPU/memory data | One resource APIService provider |
| Prometheus Adapter | custom.metrics.k8s.io in this example | Prometheus label/query contract; no external API ownership here |
| Knative Serving | Revision replicas and activation | Do not add an independent HPA to managed Revisions |
| Karpenter | Provider-specific node provisioning and instance selection | Separate capacity ownership; baseline controller placement |
| Cluster Autoscaler | Existing node-group size | Provider/cluster version match; separate capacity from Karpenter |

Install only one selected owner of each shared APIService, CRD installation and workload scaling field. Each package uses its own demo namespace. Resource sizing and node sizing operate at different levels: selecting a larger EC2 instance does not change a Pod's requests or limits. Metrics Server and Prometheus Adapter supply inputs; they are not independent workload replica controllers.

Keep changes reviewable through private site values and GitOps ownership. Back up current scaling policies before changing controllers; disabling an autoscaler does not automatically restore previous replica counts, resource requests or cloud capacity.
