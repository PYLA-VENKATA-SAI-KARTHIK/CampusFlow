import { useState, useEffect } from 'react';
import { pushNotificationService } from '../services/pushNotificationService';

export const PushNotificationOptIn = () => {
  const [isSupported, setIsSupported] = useState(false);
  const [isSubscribed, setIsSubscribed] = useState(false);
  const [loading, setLoading] = useState(false);
  const [message, setMessage] = useState<string | null>(null);

  useEffect(() => {
    const checkStatus = async () => {
      if (pushNotificationService.isPushSupported()) {
        setIsSupported(true);
        if (typeof Notification !== 'undefined' && Notification.permission === 'granted') {
          try {
            const status = await pushNotificationService.getStatus();
            setIsSubscribed(status.has_active_subscription);
          } catch (e) {
            // Ignore offline / status check errors
          }
        }
      }
    };
    checkStatus();
  }, []);

  if (!isSupported) {
    return null;
  }

  const handleToggle = async () => {
    setLoading(true);
    setMessage(null);
    try {
      if (isSubscribed) {
        const success = await pushNotificationService.unsubscribe();
        if (success) {
          setIsSubscribed(false);
          setMessage('Push notifications disabled.');
        }
      } else {
        const success = await pushNotificationService.subscribe();
        if (success) {
          setIsSubscribed(true);
          setMessage('Push notifications enabled!');
        } else {
          setMessage('Permission not granted.');
        }
      }
    } catch (err: any) {
      setMessage(err.message || 'Failed to update push subscription.');
    } finally {
      setLoading(false);
    }
  };

  return (
    <div className="flex items-center space-x-2 text-xs">
      <button
        onClick={handleToggle}
        disabled={loading}
        className={`px-3 py-1.5 rounded-xl font-bold transition-all shadow-sm flex items-center space-x-1.5 ${
          isSubscribed
            ? 'bg-emerald-50 text-emerald-700 border border-emerald-200 hover:bg-emerald-100'
            : 'bg-indigo-50 text-indigo-700 border border-indigo-200 hover:bg-indigo-100'
        }`}
        title={isSubscribed ? 'Disable browser push notifications' : 'Enable browser push notifications'}
      >
        {loading ? (
          <span className="flex items-center space-x-1">
            <span className="w-3 h-3 border-2 border-current border-t-transparent rounded-full animate-spin" />
            <span>Updating...</span>
          </span>
        ) : isSubscribed ? (
          <>
            <span className="w-2 h-2 rounded-full bg-emerald-500 animate-pulse" />
            <span>Push Enabled</span>
          </>
        ) : (
          <>
            <span className="w-2 h-2 rounded-full bg-indigo-400" />
            <span>Enable Push</span>
          </>
        )}
      </button>
      {message && <span className="text-[11px] text-slate-500 font-medium">{message}</span>}
    </div>
  );
};
