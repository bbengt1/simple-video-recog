# Platform and Infrastructure Choice

**Platform:** macOS Native on Apple Silicon
**Key Services:** None - 100% local processing with no cloud services
**Deployment Host and Regions:** Local deployment on Mac Mini or Mac Studio (Apple Silicon M1/M2/M3)

**Rationale:** The platform choice is constrained by the requirement to use Apple's Neural Engine for CoreML inference. This hardware acceleration is only accessible on macOS with Apple Silicon (M1/M2/M3 chips). Cloud deployment is explicitly out of scope due to privacy requirements - all video processing must occur on local hardware with no data transmission to external services.
