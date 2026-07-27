import logging
import asyncio
import uuid
from sqlalchemy.orm import Session
from workflows.event_bus import event_bus
from workflows.workflow_registry import workflow_registry
from workflows.workflow_executor import workflow_executor
from models.owe import WorkflowAuditLog

logger = logging.getLogger(__name__)

class WorkflowEngine:
    """
    Central workflow engine orchestrating actions safely.
    Subscribes to EventBus and delegates to Executor.
    """
    def __init__(self):
        # Dynamically subscribe to all registered workflows
        for event_name in workflow_registry._registry.keys():
            event_bus.subscribe(event_name, self.handle_event)
            
    async def handle_event(self, payload: dict):
        event_name = payload.get("event_name")
        logger.info(f"[WorkflowEngine] Handling event: {event_name}")
        
        workflow_fn = workflow_registry.get_workflow(event_name)
        if not workflow_fn:
            logger.warning(f"[WorkflowEngine] No workflow registered for {event_name}")
            return
            
        idempotency_key = payload.get("idempotency_key") or str(uuid.uuid4())
        actor = payload.get("actor", "system")
        
        # 1. Create Audit Log and check idempotency (sync wrapper via DB)
        from database import SessionLocal
        db = SessionLocal()
        try:
            # Check idempotency
            existing = db.query(WorkflowAuditLog).filter(WorkflowAuditLog.idempotency_key == idempotency_key).first()
            if existing:
                logger.info(f"[WorkflowEngine] Idempotency key {idempotency_key} already processed. Skipping.")
                return
                
            log = WorkflowAuditLog(
                workflow_id=event_name,
                idempotency_key=idempotency_key,
                actor=actor,
                status="started"
            )
            db.add(log)
            db.commit()
            db.refresh(log)
            log_id = log.id
        finally:
            db.close()
            
        # 2. Dispatch execution asynchronously
        asyncio.create_task(workflow_executor.execute(workflow_fn, log_id, payload, idempotency_key))

workflow_engine = WorkflowEngine()
