from sqlalchemy import select

from datetime import date, timedelta
from typing import List, Dict

from sqlalchemy.ext.asyncio import AsyncSession
from src.contacts.models import Contact
from src.contacts.schema import ContactCreate

class ContactRepository:

    def __init__(self, session: AsyncSession):
        self.session = session


    async def create_contact(self, contact: ContactCreate, owner_id: int) -> Contact:
        new_contact = Contact(**contact.model_dump(), owner_id=owner_id)
        self.session.add(new_contact)
        await self.session.commit()
        await self.session.refresh(new_contact)
        return new_contact


    async def get_contact(self, contact_id: int, owner_id: int) -> Contact:
        query = select(Contact).where(Contact.id == contact_id).where(Contact.owner_id == owner_id)
        result = await self.session.execute(query)
        return result.scalar_one_or_none()
    

    async def get_all_contacts(self, owner_id) -> list[Contact]:
        query = select(Contact).where(Contact.owner_id == owner_id)
        result = await self.session.execute(query)
        return result.scalars().all()
    

    async def update_contact(
        self, 
        contact_id: int, 
        contact_data: ContactCreate, 
        owner_id: int
    ) -> Contact:
        query = select(Contact).where(Contact.id == contact_id).where(Contact.owner_id == owner_id)
        result = await self.session.execute(query)
        contact = result.scalar_one_or_none()
        if contact:
            for key, value in contact_data.model_dump().items():
                setattr(contact, key, value)
            await self.session.commit()
            await self.session.refresh(contact)
        return contact
    

    async def delete_contact(self, contact_id: int, owner_id: int) -> bool:
        contact = await self.get_contact(contact_id, owner_id=owner_id)
        if contact:
            await self.session.delete(contact)
            await self.session.commit()
            return True
        return False


    async def search_contacts(
        self, 
        owner_id: int,
        first_name: str = None, 
        last_name: str = None, 
        email: str = None
    ) -> List[Contact]:
        query = select(Contact).where(Contact.owner_id == owner_id)
        if first_name:
            query = query.filter(Contact.first_name.ilike(f"%{first_name}%"))
        if last_name:
            query = query.filter(Contact.last_name.ilike(f"%{last_name}%"))
        if email:
            query = query.filter(Contact.email.ilike(f"%{email}%"))
        result = await self.session.execute(query)
        return result.scalars().all()
    

    async def get_upcoming_birthdays(self, owner_id: int) -> List[Dict]:
        upcoming_birthdays = []
        today = date.today()
        query = (
            select(Contact)
            .where(Contact.owner_id == owner_id)
            .where(Contact.birthday.isnot(None))
        )
        result = await self.session.execute(query)
        contacts = result.scalars().all()

        for contact in contacts:
            if contact.birthday:
                birthday = contact.birthday

            birthday_this_year = birthday.replace(year=today.year)

            if birthday_this_year < today:
                birthday_this_year = birthday_this_year.replace(year=today.year + 1)

            if today <= birthday_this_year <= today + timedelta(days=7):
                birthday_dict = {
                    "id": contact.id,
                    "first_name": contact.first_name,
                    "last_name": contact.last_name,
                    "email": contact.email or None,
                    "phone_number": contact.phone_number or None,
                    "birthday": birthday_this_year,
                    "additional_info": contact.additional_info or None,
                }

                if birthday_this_year.weekday() >= 5:
                    next_monday = birthday_this_year + timedelta(days=(7 - birthday_this_year.weekday()))
                    birthday_dict["birthday"] = next_monday

                upcoming_birthdays.append(birthday_dict)

        return upcoming_birthdays
