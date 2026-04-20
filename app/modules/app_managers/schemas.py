from pydantic import BaseModel, Field


class AddManageesOut(BaseModel):
    manager_employee_id: int
    requested: list[int]
    added: list[int]
    already_active: list[int]
    invalid_employee_ids: list[int]
    self_management_blocked: list[int]
    active_managees_after_operation: list[int]


class ManageeBatchIn(BaseModel):
    managees: list[int] = Field(default_factory=list)


class RevokeManageesOut(BaseModel):
    manager_employee_id: int
    requested: list[int]
    revoked: list[int]
    already_inactive: list[int]
    invalid_employee_ids: list[int]
    self_management_blocked: list[int]
    active_managees_after_operation: list[int]


class ManageeBatchResultOut(BaseModel):
    manager_employee_id: int
    processed_managees: list[int]
    affected_managees: list[int]
    skipped_managees: list[int]
    active_managees_after_operation: list[int]
