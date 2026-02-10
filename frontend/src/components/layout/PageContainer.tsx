import { type ReactNode } from 'react';

interface PageContainerProps {
  children: ReactNode;
  maxWidth?: 'narrow' | 'wide' | 'full';
  title?: string;
  description?: string;
  headerAction?: ReactNode;
}

export default function PageContainer({
  children,
  maxWidth = 'wide',
  title,
  description,
  headerAction,
}: PageContainerProps) {
  const widthClass = {
    narrow: 'max-w-4xl',
    wide: 'max-w-7xl',
    full: 'max-w-none',
  }[maxWidth];

  return (
    <div className={`${widthClass} mx-auto px-4 sm:px-6 py-6 w-full`}>
      {/* Optional Header */}
      {(title || description || headerAction) && (
        <div className="mb-6 flex flex-col sm:flex-row sm:items-center sm:justify-between gap-4">
          <div>
            {title && <h1 className="text-3xl font-bold mb-2">{title}</h1>}
            {description && <p className="text-muted-foreground">{description}</p>}
          </div>
          {headerAction && <div>{headerAction}</div>}
        </div>
      )}

      {/* Page Content */}
      {children}
    </div>
  );
}
