from typing import List, Optional

from fastapi import APIRouter, Depends, Path, Query, Request, Response, status
from sqlalchemy.exc import IntegrityError

from ..database import Session, engine, get_db
from ..exceptions import (
    DataIntigrityError,
    PostNotFound,
    UnouthorizedToManipulatePost,
    VoteConflict,
    VoteNotFound,
)
from ..models import models
from ..schemas import auth_schemas, post_schemas, vote_schemas
from ..utils import oauth2

router = APIRouter(
    prefix="/vote",
    tags=["Vote"],
)


@router.post("/", status_code=status.HTTP_201_CREATED)
def vote(
    vote: vote_schemas.Vote,
    db: Session = Depends(get_db),
    current_user: models.User = Depends(oauth2.get_current_user),
):
    target_post = db.query(models.Post).filter(models.Post.id == vote.post_id).first()
    if not target_post:
        raise PostNotFound(vote.post_id)

    vote_query = db.query(models.Vote).filter(
        models.Vote.post_id == vote.post_id, models.Vote.user_id == current_user.id
    )
    found_already_voted_post_by_user = vote_query.first()
    if vote.vote_dir == 1:
        if found_already_voted_post_by_user:
            raise VoteConflict(
                f"user {current_user.id} has already voted on the post {vote.post_id}"
            )
        else:
            new_vote = models.Vote(post_id=vote.post_id, user_id=current_user.id)
            db.add(new_vote)
            db.commit()
            return {"message": "successfully added vote"}
    else:
        if not found_already_voted_post_by_user:
            raise VoteNotFound(
                f"vote of the user {current_user.id} against the post {vote.post_id} does not exists"
            )
        else:
            vote_query.delete(synchronize_session=False)
            db.commit()
            return {"message": "successfully deleted vote"}
