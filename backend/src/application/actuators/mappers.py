from application.actuators.dto import ActuatorExecutionDto
from domain.actuators.execution import ActuatorExecution


def execution_to_dto(execution: ActuatorExecution) -> ActuatorExecutionDto:
    return ActuatorExecutionDto(
        id=execution.id,
        device_id=execution.device_id,
        success=execution.success,
        policy_applied=execution.policy_applied,
        message=execution.message,
        created_at=execution.created_at,
    )


def executions_to_dtos(executions: list[ActuatorExecution]) -> list[ActuatorExecutionDto]:
    return [execution_to_dto(execution) for execution in executions]
