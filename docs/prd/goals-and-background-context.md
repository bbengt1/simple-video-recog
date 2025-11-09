# Goals and Background Context

## Goals

- Successfully deploy a functional ML/CV system on local M1 hardware demonstrating practical video recognition capabilities
- Create automated awareness of events in monitored spaces through semantic understanding (not just motion detection)
- Build a comprehensive learning laboratory for understanding vision models, Apple Neural Engine optimization, and real-time processing pipelines
- Deliver actionable event alerts with <5% false positive rate through intelligent filtering and semantic analysis
- Produce a well-documented, open-source project demonstrating ML engineering competency for portfolio development
- Maintain 100% local processing with zero cloud dependencies, validating privacy-first architecture

## Background Context

This PRD defines the MVP for a **Local Video Recognition System** that addresses a critical gap in home security and ML learning: the lack of semantic understanding in local-first camera solutions. While cloud services (Nest, Ring) offer smart features, they compromise privacy. Existing open-source alternatives (Frigate, ZoneMinder) provide basic motion/object detection but lack the semantic reasoning ("person carrying package") that vision language models enable.

The project leverages recent advances in lightweight vision LLMs (LLaVA, Moondream) and Apple Silicon's Neural Engine to make real-time local processing feasible. Through a hybrid architecture (motion detection → CoreML filtering → LLM analysis), the system processes <1% of frames with expensive models while maintaining comprehensive awareness. This serves dual purposes: a functional home security system and a hands-on learning platform for ML/CV deployment on edge devices.

## Change Log

| Date | Version | Description | Author |
|------|---------|-------------|--------|
| 2025-11-08 | 1.0 | Initial PRD draft from Project Brief | John (PM) |

---
