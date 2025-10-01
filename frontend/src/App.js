import React, { useEffect, useMemo, useState } from "react";
import "@/App.css";
import { BrowserRouter, Routes, Route, Link, useNavigate, useParams } from "react-router-dom";
import axios from "axios";

const BACKEND_URL = process.env.REACT_APP_BACKEND_URL;
const API = `${BACKEND_URL}/api`;

// Simple i18n dictionary
const dict = {
  ro: {
    appName: "Registru Alumni",
    alumni: "Alumni",
    events: "Evenimente",
    invite: "Invitație",
    login: "Autentificare",
    logout: "Delogare",
    username: "Utilizator",
    password: "Parolă",
    signIn: "Intră",
    createAlumni: "Adaugă absolvent",
    fullName: "Nume complet",
    gradYear: "An absolvire",
    bac: "Bacalaureat promovat",
    yes: "Da",
    no: "Nu",
    path: "Parcurs",
    faculty: "Facultate",
    employed: "Piața muncii",
    other: "Altul",
    email: "Email",
    phone: "Telefon",
    save: "Salvează",
    list: "Listă",
    createEvent: "Creează eveniment",
    title: "Titlu",
    date: "Data",
    location: "Locație",
    description: "Descriere",
    generateLink: "Generează link invitație",
    copy: "Copiază",
    copied: "Copiat!",
    notFound: "Nu am găsit invitația sau evenimentul.",
    invitationFor: "Invitație pentru eveniment",
    openInvite: "Deschide invitația",
    loggedInAs: "Conectat ca",
    notLoggedIn: "Neautentificat",
  },
  en: {
    appName: "Alumni Registry",
    alumni: "Alumni",
    events: "Events",
    invite: "Invitation",
    login: "Login",
    logout: "Logout",
    username: "Username",
    password: "Password",
    signIn: "Sign in",
    createAlumni: "Add alumnus",
    fullName: "Full name",
    gradYear: "Graduation year",
    bac: "Baccalaureate passed",
    yes: "Yes",
    no: "No",
    path: "Path",
    faculty: "Faculty",
    employed: "Employed",
    other: "Other",
    email: "Email",
    phone: "Phone",
    save: "Save",
    list: "List",
    createEvent: "Create event",
    title: "Title",
    date: "Date",
    location: "Location",
    description: "Description",
    generateLink: "Generate invite link",
    copy: "Copy",
    copied: "Copied!",
    notFound: "Invitation or event not found.",
    invitationFor: "Invitation for event",
    openInvite: "Open invitation",
    loggedInAs: "Logged in as",
    notLoggedIn: "Not logged in",
  },
};

function useI18n() {
  const [lang, setLang] = useState(() => localStorage.getItem("lang") || "ro");
  const t = useMemo(() => dict[lang], [lang]);
  function toggle() {
    const next = lang === "ro" ? "en" : "ro";
    setLang(next);
    localStorage.setItem("lang", next);
  }
  return { t, lang, setLang, toggle };
}

function useAuth() {
  const [token, setToken] = useState(() => localStorage.getItem("token"));
  const [username, setUsername] = useState(() => localStorage.getItem("username"));

  function setAuth(tok, user) {
    if (tok) {
      localStorage.setItem("token", tok);
      localStorage.setItem("username", user);
    } else {
      localStorage.removeItem("token");
      localStorage.removeItem("username");
    }
    setToken(tok || null);
    setUsername(user || null);
  }

  return { token, username, setAuth };
}

function TopBar({ i18n, auth }) {
  return (
    <div className="sticky top-0 z-10 border-b border-gray-800/80 bg-black/30 backdrop-blur">
      <div className="mx-auto max-w-6xl px-4 py-3 flex items-center justify-between">
        <Link to="/" className="text-white font-semibold">{i18n.t.appName}</Link>
        <div className="flex items-center gap-3">
          <div className="lang-toggle text-gray-300">
            <button onClick={i18n.toggle} className="px-2 py-1 text-xs">
              {i18n.lang === "ro" ? "RO / EN" : "EN / RO"}
            </button>
          </div>
          <div className="login-badge">
            {auth.token ? (
              <span className="text-green-400">{i18n.t.loggedInAs}: {auth.username}</span>
            ) : (
              <span className="text-yellow-400">{i18n.t.notLoggedIn}</span>
            )}
          </div>
        </div>
      </div>
    </div>
  );
}

function LoginCard({ i18n, auth }) {
  const [username, setUsername] = useState("admin");
  const [password, setPassword] = useState("admin123");
  const [error, setError] = useState("");

  async function onSubmit(e) {
    e.preventDefault();
    setError("");
    try {
      const res = await axios.post(`${API}/auth/login`, { username, password });
      auth.setAuth(res.data.access_token, res.data.username);
    } catch (err) {
      setError("Invalid credentials");
    }
  }

  return (
    <div className="card p-4">
      <div className="section-title mb-3">{i18n.t.login}</div>
      <form onSubmit={onSubmit} className="space-y-3">
        <div>
          <label className="label">{i18n.t.username}</label>
          <input className="input" value={username} onChange={e => setUsername(e.target.value)} />
        </div>
        <div>
          <label className="label">{i18n.t.password}</label>
          <input className="input" type="password" value={password} onChange={e => setPassword(e.target.value)} />
        </div>
        {error && <div className="text-red-400 text-sm">{error}</div>}
        <div className="flex gap-2">
          <button className="btn" type="submit">{i18n.t.signIn}</button>
          {auth.token && (
            <button className="btn btn-secondary" type="button" onClick={() => auth.setAuth(null, null)}>
              {i18n.t.logout}
            </button>
          )}
        </div>
      </form>
    </div>
  );
}

function AlumniSection({ i18n, auth }) {
  const [form, setForm] = useState({
    full_name: "",
    graduation_year: new Date().getFullYear(),
    bacalaureat_passed: true,
    path: "faculty",
    email: "",
    phone: "",
  });
  const [list, setList] = useState([]);

  async function load() {
    const res = await axios.get(`${API}/alumni`);
    setList(res.data);
  }

  async function create(e) {
    e.preventDefault();
    if (!auth.token) return alert("Login required");
    await axios.post(`${API}/alumni`, form, { headers: { Authorization: `Bearer ${auth.token}` } });
    setForm({ ...form, full_name: "", email: "", phone: "" });
    await load();
  }

  useEffect(() => { load(); }, []);

  return (
    <div className="card p-4">
      <div className="section-title mb-3">{i18n.t.alumni}</div>
      <form onSubmit={create} className="grid grid-cols-1 md:grid-cols-2 gap-4">
        <div>
          <label className="label">{i18n.t.fullName}</label>
          <input className="input" value={form.full_name} onChange={e => setForm({ ...form, full_name: e.target.value })} />
        </div>
        <div>
          <label className="label">{i18n.t.gradYear}</label>
          <input className="input" type="number" value={form.graduation_year} onChange={e => setForm({ ...form, graduation_year: Number(e.target.value) })} />
        </div>
        <div>
          <label className="label">{i18n.t.bac}</label>
          <select className="input" value={form.bacalaureat_passed ? "1" : "0"} onChange={e => setForm({ ...form, bacalaureat_passed: e.target.value === "1" })}>
            <option value="1">{i18n.t.yes}</option>
            <option value="0">{i18n.t.no}</option>
          </select>
        </div>
        <div>
          <label className="label">{i18n.t.path}</label>
          <select className="input" value={form.path} onChange={e => setForm({ ...form, path: e.target.value })}>
            <option value="faculty">{i18n.t.faculty}</option>
            <option value="employed">{i18n.t.employed}</option>
            <option value="other">{i18n.t.other}</option>
          </select>
        </div>
        <div>
          <label className="label">{i18n.t.email}</label>
          <input className="input" value={form.email} onChange={e => setForm({ ...form, email: e.target.value })} />
        </div>
        <div>
          <label className="label">{i18n.t.phone}</label>
          <input className="input" value={form.phone} onChange={e => setForm({ ...form, phone: e.target.value })} />
        </div>
        <div className="md:col-span-2 flex gap-2">
          <button className="btn" type="submit">{i18n.t.save}</button>
        </div>
      </form>
      <div className="hr" />
      <div className="section-title mb-2">{i18n.t.list}</div>
      <div className="overflow-auto">
        <table className="table">
          <thead>
            <tr>
              <th>{i18n.t.fullName}</th>
              <th>{i18n.t.gradYear}</th>
              <th>{i18n.t.bac}</th>
              <th>{i18n.t.path}</th>
              <th>{i18n.t.email}</th>
              <th>{i18n.t.phone}</th>
            </tr>
          </thead>
          <tbody>
            {list.map(a => (
              <tr key={a.id} className="text-gray-200">
                <td>{a.full_name}</td>
                <td>{a.graduation_year}</td>
                <td>{a.bacalaureat_passed ? i18n.t.yes : i18n.t.no}</td>
                <td>{a.path}</td>
                <td>{a.email || "-"}</td>
                <td>{a.phone || "-"}</td>
              </tr>
            ))}
          </tbody>
        </table>
      </div>
    </div>
  );
}

function EventsSection({ i18n, auth }) {
  const [form, setForm] = useState({ title: "", date: "", location: "", description: "" });
  const [list, setList] = useState([]);
  const [copiedId, setCopiedId] = useState("");

  async function load() {
    const res = await axios.get(`${API}/events`);
    setList(res.data);
  }

  async function create(e) {
    e.preventDefault();
    if (!auth.token) return alert("Login required");
    await axios.post(`${API}/events`, form, { headers: { Authorization: `Bearer ${auth.token}` } });
    setForm({ title: "", date: "", location: "", description: "" });
    await load();
  }

  async function genLink(eventId) {
    if (!auth.token) return alert("Login required");
    const res = await axios.post(`${API}/invitations`, { event_id: eventId }, { headers: { Authorization: `Bearer ${auth.token}` } });
    const token = res.data.token;
    const link = `${window.location.origin}/invite/${token}`;
    await navigator.clipboard.writeText(link);
    setCopiedId(eventId);
    setTimeout(() => setCopiedId("") , 1500);
  }

  useEffect(() => { load(); }, []);

  return (
    <div className="card p-4">
      <div className="section-title mb-3">{i18n.t.events}</div>
      <form onSubmit={create} className="grid grid-cols-1 md:grid-cols-2 gap-4">
        <div>
          <label className="label">{i18n.t.title}</label>
          <input className="input" value={form.title} onChange={e => setForm({ ...form, title: e.target.value })} />
        </div>
        <div>
          <label className="label">{i18n.t.date}</label>
          <input className="input" type="date" value={form.date} onChange={e => setForm({ ...form, date: e.target.value })} />
        </div>
        <div>
          <label className="label">{i18n.t.location}</label>
          <input className="input" value={form.location} onChange={e => setForm({ ...form, location: e.target.value })} />
        </div>
        <div className="md:col-span-2">
          <label className="label">{i18n.t.description}</label>
          <textarea className="input h-24" value={form.description} onChange={e => setForm({ ...form, description: e.target.value })} />
        </div>
        <div className="md:col-span-2 flex gap-2">
          <button className="btn" type="submit">{i18n.t.save}</button>
        </div>
      </form>
      <div className="hr" />
      <div className="section-title mb-2">{i18n.t.list}</div>
      <div className="space-y-3">
        {list.map(ev => (
          <div key={ev.id} className="border border-gray-800 rounded-lg p-3 bg-black/20">
            <div className="flex flex-col md:flex-row md:items-center md:justify-between gap-2">
              <div>
                <div className="text-white font-medium">{ev.title}</div>
                <div className="text-gray-400 text-sm">{ev.date} · {ev.location}</div>
              </div>
              <div className="flex gap-2">
                <button className="btn" onClick={() => genLink(ev.id)}>
                  {copiedId === ev.id ? i18n.t.copied : i18n.t.generateLink}
                </button>
              </div>
            </div>
            {ev.description && <div className="text-gray-300 mt-2 text-sm">{ev.description}</div>}
          </div>
        ))}
      </div>
    </div>
  );
}

function InvitePage({ i18n }) {
  const { token } = useParams();
  const [data, setData] = useState(null);
  const [error, setError] = useState("");

  useEffect(() => {
    (async () => {
      try {
        const res = await axios.get(`${API}/invitations/${token}`);
        setData(res.data);
      } catch (e) {
        setError(i18n.t.notFound);
      }
    })();
  }, [token]);

  if (error) {
    return <div className="text-red-400">{error}</div>;
  }
  if (!data) return <div className="text-gray-300">Loading…</div>;

  const { event } = data;
  return (
    <div className="card p-4">
      <div className="section-title mb-2">{i18n.t.invitationFor}</div>
      <div className="text-white text-xl font-semibold">{event.title}</div>
      <div className="text-gray-400">{event.date} · {event.location}</div>
      {event.description && <div className="text-gray-300 mt-2">{event.description}</div>}
    </div>
  );
}

function Home() {
  const i18n = useI18n();
  const auth = useAuth();
  const [hello, setHello] = useState("");

  useEffect(() => {
    (async () => {
      try {
        const res = await axios.get(`${API}/`);
        setHello(res.data.message);
      } catch (e) {}
    })();
  }, []);

  return (
    <div className="app-shell">
      <TopBar i18n={i18n} auth={auth} />

      <div className="mx-auto max-w-6xl px-4 py-6 grid grid-cols-1 lg:grid-cols-3 gap-4">
        <div className="lg:col-span-2 space-y-4">
          <AlumniSection i18n={i18n} auth={auth} />
          <EventsSection i18n={i18n} auth={auth} />
        </div>
        <div className="space-y-4">
          <LoginCard i18n={i18n} auth={auth} />
          <div className="card p-4 text-gray-300">
            <div className="section-title mb-2">Status</div>
            <div className="text-sm">{hello || "…"}</div>
          </div>
        </div>
      </div>
    </div>
  );
}

function App() {
  return (
    <div className="App">
      <BrowserRouter>
        <Routes>
          <Route path="/" element={<Home />} />
          <Route path="/invite/:token" element={<WrapperInvite />} />
        </Routes>
      </BrowserRouter>
    </div>
  );
}

function WrapperInvite() {
  const i18n = useI18n();
  return (
    <div className="app-shell min-h-screen">
      <div className="mx-auto max-w-3xl px-4 py-6">
        <InvitePage i18n={i18n} />
      </div>
    </div>
  );
}

export default App;
