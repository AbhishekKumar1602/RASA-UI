from pydantic import BaseModel, ConfigDict


class SessionConfigCreate(BaseModel):
    session_expiration_time: int = 60
    carry_over_slots_to_new_session: bool = True


class SessionConfigResponse(BaseModel):
    model_config = ConfigDict(from_attributes=True)
    
    id: str
    session_expiration_time: int
    carry_over_slots_to_new_session: bool

