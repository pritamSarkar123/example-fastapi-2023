from typing import List, Optional

from fastapi import APIRouter, Depends, Path, Query, Request, Response, status
from sqlalchemy import func
from sqlalchemy.exc import IntegrityError

from ..database import Session, engine, get_db
from ..exceptions import DataIntigrityError, PostNotFound, UnouthorizedToManipulatePost
from ..models import models
from ..schemas import auth_schemas, post_schemas
from ..utils import oauth2

router = APIRouter(
    prefix="/post",
    tags=["Post"],
)


# models.Base.metadata.create_all(bind=engine)


@router.get(
    "/",
    status_code=status.HTTP_200_OK,
    response_model=List[post_schemas.PostResponseWithVote],
)
async def get_posts(
    db: Session = Depends(get_db),
    current_user: models.User = Depends(oauth2.get_current_user),
    offset: int = Query(default=0, ge=0),
    limit: int = Query(default=10, ge=0),
    search: Optional[str] = Query(default=""),
):
    # db.query(models.Post) and other filters, makes the query
    # .all(), .first() executes the query
    # posts = (
    #     db.query(models.Post)
    #     .filter(models.Post.title.contains(search))
    # .offset(offset)
    # .limit(limit)
    # .all()
    # )

    # by default join in sql alchemy is ***** left inner *****
    posts = (
        db.query(models.Post, func.count(models.Vote.post_id).label("votes"))
        .join(models.Vote, models.Post.id == models.Vote.post_id, isouter=True)
        .group_by(models.Post.id)
        .filter(models.Post.title.contains(search))
        .offset(offset)
        .limit(limit)
        .all()
    )
    return posts


@router.get(
    "/owned",
    status_code=status.HTTP_200_OK,
    response_model=List[post_schemas.PostResponseWithVote],
)
async def get_owned_posts(
    db: Session = Depends(get_db),
    current_user: models.User = Depends(oauth2.get_current_user),
    offset: int = Query(default=0, ge=0),
    limit: int = Query(default=10, ge=0),
    search: Optional[str] = Query(default=""),
):
    # db.query(models.Post) and other filters, makes the query
    # .all(), .first() executes the query
    posts = (
        db.query(models.Post, func.count(models.Vote.post_id).label("votes"))
        .join(models.Vote, models.Post.id == models.Vote.post_id, isouter=True)
        .group_by(models.Post.id)
        .filter(models.Post.owner_id == current_user.id)
        .filter(models.Post.title.contains(search))
        .offset(offset)
        .limit(limit)
        .all()
    )
    return posts


@router.get(
    "/{id}",
    status_code=status.HTTP_200_OK,
    response_model=post_schemas.PostResponseWithVote,
)
async def get_single_post(
    id: int = Path(),
    db: Session = Depends(get_db),
    current_user: models.User = Depends(oauth2.get_current_user),
):
    post = (
        db.query(models.Post, func.count(models.Vote.post_id).label("votes"))
        .join(models.Vote, models.Post.id == models.Vote.post_id, isouter=True)
        .group_by(models.Post.id)
        .filter(models.Post.id == id)
        .first()
    )
    if not post:
        raise PostNotFound(id)
    return post


@router.post(
    "/", status_code=status.HTTP_201_CREATED, response_model=post_schemas.PostResponse
)
async def create_post(
    post: post_schemas.CreatePost,
    db: Session = Depends(get_db),
    current_user: models.User = Depends(oauth2.get_current_user),
):
    try:
        new_post = models.Post(owner_id=current_user.id, **post.dict())
        db.add(new_post)
        db.commit()
        db.refresh(new_post)  # returning
        return new_post
    except IntegrityError as e:
        raise DataIntigrityError(e.args[0])


@router.put("/{id}", response_model=post_schemas.PostResponse)
async def update_post(
    post: post_schemas.UpdatePost,
    id: int = Path(),
    db: Session = Depends(get_db),
    current_user: models.User = Depends(oauth2.get_current_user),
):
    try:
        updating_post = db.query(models.Post).filter(models.Post.id == id)
        updated_post = updating_post.first()
        if not updated_post:
            raise PostNotFound(id)

        if current_user.id != updated_post.owner_id:
            raise UnouthorizedToManipulatePost(current_user.id)
        updating_post.update(post.dict(), synchronize_session=False)
        db.commit()
        return updating_post.first()  # equivalent to returning
    except IntegrityError as e:
        raise DataIntigrityError(e.args[0])


@router.delete("/{id}", status_code=status.HTTP_204_NO_CONTENT)
async def delete_post(
    id: int = Path(),
    db: Session = Depends(get_db),
    current_user: models.User = Depends(oauth2.get_current_user),
):
    deleting_post = db.query(models.Post).filter(models.Post.id == id)
    deleted_post = deleting_post.first()
    if not deleted_post:
        raise PostNotFound(id)

    if current_user.id != deleted_post.owner_id:
        raise UnouthorizedToManipulatePost(current_user.id)
    deleting_post.delete(synchronize_session=False)
    db.commit()
    return Response(status_code=status.HTTP_204_NO_CONTENT)
