import { useState } from "react";
import { useAsync } from "../../hooks/useAsync";
import { useAuth } from "../../state/auth";
import "./LoginScreen.css";

export function LoginScreen() {
  const { login } = useAuth();
  const loginCall = useAsync(login);
  const [username, setUsername] = useState("nguyenvana");
  const [password, setPassword] = useState("123456");

  async function submit() {
    await loginCall.run(username, password).catch(() => undefined);
  }

  return (
    <div className="login-screen">
      <div className="login-hero">
        <div className="login-logo">💳</div>
        <h1 className="login-title">BNPL Assistant</h1>
        <p className="login-subtitle">Tư vấn tài chính thông minh</p>
      </div>

      <div className="login-form">
        {loginCall.error && (
          <div className="login-error">{loginCall.error}</div>
        )}

        <div className="login-field">
          <label>Tên đăng nhập</label>
          <input
            className="login-input"
            type="text"
            value={username}
            onChange={e => setUsername(e.target.value)}
            placeholder="username"
          />
        </div>

        <div className="login-field">
          <label>Mật khẩu</label>
          <input
            className="login-input"
            type="password"
            value={password}
            onChange={e => setPassword(e.target.value)}
            placeholder="password"
          />
        </div>

        <button
          className="login-btn"
          onClick={submit}
          disabled={loginCall.loading}
        >
          {loginCall.loading ? "Đang đăng nhập..." : "Đăng nhập"}
        </button>

        <p className="login-demo-hint">Demo: nguyenvana / 123456</p>
      </div>
    </div>
  );
}
