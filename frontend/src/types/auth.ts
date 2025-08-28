// Типы для API авторизации (на основе вашего WebApp API)

export interface LoginRequest {
  email: string;
  password: string;
}

export interface SignupRequest {
  email: string;
  password: string;
  org_name: string;
}

export interface AuthResponse {
  message: string;
  // В реальности ваш API возвращает cookie sid, не токен
}

export interface User {
  id: string;
  email: string;
  org_name?: string;
}

export interface ApiError {
  detail: string;
}