# src/auth/hh_service.py
# --- agent_meta ---
# role: hh-account-service
# owner: @backend
# contract: Управляет привязкой HH аккаунтов к внутренним пользователям
# last_reviewed: 2025-08-23
# interfaces:
#   - connect_hh_account(user_id, org_id, tokens, scopes?, ua_hash?, ip_hash?) -> HHAccountInfo
#   - get_hh_account(user_id, org_id) -> HHAccountInfo | None
#   - disconnect_hh_account(user_id, org_id) -> bool
#   - refresh_hh_tokens(user_id, org_id) -> Awaitable[bool]
#   - is_hh_connected(user_id, org_id) -> bool
# --- /agent_meta ---

import time
from typing import Dict, Any, Optional, List
from dataclasses import dataclass

import aiohttp

from src.utils import get_logger
from src.hh_adapter.config import HHSettings
from src.hh_adapter.tokens import HHTokenManager
from .storage import AuthStorage

logger = get_logger("auth.hh_service")


@dataclass
class HHAccountInfo:
    """Информация о подключенном HH аккаунте пользователя."""
    user_id: str
    org_id: str
    access_token: str
    refresh_token: str
    expires_at: float
    scopes: Optional[str] = None
    connected_at: Optional[float] = None
    ua_hash: Optional[str] = None
    ip_hash: Optional[str] = None
    
    @property
    def is_expired(self) -> bool:
        """Проверка истечения токена с 5-минутным запасом."""
        return time.time() >= (self.expires_at - 300)  # 5 минут запаса
    
    @property
    def expires_in_seconds(self) -> int:
        """Количество секунд до истечения токена."""
        return max(0, int(self.expires_at - time.time()))


class HHAccountService:
    """
    Сервис управления HH аккаунтами пользователей.
    
    Обеспечивает связывание внутренних пользователей с их HH аккаунтами,
    управление OAuth2 токенами HH.ru и проверку статуса подключения.
    
    Заменяет legacy подход с hr_id на user_id + org_id модель.
    """
    
    def __init__(self, storage: AuthStorage) -> None:
        self.storage = storage
        self.hh_settings = HHSettings()
        logger.info("HHAccountService инициализирован")

    def connect_hh_account(
        self, 
        user_id: str, 
        org_id: str, 
        tokens: Dict[str, Any],
        scopes: Optional[str] = None,
        ua_hash: Optional[str] = None,
        ip_hash: Optional[str] = None
    ) -> HHAccountInfo:
        """
        Подключает HH аккаунт к внутреннему пользователю.
        
        Args:
            user_id: Идентификатор внутреннего пользователя
            org_id: Идентификатор организации пользователя
            tokens: Словарь с токенами {access_token, refresh_token, expires_at/expires_in}
            scopes: OAuth2 scope разрешения (опционально)
            ua_hash: Хеш User-Agent для безопасности
            ip_hash: Хеш IP-адреса для безопасности
            
        Returns:
            HHAccountInfo с информацией о подключенном аккаунте
            
        Raises:
            ValueError: если токены содержат некорректные данные
        """
        # Валидация токенов
        required_fields = ['access_token', 'refresh_token']
        if not all(field in tokens for field in required_fields):
            raise ValueError(f"Отсутствуют обязательные поля токенов: {required_fields}")
        
        # Расчет времени истечения
        expires_at = tokens.get('expires_at')
        if not expires_at and 'expires_in' in tokens:
            expires_at = time.time() + float(tokens['expires_in'])
        
        if not expires_at:
            logger.warning(f"Отсутствует expires_at для пользователя {user_id}")
            expires_at = time.time() + 3600  # 1 час по умолчанию
        
        now = time.time()
        
        # Сохранение в БД
        self.storage.save_hh_account(
            user_id=user_id,
            org_id=org_id,
            access_token=tokens['access_token'],
            refresh_token=tokens['refresh_token'],
            expires_at=expires_at,
            scopes=scopes,
            connected_at=now,
            ua_hash=ua_hash,
            ip_hash=ip_hash
        )
        
        logger.info(f"HH аккаунт подключен для пользователя {user_id} в организации {org_id}")
        
        return HHAccountInfo(
            user_id=user_id,
            org_id=org_id,
            access_token=tokens['access_token'],
            refresh_token=tokens['refresh_token'],
            expires_at=expires_at,
            scopes=scopes,
            connected_at=now,
            ua_hash=ua_hash,
            ip_hash=ip_hash
        )
    
    def get_hh_account(self, user_id: str, org_id: str) -> Optional[HHAccountInfo]:
        """
        Получает информацию о HH аккаунте пользователя.
        
        Args:
            user_id: Идентификатор пользователя
            org_id: Идентификатор организации
            
        Returns:
            HHAccountInfo или None, если аккаунт не подключен
        """
        account_data = self.storage.get_hh_account(user_id, org_id)
        if not account_data:
            return None
        
        return HHAccountInfo(
            user_id=account_data['user_id'],
            org_id=account_data['org_id'],
            access_token=account_data['access_token'],
            refresh_token=account_data['refresh_token'],
            expires_at=account_data['expires_at'],
            scopes=account_data.get('scopes'),
            connected_at=account_data.get('connected_at'),
            ua_hash=account_data.get('ua_hash'),
            ip_hash=account_data.get('ip_hash')
        )
    
    def disconnect_hh_account(self, user_id: str, org_id: str) -> bool:
        """
        Отключает HH аккаунт от внутреннего пользователя.
        
        Args:
            user_id: Идентификатор пользователя
            org_id: Идентификатор организации
            
        Returns:
            True если аккаунт был отключен, False если не был подключен
        """
        if not self.storage.get_hh_account(user_id, org_id):
            logger.info(f"HH аккаунт не найден для отключения: пользователь {user_id}, организация {org_id}")
            return False
        
        self.storage.delete_hh_account(user_id, org_id)
        logger.info(f"HH аккаунт отключен для пользователя {user_id} в организации {org_id}")
        return True
    
    def is_hh_connected(self, user_id: str, org_id: str) -> bool:
        """
        Проверяет, подключен ли HH аккаунт у пользователя.
        
        Args:
            user_id: Идентификатор пользователя  
            org_id: Идентификатор организации
            
        Returns:
            True если HH аккаунт подключен и токены действительны
        """
        account = self.get_hh_account(user_id, org_id)
        if not account:
            return False
        
        # Проверяем не истекли ли токены
        if account.is_expired:
            logger.warning(f"Токены HH истекли для пользователя {user_id}")
            return False
            
        return True
    
    async def refresh_hh_tokens(self, user_id: str, org_id: str) -> bool:
        """
        Обновляет токены HH аккаунта через HHTokenManager.
        
        Args:
            user_id: Идентификатор пользователя
            org_id: Идентификатор организации
            
        Returns:
            True если токены обновлены успешно
        """
        try:
            # Получаем текущий HH аккаунт
            hh_account = self.get_hh_account(user_id, org_id)
            if not hh_account:
                logger.warning(f"Нет HH аккаунта для обновления токенов: {user_id}")
                return False
            
            # Создаем HHTokenManager для обновления токенов
            async with aiohttp.ClientSession() as session:
                token_manager = HHTokenManager(
                    settings=self.hh_settings,
                    session=session,
                    access_token=hh_account.access_token,
                    refresh_token=hh_account.refresh_token,
                    expires_in=hh_account.expires_in_seconds
                )
                
                # Принудительно обновляем токены
                try:
                    new_access_token = await token_manager.get_valid_access_token()
                    logger.info(f"Токены HH успешно обновлены для пользователя {user_id}")
                    
                    # Сохраняем обновленные токены в БД
                    updated_tokens = {
                        "access_token": token_manager.access_token,
                        "refresh_token": token_manager.refresh_token,
                        "expires_at": token_manager.expires_at
                    }
                    self.storage.update_hh_tokens(user_id, org_id, updated_tokens)
                    
                    return True
                    
                except Exception as refresh_error:
                    logger.error(f"Ошибка обновления токенов HH для {user_id}: {refresh_error}")
                    return False
                    
        except Exception as e:
            logger.error(f"Критическая ошибка refresh_hh_tokens для {user_id}: {e}")
            return False
    
    def get_connected_users(self, org_id: Optional[str] = None) -> List[HHAccountInfo]:
        """
        Возвращает список пользователей с подключенными HH аккаунтами.
        
        Args:
            org_id: Фильтр по организации (опционально)
            
        Returns:
            Список HHAccountInfo для подключенных пользователей
        """
        accounts_data = self.storage.list_hh_accounts(org_id)
        return [
            HHAccountInfo(
                user_id=acc['user_id'],
                org_id=acc['org_id'],
                access_token=acc['access_token'],
                refresh_token=acc['refresh_token'],
                expires_at=acc['expires_at'],
                scopes=acc.get('scopes'),
                connected_at=acc.get('connected_at'),
                ua_hash=acc.get('ua_hash'),
                ip_hash=acc.get('ip_hash')
            )
            for acc in accounts_data
        ]