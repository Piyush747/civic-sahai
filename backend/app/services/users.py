from __future__ import annotations

from sqlalchemy.orm import Session
from app.db.models import User
from app.repositories.users import UserRepository
from app.schemas.users import UserCreate, UserUpdate


class UserNotFoundError(Exception):
    pass


class UserService:
    def __init__(self, db: Session):
        self.repository = UserRepository(db)

    def create(self, data: UserCreate) -> User:
        name = data.name.strip()
        return self.repository.create(User(name=name, initials=self._initials(name), email=str(data.email).lower(), user_type=data.user_type.value))

    def get(self, user_id: str) -> User:
        user = self.repository.get(user_id)
        if user is None:
            raise UserNotFoundError(user_id)
        return user

    def list(self) -> tuple[list[User], int]:
        return self.repository.list()

    def update(self, user_id: str, data: UserUpdate) -> User:
        user = self.get(user_id)
        if data.name is not None:
            user.name = data.name.strip()
            user.initials = self._initials(user.name)
        if data.email is not None:
            user.email = str(data.email).lower()
        if data.user_type is not None:
            user.user_type = data.user_type.value
        return self.repository.update(user)

    @staticmethod
    def _initials(name: str) -> str:
        parts = [part for part in name.split() if part]
        return "".join(part[0] for part in parts[:2]).upper()

    def delete(self, user_id: str) -> None:
        self.repository.delete(self.get(user_id))

