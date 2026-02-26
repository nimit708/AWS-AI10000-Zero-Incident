"""
Lambda Timeout Remediation handler for Step Functions.
"""
import json
import logging
from typing import Dict, Any
from datetime import datetime
from src.remediation.lambda_remediation import LambdaTimeoutHandler
from src.models import IncidentEvent
from config import AWS_REGION

logger = logging.getLogger()
logger.setLevel(logging.INFO)


def remediate(event: Dict[str, Any], context: Any) -> Dict[str, Any]:
    """
    Lambda handler for Lambda timeout remediation.
    
    Args:
        event: Event from Step Functions containing incident data
        context: Lambda context
        
    Returns:
        Remediation result
    """
    try:
        logger.info(f"Lambda timeout remediation handler invoked")
        logger.info(f"Event: {json.dumps(event)}")
        
        # Extract incident data
        incident_data = event.get('incident', {})
        
        if not incident_data:
            logger.error("No incident data in event")
            return {
                'statusCode': 400,
                'success': False,
                'error': 'No incident data provided'
            }
        
        # Create IncidentEvent
        incident = IncidentEvent(**incident_data)
        
        logger.info(f"Processing incident: {incident.incident_id}")
        
        # Execute remediation
        handler = LambdaTimeoutHandler(region_name=AWS_REGION, dry_run=False)
        result = handler.remediate(incident)
        
        logger.info(f"Remediation result: Success={result.success}")
        
        # Return result
        return {
            'statusCode': 200,
            'success': result.success,
            'actions_performed': result.actions_performed,
            'error_message': result.error_message,
            'incident_id': incident.incident_id,
            'timestamp': datetime.utcnow().isoformat() + 'Z'
        }
        
    except Exception as e:
        logger.error(f"Error in Lambda timeout remediation: {e}", exc_info=True)
        return {
            'statusCode': 500,
            'success': False,
            'error': str(e)
        }
