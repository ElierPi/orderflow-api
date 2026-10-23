import { useEffect, useState, type FormEvent } from "react";
import {
  ArrowDownUp,
  ArrowRight,
  Boxes,
  Check,
  ChevronRight,
  LayoutDashboard,
  LogOut,
  Package,
  ShieldCheck,
  ShoppingBag,
  Users,
} from "lucide-react";
import { api, body, setToken, type User } from "./api";
import { ErrorMessage, Submit } from "./components";
import DashboardPage from "./pages/Dashboard";
import ProductsPage from "./pages/Products";
import CustomersPage from "./pages/Customers";
import OrdersPage from "./pages/Orders";
import InventoryPage from "./pages/Inventory";

const navigation = [
  { id: "overview", label: "Overview", icon: LayoutDashboard },
  { id: "products", label: "Products", icon: Package },
  { id: "customers", label: "Customers", icon: Users },
  { id: "orders", label: "Orders", icon: ShoppingBag },
  { id: "inventory", label: "Inventory", icon: ArrowDownUp },
];
export function Brand() {
  return (
    <div className="brand">
      <span className="brand-mark">
        <Boxes size={24} strokeWidth={1.6} />
      </span>
      orderflow<span className="brand-period">.</span>
    </div>
  );
}

function SignIn({
  onLogin,
  expired,
}: {
  onLogin: (user: User) => void;
  expired: boolean;
}) {
  const [register, setRegister] = useState(false);
  const [busy, setBusy] = useState(false);
  const [error, setError] = useState(
    expired ? "Your session expired. Please sign in again." : "",
  );
  const [success, setSuccess] = useState(false);
  async function submit(event: FormEvent<HTMLFormElement>) {
    event.preventDefault();
    setBusy(true);
    setError("");
    setSuccess(false);
    const data = Object.fromEntries(new FormData(event.currentTarget));
    try {
      if (register) {
        await api("/auth/register", { method: "POST", body: body(data) });
        setRegister(false);
        setSuccess(true);
      } else {
        const token = await api<{ access_token: string }>("/auth/login", {
          method: "POST",
          body: body(data),
        });
        setToken(token.access_token);
        onLogin(await api<User>("/auth/me"));
      }
    } catch (error) {
      setToken("");
      setError((error as Error).message);
    } finally {
      setBusy(false);
    }
  }
  return (
    <main className="login">
      <section className="login-story">
        <Brand />
        <div>
          <span className="eyebrow">A CLEARER WAY TO WORK</span>
          <h1>
            Good business.
            <br />
            Better flow.
          </h1>
          <p>
            Bring your products, people, and orders together. A little less
            complexity. A lot more clarity.
          </p>
          <div className="flow-illustration" aria-hidden="true">
            <div>
              <Package size={25} />
              <span>Products</span>
              <Check size={14} />
            </div>
            <span className="flow-line" />
            <div>
              <ShoppingBag size={25} />
              <span>Orders</span>
              <Check size={14} />
            </div>
            <span className="flow-line" />
            <div>
              <ArrowDownUp size={25} />
              <span>Inventory</span>
              <Check size={14} />
            </div>
          </div>
        </div>
        <small>ORDERFLOW / OPERATIONS, IN ORDER.</small>
      </section>
      <section className="login-panel">
        <div className="login-form">
          <span className="mini-icon">
            <ShieldCheck size={22} />
          </span>
          <div className="eyebrow">YOUR WORKSPACE AWAITS</div>
          <h2>{register ? "Join the workspace" : "Welcome back"}</h2>
          <p>
            {register
              ? "Create an operator account to get started."
              : "Sign in to keep things moving."}
          </p>
          <ErrorMessage message={error} />
          {success && (
            <div className="success" role="status">
              Account created. You can now sign in.
            </div>
          )}
          <form onSubmit={submit}>
            <label>
              Email address
              <input
                name="email"
                type="email"
                autoComplete="username"
                required
                maxLength={254}
                placeholder="you@company.com"
              />
            </label>
            <label>
              Password
              <input
                name="password"
                type="password"
                autoComplete={register ? "new-password" : "current-password"}
                minLength={register ? 12 : 1}
                maxLength={128}
                required
                placeholder={
                  register ? "At least 12 characters" : "Your password"
                }
              />
            </label>
            {register && (
              <small>
                12–128 characters. Your account will have operator permissions.
              </small>
            )}
            <Submit busy={busy}>
              {register ? "Create account" : "Sign in"}
              <ArrowRight size={17} />
            </Submit>
          </form>
          <p className="login-switch">
            {register ? "Already have an account?" : "New to OrderFlow?"}{" "}
            <button
              onClick={() => {
                setRegister(!register);
                setError("");
                setSuccess(false);
              }}
            >
              {register ? "Sign in" : "Create an account"}
            </button>
          </p>
        </div>
        <small className="login-footer">
          A simpler workspace for the work that matters.
        </small>
      </section>
    </main>
  );
}

export default function App() {
  const [user, setUser] = useState<User | null>(null);
  const [expired, setExpired] = useState(false);
  const [page, setPage] = useState(
    () => window.location.hash.slice(1) || "overview",
  );
  const [notice, setNotice] = useState("");
  useEffect(() => {
    const onHash = () => setPage(window.location.hash.slice(1) || "overview");
    const onExpired = () => {
      setToken("");
      setUser(null);
      setExpired(true);
    };
    window.addEventListener("hashchange", onHash);
    window.addEventListener("session-expired", onExpired);
    return () => {
      window.removeEventListener("hashchange", onHash);
      window.removeEventListener("session-expired", onExpired);
    };
  }, []);
  useEffect(() => {
    if (notice) {
      const id = setTimeout(() => setNotice(""), 5000);
      return () => clearTimeout(id);
    }
  }, [notice]);
  if (!user)
    return (
      <SignIn
        onLogin={(value) => {
          setUser(value);
          setExpired(false);
        }}
        expired={expired}
      />
    );
  const current = navigation.find((item) => item.id === page) || navigation[0];
  return (
    <div className="workspace">
      <aside className="sidebar">
        <Brand />
        <div className="workspace-switch">
          <span className="workspace-avatar">O</span>
          <div>
            <strong>My workspace</strong>
            <small>OrderFlow Operations</small>
          </div>
          <ChevronRight size={15} />
        </div>
        <div className="nav-label">WORKSPACE</div>
        <nav aria-label="Main navigation">
          {navigation.map((item) => (
            <a
              href={`#${item.id}`}
              key={item.id}
              className={current.id === item.id ? "active" : ""}
              aria-current={current.id === item.id ? "page" : undefined}
            >
              <item.icon size={19} strokeWidth={1.7} />
              {item.label}
              {current.id === item.id && <span className="nav-active-dot" />}
            </a>
          ))}
        </nav>
        <div className="sidebar-note">
          <span className="mini-icon">
            <Boxes size={19} />
          </span>
          <strong>Everything, connected.</strong>
          <p>From the first product to the last delivery.</p>
          <a
            href={`${import.meta.env.VITE_API_URL || "/api"}/docs`}
            target="_blank"
            rel="noreferrer"
          >
            Explore the API
            <ArrowRight size={14} />
          </a>
        </div>
        <div className="user">
          <span className="avatar">{user.email.slice(0, 1).toUpperCase()}</span>
          <div>
            <strong title={user.email}>{user.email.split("@")[0]}</strong>
            <small>
              {user.role === "admin" ? "Administrator" : "Operator"}
            </small>
          </div>
          <button
            className="icon-button"
            aria-label="Sign out"
            onClick={() => {
              setToken("");
              setUser(null);
              setExpired(false);
              setNotice("");
            }}
          >
            <LogOut size={18} />
          </button>
        </div>
      </aside>
      <div className="main-shell">
        <header className="topbar">
          <span>
            Workspace
            <ChevronRight size={14} />
            <strong>{current.label}</strong>
          </span>
          <span className="topbar-date">
            {new Intl.DateTimeFormat("en-US", {
              month: "short",
              day: "numeric",
              year: "numeric",
            }).format(new Date())}
          </span>
        </header>
        <main className="content">
          {notice && (
            <div className="toast" role="status">
              <Check size={18} />
              {notice}
              <button
                aria-label="Dismiss notification"
                onClick={() => setNotice("")}
              >
                ×
              </button>
            </div>
          )}
          {current.id === "overview" && <DashboardPage />}
          {current.id === "products" && (
            <ProductsPage admin={user.role === "admin"} notify={setNotice} />
          )}
          {current.id === "customers" && (
            <CustomersPage admin={user.role === "admin"} notify={setNotice} />
          )}
          {current.id === "orders" && <OrdersPage notify={setNotice} />}
          {current.id === "inventory" && <InventoryPage notify={setNotice} />}
        </main>
        <footer className="workspace-footer">
          <span>ORDERFLOW</span>
          <span>Operations, in order.</span>
        </footer>
      </div>
    </div>
  );
}
