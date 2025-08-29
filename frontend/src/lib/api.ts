import axios, { AxiosError } from 'axios';
import type { AxiosInstance } from 'axios';
import type { LoginRequest, SignupRequest, AuthResponse, User, ApiError } from '../types/auth';
import type { SessionInitResponse, FeatureListResponse } from '../types/api';

class ApiClient {
  private client: AxiosInstance;

  constructor(baseURL: string = 'http://localhost:8080') {
    this.client = axios.create({
      baseURL,
      withCredentials: true, // Важно для работы с session cookies
      headers: {
        'Content-Type': 'application/json',
      },
    });

    // Перехватчик для обработки ошибок
    this.client.interceptors.response.use(
      (response) => response,
      (error: AxiosError) => {
        if (error.response?.status === 401) {
          // Перенаправляем на авторизацию только если мы НЕ на странице авторизации
          const currentPath = window.location.pathname;
          if (currentPath !== '/' && currentPath !== '/auth') {
            window.location.href = '/auth';
          }
          // Если мы уже на странице авторизации, просто пропускаем ошибку дальше
        }
        return Promise.reject(error);
      }
    );
  }

  // Методы авторизации
  async login(credentials: LoginRequest): Promise<AuthResponse> {
    try {
      const response = await this.client.post<AuthResponse>('/auth/login', credentials);
      return response.data;
    } catch (error) {
      throw this.handleError(error);
    }
  }

  async signup(data: SignupRequest): Promise<AuthResponse> {
    try {
      const response = await this.client.post<AuthResponse>('/auth/signup', data);
      return response.data;
    } catch (error) {
      throw this.handleError(error);
    }
  }

  async logout(): Promise<void> {
    try {
      await this.client.post('/auth/logout');
    } catch (error) {
      throw this.handleError(error);
    }
  }

  // Получение информации о текущем пользователе
  async getCurrentUser(): Promise<User> {
    try {
      const response = await this.client.get<User>('/me');
      return response.data;
    } catch (error) {
      throw this.handleError(error);
    }
  }

  // Проверка статуса подключения HH.ru
  async getHHStatus(): Promise<{ is_connected: boolean; expires_in_seconds?: number; connected_at?: number }> {
    try {
      const response = await this.client.get('/auth/hh/status');
      return response.data;
    } catch (error) {
      throw this.handleError(error);
    }
  }

  // Инициация подключения к HH.ru (redirect)
  async connectToHH(): Promise<void> {
    try {
      const response = await this.client.get('/auth/hh/connect');
      // Если backend вернул JSON с auth_url, делаем redirect
      if (response.data && response.data.auth_url) {
        window.location.href = response.data.auth_url;
      }
    } catch (error: any) {
      console.error('HH connect error:', error);
      
      // Если 409 Conflict - аккаунт уже подключен
      if (error.response?.status === 409) {
        throw error; // Пробрасываем оригинальную ошибку с кодом
      }
      
      throw new Error('Не удалось подключиться к HH.ru');
    }
  }


  // Инициация сессии с загрузкой документов
  async initSession(formData: FormData): Promise<SessionInitResponse> {
    try {
      const response = await this.client.post<SessionInitResponse>('/sessions/init_upload', formData, {
        headers: {
          'Content-Type': 'multipart/form-data',
        },
      });
      return response.data;
    } catch (error) {
      throw this.handleError(error);
    }
  }

  // Получение списка доступных AI фич
  async getFeatures(): Promise<FeatureListResponse> {
    try {
      const response = await this.client.get<FeatureListResponse>('/features/');
      return response.data;
    } catch (error) {
      throw this.handleError(error);
    }
  }

  // Проверка готовности API
  async checkHealth(): Promise<boolean> {
    try {
      await this.client.get('/healthz');
      return true;
    } catch (error) {
      return false;
    }
  }

  private handleError(error: any): Error {
    console.log('Raw error:', error);
    console.log('Error response:', error.response?.data);
    
    // Проверяем различные поля в ответе backend
    const responseData = error.response?.data;
    if (responseData) {
      // Проверяем наиболее частые поля с сообщениями об ошибке
      if (typeof responseData.detail === 'string') {
        return new Error(responseData.detail);
      }
      if (typeof responseData.message === 'string') {
        return new Error(responseData.message);
      }
      if (typeof responseData.error === 'string') {
        return new Error(responseData.error);
      }
      // Если responseData это строка
      if (typeof responseData === 'string') {
        return new Error(responseData);
      }
      // Если есть статус код, используем его
      if (error.response?.status) {
        return new Error(`Ошибка сервера (${error.response.status})`);
      }
    }
    
    // Fallback на стандартное сообщение axios
    if (error.message) {
      return new Error(error.message);
    }
    
    return new Error('Произошла неизвестная ошибка');
  }
}

// Экспортируем синглтон для использования в компонентах
export const apiClient = new ApiClient();