import "./Overlay.css";
import { useEffect } from "react";

interface OverlayProps {
  id: string;
  children: React.ReactNode;
  open: boolean;
  onClose: () => void;
  onCloseButtonClick?: () => void;
  closeLabel?: string;
  modal?: boolean;
  lightDismiss?: boolean;
  hasCloseButton?: boolean;
}

interface OverlayHeaderProps {
  children: React.ReactNode;
}

interface OverlayBodyProps {
  children: React.ReactNode;
}

export function Overlay({
  id,
  children,
  open,
  onClose,
  onCloseButtonClick,
  closeLabel = "Close",
  lightDismiss = true,
  hasCloseButton = true
}: OverlayProps) {
  useEffect(() => {
    if (open) {
      document.body.style.overflow = "hidden";
    } else {
      document.body.style.overflow = "";
    }
    return () => {
      document.body.style.overflow = "";
    };
  }, [open]);

  if (!open) return null;

  const handleBackdropClick = (e: React.MouseEvent) => {
    if (lightDismiss && e.target === e.currentTarget) {
      onClose();
    }
  };

  return (
    <div id={id} className="overlay-backdrop" onClick={handleBackdropClick}>
      <div className="overlay-content">
        {hasCloseButton && (
          <button className="overlay-close" onClick={onCloseButtonClick || onClose}>
            {closeLabel} ✕
          </button>
        )}
        {children}
      </div>
    </div>
  );
}

Overlay.Header = function OverlayHeader({ children }: OverlayHeaderProps) {
  return <div className="overlay-header">{children}</div>;
};

Overlay.Body = function OverlayBody({ children }: OverlayBodyProps) {
  return <div className="overlay-body">{children}</div>;
};
