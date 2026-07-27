import React from 'react';
import { AlertTriangle, RefreshCcw } from 'lucide-react';

class ErrorBoundary extends React.Component {
  constructor(props) {
    super(props);
    this.state = { hasError: false, error: null, errorInfo: null };
  }

  static getDerivedStateFromError(error) {
    return { hasError: true };
  }

  componentDidCatch(error, errorInfo) {
    this.setState({ error, errorInfo });
    console.error("React Error Boundary Caught:", error, errorInfo);
  }

  render() {
    if (this.state.hasError) {
      return (
        <div className="min-h-screen bg-slate-950 flex flex-col items-center justify-center p-6 text-center">
          <div className="bg-red-500/10 border border-red-500/30 p-8 rounded-3xl max-w-lg w-full backdrop-blur-md">
            <div className="w-20 h-20 bg-red-500/20 rounded-full flex items-center justify-center mx-auto mb-6">
              <AlertTriangle className="w-10 h-10 text-red-400" />
            </div>
            <h1 className="text-3xl font-bold text-white mb-4">Something went wrong.</h1>
            <p className="text-slate-300 mb-8">
              The application encountered an unexpected error. Please refresh the page or try logging out.
            </p>
            <div className="flex gap-4 justify-center">
              <button 
                onClick={() => window.location.reload()}
                className="bg-red-500 hover:bg-red-600 text-white font-bold py-3 px-6 rounded-xl transition-all flex items-center gap-2"
              >
                <RefreshCcw className="w-5 h-5" /> Reload Page
              </button>
            </div>
            {import.meta.env.MODE === 'development' && this.state.error && (
              <div className="mt-8 text-left bg-slate-900 p-4 rounded-xl overflow-auto text-xs text-red-400 border border-red-500/20">
                <p className="font-bold mb-2">{this.state.error.toString()}</p>
                <pre>{this.state.errorInfo?.componentStack}</pre>
              </div>
            )}
          </div>
        </div>
      );
    }

    return this.props.children; 
  }
}

export default ErrorBoundary;
