# Dashboard Visualization (Phase 3)

For Phase 3, consider adding Grafana dashboard for visual monitoring:

**Setup:**
1. Export metrics to Prometheus format (add `/metrics` endpoint)
2. Run Prometheus server locally to scrape metrics
3. Configure Grafana to visualize Prometheus data

**Key Dashboards:**
- **Processing Pipeline:** Frames processed, motion detection rate, events created
- **Performance:** CoreML/LLM inference times with NFR target lines
- **Resources:** CPU, memory, storage usage over time
- **Errors:** Error rates by type, recent error log tail

**Alternative:** Simple web dashboard in Phase 2 can display latest metrics from `logs/metrics.json` via API endpoint.

---
