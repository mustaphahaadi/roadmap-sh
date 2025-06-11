import logging
import logging.handlers
import json
import sys
from datetime import datetime
from pathlib import Path
from typing import Optional, Dict, Any
import traceback


class JSONFormatter(logging.Formatter):
    """Custom JSON formatter for structured logging"""
    
    def format(self, record):
        log_entry = {
            'timestamp': datetime.fromtimestamp(record.created).isoformat(),
            'level': record.levelname,
            'logger': record.name,
            'message': record.getMessage(),
            'module': record.module,
            'function': record.funcName,
            'line': record.lineno
        }
        
        # Add exception info if present
        if record.exc_info:
            log_entry['exception'] = self.formatException(record.exc_info)
        
        # Add extra fields if present
        if hasattr(record, 'user_id'):
            log_entry['user_id'] = record.user_id
        if hasattr(record, 'request_id'):
            log_entry['request_id'] = record.request_id
        if hasattr(record, 'extra_data'):
            log_entry['extra_data'] = record.extra_data
            
        return json.dumps(log_entry, ensure_ascii=False)


class LoggingSystem:
    """Centralized logging system with multiple handlers and formatters"""
    
    def __init__(self, app_name: str = "MyApp", log_dir: str = "logs"):
        self.app_name = app_name
        self.log_dir = Path(log_dir)
        self.log_dir.mkdir(exist_ok=True)
        
        # Configure root logger
        self.root_logger = logging.getLogger()
        self.root_logger.setLevel(logging.DEBUG)
        
        # Clear existing handlers
        self.root_logger.handlers.clear()
        
        self._setup_handlers()
        
    def _setup_handlers(self):
        """Setup various logging handlers"""
        
        # Console handler with colored output
        console_handler = logging.StreamHandler(sys.stdout)
        console_handler.setLevel(logging.INFO)
        console_formatter = logging.Formatter(
            '%(asctime)s | %(levelname)-8s | %(name)s | %(message)s',
            datefmt='%Y-%m-%d %H:%M:%S'
        )
        console_handler.setFormatter(console_formatter)
        self.root_logger.addHandler(console_handler)
        
        # File handler for general logs
        file_handler = logging.handlers.RotatingFileHandler(
            self.log_dir / f"{self.app_name}.log",
            maxBytes=10*1024*1024,  # 10MB
            backupCount=5
        )
        file_handler.setLevel(logging.DEBUG)
        file_formatter = logging.Formatter(
            '%(asctime)s | %(levelname)-8s | %(name)s:%(lineno)d | %(message)s'
        )
        file_handler.setFormatter(file_formatter)
        self.root_logger.addHandler(file_handler)
        
        # JSON file handler for structured logs
        json_handler = logging.handlers.RotatingFileHandler(
            self.log_dir / f"{self.app_name}_structured.json",
            maxBytes=10*1024*1024,
            backupCount=5
        )
        json_handler.setLevel(logging.INFO)
        json_handler.setFormatter(JSONFormatter())
        self.root_logger.addHandler(json_handler)
        
        # Error file handler
        error_handler = logging.handlers.RotatingFileHandler(
            self.log_dir / f"{self.app_name}_errors.log",
            maxBytes=5*1024*1024,
            backupCount=3
        )
        error_handler.setLevel(logging.ERROR)
        error_handler.setFormatter(file_formatter)
        self.root_logger.addHandler(error_handler)
    
    def get_logger(self, name: str) -> logging.Logger:
        """Get a logger with the specified name"""
        return logging.getLogger(name)
    
    def log_with_context(self, logger_name: str, level: str, message: str, 
                        user_id: Optional[str] = None, 
                        request_id: Optional[str] = None,
                        extra_data: Optional[Dict[str, Any]] = None):
        """Log with additional context information"""
        logger = self.get_logger(logger_name)
        
        # Create log record with extra context
        extra = {}
        if user_id:
            extra['user_id'] = user_id
        if request_id:
            extra['request_id'] = request_id
        if extra_data:
            extra['extra_data'] = extra_data
        
        getattr(logger, level.lower())(message, extra=extra)


class DatabaseLogger:
    """Example database operation logger"""
    
    def __init__(self, logging_system: LoggingSystem):
        self.logger = logging_system.get_logger("database")
    
    def log_query(self, query: str, params: Optional[Dict] = None, 
                  execution_time: Optional[float] = None):
        """Log database query with execution details"""
        message = f"Executing query: {query[:100]}..."
        if execution_time:
            message += f" (took {execution_time:.3f}s)"
        
        extra_data = {"query": query}
        if params:
            extra_data["params"] = params
        if execution_time:
            extra_data["execution_time"] = execution_time
            
        self.logger.info(message, extra={"extra_data": extra_data})
    
    def log_error(self, error: Exception, query: Optional[str] = None):
        """Log database error"""
        message = f"Database error: {str(error)}"
        extra_data = {"error_type": type(error).__name__}
        if query:
            extra_data["failed_query"] = query
            
        self.logger.error(message, extra={"extra_data": extra_data}, exc_info=True)


class APILogger:
    """Example API request/response logger"""
    
    def __init__(self, logging_system: LoggingSystem):
        self.logger = logging_system.get_logger("api")
    
    def log_request(self, method: str, endpoint: str, user_id: Optional[str] = None,
                   request_id: Optional[str] = None, ip_address: Optional[str] = None):
        """Log incoming API request"""
        message = f"{method} {endpoint}"
        extra_data = {
            "method": method,
            "endpoint": endpoint,
            "ip_address": ip_address
        }
        
        extra = {"extra_data": extra_data}
        if user_id:
            extra["user_id"] = user_id
        if request_id:
            extra["request_id"] = request_id
            
        self.logger.info(message, extra=extra)
    
    def log_response(self, status_code: int, response_time: float,
                    request_id: Optional[str] = None):
        """Log API response"""
        message = f"Response: {status_code} (took {response_time:.3f}s)"
        extra_data = {
            "status_code": status_code,
            "response_time": response_time
        }
        
        extra = {"extra_data": extra_data}
        if request_id:
            extra["request_id"] = request_id
            
        level = "warning" if status_code >= 400 else "info"
        getattr(self.logger, level)(message, extra=extra)


class SecurityLogger:
    """Security-focused logger for authentication and authorization events"""
    
    def __init__(self, logging_system: LoggingSystem):
        self.logger = logging_system.get_logger("security")
    
    def log_login_attempt(self, username: str, success: bool, ip_address: str,
                         user_agent: Optional[str] = None):
        """Log login attempts"""
        status = "successful" if success else "failed"
        message = f"Login attempt {status} for user: {username} from {ip_address}"
        
        extra_data = {
            "username": username,
            "success": success,
            "ip_address": ip_address,
            "user_agent": user_agent,
            "event_type": "login_attempt"
        }
        
        level = "info" if success else "warning"
        getattr(self.logger, level)(message, extra={"extra_data": extra_data})
    
    def log_permission_denied(self, user_id: str, resource: str, action: str):
        """Log permission denied events"""
        message = f"Permission denied: User {user_id} attempted {action} on {resource}"
        extra_data = {
            "user_id": user_id,
            "resource": resource,
            "action": action,
            "event_type": "permission_denied"
        }
        
        self.logger.warning(message, extra={"extra_data": extra_data})


# Usage Examples
def demo_logging_system():
    """Demonstrate the logging system usage"""
    
    # Initialize the logging system
    logging_system = LoggingSystem("MyWebApp")
    
    # Create specialized loggers
    db_logger = DatabaseLogger(logging_system)
    api_logger = APILogger(logging_system)
    security_logger = SecurityLogger(logging_system)
    
    # Get a general application logger
    app_logger = logging_system.get_logger("application")
    
    print("=== Logging System Demo ===")
    print("Check the 'logs' directory for output files")
    print()
    
    # General application logging
    app_logger.info("Application started successfully")
    app_logger.debug("Loading configuration files")
    app_logger.warning("Configuration file not found, using defaults")
    
    # Database logging
    db_logger.log_query(
        "SELECT * FROM users WHERE id = %s", 
        params={"id": 123}, 
        execution_time=0.045
    )
    
    # API logging
    api_logger.log_request("GET", "/api/users/123", user_id="user456", 
                          request_id="req789", ip_address="192.168.1.1")
    api_logger.log_response(200, 0.125, request_id="req789")
    
    # Security logging
    security_logger.log_login_attempt("john_doe", True, "192.168.1.1", 
                                     "Mozilla/5.0 Chrome/91.0")
    security_logger.log_permission_denied("user456", "/admin/users", "DELETE")
    
    # Contextual logging
    logging_system.log_with_context(
        "business_logic", "info", 
        "Order processed successfully",
        user_id="user123",
        request_id="req456",
        extra_data={"order_id": "ORDER789", "amount": 99.99}
    )
    
    # Error logging with exception
    try:
        raise ValueError("Example error for demonstration")
    except Exception as e:
        app_logger.error("An error occurred during processing", exc_info=True)
        db_logger.log_error(e, "SELECT * FROM invalid_table")
    
    print("Logging demo completed!")


if __name__ == "__main__":
    demo_logging_system()