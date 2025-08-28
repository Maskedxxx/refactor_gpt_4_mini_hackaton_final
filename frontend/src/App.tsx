import React from 'react';
import { AuthPage } from './pages/AuthPage';

function App() {
  // Пока показываем только страницу авторизации
  // В будущем добавим роутинг для разных страниц
  return (
    <div className="App">
      <AuthPage />
    </div>
  );
}

export default App;