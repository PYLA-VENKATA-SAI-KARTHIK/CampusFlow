import { useEffect, useRef } from 'react';
import { useNavigate } from 'react-router-dom';
import { useAuthStore } from '../store/authStore';

const INACTIVITY_TIMEOUT_MS = 5 * 60 * 1000; // 5 minutes

export const useInactivityTimeout = () => {
  const { isAuthenticated, clearSession } = useAuthStore();
  const navigate = useNavigate();
  const timerRef = useRef<ReturnType<typeof setTimeout> | null>(null);
  const lastActiveRef = useRef<number>(Date.now());

  useEffect(() => {
    if (!isAuthenticated) {
      if (timerRef.current) {
        clearTimeout(timerRef.current);
        timerRef.current = null;
      }
      return;
    }

    const handleLogout = () => {
      clearSession();
      navigate('/login?reason=inactivity', { replace: true });
    };

    const resetTimer = () => {
      const now = Date.now();
      // Throttle event handling: only reset if at least 1 second has passed
      if (now - lastActiveRef.current < 1000) {
        return;
      }
      lastActiveRef.current = now;

      if (timerRef.current) {
        clearTimeout(timerRef.current);
      }
      timerRef.current = setTimeout(handleLogout, INACTIVITY_TIMEOUT_MS);
    };

    // Initial timer setup
    timerRef.current = setTimeout(handleLogout, INACTIVITY_TIMEOUT_MS);

    // Activity event listeners
    const activityEvents = ['mousedown', 'mousemove', 'keydown', 'scroll', 'touchstart', 'wheel'];
    activityEvents.forEach((event) => {
      window.addEventListener(event, resetTimer, { passive: true });
    });

    return () => {
      if (timerRef.current) {
        clearTimeout(timerRef.current);
      }
      activityEvents.forEach((event) => {
        window.removeEventListener(event, resetTimer);
      });
    };
  }, [isAuthenticated, clearSession, navigate]);
};

