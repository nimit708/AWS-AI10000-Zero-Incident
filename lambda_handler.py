"""
Main Lambda handler for incident ingestion and processing.

This handler receives events from CloudWatch or API Gateway, validates and normalizes them,
queries the Bedrock AI Agent, routes based on confidence, and creates incident records.
"""
import json
import logging
import os
from typing import Dict, Any, Optional
from datetime import datetime, timezone

from src.utils.validation import validate_event
from src.utils.normalization import normalize_event
from src.services.bedrock_agent_service import BedrockAgentService
from src.services.routing_service import RoutingService
from src.services.dynamodb_service import DynamoDBService
from src.services.sns_service import SNSService
from src.services.ai_agent_executor import AIAgentExecutor
from src.services.pattern_matcher import PatternMatcher
from src.models import IncidentEvent, IncidentRecord
from config import (
    BEDROCK_AGENT_MODEL,
    BEDROCK_EMBEDDING_MODEL,
    CONFIDENCE_THRESHOLD,
    AWS_REGION,
    SNS_SUMMARY_TOPIC_ARN,
    SNS_URGENT_TOPIC_ARN,
    INCIDENT_TABLE_NAME,
    RESOURCE_LOCK_TABLE_NAME,
    KNOWLEDGE_BASE_BUCKET
)

# Configure logging
logger = logging.getLogger()
logger.setLevel(logging.INFO)


class IngestionHandler:
    """
    Main handler for incident ingestion and processing.
    
    Orchestrates the complete incident processing flow:
    1. Event validation and normalization
    2. Bedrock AI Agent query
    3. Confidence-based routing
    4. Incident record creation
    5. Remediation execution or Step Functions invocation
    """

    def __init__(
        self,
        region_name: str = AWS_REGION,
        confidence_threshold: float = CONFIDENCE_THRESHOLD
    ):
        """
        Initialize ingestion handler with all required services.
        
        Args:
            region_name: AWS region
            confidence_threshold: Confidence threshold for routing
        """
        self.region_name = region_name
        self.confidence_threshold = confidence_threshold
        
        # Initialize services
        self.bedrock_service = BedrockAgentService(
            agent_model=BEDROCK_AGENT_MODEL,
            embedding_model=BEDROCK_EMBEDDING_MODEL,
            region_name=region_name,
            confidence_threshold=confidence_threshold
        )
        self.routing_service = RoutingService(confidence_threshold=confidence_threshold)
        self.dynamodb_service = DynamoDBService(
            table_name=INCIDENT_TABLE_NAME,
            region_name=region_name
        )
        self.sns_service = SNSService(
            summary_topic_arn=SNS_SUMMARY_TOPIC_ARN,
            urgent_topic_arn=SNS_URGENT_TOPIC_ARN,
            region_name=region_name,
            summary_model=os.environ.get('BEDROCK_SUMMARY_MODEL')
        )
        self.ai_executor = AIAgentExecutor(region_name=region_name)
        self.pattern_matcher = PatternMatcher()
        
        # Initialize knowledge base service
        from src.services.knowledge_base_service import KnowledgeBaseService
        kb_bucket = os.environ.get('KNOWLEDGE_BASE_BUCKET', 'incident-kb-923906573163')
        self.knowledge_base_service = KnowledgeBaseService(
            region_name=region_name,
            bucket_name=kb_bucket
        )

    def process_event(self, event: Dict[str, Any]) -> Dict[str, Any]:
        """
        Process incoming event through the complete incident management flow.
        
        Requirements:
        - 1.1: Accept events from CloudWatch and API Gateway
        - 1.2: Process events in real-time
        - 1.3: Validate event structure
        - 1.4: Extract required fields
        - 1.5: Normalize events to IncidentEvent
        - 2.1: Query Bedrock AI Agent
        
        Args:
            event: Raw event from CloudWatch or API Gateway
            
        Returns:
            Dict with processing result
        """
        start_time = datetime.now(timezone.utc)
        
        try:
            # Step 1: Validate event (Requirement 1.3)
            logger.info("Validating incoming event")
            validation_result = validate_event(event)
            
            if not validation_result.valid:
                logger.error(f"Event validation failed: {validation_result.error}")
                return self._create_error_response(
                    status_code=400,
                    message="Invalid event structure",
                    details=validation_result.error
                )
            
            # Step 2: Normalize event (Requirement 1.5)
            logger.info("Normalizing event to IncidentEvent")
            incident = normalize_event(event)
            logger.info(f"Created incident: {incident.incident_id}, type: {incident.event_type}")
            
            # Step 3: Create initial incident record (Requirement 12.1)
            logger.info("Creating incident record in DynamoDB")
            incident_record = IncidentRecord.from_incident_event(incident)
            record_created = self.dynamodb_service.create_incident_record(incident_record)
            
            if not record_created:
                logger.warning("Failed to create incident record, continuing processing")
            
            # Store timestamp for later updates
            incident_timestamp = incident_record.timestamp
            
            # Step 4: Query Bedrock AI Agent (Requirement 2.1)
            logger.info("Querying Bedrock AI Agent for similar incidents")
            agent_response = self.bedrock_service.query_ai_agent(incident)
            logger.info(f"Agent response - Match: {agent_response.match_found}, Confidence: {agent_response.confidence}")
            
            # Log resolution steps for debugging
            if agent_response.resolution_steps:
                logger.info(f"Resolution steps count: {len(agent_response.resolution_steps)}")
                for i, step in enumerate(agent_response.resolution_steps[:3], 1):  # Log first 3 steps
                    logger.info(f"Step {i}: action={step.action}, target={step.target}, params={json.dumps(step.parameters, default=str)[:200]}")
            
            # Step 5: Route based on confidence (Requirement 3.1)
            logger.info("Determining routing path")
            routing_path = self.routing_service.route_incident(incident, agent_response)
            routing_reason = self.routing_service.get_routing_reason(agent_response)
            routing_decision = {
                'path': routing_path,
                'reason': routing_reason,
                'confidence': agent_response.confidence
            }
            logger.info(f"Routing decision: {routing_decision['path']}, Reason: {routing_decision['reason']}")
            
            # Step 6: Execute remediation based on path
            remediation_result = None
            
            if routing_decision['path'] == 'fast_path':
                # Fast path: AI Agent remediation (Requirement 3.2)
                logger.info("Executing fast path - AI Agent remediation")
                remediation_result = self.ai_executor.execute_remediation_steps(
                    incident,
                    agent_response
                )
                
                # Send notification for fast path (AI-powered)
                if remediation_result:
                    logger.info(f"Fast path remediation result: Success={remediation_result.success}")
                    self._update_incident_with_result(incident, incident_timestamp, remediation_result, routing_decision)
                    
                    # Send SNS notification regardless of success/failure
                    if remediation_result.success:
                        self.sns_service.send_summary_notification(
                            incident_id=incident.incident_id,
                            event_type=incident.event_type,
                            severity=incident.severity,
                            remediation_summary=f"AI-powered remediation completed successfully",
                            actions_taken=remediation_result.actions_performed,
                            affected_resources=incident.affected_resources
                        )
                    else:
                        # Send urgent alert for failed AI remediation
                        self.sns_service.send_urgent_alert(
                            incident_id=incident.incident_id,
                            event_type=incident.event_type,
                            severity=incident.severity,
                            reason="AI-powered remediation failed",
                            affected_resources=incident.affected_resources,
                            recommended_actions=[
                                "Review AI-generated steps in logs",
                                "Check if knowledge base needs more examples",
                                "Consider manual remediation"
                            ],
                            incident_details={
                                'error': remediation_result.error_message,
                                'actions_attempted': remediation_result.actions_performed,
                                'ai_confidence': routing_decision['confidence']
                            }
                        )
                
            elif routing_decision['path'] == 'structured_path':
                # Structured path: Pattern matching and Step Functions (Requirement 4.1)
                logger.info("Executing structured path - Pattern matching")
                pattern = self.pattern_matcher.match_pattern(incident)
                logger.info(f"Identified pattern: {pattern}")
                
                # For now, we'll invoke the appropriate remediation handler directly
                # In production, this would trigger Step Functions
                remediation_result = self._execute_structured_remediation(incident, pattern)
                
            elif routing_decision['path'] == 'escalation':
                # Escalation path: Send urgent alert (Requirement 3.6)
                logger.warning("Escalating incident - no remediation path found")
                self._handle_escalation(incident, incident_timestamp, routing_decision)
                remediation_result = None
            
            # Step 7: Update incident record and send notifications for structured path
            if remediation_result and routing_decision['path'] == 'structured_path':
                if isinstance(remediation_result, dict) and 'execution_arn' in remediation_result:
                    # Step Functions execution started
                    logger.info(f"Step Functions execution: {remediation_result['execution_arn']}")
                    # Update incident with execution info
                    # Step Functions will handle the final status update
                    logger.info(f"Step Functions will handle status updates for incident {incident.incident_id}")
                else:
                    # Direct remediation result
                    logger.info(f"Remediation result: Success={remediation_result.success}")
                    self._update_incident_with_result(incident, incident_timestamp, remediation_result, routing_decision)
                    
                    # Step 8: Send notification for structured path
                    if remediation_result.success:
                        self.sns_service.send_summary_notification(
                            incident_id=incident.incident_id,
                            event_type=incident.event_type,
                            severity=incident.severity,
                            remediation_summary=f"Pattern-based remediation completed successfully",
                            actions_taken=remediation_result.actions_performed,
                            affected_resources=incident.affected_resources
                        )
            
            # Calculate processing time
            processing_time = (datetime.now(timezone.utc) - start_time).total_seconds()
            logger.info(f"Event processing completed in {processing_time:.2f}s")
            
            # Determine remediation success for response
            remediation_success = None
            if remediation_result:
                if isinstance(remediation_result, dict):
                    # Step Functions execution or dict result
                    remediation_success = remediation_result.get('success')
                elif hasattr(remediation_result, 'success'):
                    # RemediationResult object
                    remediation_success = remediation_result.success
            
            return self._create_success_response(
                incident_id=incident.incident_id,
                routing_path=routing_decision['path'],
                routing_reason=routing_decision['reason'],
                confidence=routing_decision.get('confidence', agent_response.confidence),
                remediation_success=remediation_success,
                processing_time=processing_time
            )
            
        except Exception as e:
            logger.error(f"Unexpected error processing event: {e}", exc_info=True)
            return self._create_error_response(
                status_code=500,
                message="Internal processing error",
                details=str(e)
            )

    def _execute_structured_remediation(
        self,
        incident: IncidentEvent,
        pattern: str
    ) -> Optional[Any]:
        """
        Execute structured remediation by triggering Step Functions.
        
        Step Functions will orchestrate the remediation workflow and invoke
        the appropriate Lambda function based on the pattern.
        
        Args:
            incident: IncidentEvent to remediate
            pattern: Identified pattern
            
        Returns:
            Dict with execution details or None
        """
        try:
            import boto3
            import os
            
            # Get Step Functions ARN from environment
            state_machine_arn = os.environ.get('STATE_MACHINE_ARN')
            if not state_machine_arn:
                logger.error("STATE_MACHINE_ARN not configured")
                return None
            
            # Prepare input for Step Functions
            sf_input = {
                'incident': {
                    'incident_id': incident.incident_id,
                    'event_type': incident.event_type,
                    'severity': incident.severity,
                    'resource_id': incident.resource_id,
                    'affected_resources': incident.affected_resources,
                    'description': incident.description,
                    'metadata': incident.metadata,
                    'timestamp': incident.timestamp,
                    'source': incident.source
                },
                'pattern': pattern,
                'pattern_display': self.pattern_matcher.get_pattern_display_name(pattern),
                'routing_path': 'structured_path'
            }
            
            # Start Step Functions execution
            sf_client = boto3.client('stepfunctions', region_name=self.region_name)
            
            execution_name = f"incident-{incident.incident_id[:8]}-{int(datetime.now(timezone.utc).timestamp())}"
            
            logger.info(f"Starting Step Functions execution: {execution_name}")
            logger.info(f"Pattern: {pattern}, State Machine: {state_machine_arn}")
            
            response = sf_client.start_execution(
                stateMachineArn=state_machine_arn,
                name=execution_name,
                input=json.dumps(sf_input)
            )
            
            execution_arn = response['executionArn']
            logger.info(f"Step Functions execution started: {execution_arn}")
            
            # Return execution details (not waiting for completion)
            # The Step Functions will handle the remediation asynchronously
            return {
                'execution_arn': execution_arn,
                'execution_name': execution_name,
                'pattern': pattern,
                'status': 'RUNNING'
            }
            
        except Exception as e:
            logger.error(f"Error triggering Step Functions: {e}", exc_info=True)
            return None

    def _handle_escalation(
        self,
        incident: IncidentEvent,
        incident_timestamp: int,
        routing_decision: Dict[str, Any]
    ):
        """
        Handle incident escalation.
        
        Requirement 3.6: Escalate failed remediations
        Requirement 13.2: Send urgent alerts
        
        Args:
            incident: IncidentEvent to escalate
            incident_timestamp: Incident timestamp for DynamoDB update
            routing_decision: Routing decision details
        """
        logger.warning(f"Escalating incident {incident.incident_id}")
        
        # Update incident status to escalated
        try:
            self.dynamodb_service.update_incident_status(
                incident_id=incident.incident_id,
                timestamp=incident_timestamp,
                new_status='escalated',
                resolution_steps=[],
                confidence=0.0
            )
        except Exception as e:
            logger.error(f"Error updating incident status to escalated: {e}")
        
        # Send urgent alert
        self.sns_service.send_urgent_alert(
            incident_id=incident.incident_id,
            event_type=incident.event_type,
            severity=incident.severity,
            affected_resources=incident.affected_resources,
            reason=routing_decision.get('reason', 'Unknown'),
            recommended_actions=[
                "Review incident details in DynamoDB",
                "Check CloudWatch logs for more information",
                "Manually investigate affected resources",
                "Consider manual remediation"
            ],
            incident_details=incident.metadata
        )

    def _update_incident_with_result(
        self,
        incident: IncidentEvent,
        incident_timestamp: int,
        remediation_result: Any,
        routing_decision: Dict[str, Any]
    ):
        """
        Update incident record with remediation results.
        
        Args:
            incident: IncidentEvent
            incident_timestamp: Incident timestamp for DynamoDB update
            remediation_result: RemediationResult
            routing_decision: Routing decision details
        """
        try:
            status = 'resolved' if remediation_result.success else 'failed'
            
            self.dynamodb_service.update_incident_status(
                incident_id=incident.incident_id,
                timestamp=incident_timestamp,
                new_status=status,
                resolution_steps=remediation_result.actions_performed,
                confidence=routing_decision.get('confidence', 0.0)
            )
            logger.info(f"Updated incident {incident.incident_id} status to {status}")
            
            # Add to knowledge base if successfully resolved
            if remediation_result.success:
                self._add_to_knowledge_base(incident, remediation_result, routing_decision)
            
        except Exception as e:
            logger.error(f"Error updating incident record: {e}")
    
    def _add_to_knowledge_base(
        self,
        incident: IncidentEvent,
        remediation_result: Any,
        routing_decision: Dict[str, Any]
    ):
        """
        Add successfully resolved incident to knowledge base.
        
        Args:
            incident: IncidentEvent
            remediation_result: RemediationResult
            routing_decision: Routing decision details
        """
        try:
            # Create a simplified incident document for S3
            # Bypass Pydantic validation by creating dict directly
            incident_document = {
                'incident_id': incident.incident_id,
                'timestamp': incident.timestamp,
                'event_type': incident.event_type,
                'severity': incident.severity,
                'affected_resources': incident.affected_resources,
                'symptoms': [
                    incident.description,
                    f"{incident.event_type} affecting {', '.join(incident.affected_resources[:2])}"
                ],
                'root_cause': self._determine_root_cause(incident.event_type),
                'resolution_steps': [
                    {
                        'step_number': i,
                        'action': 'execute',
                        'target': 'system',
                        'description': action,
                        'parameters': {}
                    }
                    for i, action in enumerate(remediation_result.actions_performed, 1)
                ],
                'resolution_time': remediation_result.resolution_time,
                'outcome': 'success',
                'metadata': {
                    'confidence_score': routing_decision.get('confidence', 0.0),
                    'routing_path': routing_decision.get('path', 'unknown'),
                    'source': incident.source,
                    'description': incident.description
                }
            }
            
            # Store directly to S3 without Pydantic validation
            success = self._store_to_s3(incident_document)
            
            if success:
                logger.info(f"✓ Added incident {incident.incident_id} to knowledge base")
            else:
                logger.warning(f"Failed to add incident {incident.incident_id} to knowledge base")
                
        except Exception as e:
            logger.error(f"Error adding to knowledge base: {e}", exc_info=True)
    
    def _determine_root_cause(self, event_type: str) -> str:
        """Determine root cause based on event type."""
        root_cause_map = {
            'Lambda Timeout': 'Function execution exceeded configured timeout limit',
            'EC2 CPU Spike': 'High CPU utilization on EC2 instance',
            'SSL Certificate Expiration': 'SSL/TLS certificate has expired or is expiring soon',
            'SSL Certificate Error': 'SSL/TLS certificate has expired or is expiring soon',
            'Network Timeout': 'Network connection timeout or latency issue',
            'Service Unhealthy': 'Service health check failures or crashes',
            'Deployment Failure': 'Application deployment or update failed'
        }
        return root_cause_map.get(event_type, f'Issue related to {event_type}')
    
    def _store_to_s3(self, incident_document: Dict[str, Any]) -> bool:
        """Store incident document directly to S3."""
        try:
            import json
            from datetime import datetime
            
            # Generate S3 key
            timestamp = datetime.fromisoformat(incident_document['timestamp'].replace('Z', '+00:00'))
            s3_key = f"incidents/{timestamp.year}/{timestamp.month:02d}/{incident_document['incident_id']}.json"
            
            # Convert to JSON
            incident_json = json.dumps(incident_document, indent=2)
            
            # Upload to S3
            self.knowledge_base_service.s3_client.put_object(
                Bucket=self.knowledge_base_service.bucket_name,
                Key=s3_key,
                Body=incident_json,
                ContentType='application/json',
                Metadata={
                    'incident_id': incident_document['incident_id'],
                    'event_type': incident_document['event_type'],
                    'severity': incident_document['severity'],
                    'outcome': incident_document['outcome']
                }
            )
            
            logger.info(f"Stored incident in S3: {s3_key}")
            return True
            
        except Exception as e:
            logger.error(f"Error storing to S3: {e}")
            return False

    def _create_success_response(
        self,
        incident_id: str,
        routing_path: str,
        routing_reason: str,
        confidence: float,
        remediation_success: Optional[bool],
        processing_time: float
    ) -> Dict[str, Any]:
        """Create success response."""
        return {
            'statusCode': 200,
            'body': json.dumps({
                'success': True,
                'incident_id': incident_id,
                'routing_path': routing_path,
                'routing_reason': routing_reason,
                'confidence': confidence,
                'remediation_success': remediation_success,
                'processing_time_seconds': processing_time
            })
        }

    def _create_error_response(
        self,
        status_code: int,
        message: str,
        details: Any = None
    ) -> Dict[str, Any]:
        """Create error response."""
        return {
            'statusCode': status_code,
            'body': json.dumps({
                'success': False,
                'error': message,
                'details': details
            })
        }


# Global handler instance (reused across Lambda invocations)
_handler_instance = None


def lambda_handler(event: Dict[str, Any], context: Any) -> Dict[str, Any]:
    """
    AWS Lambda handler function.
    
    This is the entry point for Lambda invocations from CloudWatch or API Gateway.
    
    Args:
        event: Event data from CloudWatch or API Gateway
        context: Lambda context object
        
    Returns:
        Response dict with statusCode and body
    """
    global _handler_instance
    
    # Initialize handler on first invocation (Lambda container reuse)
    if _handler_instance is None:
        logger.info("Initializing IngestionHandler")
        _handler_instance = IngestionHandler()
    
    # Log request ID for tracing
    request_id = context.aws_request_id if context else 'local'
    logger.info(f"Processing event - Request ID: {request_id}")
    
    # Process event
    return _handler_instance.process_event(event)
