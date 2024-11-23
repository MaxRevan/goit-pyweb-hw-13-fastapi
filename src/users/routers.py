from fastapi import APIRouter, Depends, HTTPException, UploadFile, File, status
from fastapi_limiter.depends import RateLimiter
from sqlalchemy.ext.asyncio import AsyncSession
import cloudinary
import cloudinary.uploader

from config.db import get_db
from config.general import settings
from src.auth.utils import get_current_user
from src.auth.schema import UserResponse
from src.auth.repos import UserRepository
from src.auth.models import User


router = APIRouter()


@router.get("/me/", response_model=UserResponse)
async def read_users_me(current_user: User = Depends(get_current_user)):
    return current_user


@router.patch(
        '/avatar', 
        response_model=UserResponse, 
        description='No more than 5 requests per 30 seconds',
        dependencies=[Depends(RateLimiter(times=5, seconds=30))]
)
async def update_avatar_user(
    file: UploadFile = File(), 
    current_user: User = Depends(get_current_user),
    db: AsyncSession = Depends(get_db),
):
    cloudinary.config(
        cloud_name=settings.cloudinary_name,
        api_key=settings.cloudinary_api_key,
        api_secret=settings.cloudinary_api_secret,
        secure=True
    )
    try:
        r = cloudinary.uploader.upload(
            file.file, 
            public_id=f'avatars/{current_user.username}',
            overwrite=True,
        )
        src_url = cloudinary.CloudinaryImage(f'avatars/{current_user.username}')\
                        .build_url(width=250, height=250, crop='fill', version=r.get('version'))
    except Exception as e:
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail=f"Error uploading avatar: {str(e)}"
        )
    user_repo = UserRepository(db)
    user = await user_repo.update_avatar(current_user.email, src_url)
    return user
