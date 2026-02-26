"""
Pattern Matcher Lambda handler for Step Functions.
This is the entry point for the PatternMatcherLambda function.
"""
import json
import logging
from typing import Dict, Any
from src.services.pattern_matcher import PatternMatcher
from src.models import IncidentEvent

logger = logging.getLogger()
logger.setLevel(logging.INFO)


def evaluate_pattern(event: Dict[str, Any], context: Any) -> Dict[str, Any]:
    """
    Lambda handler for pattern matching.
    
    This is invoked by Step Functions to identify the incident pattern.
    
    Args:
        event: Event from Step Functions containing incident data
        context: Lambda context
        
    Returns:
        Dict with pattern information
    """
    try:
        logger.info(f"Pattern matcher invoked")
        logger.info(f"Event: {json.dumps(event)}")
        
        # Extract incident data
        incident_data = event.get('incident', {})
        
        if not incident_data:
            logger.error("No incident data in event")
            return {
                'pattern': 'Unknown',
                'pattern_display': 'Unknown',
                'error': 'No incident data provided'
            }
        
        # Create IncidentEvent from data
        incident = IncidentEvent(**incident_data)
        
        logger.info(f"Processing incident: {incident.incident_id}")
        logger.info(f"Event type: {incident.event_type}")
        
        # Match pattern
        pattern_matcher = PatternMatcher()
        pattern = pattern_matcher.match_pattern(incident)
        pattern_display = pattern_matcher.get_pattern_display_name(pattern)
        
        logger.info(f"Matched pattern: {pattern} ({pattern_display})")
        
        # Return pattern information
        return {
            'pattern': pattern_display,  # Use display name for Step Functions
            'pattern_code': pattern,  # Include code version too
            'pattern_display': pattern_display,
            'incident_id': incident.incident_id,
            'confidence': pattern_matcher.get_pattern_confidence(incident, pattern)
        }
        
    except Exception as e:
        logger.error(f"Error in pattern matcher: {e}", exc_info=True)
        return {
            'pattern': 'Unknown',
            'pattern_display': 'Unknown',
            'error': str(e)
        }
