"""
RoboPulse Fleet Command Center
Day 4 - shared FastAPI dependencies.

Day 5 - Adding get_current_user and require_role
"""

from collections.abc import AsyncGenerator

import jwt
from fastapi import Depends, HTTPException, status
from fastapi.security import OAuth2PasswordBearer
from sqlalchemy import select

from sqlalchemy.ext.asyncio import AsyncSession

from app.database import AsyncSessionLocal
from app.models import User, UserRole
from app.security import decode_access_token

#this is a FastAPI dependency that provides an async database session to any route that needs it.
async def get_db() -> AsyncGenerator[AsyncSession, None]:
    async with AsyncSessionLocal() as session:
        yield session

#We need to create a dependency that will extract the current user from the JWT token
#provided in the Authorization header of the request
oauth2_scheme = OAuth2PasswordBearer(tokenUrl="auth/token")

#Next, we need to create a dependency that will extract the current user from the JWT token
async def get_current_user(
        token: str = Depends(oauth2_scheme),
        db: AsyncSession = Depends(get_db),
) -> User:
    #we will be using the decode_access_doken function to decode the JWT token and extract the username
    #from the payload

    #we also want to catch any exceptions that might occur during the decoding process, such as inavlid
    # token or a missing username
    credentials_exception = HTTPException(
        status_code=status.HTTP_401_UNAUTHORIZED,
        detail="Could not validate credentials",
        headers={"WWW-Authenticate": "Bearer"}
    )
    try:
        payload = decode_access_token(token)
        #note that 'sub' is the standard claim name for the subject of the token,
        #  which in our case is the username
        username = payload.get("sub")
        if username is None:
            raise credentials_exception
    except jwt.InvalidTokenError:
        raise credentials_exception

    #finally, we can query the database for the user with the extracted username
    result = await db.execute(select(User).where(User.username == username))
    user = result.scalar_one_or_none()
    if user is None:
        raise credentials_exception
    return user


#We need a dependency that will check if the current user has the required role(s)
#necessary to access a particular route
def require_role(*allowed_roles: UserRole):
    async def role_checker(current_user: User = Depends(get_current_user)) -> User:
        if current_user.role not in allowed_roles:
            raise HTTPException(
                status_code=status.HTTP_403_FORBIDDEN,
                detail=(
                    f"Role '{current_user.role.value}' is not permitted to perform this action"
                ),
            )
        return current_user
    return role_checker