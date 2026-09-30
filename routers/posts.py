from fastapi import FastAPI, Response, status, HTTPException, Depends, APIRouter
from sqlalchemy.orm import Session
from sqlalchemy import create_engine, func
from sqlalchemy.ext.declarative import declarative_base
from .. import models, schemas, utils, oauth2
from ..database import engine, get_db
from typing import List, Optional

router = APIRouter(tags=['Posts'])

@router.get("/sqlalchemy")
def test_posts(db: Session = Depends(get_db)):
    # Using SQLAlchemy's ORM method to query all posts from the Post model.
    # posts = db.query(models.Post).all()
    return {"data": "success"}

@router.get("/posts", response_model=List[schemas.PostOut])
def get_posts(db: Session = Depends(get_db), current_user: int = Depends(oauth2.get_current_user), limit: int = 10, skip: int = 0, search: Optional[str] = ""):
    # Using SQLAlchemy's ORM method to query all posts from the Post model.
    # posts = db.query(models.Post).all()
    results = (
        db.query(models.Post, func.count(models.Vote.post_id).label("votes"))
        .join(models.Vote, models.Vote.post_id == models.Post.id, isouter=True)
        .group_by(models.Post.id)
        .filter(models.Post.title.contains(search))
        .limit(limit)
        .offset(skip)
        .all()
    )
    return results

@router.post("/posts", status_code=status.HTTP_201_CREATED)
def create_posts(post: schemas.PostCreate, db: Session = Depends(get_db), current_user: int = Depends(oauth2.get_current_user)):

    print(current_user.id)
    new_post = models.Post(owner_id=current_user.id,**post.model_dump())
    db.add(new_post)
    db.commit()
    db.refresh(new_post)
    return new_post

@router.get("/posts/{id}", response_model=schemas.PostOut)
def get_post(id: int, db: Session = Depends(get_db), current_user: int = Depends(oauth2.get_current_user)):
    post = db.query(models.Post).filter(models.Post.id == id).first()
    
    if not post:
        raise HTTPException(status_code=status.HTTP_404_NOT_FOUND,
                            detail = f"The post with id: {id} was not found")
    
    # Join posts with votes to count the number of votes for this post
    result = db.query(models.Post, func.count(models.Vote.post_id).label("votes")).join(
        models.Vote, models.Vote.post_id == models.Post.id, isouter=True
    ).group_by(models.Post.id).filter(models.Post.id == id).first()
    
    return result
   

@router.delete("/posts/{id}", status_code=status.HTTP_204_NO_CONTENT)
def delete_post(id: int, db: Session = Depends(get_db), current_user: int = Depends(oauth2.get_current_user) ):

    post_query = db.query(models.Post).filter(models.Post.id == id)
    post = post_query.first()
   

    if post is None:
        raise HTTPException(status_code=status.HTTP_404_NOT_FOUND,
                            detail = f"The post with id: {id} was not found")

    if post.owner_id != current_user.id:
        raise HTTPException(status.HTTP_403_FORBIDDEN, detail="Not Authorized to perform requested action")

    post_query.delete(synchronize_session = False)
    db.commit()
    return Response(status_code=status.HTTP_204_NO_CONTENT)

@router.put("/posts/{id}", response_model=schemas.Post)
def update_post(id: int, updated_post: schemas.PostCreate, db: Session = Depends(get_db), current_user: int = Depends(oauth2.get_current_user)):
    post_query = db.query(models.Post).filter(models.Post.id == id)
    post = post_query.first()
    if post is None:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail=f"Post with id: {id} does not exist"
        )
    if post.owner_id != current_user.id:
            raise HTTPException(status.HTTP_403_FORBIDDEN, detail="Not Authorized to perform requested action")
    
    post_query.update(post.model_dump(), synchronize_session = False)
    db.commit()
    updated_post = post_query.first()
    
    return updated_post