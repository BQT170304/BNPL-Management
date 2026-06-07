import React from 'react';
import './MobileFrame.css';

interface Props {
  children: React.ReactNode;
}

export function MobileFrame({ children }: Props) {
  return (
    <div className="phone-outer">
      <div className="phone-inner">
        <div className="status-bar">
          <span>9:41</span>
          <div className="status-icons">
            <span>●●●</span>
            <span>WiFi</span>
            <span>🔋</span>
          </div>
        </div>
        <div className="phone-content">
          {children}
        </div>
      </div>
    </div>
  );
}
