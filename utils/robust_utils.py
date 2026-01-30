"""
Robust error handling and fallback utilities for the drug discovery system
"""

import logging
import time
import functools
from typing import Any, Callable, Optional
from pathlib import Path
from config import config

# Setup logging
def setup_logging():
    """Setup comprehensive logging"""
    log_config = config.get('logging')

    # Create logs directory
    log_file = Path(log_config.get('file', 'logs/drug_discovery.log'))
    log_file.parent.mkdir(parents=True, exist_ok=True)

    logging.basicConfig(
        level=getattr(logging, log_config.get('level', 'INFO')),
        format='%(asctime)s - %(name)s - %(levelname)s - %(message)s',
        handlers=[
            logging.FileHandler(log_file),
            logging.StreamHandler()
        ]
    )

    # Reduce verbosity of some libraries
    logging.getLogger('transformers').setLevel(logging.WARNING)
    logging.getLogger('torch').setLevel(logging.WARNING)
    logging.getLogger('sentence_transformers').setLevel(logging.WARNING)

    return logging.getLogger(__name__)

logger = setup_logging()

class AgentError(Exception):
    """Base exception for agent errors"""
    pass

class APIError(AgentError):
    """API-related errors"""
    pass

class ModelError(AgentError):
    """ML model-related errors"""
    pass

class DataError(AgentError):
    """Data-related errors"""
    pass

def robust_call(max_retries: int = 3, delay: float = 1.0, backoff: float = 2.0):
    """
    Decorator for robust function calls with retries and error handling

    Args:
        max_retries: Maximum number of retry attempts
        delay: Initial delay between retries
        backoff: Backoff multiplier for delay
    """
    def decorator(func: Callable) -> Callable:
        @functools.wraps(func)
        def wrapper(*args, **kwargs) -> Any:
            last_exception = None
            current_delay = delay

            for attempt in range(max_retries + 1):
                try:
                    return func(*args, **kwargs)
                except Exception as e:
                    last_exception = e
                    logger.warning(f"Attempt {attempt + 1}/{max_retries + 1} failed for {func.__name__}: {e}")

                    if attempt < max_retries:
                        logger.info(f"Retrying in {current_delay:.1f} seconds...")
                        time.sleep(current_delay)
                        current_delay *= backoff
                    else:
                        logger.error(f"All {max_retries + 1} attempts failed for {func.__name__}")

            # If we get here, all retries failed
            raise last_exception

        return wrapper
    return decorator

def safe_api_call(api_func: Callable, fallback_func: Optional[Callable] = None, *args, **kwargs):
    """
    Safely call an API function with automatic fallback

    Args:
        api_func: The API function to call
        fallback_func: Fallback function to call if API fails
        *args, **kwargs: Arguments to pass to the functions
    """
    try:
        logger.debug(f"Calling API function: {api_func.__name__}")
        result = api_func(*args, **kwargs)

        # Check if result is valid (not empty/null)
        if result is None or (hasattr(result, '__len__') and len(result) == 0):
            raise APIError("API returned empty result")

        return result

    except Exception as e:
        logger.warning(f"API call failed: {e}")
        if fallback_func:
            try:
                logger.info(f"Using fallback function: {fallback_func.__name__}")
                return fallback_func(*args, **kwargs)
            except Exception as fallback_e:
                logger.error(f"Fallback also failed: {fallback_e}")
                raise AgentError(f"Both API and fallback failed: {e}, {fallback_e}")
        else:
            raise AgentError(f"API call failed and no fallback available: {e}")

def safe_model_operation(model_func: Callable, fallback_func: Optional[Callable] = None, *args, **kwargs):
    """
    Safely perform ML model operations with fallback

    Args:
        model_func: The model operation function
        fallback_func: Fallback function if model operation fails
        *args, **kwargs: Arguments to pass to the functions
    """
    if not config.is_ml_enabled('prediction'):  # Generic check, can be made specific
        if fallback_func:
            logger.info("ML disabled, using fallback")
            return fallback_func(*args, **kwargs)
        else:
            raise ModelError("ML operations disabled and no fallback available")

    try:
        logger.debug(f"Performing model operation: {model_func.__name__}")
        return model_func(*args, **kwargs)

    except Exception as e:
        logger.warning(f"Model operation failed: {e}")
        if fallback_func:
            try:
                logger.info(f"Using model fallback: {fallback_func.__name__}")
                return fallback_func(*args, **kwargs)
            except Exception as fallback_e:
                logger.error(f"Model fallback also failed: {fallback_e}")
                raise ModelError(f"Both model operation and fallback failed: {e}, {fallback_e}")
        else:
            raise ModelError(f"Model operation failed and no fallback available: {e}")

def check_memory_usage():
    """Check current memory usage and warn if high"""
    try:
        import psutil
        process = psutil.Process()
        memory_gb = process.memory_info().rss / (1024**3)
        max_memory = config.get_memory_limit()

        if memory_gb > max_memory * 0.8:
            logger.warning(".1f")
        elif memory_gb > max_memory:
            logger.error(".1f")
            return False

        return True
    except ImportError:
        logger.debug("psutil not available for memory monitoring")
        return True
    except Exception as e:
        logger.debug(f"Memory check failed: {e}")
        return True

def validate_data_structure(data, expected_keys=None):
    """
    Validate data structure and convert types if needed

    Args:
        data: Data to validate
        expected_keys: List of expected keys in the data
    """
    if data is None:
        raise DataError("Data is None")

    # Convert numpy types to Python types for JSON serialization
    if hasattr(data, 'item'):  # numpy scalar
        data = data.item()
    elif hasattr(data, 'tolist'):  # numpy array
        data = data.tolist()
    elif isinstance(data, dict):
        data = {k: validate_data_structure(v) for k, v in data.items()}
    elif isinstance(data, (list, tuple)):
        data = [validate_data_structure(item) for item in data]

    # Check expected keys if provided
    if expected_keys and isinstance(data, dict):
        missing_keys = set(expected_keys) - set(data.keys())
        if missing_keys:
            logger.warning(f"Missing expected keys: {missing_keys}")

    return data

def create_error_response(agent_name: str, error: Exception, fallback_data=None):
    """
    Create a standardized error response for agents

    Args:
        agent_name: Name of the agent
        error: The exception that occurred
        fallback_data: Optional fallback data to include
    """
    error_msg = f"{agent_name} analysis failed: {str(error)}"

    response = {
        'agent': agent_name,
        'insights': error_msg,
        'data': fallback_data or [],
        'charts': {},
        'error': True,
        'error_type': type(error).__name__
    }

    logger.error(f"Agent {agent_name} error response: {error_msg}")
    return response

def health_check():
    """Perform a comprehensive health check"""
    health_status = {
        'overall': 'healthy',
        'checks': {},
        'timestamp': time.time()
    }

    # Check configuration
    try:
        config.get('app', 'port')
        health_status['checks']['config'] = 'ok'
    except Exception as e:
        health_status['checks']['config'] = f'error: {e}'
        health_status['overall'] = 'unhealthy'

    # Check data directories
    try:
        config.ensure_directories()
        health_status['checks']['directories'] = 'ok'
    except Exception as e:
        health_status['checks']['directories'] = f'error: {e}'
        health_status['overall'] = 'unhealthy'

    # Check memory
    if not check_memory_usage():
        health_status['checks']['memory'] = 'warning'
        if health_status['overall'] == 'healthy':
            health_status['overall'] = 'degraded'

    # Check if we can import all agents
    agents_to_check = [
        'market_agent', 'exim_agent', 'patent_agent', 'clinical_agent',
        'internal_agent', 'web_agent', 'literature_agent'
    ]

    if config.is_ml_enabled('prediction'):
        agents_to_check.extend(['ml_prediction_agent'])

    if config.is_ml_enabled('generative_ai'):
        agents_to_check.extend(['generative_ai_agent'])

    if config.is_ml_enabled('nlp_analysis'):
        agents_to_check.extend(['nlp_analysis_agent'])

    for agent_module in agents_to_check:
        try:
            __import__(f'agents.{agent_module}')
            health_status['checks'][f'agent_{agent_module}'] = 'ok'
        except Exception as e:
            health_status['checks'][f'agent_{agent_module}'] = f'error: {e}'
            health_status['overall'] = 'unhealthy'

    return health_status