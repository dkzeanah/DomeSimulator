import { StrictMode, lazy, Suspense } from "react";
import { createRoot } from "react-dom/client";
import { BrowserRouter, Route, Routes } from "react-router-dom";
import Layout from "./components/Layout";
import { SessionProvider } from "./lib/session";
import Home from "./pages/Home";
import "./styles.css";

const Book = lazy(() => import("./pages/Book"));
const Sample = lazy(() => import("./pages/Sample"));
const Start = lazy(() => import("./pages/Start"));
const Build = lazy(() => import("./pages/Build"));
const Network = lazy(() => import("./pages/Network"));
const Back = lazy(() => import("./pages/Back"));
const Kit = lazy(() => import("./pages/Kit"));
const Account = lazy(() => import("./pages/Account"));
const Recyclers = lazy(() => import("./pages/Recyclers"));
const Thanks = lazy(() => import("./pages/Thanks"));
const Admin = lazy(() => import("./pages/Admin"));
const Confirm = lazy(() => import("./pages/Mailbox").then((m) => ({ default: m.Confirm })));
const Unsubscribe = lazy(() => import("./pages/Mailbox").then((m) => ({ default: m.Unsubscribe })));
const Privacy = lazy(() => import("./pages/Mailbox").then((m) => ({ default: m.Privacy })));
const AdminList = lazy(() => import("./pages/AdminList"));
const AdminAnalytics = lazy(() => import("./pages/AdminAnalytics"));
const NotFound = lazy(() => import("./pages/NotFound"));

createRoot(document.getElementById("root")!).render(
  <StrictMode>
    <BrowserRouter>
      <SessionProvider>
        <Suspense fallback={<div className="p-8 muted">Loading...</div>}>
          <Routes>
            <Route element={<Layout />}>
              <Route index element={<Home />} />
              <Route path="book" element={<Book />} />
              <Route path="sample" element={<Sample />} />
              <Route path="start" element={<Start />} />
              <Route path="build" element={<Build />} />
              <Route path="network" element={<Network />} />
              <Route path="back" element={<Back />} />
              <Route path="kit/*" element={<Kit />} />
              <Route path="account/*" element={<Account />} />
              <Route path="recyclers" element={<Recyclers />} />
              <Route path="thanks/:ref" element={<Thanks />} />
              <Route path="checkout/test/:ref" element={<Thanks test />} />
              <Route path="admin" element={<Admin />} />
              <Route path="admin/list" element={<AdminList />} />
              <Route path="admin/analytics" element={<AdminAnalytics />} />
              <Route path="confirm" element={<Confirm />} />
              <Route path="unsubscribe" element={<Unsubscribe />} />
              <Route path="privacy" element={<Privacy />} />
              <Route path="*" element={<NotFound />} />
            </Route>
          </Routes>
        </Suspense>
      </SessionProvider>
    </BrowserRouter>
  </StrictMode>,
);
