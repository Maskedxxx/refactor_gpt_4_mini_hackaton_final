import React from 'react';
import { BrowserRouter as Router, Routes, Route, Navigate } from 'react-router-dom';
import { AuthPage } from './pages/AuthPage';
import DashboardPage from './pages/DashboardPage';
import CreateProjectPage from './pages/CreateProjectPage';
import { ProtectedRoute } from './components/auth/ProtectedRoute';

function App() {
  return (
    <Router>
      <div className="App">
        <Routes>
          {/* Public routes */}
          <Route path="/" element={<AuthPage />} />
          <Route path="/auth" element={<AuthPage />} />
          
          {/* Protected routes */}
          <Route 
            path="/dashboard" 
            element={
              <ProtectedRoute>
                <DashboardPage />
              </ProtectedRoute>
            } 
          />
          
          {/* Profile page placeholder */}
          <Route 
            path="/profile" 
            element={
              <ProtectedRoute>
                <div className="text-center py-12">
                  <h1 className="text-2xl font-bold text-gray-900">Профиль</h1>
                  <p className="text-gray-600 mt-2">Страница в разработке</p>
                </div>
              </ProtectedRoute>
            } 
          />
          
          {/* Project creation */}
          <Route 
            path="/project/create" 
            element={
              <ProtectedRoute>
                <CreateProjectPage />
              </ProtectedRoute>
            } 
          />
          
          {/* AI Tools workspace placeholder */}
          <Route 
            path="/project/:sessionId/tools" 
            element={
              <ProtectedRoute>
                <div className="text-center py-12">
                  <h1 className="text-2xl font-bold text-gray-900">AI Инструменты</h1>
                  <p className="text-gray-600 mt-2">Страница в разработке</p>
                </div>
              </ProtectedRoute>
            } 
          />
          
          {/* Projects list placeholder */}
          <Route 
            path="/projects" 
            element={
              <ProtectedRoute>
                <div className="text-center py-12">
                  <h1 className="text-2xl font-bold text-gray-900">История проектов</h1>
                  <p className="text-gray-600 mt-2">Страница в разработке</p>
                </div>
              </ProtectedRoute>
            } 
          />
          
          {/* Default redirect */}
          <Route path="*" element={<Navigate to="/" replace />} />
        </Routes>
      </div>
    </Router>
  );
}

export default App;