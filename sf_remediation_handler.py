"""
Step Functions remediation handler wrapper.
This handler is invoked by Step Functions and calls the appropriate remediation class.
"""
import json
import logging
from typing import Dict, Any
from datetime import datetime

# Import all remediation handlers
from src.remediation.ec2_remediation import EC2RemediationHandler
from src.remediation.lambda_remediation import LambdaTimeoutHandler
from src.remediation.ssl_certificate_remediation import SSLCertificateHandler
from src.remediation.network_timeout_remediation import NetworkTimeoutHandler
from src.remediation.deployment_failure_remediation import DeploymentFailureHandler
from src.remediation.service_health_remediation import ServiceHealthHandler
from src.models import IncidentEvent
from config import AWS_REGION

logger = logging.getLogger()
logger.setLevel(logging.INFO)

# Map pattern types to handler classes
REMEDIATION_HANDLERS = {
    'ec2_cpu_memory_spike': EC2RemediationHandler,
    'EC2 CPU/Memory Spike': EC2RemediationHandler,
    'lambda_timeout': LambdaTimeoutHandler,
    'Lambda Timeout': LambdaTimeoutHandler,
    'ssl_certificate_error': SSLCertificateHandler,
    'SSL Certificate Error': SSLCertificateHandler,
    'network_timeout': NetworkTimeoutHandler,
    'Network Timeout': NetworkTimeoutHandler,
    'deployment_failure': DeploymentFailureHandler,
    'Deployment Failure': DeploymentFailureHandler,
    'service_unhealthy': ServiceHealthHandler,
    'Service Unhealthy/Crash': ServiceHealthHandler,
}


def lambda_handler(event: Dict[str, Any], context: Any) -> Dict[str, Any]:
    """
    Step Functions remediation handler.
    
    This is invoked by Step Functions for each remediation Lambda.
    It extracts the incident data, determines the pattern, and invokes
    the appropriate remediation handler.
    
    Args:
        event: Event from Step Functions containing incident data
        context: Lambda context
        
    Returns:
        Remediation result
    """
    try:
        logger.info(f"Step Functions remediation handler invoked")
        logger.info(f"Event: {json.dumps(event)}")
        
        # Extract incident data
        incident_data = event.get('incident', {})
        pattern = event.get('pattern', 'unknown')
        
        # Determine which handler to use based on function name
        function_name = context.function_name if context else 'unknown'
        logger.info(f"Function: {function_name}, Pattern: {pattern}")
        
        # Map function name to handler
        handler_class = None
        if 'EC2' in function_name:
            handler_class = EC2RemediationHandler
        elif 'Lambda' in function_name and 'Remediation' in function_name:
            handler_class = LambdaTimeoutHandler
        elif 'SSL' in function_name:
            handler_class = SSLCertificateHandler
        elif 'Network' in function_name:
            handler_class = NetworkTimeoutHandler
        elif 'Deployment' in function_name:
            handler_class = DeploymentFailureHandler
        elif 'Service' in function_name:
            handler_class = ServiceHealthHandler
        else:
            # Try to get from pattern
            handler_class = REMEDIATION_HANDLERS.get(pattern)
        
        if not handler_class:
            logger.error(f"No handler found for pattern: {pattern}, function: {function_name}")
            return {
                'statusCode': 400,
                'pattern': pattern,
                'success': False,
                'error': f'No handler found for pattern: {pattern}'
            }
        
        # Create IncidentEvent from incident data
        incident = IncidentEvent(**incident_data)
        
        logger.info(f"Processing incident: {incident.incident_id}")
        logger.info(f"Event type: {incident.event_type}")
        logger.info(f"Using handler: {handler_class.__name__}")
        
        # Instantiate and execute handler
        handler = handler_class(region_name=AWS_REGION, dry_run=False)
        result = handler.remediate(incident)
        
        logger.info(f"Remediation result: Success={result.success}")
        
        # Return result in format expected by Step Functions
        return {
            'statusCode': 200,
            'pattern': pattern,
            'success': result.success,
            'actions_performed': result.actions_performed,
            'error_message': result.error_message,
            'incident_id': incident.incident_id,
            'timestamp': datetime.utcnow().isoformat() + 'Z'
        }
        
    except Exception as e:
        logger.error(f"Error in remediation handler: {e}", exc_info=True)
        return {
            'statusCode': 500,
            'pattern': event.get('pattern', 'unknown'),
            'success': False,
            'error': str(e),
            'incident_id': event.get('incident', {}).get('incident_id', 'unknown')
        }
