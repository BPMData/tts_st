import { useEffect, useState } from 'react';
import { useRegisterSW } from 'virtual:pwa-register/react';
import { strings } from '../shared/strings.ts';

export function App() {
  const [online, setOnline] = useState(navigator.onLine);
  const [cacheError, setCacheError] = useState(false);
  const {
    offlineReady: [offlineReady],
    needRefresh: [needRefresh],
    updateServiceWorker,
  } = useRegisterSW({ onRegisterError: () => setCacheError(true) });

  useEffect(() => {
    const updateConnection = () => setOnline(navigator.onLine);
    window.addEventListener('online', updateConnection);
    window.addEventListener('offline', updateConnection);
    return () => {
      window.removeEventListener('online', updateConnection);
      window.removeEventListener('offline', updateConnection);
    };
  }, []);

  return (
    <>
      <a className="skip-link" href="#main">{strings.skipLink}</a>
      <div className="mx-auto max-w-3xl px-6 py-10 sm:px-10 sm:py-16">
        <header className="mb-14 flex items-center gap-4">
          <img src="/icons/icon.svg" alt="" width="64" height="64" />
          <div>
            <p className="text-3xl font-bold tracking-tight">{strings.appName}</p>
            <p className="mt-1 text-base">{strings.suite}</p>
          </div>
        </header>
        <main id="main" tabIndex={-1}>
          <h1 className="text-4xl font-bold leading-tight sm:text-5xl">{strings.welcome}</h1>
          <p className="mt-5 text-2xl leading-relaxed">{strings.description}</p>
          <p className="mt-6">{strings.introduction}</p>
          <p className="mt-3">{strings.progress}</p>
          <div role="status" aria-live="polite" aria-atomic="true" className="status-panel my-8 rounded-2xl border-2 p-5">
            <p className="font-bold">{online ? strings.online : strings.offline}</p>
            {offlineReady && <p className="mt-2">{strings.offlineReady}</p>}
            {cacheError && <p className="mt-2">{strings.offlineError}</p>}
            {needRefresh && <p className="mt-2">{strings.updateReady}</p>}
          </div>
          {needRefresh && (
            <button type="button" className="update-button mb-8 rounded-xl px-6 py-3 font-bold" onClick={() => void updateServiceWorker(true).catch(() => setCacheError(true))}>
              {strings.update}
            </button>
          )}
          <details className="border-t py-4">
            <summary className="cursor-pointer py-3 font-bold">{strings.installTitle}</summary>
            <p className="mt-3">{strings.installChrome}</p>
            <p className="mt-3">{strings.installSafari}</p>
            <p className="mt-3">{strings.installOffline}</p>
          </details>
          <details className="border-t py-4">
            <summary className="cursor-pointer py-3 font-bold">{strings.privacyTitle}</summary>
            <p className="mt-3">{strings.privacy}</p>
          </details>
        </main>
      </div>
    </>
  );
}
