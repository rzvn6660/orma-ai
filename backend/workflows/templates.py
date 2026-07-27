import logging
from workflows.workflow_context import WorkflowContext
from workflows.retry_manager import retry_manager
from workflows.approval_manager import approval_manager

logger = logging.getLogger(__name__)

async def medicine_workflow(ctx: WorkflowContext):
    """
    Template for handling medicine creation/updates.
    Never automatically modifies medications.
    """
    logger.info(f"[Workflow] Starting medicine_workflow. ID: {ctx.workflow_id}")
    action = ctx.payload.get("action")
    
    if action == "delete" or action == "modify":
        # Requires approval
        req = approval_manager.request_approval(ctx.db, ctx.log_id, action, ctx.payload)
        logger.info(f"[Workflow] Paused for approval. Request ID: {req.id}")
        return "pending_approval"
        
    # Safe to process creation
    async def _add_medicine():
        # Here it would interact with models.medicine (simulated)
        logger.info(f"[Workflow] Executing _add_medicine step for payload: {ctx.payload}")
        return {"status": "success", "step": "add_medicine"}
        
    result = await retry_manager.execute_with_retry(_add_medicine)
    return "completed"

async def appointment_workflow(ctx: WorkflowContext):
    logger.info(f"[Workflow] Starting appointment_workflow. ID: {ctx.workflow_id}")
    action = ctx.payload.get("action")
    
    if action == "reschedule" or action == "cancel":
        req = approval_manager.request_approval(ctx.db, ctx.log_id, action, ctx.payload)
        return "pending_approval"
        
    async def _add_appointment():
        logger.info(f"[Workflow] Executing _add_appointment step")
        return {"status": "success", "step": "add_appointment"}
        
    await retry_manager.execute_with_retry(_add_appointment)
    return "completed"

async def emergency_workflow(ctx: WorkflowContext):
    """
    High priority. Immediately notifies caregivers.
    """
    logger.info(f"[Workflow] Starting emergency_workflow. ID: {ctx.workflow_id}")
    
    async def _trigger_emergency():
        # Interact with emergency models/APIs
        logger.warning(f"[Workflow] Executing emergency trigger!")
        return {"status": "success", "step": "trigger_emergency"}
        
    await retry_manager.execute_with_retry(_trigger_emergency, max_retries=5)
    return "completed"
