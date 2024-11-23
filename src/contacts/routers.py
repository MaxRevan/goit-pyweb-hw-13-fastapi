from fastapi import APIRouter, Query, Depends, HTTPException, status
from sqlalchemy.ext.asyncio import AsyncSession
from fastapi_limiter.depends import RateLimiter

from config.db import get_db
from src.contacts.schema import ContactCreate, ContactResponse, ContactUpdate
from src.contacts.repos import ContactRepository
from src.auth.models import User
from src.auth.utils import get_current_user, RoleChecker
from src.auth.schema import RoleEnum


router = APIRouter()


@router.get(
        "/search", 
        response_model=list[ContactResponse], 
        description='No more than 5 requests per 30 seconds',
        dependencies=[Depends(RateLimiter(times=5, seconds=30))]
)
async def search_contacts(
    first_name: str = Query(None, alias="first_name"),
    last_name: str = Query(None),
    email: str = Query(None),
    user: User = Depends(get_current_user),
    db: AsyncSession = Depends(get_db)
):
    if not first_name and not last_name and not email:
        raise HTTPException(status_code=status.HTTP_404_NOT_FOUND, detail="At least one search parameter is required")
    contact_repo = ContactRepository(db)
    contacts = await contact_repo.search_contacts(
        user.id,
        first_name=first_name, 
        last_name=last_name, 
        email=email
    )
    return contacts


@router.get(
        "/upcoming_birthdays", 
        description='No more than 5 requests per 30 seconds',
        dependencies=[Depends(RateLimiter(times=5, seconds=30))],
        response_model=list[ContactResponse]
)
async def upcoming_birthdays(
    user: User = Depends(get_current_user),
    db: AsyncSession = Depends(get_db)
):
    contact_repo = ContactRepository(db)
    contacts = await contact_repo.get_upcoming_birthdays(user.id)
    print(f"Found {len(contacts)} upcoming birthdays for user {user.id}")
    if not contacts:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND, 
            detail="No contacts with birthdays in the next 7 days"
        )
    return contacts


@router.post("/", 
            response_model=ContactResponse, 
            status_code=status.HTTP_201_CREATED,
            description='No more than 5 requests per 30 seconds',
            dependencies=[Depends(RateLimiter(times=5, seconds=30))]
)
async def create_contact(
    contact: ContactCreate,
    user: User = Depends(get_current_user),
    db: AsyncSession = Depends(get_db)
):
    contact_repo = ContactRepository(db)
    return await contact_repo.create_contact(contact, user.id)
     

@router.get(
        "/{contact_id}", 
        description='No more than 5 requests per 30 seconds',
        dependencies=[Depends(RateLimiter(times=5, seconds=30))],
        response_model=ContactResponse
)
async def get_contact(
    contact_id: int, 
    user: User = Depends(get_current_user),
    db: AsyncSession = Depends(get_db)
):
    contact_repo = ContactRepository(db)
    contact = await contact_repo.get_contact(contact_id, user.id)
    if not contact:
        raise HTTPException(status_code=status.HTTP_404_NOT_FOUND, detail="Contact not found")
    return contact


@router.get(
        "/", 
        response_model=list[ContactResponse], 
        description='No more than 5 requests per 30 seconds',
        dependencies=[Depends(RateLimiter(times=5, seconds=30))],
)
async def get_all_contacts(
    user: User = Depends(RoleChecker([RoleEnum.ADMIN, RoleEnum.USER])),
    # user: User = Depends(get_current_user),
    db: AsyncSession = Depends(get_db)
):
    contact_repo = ContactRepository(db)
    contacts = await contact_repo.get_all_contacts(user.id)
    return contacts


@router.put(
        "/{contact_id}", 
        response_model=ContactResponse, 
        status_code=status.HTTP_200_OK,
        description='No more than 5 requests per 30 seconds',
        dependencies=[Depends(RateLimiter(times=5, seconds=30))]
)
async def update_contact(
    contact_id: int, 
    contact_data: ContactUpdate, 
    user: User = Depends(get_current_user),
    db: AsyncSession = Depends(get_db)
):
    contact_repo = ContactRepository(db)
    contact = await contact_repo.update_contact(contact_id, contact_data, user.id)
    if not contact:
        raise HTTPException(status_code=status.HTTP_404_NOT_FOUND, detail="Contact not found")
    return contact


@router.delete(
        "/{contact_id}", 
        status_code=status.HTTP_204_NO_CONTENT,
        description='No more than 5 requests per 30 seconds',
        dependencies=[Depends(RateLimiter(times=5, seconds=30))]
)
async def get_contact(
    contact_id: int, 
    user: User = Depends(get_current_user),
    db: AsyncSession = Depends(get_db)
):
    contact_repo = ContactRepository(db)
    success = await contact_repo.delete_contact(contact_id, user.id)
    if not success:
        raise HTTPException(status_code=status.HTTP_404_NOT_FOUND, detail="Contact not found")
    return {"message": "Contact deleted successfully"}


