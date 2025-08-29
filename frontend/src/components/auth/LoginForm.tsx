import React, { useState } from 'react';
import { apiClient } from '../../lib/api';
import type { LoginRequest } from '../../types/auth';

interface LoginFormProps {
  onSuccess: () => void;
}

export const LoginForm: React.FC<LoginFormProps> = ({ onSuccess }) => {
  const [formData, setFormData] = useState<LoginRequest>({
    email: '',
    password: '',
  });
  const [isLoading, setIsLoading] = useState(false);
  const [error, setError] = useState<string | null>(null);

  const handleSubmit = async (e: React.FormEvent) => {
    e.preventDefault();
    setError(null);
    setIsLoading(true);

    try {
      // Минимальная задержка для лучшего UX
      const [result] = await Promise.all([
        apiClient.login(formData),
        new Promise(resolve => setTimeout(resolve, 500))
      ]);
      onSuccess(); // Перенаправляем на главную страницу
    } catch (err) {
      // Улучшенная обработка ошибок
      console.error('Login error:', err);
      if (err instanceof Error) {
        // Переводим часто встречающиеся ошибки
        if (err.message.includes('401') || err.message.includes('Unauthorized')) {
          setError('Неверный email или пароль');
        } else if (err.message.includes('404')) {
          setError('Пользователь не найден');
        } else if (err.message.includes('Network')) {
          setError('Ошибка сети. Проверьте подключение к интернету');
        } else {
          setError(err.message);
        }
      } else {
        setError('Произошла неожиданная ошибка');
      }
    } finally {
      setIsLoading(false);
    }
  };

  const handleChange = (e: React.ChangeEvent<HTMLInputElement>) => {
    const { name, value } = e.target;
    // Очистка сообщения об ошибке при новом вводе
    if (error) {
      setError(null);
    }
    setFormData(prev => ({
      ...prev,
      [name]: value,
    }));
  };

  return (
    <form className="space-y-6" onSubmit={handleSubmit}>
      <div>
        <label htmlFor="email" className="block text-sm font-medium text-gray-700">
          Email
        </label>
        <div className="mt-1">
          <input
            id="email"
            name="email"
            type="email"
            autoComplete="email"
            required
            value={formData.email}
            onChange={handleChange}
            className="block w-full rounded-md border-gray-300 shadow-sm focus:border-indigo-500 focus:ring-indigo-500 sm:text-sm"
            placeholder="your@email.com"
          />
        </div>
      </div>

      <div>
        <label htmlFor="password" className="block text-sm font-medium text-gray-700">
          Пароль
        </label>
        <div className="mt-1">
          <input
            id="password"
            name="password"
            type="password"
            autoComplete="current-password"
            required
            value={formData.password}
            onChange={handleChange}
            className="block w-full rounded-md border-gray-300 shadow-sm focus:border-indigo-500 focus:ring-indigo-500 sm:text-sm"
            placeholder="••••••••"
          />
        </div>
      </div>

      {error && (
        <div className="rounded-md bg-red-50 p-4">
          <div className="text-sm text-red-700">
            {error}
          </div>
        </div>
      )}

      <div>
        <button
          type="submit"
          disabled={isLoading}
          className="w-full flex justify-center py-2 px-4 border border-transparent rounded-md shadow-sm text-sm font-medium text-white bg-indigo-600 hover:bg-indigo-700 focus:outline-none focus:ring-2 focus:ring-offset-2 focus:ring-indigo-500 disabled:opacity-50 disabled:cursor-not-allowed"
        >
          {isLoading ? 'Вход...' : 'Войти'}
        </button>
      </div>
    </form>
  );
};
