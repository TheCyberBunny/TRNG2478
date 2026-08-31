"""
Robopulse command center
Day 5 - authentication endpoints
"""

from fastapi import APIRouter, Depends, HTTPException, status
from fastapi.security import OAuth2PasswordRequestForm
from sqlalchemy import select
from sqlalchemy.ext.asyncio import AsyncSession

from app.dependencies import get_db, require_role
from app.models import User, UserRole
from app.schemas.user import Token, UserCreate, UserRead
from app.security import create_access_token, hash_password, verify_password


#First step is to set up the router for our endpoints
router = APIRouter(prefix="/auth", tags=["auth"])

#next step is to define our login endpoint, which will accept a username and password
# verify the credetials, and return our JWT access token IF the credentials are valid.
@router.post("/token", response_model=Token)
async def login(
    #we will use the OAuth2PasswordRequestForm dependency to extract the username and password
    #from the request body. Note that this is sent as form data, NOT JSON thanks to  the Depends()
    form_data: OAuth2PasswordRequestForm = Depends(),
    db: AsyncSession = Depends(get_db),
) -> Token:
    #our db call to select our user
    result = await db.execute(select(User).where(User.username == form_data.username))
    user = result.scalar_one_or_none()

    #check to verify if the password is correct
    if user is None or not verify_password(form_data.password, user.hashed_password):
        raise HTTPException(
            status_code=status.HTTP_401_UNAUTHORIZED,
            detail="Incorrect username or password",
            headers={"WWW-Authenticate": "Bearer"}
        )

    #set our access token
    access_token = create_access_token(data={"sub": user.username, "role": user.role.value})
    return Token(access_token=access_token, token_type="bearer")


#function to register a new user. This endpoint is protected by the require_role dependency, which will
#require the user to have the Fleet Admin role
@router.post("/register", response_model=UserRead, status_code=status.HTTP_201_CREATED)
async def register_user(
    payload: UserCreate,
    db: AsyncSession = Depends(get_db),
    _: User = Depends(require_role(UserRole.FLEET_ADMIN)),
) -> User:
    #checking if the username already exists in the db
    existing = await db.execute(select(User).where(User.username == payload.username))
    if existing.scalar_one_or_none() is not None:
        raise HTTPException(
            status_code=status.HTTP_400_BAD_REQUEST,
            detail=f"Username '{payload.username}' is already taken",
        )

    #create a new User object with the provided username, hashed password, and role
    user = User(
        username = payload.username,
        hashed_password=hash_password(payload.password),
        role=payload.role
    )

    #add that new user object to the db
    db.add(user)
    #commit the db transaction
    await db.commit()
    #refresh the user object so that we get the id the db generated
    await db.refresh(user)
    return user