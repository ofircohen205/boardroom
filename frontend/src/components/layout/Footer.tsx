import { Link } from 'react-router-dom';
import { Github } from 'lucide-react';

export default function Footer() {
  const currentYear = new Date().getFullYear();

  return (
    <footer className="mt-auto border-t border-border bg-card/20 backdrop-blur-sm">
      <div className="max-w-7xl mx-auto px-4 sm:px-6 lg:px-8 py-6">
        <div className="flex flex-col sm:flex-row items-center justify-between gap-4">
          {/* Left: Branding */}
          <div className="text-sm text-muted-foreground">
            © {currentYear} Boardroom. Multi-agent financial analysis.
          </div>

          {/* Right: Links */}
          <div className="flex items-center space-x-4">
            <Link
              to="https://github.com/ofircohen/boardroom"
              target="_blank"
              rel="noopener noreferrer"
              className="text-muted-foreground hover:text-foreground transition-colors flex items-center space-x-1"
            >
              <Github className="w-4 h-4" />
              <span className="text-sm">GitHub</span>
            </Link>
            <span className="text-muted-foreground text-sm">v1.0.0</span>
          </div>
        </div>
      </div>
    </footer>
  );
}
