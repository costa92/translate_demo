# Changelog

All notable changes to the Unified Knowledge Base System will be documented in this file.

The format is based on [Keep a Changelog](https://keepachangelog.com/en/1.0.0/),
and this project adheres to [Semantic Versioning](https://semver.org/spec/v2.0.0.html).

## [1.0.0] - 2025-07-18

### Added
- Initial release of the Unified Knowledge Base System
- Multiple storage backends support (in-memory, Notion, vector databases, cloud storage)
- Flexible document processing with various chunking strategies
- Advanced retrieval with semantic, keyword, and hybrid search
- High-quality generation with multiple LLM providers
- Multi-agent architecture for specialized knowledge tasks
- Comprehensive API with RESTful and WebSocket endpoints
- Docker and Kubernetes deployment support
- Monitoring system with health checks and performance metrics

### Changed
- Unified two separate knowledge base implementations into a single cohesive platform
- Consolidated all code under `src/knowledge_base/` directory
- Standardized interfaces across all components

### Removed
- Duplicate implementations from `knowledge_base/` and `src/agents/knowledge_base/`