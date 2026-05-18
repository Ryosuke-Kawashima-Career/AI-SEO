from fastapi import APIRouter, Depends, HTTPException, status
from sqlalchemy import select
from sqlalchemy.orm import Session

from app.core.database import get_db
from app.models.url import RegisteredUrl
from app.schemas.url import UrlCreate, UrlResponse

router = APIRouter(prefix="/api/urls", tags=["urls"])


@router.get("", response_model=list[UrlResponse])
def list_urls(db: Session = Depends(get_db)) -> list[RegisteredUrl]:
    return list(
        db.execute(select(RegisteredUrl).order_by(RegisteredUrl.id)).scalars().all()
    )


@router.post("", response_model=UrlResponse, status_code=status.HTTP_201_CREATED)
def create_url(payload: UrlCreate, db: Session = Depends(get_db)) -> RegisteredUrl:
    url_str = str(payload.url)
    existing = db.execute(
        select(RegisteredUrl).where(RegisteredUrl.url == url_str)
    ).scalar_one_or_none()
    if existing is not None:
        raise HTTPException(
            status_code=status.HTTP_409_CONFLICT,
            detail="This URL is already registered",
        )
    obj = RegisteredUrl(url=url_str, label=payload.label)
    db.add(obj)
    db.commit()
    db.refresh(obj)
    return obj


@router.delete("/{url_id}", status_code=status.HTTP_204_NO_CONTENT)
def delete_url(url_id: int, db: Session = Depends(get_db)) -> None:
    obj = db.get(RegisteredUrl, url_id)
    if obj is None:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND, detail="URL not found"
        )
    db.delete(obj)
    db.commit()
