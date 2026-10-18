import React from 'react';
import { createRoot } from 'react-dom/client';
import Router from './Router';
import './index.css';
import './app.css';
createRoot(document.getElementById('root')!).render(<React.StrictMode><Router /></React.StrictMode>);
