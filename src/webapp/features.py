# src/webapp/features.py
# --- agent_meta ---
# role: webapp-features
# owner: @backend
# contract: Универсальные роуты для LLM-фич через FeatureRegistry
# last_reviewed: 2025-08-15
# interfaces:
#   - POST /features/{feature_name}/generate
#   - GET /features (список доступных фич)
# --- /agent_meta ---

from __future__ import annotations

from typing import Dict, Any, Optional

from fastapi import APIRouter, HTTPException
from pydantic import BaseModel, Field

from src.utils import get_logger
from src.models.resume_models import ResumeInfo
from src.models.vacancy_models import VacancyInfo
from src.llm_features.registry import get_global_registry, FeatureInfo
from src.llm_features.base.options import BaseLLMOptions
from src.llm_features.base.errors import FeatureNotFoundError, FeatureRegistrationError
from src.webapp.storage_docs import ResumeStore, VacancyStore, SessionStore

logger = get_logger(__name__)
router = APIRouter(prefix="/features", tags=["LLM Features"])
_resume_store = ResumeStore()
_vacancy_store = VacancyStore()
_session_store = SessionStore()


class FeatureGenerateRequest(BaseModel):
    """Запрос на генерацию для любой LLM-фичи."""
    session_id: Optional[str] = Field(default=None, description="Сессия с сохранёнными резюме/вакансией")
    resume: Optional[ResumeInfo] = Field(default=None, description="Резюме (если нет session_id)")
    vacancy: Optional[VacancyInfo] = Field(default=None, description="Вакансия (если нет session_id)")
    options: Optional[Dict[str, Any]] = Field(default_factory=dict, description="Опции фичи")
    version: Optional[str] = Field(default=None, description="Версия фичи")


class FeatureGenerateResponse(BaseModel):
    """Ответ генерации LLM-фичи."""
    feature_name: str
    version: str
    result: Dict[str, Any]  # Универсальный результат
    formatted_output: Optional[str] = Field(default=None, description="Форматированный вывод")


class FeatureApiInfo(BaseModel):
    """API представление информации о фиче (без generator_class)."""
    name: str
    version: str
    description: str
    default_config: Dict[str, Any]


class FeatureListResponse(BaseModel):
    """Список доступных фич."""
    features: Dict[str, Dict[str, Any]]


@router.get("/", response_model=FeatureListResponse)
async def list_features():
    """Получить список всех доступных LLM-фич."""
    registry = get_global_registry()
    features = registry.list_features()
    
    # Конвертируем в API-дружелюбный формат
    features_dict = {}
    for feature in features:
        if feature.name not in features_dict:
            features_dict[feature.name] = {
                "description": feature.description,
                "versions": [],
                "default_version": "v1"  # TODO: получить из реестра
            }
        features_dict[feature.name]["versions"].append(feature.version)
    
    logger.info("Запрошен список фич: %d доступно", len(features_dict))
    return FeatureListResponse(features=features_dict)


@router.post("/{feature_name}/generate", response_model=FeatureGenerateResponse)
async def generate_feature(
    feature_name: str,
    request: FeatureGenerateRequest,
    version: Optional[str] = None  # Query parameter для версии
):
    """Универсальный роут для генерации любой LLM-фичи."""
    try:
        # Получаем генератор из реестра  
        registry = get_global_registry()
        # Версия: query parameter имеет приоритет над версией в теле
        final_version = version or request.version
        generator = registry.get_generator(
            feature_name, 
            version=final_version
        )
        
        # Конвертируем options в специфичный тип, если требуется
        options: BaseLLMOptions
        if feature_name == "interview_checklist":
            from src.llm_interview_checklist.options import InterviewChecklistOptions
            options = InterviewChecklistOptions(**(request.options or {}))
        elif feature_name == "interview_simulation":
            from src.llm_interview_simulation.options import InterviewSimulationOptions
            options = InterviewSimulationOptions(**(request.options or {}))
        else:
            options = BaseLLMOptions(**(request.options or {}))
        
        # Источник данных: session_id или прямые модели из тела
        resume_model: Optional[ResumeInfo] = None
        vacancy_model: Optional[VacancyInfo] = None

        if request.session_id:
            sess = _session_store.get(request.session_id)
            if not sess:
                raise HTTPException(status_code=404, detail="Session not found or expired")
            resume_model = _resume_store.get(sess["resume_id"])  # type: ignore[index]
            vacancy_model = _vacancy_store.get(sess["vacancy_id"])  # type: ignore[index]
            if not resume_model or not vacancy_model:
                raise HTTPException(status_code=404, detail="Session documents not found")
        else:
            if not request.resume or not request.vacancy:
                raise HTTPException(status_code=400, detail="Either provide session_id or both resume and vacancy")
            resume_model = request.resume
            vacancy_model = request.vacancy

        logger.info(
            "Генерация %s@%s: resume_title=%s, vacancy=%s", 
            feature_name,
            final_version or "default",
            getattr(resume_model, "title", None) or "Unknown",
            getattr(vacancy_model, "name", None) or "Unknown",
        )
        
        # Генерируем результат
        result = await generator.generate(
            resume=resume_model,
            vacancy=vacancy_model, 
            options=options
        )
        
        # Форматируем вывод (если поддерживается)
        formatted_output = None
        if hasattr(generator, 'format_for_output'):
            try:
                formatted_output = generator.format_for_output(result)
            except Exception as e:
                logger.warning("Ошибка форматирования вывода %s: %s", feature_name, str(e))
        
        # Конвертируем результат в dict для универсального API
        if hasattr(result, 'model_dump'):
            result_dict = result.model_dump()
        elif hasattr(result, 'dict'):
            result_dict = result.dict()
        else:
            result_dict = {"output": str(result)}
        
        logger.info("Генерация %s завершена успешно", feature_name)
        
        return FeatureGenerateResponse(
            feature_name=feature_name,
            version=final_version or "default", 
            result=result_dict,
            formatted_output=formatted_output
        )
        
    except FeatureNotFoundError as e:
        logger.error("Фича не найдена: %s", str(e))
        raise HTTPException(status_code=404, detail=f"Feature not found: {str(e)}")
    
    except FeatureRegistrationError as e:
        logger.error("Ошибка создания генератора: %s", str(e))
        raise HTTPException(status_code=500, detail=f"Generator error: {str(e)}")
    
    except Exception as e:
        logger.error("Ошибка генерации %s: %s", feature_name, str(e))
        raise HTTPException(
            status_code=500, 
            detail=f"Generation failed for {feature_name}: {str(e)}"
        )
