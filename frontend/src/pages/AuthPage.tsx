import React, { useState } from 'react';
import { useNavigate } from 'react-router-dom';
import { LoginForm } from '../components/auth/LoginForm';
import { SignupForm } from '../components/auth/SignupForm';

type AuthMode = 'login' | 'signup';

export const AuthPage: React.FC = () => {
  const [mode, setMode] = useState<AuthMode>('login');
  const navigate = useNavigate();

  const handleAuthSuccess = () => {
    // Перенаправляем на Dashboard после успешной авторизации
    navigate('/dashboard');
  };

  return (
    <div className="min-h-screen flex items-center justify-center bg-gray-50 py-12 px-4 sm:px-6 lg:px-8">
      <div className="max-w-md w-full space-y-8">
        <div>
          <h2 className="mt-6 text-center text-3xl font-extrabold text-gray-900">
            HR Assistant
          </h2>
          <p className="mt-2 text-center text-sm text-gray-600">
            Система для работы с резюме и вакансиями
          </p>
        </div>

        {/* Переключатель вкладок */}
        <div className="flex rounded-lg bg-gray-100 p-1">
          <button
            onClick={() => setMode('login')}
            className={`flex-1 px-4 py-2 text-sm font-medium rounded-md transition-colors ${
              mode === 'login'
                ? 'bg-white text-gray-900 shadow'
                : 'text-gray-500 hover:text-gray-700'
            }`}
          >
            Вход
          </button>
          <button
            onClick={() => setMode('signup')}
            className={`flex-1 px-4 py-2 text-sm font-medium rounded-md transition-colors ${
              mode === 'signup'
                ? 'bg-white text-gray-900 shadow'
                : 'text-gray-500 hover:text-gray-700'
            }`}
          >
            Регистрация
          </button>
        </div>

        {/* Формы */}
        <div className="bg-white py-8 px-4 shadow sm:rounded-lg sm:px-10">
          {mode === 'login' ? (
            <LoginForm onSuccess={handleAuthSuccess} />
          ) : (
            <SignupForm onSuccess={handleAuthSuccess} />
          )}
        </div>

        {/* Информация о приложении */}
        <div className="text-center">
          <p className="text-xs text-gray-500">
            Для полноценной работы требуется подключение к HH.ru
          </p>
        </div>
      </div>
    </div>
  );
};