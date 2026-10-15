import { Component, type ErrorInfo, type ReactNode } from "react";
import { AlertCircle, RotateCcw } from "lucide-react";

interface Props {
  children: ReactNode;
  fallbackTitle?: string;
  onReset?: () => void;
}

interface State {
  hasError: boolean;
  error: Error | null;
}

export class ErrorBoundary extends Component<Props, State> {
  public state: State = {
    hasError: false,
    error: null,
  };

  public static getDerivedStateFromError(error: Error): State {
    return { hasError: true, error };
  }

  public componentDidCatch(error: Error, errorInfo: ErrorInfo) {
    console.error("ErrorBoundary caught an unhandled rendering error:", error, errorInfo);
  }

  public handleReset = () => {
    this.setState({ hasError: false, error: null });
    if (this.props.onReset) {
      this.props.onReset();
    }
  };

  public render() {
    if (this.state.hasError) {
      return (
        <div className="rounded-2xl border border-rose-500/40 bg-rose-950/40 p-6 my-6 text-rose-200 shadow-xl backdrop-blur-sm">
          <div className="flex items-start gap-3">
            <AlertCircle className="w-6 h-6 text-rose-400 flex-shrink-0 mt-0.5" />
            <div className="space-y-2 flex-grow">
              <h3 className="text-base font-bold text-white">
                {this.props.fallbackTitle || "An unexpected error occurred while rendering screening results"}
              </h3>
              <p className="text-xs text-rose-300 font-mono bg-black/50 p-3 rounded-lg overflow-x-auto border border-rose-900/50">
                {this.state.error?.message || "Unknown client rendering error"}
              </p>
              <p className="text-xs text-neutral-400">
                Your target job description and uploaded candidate resumes remain intact in memory. You can adjust weights or retry screening immediately.
              </p>
              <div className="pt-2">
                <button
                  type="button"
                  onClick={this.handleReset}
                  className="inline-flex items-center gap-1.5 rounded-lg bg-rose-600 hover:bg-rose-500 px-4 py-2 text-xs font-semibold text-white transition-colors cursor-pointer shadow"
                >
                  <RotateCcw className="w-3.5 h-3.5" />
                  <span>Dismiss &amp; Retry</span>
                </button>
              </div>
            </div>
          </div>
        </div>
      );
    }

    return this.props.children;
  }
}
