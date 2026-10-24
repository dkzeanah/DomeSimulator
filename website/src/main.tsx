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
const CutList = lazy(() => import("./pages/CutList"));
const WedgeCalculator = lazy(() => import("./pages/WedgeCalculator"));
const SketchPage = lazy(() => import("./pages/Tools").then((m) => ({ default: m.SketchPage })));
const SoftwarePage = lazy(() => import("./pages/Tools").then((m) => ({ default: m.SoftwarePage })));
const MyLinksPage = lazy(() => import("./pages/Tools").then((m) => ({ default: m.MyLinksPage })));
const ToolsPage = lazy(() => import("./pages/Tools").then((m) => ({ default: m.ToolsPage })));
const AdminTools = lazy(() => import("./pages/AdminTools"));
const EpisodeList = lazy(() => import("./pages/Episodes").then((m) => ({ default: m.EpisodeList })));
const EpisodePage = lazy(() => import("./pages/Episodes").then((m) => ({ default: m.EpisodePage })));
const Admin = lazy(() => import("./pages/Admin"));
const Confirm = lazy(() => import("./pages/Mailbox").then((m) => ({ default: m.Confirm })));
const Unsubscribe = lazy(() => import("./pages/Mailbox").then((m) => ({ default: m.Unsubscribe })));
const Privacy = lazy(() => import("./pages/Mailbox").then((m) => ({ default: m.Privacy })));
const AdminList = lazy(() => import("./pages/AdminList"));
const AdminAnalytics = lazy(() => import("./pages/AdminAnalytics"));
const AdminUsers = lazy(() => import("./pages/AdminUsers"));
const AdminOps = lazy(() => import("./pages/AdminOps"));
const AdminAgents = lazy(() => import("./pages/AdminAgents"));
const Reset = lazy(() => import("./pages/Mailbox").then((m) => ({ default: m.Reset })));
const Verify = lazy(() => import("./pages/Mailbox").then((m) => ({ default: m.Verify })));
const Kids = lazy(() => import("./pages/Kids"));
const AdminStories = lazy(() => import("./pages/AdminStories"));
const StoryRender = lazy(() => import("./storytime/StoryRender"));
const MyKids = lazy(() => import("./pages/MyKids"));
const MediaPage = lazy(() => import("./pages/Media"));
const Portal = lazy(() => import("./pages/Portal"));
const Card = lazy(() => import("./pages/Card"));
const Domes = lazy(() => import("./pages/Domes"));
const DomeClassPage = lazy(() => import("./pages/Domes").then((m) => ({ default: m.DomeClassPage })));
const AdminStudio = lazy(() => import("./pages/AdminStudio"));
const AdminProjects = lazy(() => import("./pages/AdminProjects"));
const NotFound = lazy(() => import("./pages/NotFound"));

createRoot(document.getElementById("root")!).render(
  <StrictMode>
    <BrowserRouter>
      <SessionProvider>
        <Suspense fallback={<div className="p-8 muted">Loading...</div>}>
          <Routes>
            {/* the film renderer (sketch_claude storytime): bare, no site chrome */}
            <Route path="storytime-render" element={<StoryRender />} />
            {/* a private story, by its link only: no site chrome, no listing */}
            <Route path="mykids" element={<MyKids />} />
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
              <Route path="cutlist/:ref" element={<CutList />} />
              <Route path="checkout/test/:ref" element={<Thanks test />} />
              <Route path="kids" element={<Kids />} />
              <Route path="kids/:story" element={<Kids />} />
              <Route path="media" element={<MediaPage />} />
              <Route path="episodes" element={<EpisodeList />} />
              <Route path="calculator" element={<WedgeCalculator />} />
              <Route path="sketch" element={<SketchPage />} />
              <Route path="software" element={<SoftwarePage />} />
              <Route path="mylinks" element={<MyLinksPage />} />
              <Route path="tools" element={<ToolsPage />} />
              <Route path="admin/tools" element={<AdminTools />} />
              <Route path="episodes/:slug" element={<EpisodePage />} />
              <Route path="portal" element={<Portal />} />
              <Route path="portal/:space" element={<Portal />} />
              <Route path="portal/house/:owner" element={<Portal />} />
              <Route path="portal/island" element={<Portal island />} />
              <Route path="card" element={<Card />} />
              <Route path="links" element={<Card />} />
              <Route path="domes" element={<Domes />} />
              <Route path="domes/:longIn" element={<DomeClassPage />} />
              <Route path="admin" element={<Admin />} />
              <Route path="admin/studio" element={<AdminStudio />} />
              <Route path="admin/projects" element={<AdminProjects />} />
              <Route path="admin/list" element={<AdminList />} />
              <Route path="admin/analytics" element={<AdminAnalytics />} />
              <Route path="admin/users" element={<AdminUsers />} />
              <Route path="admin/ops" element={<AdminOps />} />
              <Route path="admin/agents" element={<AdminAgents />} />
              <Route path="admin/stories" element={<AdminStories />} />
              <Route path="reset" element={<Reset />} />
              <Route path="verify" element={<Verify />} />
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
