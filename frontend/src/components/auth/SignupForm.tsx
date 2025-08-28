import React, { useState } from 'react';
import { apiClient } from '../../lib/api';
import type { SignupRequest } from '../../types/auth';

interface SignupFormProps {
  onSuccess: () => void;
}

export const SignupForm: React.FC<SignupFormProps> = ({ onSuccess }) => {
  const [formData, setFormData] = useState<SignupRequest>({
    email: '',
    password: '',
    org_name: '',
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
        apiClient.signup(formData),
        new Promise(resolve => setTimeout(resolve, 500))
      ]);
      onSuccess(); // Автоматически логинит после регистрации
    } catch (err) {
      // Улучшенная обработка ошибок
      console.error('Signup error:', err);
      if (err instanceof Error) {
        // Переводим часто встречающиеся ошибки
        if (err.message.includes('409') || err.message.includes('already exists')) {
          setError('Пользователь с таким email уже существует');
        } else if (err.message.includes('400') || err.message.includes('validation')) {
          setError('Проверьте правильность заполнения полей');
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
    setFormData(prev => ({
      ...prev,
      [name]: value,
    }));
  };

  return (
    <form className="space-y-6" onSubmit={handleSubmit}>
      <div>
        <label htmlFor="signup-email" className="block text-sm font-medium text-gray-700">
          Email
        </label>
        <div className="mt-1">
          <input
            id="signup-email"
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
        <label htmlFor="signup-password" className="block text-sm font-medium text-gray-700">
          Пароль
        </label>
        <div className="mt-1">
          <input
            id="signup-password"
            name="password"
            type="password"
            autoComplete="new-password"
            required
            minLength={6}
            value={formData.password}
            onChange={handleChange}
            className="block w-full rounded-md border-gray-300 shadow-sm focus:border-indigo-500 focus:ring-indigo-500 sm:text-sm"
            placeholder="••••••••"
          />
        </div>
        <p className="mt-1 text-sm text-gray-500">Минимум 6 символов</p>
      </div>

      <div>
        <label htmlFor="org-name" className="block text-sm font-medium text-gray-700">
          Название организации
        </label>
        <div className="mt-1">
          <input
            id="org-name"
            name="org_name"
            type="text"
            required
            value={formData.org_name}
            onChange={handleChange}
            className="block w-full rounded-md border-gray-300 shadow-sm focus:border-indigo-500 focus:ring-indigo-500 sm:text-sm"
            placeholder="Ваша компания"
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
          {isLoading ? 'Регистрация...' : 'Создать аккаунт'}
        </button>
      </div>
    </form>
  );
};