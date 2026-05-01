import { Component, type ReactNode } from "react";
import { Button } from "@/components/ui/button";

interface Props {
  children: ReactNode;
}

interface State {
  error: Error | null;
}

export class ErrorBoundary extends Component<Props, State> {
  state: State = { error: null };

  static getDerivedStateFromError(error: Error): State {
    return { error };
  }

  componentDidCatch(error: Error, info: unknown) {
    console.error("Uncaught error:", error, info);
  }

  reset = () => this.setState({ error: null });

  render() {
    if (!this.state.error) return this.props.children;

    return (
      <div className="min-h-screen grid place-items-center px-6 bg-surface-cream">
        <div className="max-w-md text-center">
          <div className="text-[10px] font-mono uppercase tracking-[0.3em] text-error">
            ✖ Something broke
          </div>
          <h1 className="mt-2 font-display text-3xl font-bold text-brand-brown-darker">
            We hit an unexpected error
          </h1>
          <p className="mt-3 text-brand-brown-light text-sm">
            {this.state.error.message ||
              "Please try again. If the problem persists, contact support."}
          </p>
          <div className="mt-6 flex justify-center gap-3">
            <Button variant="outline" onClick={() => location.reload()}>
              Reload page
            </Button>
            <Button onClick={this.reset}>Try again</Button>
          </div>
        </div>
      </div>
    );
  }
}
