from pydantic import BaseModel, EmailStr
from datetime import date


class Contact(BaseModel):
    first_name: str
    last_name: str
    email: EmailStr
    phone_number: str
    birthday: date
    additional_info: str | None = None

class ContactResponse(Contact):
    id: int

    class Config:
        from_atributes = True

class ContactCreate(Contact):
    pass

class ContactUpdate(Contact):
    pass