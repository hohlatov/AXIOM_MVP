import uuid

from pydantic import BaseModel, EmailStr, Field, field_validator


class UserRegister(BaseModel):
    email: EmailStr
    password: str = Field(min_length=8)
    grade: int | None = None
    parental_consent: bool = Field(
        description="Согласие родителя/законного представителя на обработку персональных данных "
                    "несовершеннолетнего (152-ФЗ). Обязательно — должно быть true."
    )

    @field_validator("parental_consent")
    @classmethod
    def consent_must_be_given(cls, v: bool) -> bool:
        if not v:
            raise ValueError(
                "Для регистрации требуется согласие родителя/законного представителя "
                "на обработку персональных данных"
            )
        return v


class UserLogin(BaseModel):
    email: EmailStr
    password: str


class UserOut(BaseModel):
    id: uuid.UUID
    email: EmailStr | None
    grade: int | None
    parental_consent_given: bool

    class Config:
        from_attributes = True


class TokenPair(BaseModel):
    access_token: str
    refresh_token: str
    token_type: str = "bearer"


class RefreshRequest(BaseModel):
    refresh_token: str


class PasswordResetRequest(BaseModel):
    email: EmailStr


class PasswordResetConfirm(BaseModel):
    token: str
    new_password: str = Field(min_length=8)
