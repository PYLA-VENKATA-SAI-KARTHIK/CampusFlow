import { Component, type ErrorInfo, type ReactNode } from 'react';
import { CampusFlowLogo } from './common/CampusFlowLogo';

interface Props {
  children: ReactNode;
  fallback?: ReactNode;
}

interface State {
  hasError: boolean;
  error: Error | null;
  errorInfo: ErrorInfo | null;
}

export class ErrorBoundary extends Component<Props, State> {
  public state: State = {
    hasError: false,
    error: null,
    errorInfo: null,
  };

  public static getDerivedStateFromError(error: Error): Partial<State> {
    return { hasError: true, error };
  }

  public componentDidCatch(error: Error, errorInfo: ErrorInfo) {
    console.error('CampusFlow ErrorBoundary caught an unhandled error:', error, errorInfo);
    this.setState({ errorInfo });
  }

  private handleReset = () => {
    this.setState({ hasError: false, error: null, errorInfo: null });
    window.location.href = '/';
  };

  private handleReload = () => {
    window.location.reload();
  };

  public render() {
    if (this.state.hasError) {
      if (this.props.fallback) {
        return this.props.fallback;
      }

      return (
        <div className="min-h-screen bg-slate-950 text-slate-100 flex flex-col justify-center items-center px-4 py-12 selection:bg-indigo-500 selection:text-white font-sans antialiased">
          <div className="w-full max-w-lg bg-slate-900 border border-slate-800/80 rounded-2xl p-6 sm:p-8 shadow-2xl space-y-6 text-center animate-fade-in">
            <div className="flex justify-center">
              <CampusFlowLogo size="md" variant="light" />
            </div>

            <div className="w-12 h-12 rounded-2xl bg-rose-500/10 border border-rose-500/20 text-rose-400 mx-auto flex items-center justify-center">
              <svg className="w-6 h-6" fill="none" viewBox="0 0 24 24" stroke="currentColor">
                <path strokeLinecap="round" strokeLinejoin="round" strokeWidth="2" d="M12 9v2m0 4h.01m-6.938 4h13.856c1.54 0 2.502-1.667 1.732-3L13.732 4c-.77-1.333-2.694-1.333-3.464 0L3.34 16c-.77 1.333.192 3 1.732 3z" />
              </svg>
            </div>

            <div className="space-y-2">
              <h2 className="text-xl sm:text-2xl font-black tracking-tight text-white">
                Workspace Encountered an Issue
              </h2>
              <p className="text-xs sm:text-sm text-slate-400 leading-relaxed max-w-md mx-auto">
                An unexpected interface error occurred during view rendering. Your data and account status are safe.
              </p>
            </div>

            {this.state.error && (
              <div className="bg-slate-950/80 border border-slate-800 rounded-xl p-3.5 text-left overflow-auto max-h-36 scrollbar-thin">
                <p className="text-[11px] font-mono text-rose-400 font-semibold break-words">
                  {this.state.error.message || 'Unknown render exception'}
                </p>
              </div>
            )}

            <div className="flex flex-col sm:flex-row items-center justify-center gap-3 pt-2">
              <button
                type="button"
                onClick={this.handleReload}
                className="w-full sm:w-auto px-5 py-2.5 rounded-xl bg-indigo-600 hover:bg-indigo-700 text-white text-xs font-bold shadow-md shadow-indigo-600/20 transition active:scale-[0.98] focus:outline-none focus:ring-2 focus:ring-indigo-500"
              >
                Reload Workspace
              </button>
              <button
                type="button"
                onClick={this.handleReset}
                className="w-full sm:w-auto px-5 py-2.5 rounded-xl bg-slate-800 hover:bg-slate-700 text-slate-200 text-xs font-bold border border-slate-700 transition active:scale-[0.98] focus:outline-none focus:ring-2 focus:ring-slate-600"
              >
                Return to Home
              </button>
            </div>
          </div>
        </div>
      );
    }

    return this.props.children;
  }
}
