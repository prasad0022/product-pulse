# Product Pulse — LLM Synthesis

The investigation response is now schema-driven.

Output sections:
- Findings
- Evidence
- Root-cause candidates
- Recommended actions
- Sources
- Disclaimer

The LLM provider is optional. `PRODUCT_PULSE_LLM=none` keeps the project runnable without an API key; `PRODUCT_PULSE_LLM=gemini` enables the Gemini adapter when a free-tier API key is configured.

The application must treat generated root causes as candidates, not verified causality.
