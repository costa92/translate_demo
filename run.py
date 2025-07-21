"""
Main entry point for the knowledge base API server.
"""

import argparse
import os
import sys
import logging
from pathlib import Path

# Configure logging
logging.basicConfig(
    level=logging.INFO,
    format='%(asctime)s - %(name)s - %(levelname)s - %(message)s',
    handlers=[logging.StreamHandler()]
)
logger = logging.getLogger("kb_api")

def main():
    """
    Main entry point for the knowledge base API server.
    """
    parser = argparse.ArgumentParser(description="Knowledge Base API Server")
    parser.add_argument("--host", default=os.environ.get("KB_API_HOST", "0.0.0.0"), help="Host to bind the server to")
    parser.add_argument("--port", type=int, default=int(os.environ.get("KB_API_PORT", "8000")), help="Port to bind the server to")
    parser.add_argument("--debug", action="store_true", default=os.environ.get("KB_API_DEBUG", "false").lower() == "true", help="Enable debug mode")
    parser.add_argument("--log-level", default=os.environ.get("KB_SYSTEM_LOG_LEVEL", "INFO"), help="Logging level")
    parser.add_argument("--config", default=os.environ.get("KB_CONFIG_PATH", "config.yaml"), help="Path to config file")

    args = parser.parse_args()

    # Set log level
    log_level = getattr(logging, args.log_level.upper(), logging.INFO)
    logger.setLevel(log_level)

    # Check if config file exists
    config_path = Path(args.config)
    if not config_path.exists():
        logger.warning(f"Config file {args.config} does not exist, using default configuration")

    logger.info(f"Starting Knowledge Base API server on {args.host}:{args.port}")
    logger.info(f"Debug mode: {args.debug}")
    logger.info(f"Log level: {args.log_level}")
    logger.info(f"Config file: {args.config}")

    try:
        # Apply the orchestrator patch to handle missing agents gracefully
        try:
            from orchestrator_patch import patch_orchestrator
            patch_orchestrator()
        except Exception as e:
            logger.warning(f"Failed to apply orchestrator patch: {e}")

        # Import here to avoid circular imports
        from knowledge_base.api.server import run_app
        from knowledge_base.core.config import Config

        # Create config
        config = Config()
        config.api.host = args.host
        config.api.port = args.port
        config.system.debug = args.debug

        # Run the server
        run_app(config)
    except ImportError as e:
        logger.error(f"Failed to import required modules: {e}")
        logger.error("Make sure you have installed all required dependencies")
        sys.exit(1)
    except Exception as e:
        logger.error(f"Failed to start server: {e}")
        sys.exit(1)

if __name__ == "__main__":
    main()