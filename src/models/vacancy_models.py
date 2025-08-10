# src/models/vacancy_models.py
# --- agent_meta ---
# role: domain-model
# owner: @backend
# contract: Pydantic модели домена для вакансий (VacancyInfo и связанные типы)
# last_reviewed: 2025-08-10
# interfaces:
#   - VacancyInfo
#   - EmploymentForm, ExperienceVac и пр.
# --- /agent_meta ---

from typing import List, Optional
from pydantic import BaseModel, Field


class EmploymentForm(BaseModel):
    """Модель формы занятости"""
    id: str = Field(..., description="Идентификатор формы занятости")

    class Config:
        extra = "forbid"


class ExperienceVac(BaseModel):
    """Модель требуемого опыта"""
    id: str = Field(..., description="Идентификатор требуемого опыта")

    class Config:
        extra = "forbid"


class Schedule(BaseModel):
    """Модель графика работы"""
    id: str = Field(..., description="Идентификатор графика работы")

    class Config:
        extra = "forbid"


class Employment(BaseModel):
    """Модель типа занятости"""
    id: str = Field(..., description="Идентификатор типа занятости")

    class Config:
        extra = "forbid"


class ProfessionalRole(BaseModel):
    """Модель профессиональной роли"""
    name: str = Field(..., description="Название профессиональной роли")

    class Config:
        extra = "forbid"


class VacancyInfo(BaseModel):
    """
    Модель данных вакансии.
    
    Attributes:
        name: Название вакансии
        company_name: Название компании
        description: Описание вакансии в html
        key_skills: Список ключевых навыков
        professional_roles: Список требуемых профессиональных ролей
        employment_form: Форма занятости
        experience: Требуемый опыт работы
        schedule: График работы
        employment: Тип занятости
    """
    name: str = Field(..., description="Название вакансии")
    company_name: str = Field(..., description="Название компании")
    description: str = Field(..., description="Описание вакансии в html")
    key_skills: List[str] = Field(..., description="Список ключевых навыков")
    professional_roles: List[ProfessionalRole] = Field(default_factory=list, description="Список требуемых профессиональных ролей")
    employment_form: Optional[EmploymentForm] = Field(None, description="Форма занятости")
    experience: Optional[ExperienceVac] = Field(None, description="Требуемый опыт работы")
    schedule: Optional[Schedule] = Field(None, description="График работы")
    employment: Optional[Employment] = Field(None, description="Тип занятости")

    class Config:
        extra = "forbid"
        title = "VacancyInfo"
