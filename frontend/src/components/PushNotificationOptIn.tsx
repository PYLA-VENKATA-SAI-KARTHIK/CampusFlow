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
        try {
          const status = await pushNotificationService.getStatus();
          setIsSubscribed(status.has_active_subscription);
        } catch (e) {
          // Ignore offline / status check errors
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
        className={`px-3 py-1.5 rounded-md font-medium transition-colors ${
          isSubscribed
            ? 'bg-green-100 text-green-800 hover:bg-green-200'
            : 'bg-blue-100 text-blue-800 hover:bg-blue-200'
        }`}
        title={isSubscribed ? 'Disable browser push notifications' : 'Enable browser push notifications'}
      >
        {loading ? 'Updating...' : isSubscribed ? '🔔 Push Enabled' : '🔕 Enable Push'}
      </button>
      {message && <span className="text-gray-500">{message}</span>}
    </div>
  );
};
