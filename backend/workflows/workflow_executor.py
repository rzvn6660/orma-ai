import logging
import asyncio
from datetime import datetime
from database import SessionLocal
from workflows.workflow_context import WorkflowContext
from models.owe import WorkflowAuditLog

logger = logging.getLogger(__name__)

class WorkflowExecutor:
    """
    Executes workflows asynchronously.
    """
    
    async def execute(self, workflow_fn, log_id: int, payload: dict, idempotency_key: str):
        # We create a new DB session for the async task
        db = SessionLocal()
        try:
            ctx = WorkflowContext(
                db=db,
                workflow_id=workflow_fn.__name__,
                idempotency_key=idempotency_key,
                payload=payload,
                log_id=log_id
            )
            
            # Execute template
            final_status = await workflow_fn(ctx)
            
            # Update log
            log = db.query(WorkflowAuditLog).filter(WorkflowAuditLog.id == log_id).first()
            if log:
                log.status = final_status
                if final_status == "completed":
                    log.completed_at = datetime.utcnow()
                db.commit()
                
            # Broadcast completion if not pending approval
            if final_status == "completed":
                from workflows.event_bus import event_bus
                await event_bus.publish("WorkflowCompleted", {"workflow": workflow_fn.__name__, "log_id": log_id})
                
        except Exception as e:
            logger.error(f"[WorkflowExecutor] Fatal error executing workflow {log_id}: {str(e)}")
            log = db.query(WorkflowAuditLog).filter(WorkflowAuditLog.id == log_id).first()
            if log:
                log.status = "failed"
                fails = log.failures or []
                fails.append(str(e))
                log.failures = fails
                db.commit()
        finally:
            db.close()

workflow_executor = WorkflowExecutor()
