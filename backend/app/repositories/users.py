from __future__ import annotations

from sqlalchemy import func, select
from sqlalchemy.orm import Session
from app.db.models import User


class UserRepository:
    def __init__(self, db: Session):
        self.db = db

    def create(self, user: User) -> User:
        self.db.add(user)
        self.db.commit()
        self.db.refresh(user)
        return user

    def get(self, user_id: str) -> User | None:
        return self.db.get(User, user_id)

    def list(self) -> tuple[list[User], int]:
        users = list(self.db.scalars(select(User).order_by(User.created_at.desc(), User.id.desc())))
        return users, int(self.db.scalar(select(func.count()).select_from(User)) or 0)

    def update(self, user: User) -> User:
        self.db.commit()
        self.db.refresh(user)
        return user

    def delete(self, user: User) -> None:
        self.db.delete(user)
        self.db.commit()

