import { Component, type ErrorInfo, type ReactNode } from "react";

type ErrorBoundaryProps = {
  children: ReactNode;
};

type ErrorBoundaryState = {
  error: Error | null;
};

export class ErrorBoundary extends Component<ErrorBoundaryProps, ErrorBoundaryState> {
  state: ErrorBoundaryState = { error: null };

  static getDerivedStateFromError(error: Error): ErrorBoundaryState {
    return { error };
  }

  componentDidCatch(error: Error, info: ErrorInfo) {
    console.error("Dashboard crashed", error, info.componentStack);
  }

  render() {
    if (this.state.error) {
      return (
        <div className="mx-auto max-w-2xl px-4 py-16 text-center">
          <h1 className="text-2xl font-bold text-slate-900">Something went wrong</h1>
          <p className="mt-2 text-sm text-slate-600">
            The dashboard hit an unexpected error. Your greenhouse data is still safe.
          </p>
          <pre className="mt-4 overflow-x-auto rounded-md bg-slate-100 p-3 text-left text-xs text-slate-700">
            {this.state.error.message}
          </pre>
          <button
            type="button"
            onClick={() => window.location.reload()}
            className="mt-6 rounded-md bg-ok-600 px-4 py-2 text-sm font-medium text-white hover:bg-ok-700"
          >
            Reload dashboard
          </button>
        </div>
      );
    }
    return this.props.children;
  }
}
