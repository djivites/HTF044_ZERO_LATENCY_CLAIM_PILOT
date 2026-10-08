import React from 'react';
import ReactDOM from 'react-dom/client';
import App from './App.jsx';
import '../css/style.css';

const rootEl = document.getElementById('root');
if (rootEl) {
  // Hide static fallback elements when React mounts
  const staticLanding = document.getElementById('view-landing');
  const staticApp = document.getElementById('view-app-shell');
  const staticInv = document.getElementById('view-investigation');
  if (staticLanding) staticLanding.style.display = 'none';
  if (staticApp) staticApp.style.display = 'none';
  if (staticInv) staticInv.style.display = 'none';

  ReactDOM.createRoot(rootEl).render(
    <React.StrictMode>
      <App />
    </React.StrictMode>
  );
}
