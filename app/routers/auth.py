from fastapi import APIRouter, Depends, status
from fastapi.security.oauth2 import OAuth2PasswordRequestForm

from ..database import Session, engine, get_db
from ..exceptions import InvalidUserCredentials
from ..models import models
from ..schemas import auth_schemas, user_schemas
from ..utils import hash_password, oauth2

router = APIRouter(
    tags=["Authentication"],
)


@router.post(
    "/login",
    status_code=status.HTTP_202_ACCEPTED,
    response_model=auth_schemas.TokenResponse,
)
def login(
    user_creds: OAuth2PasswordRequestForm = Depends(), db: Session = Depends(get_db)
):
    user = (
        db.query(models.User).filter(models.User.email == user_creds.username).first()
    )
    if not user:
        raise InvalidUserCredentials("Invalid Credentials")
    if not hash_password.verify(user_creds.password, user.password):
        raise InvalidUserCredentials("Invalid Credentials")

    access_token = oauth2.create_access_token(
        data={
            "user_id": user.id,
        }
    )
    # token_response = auth_schemas.TokenResponse(
    #     **{"access_token": access_token, "token_type": "bearer"}
    # )
    return {
        "access_token": access_token,
        "token_type": "bearer",
    }  # dictionary is also ok for schemas
