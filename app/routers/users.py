from typing import List

from fastapi import APIRouter, Depends, Path, Request, Response, status
from sqlalchemy.exc import IntegrityError

from ..database import Session, engine, get_db
from ..exceptions import DataIntigrityError, PostNotFound, UserNotFound
from ..models import models
from ..schemas import user_schemas
from ..utils import hash_password

router = APIRouter(
    prefix="/user",
    tags=["User"],
)

# models.Base.metadata.create_all(bind=engine)


@router.post(
    "/", status_code=status.HTTP_201_CREATED, response_model=user_schemas.UserResponse
)
async def create_user(user: user_schemas.UserCreate, db: Session = Depends(get_db)):
    try:
        hashed_password = hash_password.hash_plain_text_password(user.password)
        user.password = hashed_password
        new_user = models.User(**user.dict())
        db.add(new_user)
        db.commit()
        db.refresh(new_user)  # returning
        return new_user
    except IntegrityError as e:
        raise DataIntigrityError(e.args[0])


@router.get(
    "/{id}", status_code=status.HTTP_200_OK, response_model=user_schemas.UserResponse
)
async def get_user(id: int = Path(), db: Session = Depends(get_db)):
    user = db.query(models.User).filter(models.User.id == id).first()
    if not user:
        raise UserNotFound(id)
    return user
