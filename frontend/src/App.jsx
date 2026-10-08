import React, { useState, useEffect } from 'react';
import Home from './pages/Home';
import Investigation from './pages/Investigation';
import CaseAnalysis from './pages/CaseAnalysis';
import { DEMO_CASES } from './services/api';
import '../css/style.css';

/**
 * Route Mapping Helper
 */
function getRouteFromHash() {
  const hash = window.location.hash.replace('#/', '').replace('#', '');
  if (['create-case', 'investigation', 'dashboard', 'graph', 'response'].includes(hash)) {
    return hash;
  }
  return 'landing';
}

/**
 * Root React Application
 * Features hash-based URL routing, browser history (back/forward) support,
 * and strict separation between clean user input and live demo data.
 */
export default function App() {
  const [currentPage, setCurrentPage] = useState(getRouteFromHash());
  const [activeCaseKey, setActiveCaseKey] = useState(null);
  
  // activeCaseData is NULL by default unless user creates a case or loads a demo
  const [activeCaseData, setActiveCaseData] = useState(null);

  // Synchronize hash routing with state and browser history
  useEffect(() => {
    const handleHashChange = () => {
      const route = getRouteFromHash();
      setCurrentPage(route);
    };

    window.addEventListener('hashchange', handleHashChange);
    return () => window.removeEventListener('hashchange', handleHashChange);
  }, []);

  const navigate = (pageName) => {
    setCurrentPage(pageName);
    window.location.hash = pageName === 'landing' ? '#/' : `#/${pageName}`;
    window.scrollTo({ top: 0, behavior: 'smooth' });
  };

  // User explicitly launches Create Case (starts completely blank)
  const handleStartCleanCase = () => {
    setActiveCaseKey(null);
    navigate('create-case');
  };

  // User explicitly clicks "Explore Live Demo"
  const handleLaunchLiveDemo = (presetKey = 'laptop') => {
    setActiveCaseKey(presetKey);
    const demoData = DEMO_CASES[presetKey] || DEMO_CASES.laptop;
    setActiveCaseData(demoData);
    navigate('dashboard');
  };

  const handleInvestigationDone = () => {
    navigate('dashboard');
  };

  return (
    <div className="claimpilot-app">
      {/* Page 1: Landing Page */}
      {currentPage === 'landing' && (
        <Home
          onGetStarted={handleStartCleanCase}
          onDemoCase={handleLaunchLiveDemo}
        />
      )}

      {/* Page 3: Investigation Pipeline */}
      {currentPage === 'investigation' && (
        <Investigation
          caseTitle={activeCaseData?.title || 'Active Case Investigation'}
          onComplete={handleInvestigationDone}
          onBack={() => navigate('create-case')}
        />
      )}

      {/* Pages 2, 4, 5, 6: Case Analysis Workspace (Dashboard, Create Case, Graph, Response) */}
      {['dashboard', 'create-case', 'graph', 'response'].includes(currentPage) && (
        <CaseAnalysis
          activeView={currentPage}
          activeCaseKey={activeCaseKey}
          caseData={activeCaseData}
          onCaseUpdate={(updated) => setActiveCaseData(updated)}
          onLoadDemo={(presetKey) => handleLaunchLiveDemo(presetKey)}
          onNavigate={(target) => navigate(target)}
        />
      )}
    </div>
  );
}
