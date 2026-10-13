"use client";

import Link from "next/link";
import {
  ArrowRight,
  Bot,
  CheckCircle2,
  Cpu,
  Layers,
  MapPin,
  Mic,
  Navigation,
  Search,
  ShieldCheck,
  ShoppingBag,
  Sparkles,
  Store,
} from "lucide-react";

export default function LandingPage() {
  return (
    <div className="min-h-screen bg-slate-50 text-slate-900 selection:bg-orange-500 selection:text-white dark:bg-slate-950 dark:text-slate-100">
      {/* Navigation Header */}
      <header className="sticky top-0 z-50 border-b border-slate-200/80 bg-white/80 backdrop-blur-md dark:border-slate-800/80 dark:bg-slate-950/80">
        <div className="mx-auto flex h-16 max-w-7xl items-center justify-between px-4 sm:px-6 lg:px-8">
          <div className="flex items-center gap-3">
            <span className="flex h-10 w-10 items-center justify-center rounded-xl bg-gradient-to-tr from-orange-600 to-amber-500 text-white shadow-md shadow-orange-500/20">
              <ShoppingBag className="h-5 w-5" />
            </span>
            <span className="text-xl font-bold tracking-tight text-slate-900 dark:text-white">
              OmniMission <span className="text-orange-600">AI</span>
            </span>
          </div>

          <nav className="hidden items-center gap-8 md:flex">
            <a href="#how-it-works" className="text-sm font-medium text-slate-600 transition hover:text-slate-900 dark:text-slate-400 dark:hover:text-white">
              How It Works
            </a>
            <a href="#personas" className="text-sm font-medium text-slate-600 transition hover:text-slate-900 dark:text-slate-400 dark:hover:text-white">
              Personas
            </a>
            <a href="#architecture" className="text-sm font-medium text-slate-600 transition hover:text-slate-900 dark:text-slate-400 dark:hover:text-white">
              Google Cloud Stack
            </a>
          </nav>

          <div className="flex items-center gap-3">
            <Link
              href="/login"
              className="rounded-lg px-4 py-2 text-sm font-medium text-slate-700 transition hover:bg-slate-100 dark:text-slate-300 dark:hover:bg-slate-800"
            >
              Sign In
            </Link>
            <Link
              href="/register"
              className="flex items-center gap-1.5 rounded-lg bg-orange-600 px-4 py-2 text-sm font-semibold text-white shadow-sm transition hover:bg-orange-500"
            >
              Get Started <ArrowRight className="h-4 w-4" />
            </Link>
          </div>
        </div>
      </header>

      {/* Hero Section */}
      <section className="relative overflow-hidden pt-12 pb-20 sm:pt-20 sm:pb-32">
        <div className="mx-auto max-w-7xl px-4 sm:px-6 lg:px-8">
          <div className="grid items-center gap-12 lg:grid-cols-12">
            <div className="space-y-6 lg:col-span-7">
              <div className="inline-flex items-center gap-2 rounded-full border border-orange-200 bg-orange-50/70 px-3.5 py-1.5 text-xs font-semibold text-orange-700 dark:border-orange-900/50 dark:bg-orange-950/30 dark:text-orange-300">
                <Sparkles className="h-3.5 w-3.5 text-orange-600" />
                Google AI Hackathon • Multimodal Phygital Engine
              </div>

              <h1 className="text-4xl font-extrabold tracking-tight sm:text-5xl lg:text-6xl">
                From Inspiration to <span className="bg-gradient-to-r from-orange-600 to-amber-500 bg-clip-text text-transparent">In-Store Aisle</span> in Seconds
              </h1>

              <p className="max-w-2xl text-lg text-slate-600 dark:text-slate-300">
                Turn complex recipes, travel lists, and voice prompts into grounded shopping baskets resolved against real inventory in local stores—with exact aisle coordinates and smart in-stock substitutions.
              </p>

              <div className="flex flex-wrap items-center gap-4 pt-2">
                <Link
                  href="/login?redirect=/app"
                  className="flex items-center gap-2 rounded-xl bg-orange-600 px-6 py-3.5 text-base font-semibold text-white shadow-lg shadow-orange-600/25 transition hover:bg-orange-500 hover:shadow-orange-600/35"
                >
                  <ShoppingBag className="h-5 w-5" /> Start Shopper Mission
                </Link>
                <Link
                  href="/login?redirect=/merchant"
                  className="flex items-center gap-2 rounded-xl border border-slate-300 bg-white px-6 py-3.5 text-base font-semibold text-slate-800 shadow-sm transition hover:bg-slate-50 dark:border-slate-800 dark:bg-slate-900 dark:text-slate-200 dark:hover:bg-slate-800"
                >
                  <Store className="h-5 w-5 text-indigo-500" /> Merchant Command Portal
                </Link>
              </div>

              {/* Quick stats / highlights */}
              <div className="grid grid-cols-3 gap-6 pt-6 border-t border-slate-200 dark:border-slate-800">
                <div>
                  <div className="text-2xl font-bold text-slate-900 dark:text-white">100%</div>
                  <div className="text-xs text-slate-500">Strictly Grounded SKUs</div>
                </div>
                <div>
                  <div className="text-2xl font-bold text-slate-900 dark:text-white">&lt;200ms</div>
                  <div className="text-xs text-slate-500">Hybrid RRF Search</div>
                </div>
                <div>
                  <div className="text-2xl font-bold text-slate-900 dark:text-white">Aisles 1–12</div>
                  <div className="text-xs text-slate-500">In-Store Route Map</div>
                </div>
              </div>
            </div>

            {/* Live Interactive Mission Simulation Card */}
            <div className="lg:col-span-5">
              <div className="relative rounded-2xl border border-slate-200 bg-white p-6 shadow-2xl dark:border-slate-800 dark:bg-slate-900">
                <div className="flex items-center justify-between border-b border-slate-100 pb-4 dark:border-slate-800">
                  <div className="flex items-center gap-2">
                    <span className="h-3 w-3 rounded-full bg-emerald-500 animate-pulse" />
                    <span className="text-xs font-semibold uppercase tracking-wider text-slate-500">Live Agent Pipeline</span>
                  </div>
                  <span className="rounded bg-orange-100 px-2 py-0.5 text-xs font-medium text-orange-800 dark:bg-orange-950 dark:text-orange-300">
                    Indiranagar Branch
                  </span>
                </div>

                <div className="mt-4 space-y-3">
                  <div className="rounded-xl bg-slate-50 p-3.5 text-sm dark:bg-slate-800/60">
                    <div className="text-xs font-semibold text-slate-500">Customer Prompt:</div>
                    <div className="mt-0.5 font-medium text-slate-800 dark:text-slate-100">
                      &quot;Eggless cake with good protein for 6 people under ₹600&quot;
                    </div>
                  </div>

                  {/* Agent Reasoning Steps */}
                  <div className="space-y-2 text-xs">
                    <div className="flex items-center gap-2 text-emerald-600 dark:text-emerald-400">
                      <CheckCircle2 className="h-4 w-4 shrink-0" />
                      <span>Intent extracted: Servings=6, Budget=₹600, Dietary=Eggless</span>
                    </div>
                    <div className="flex items-center gap-2 text-emerald-600 dark:text-emerald-400">
                      <CheckCircle2 className="h-4 w-4 shrink-0" />
                      <span>Grounded catalog match: 5 items located in Aisle 2 &amp; 3</span>
                    </div>
                    <div className="flex items-center gap-2 text-amber-600 dark:text-amber-400">
                      <Sparkles className="h-4 w-4 shrink-0" />
                      <span>Substituted: Raw Whey substituted with High-Protein Curd</span>
                    </div>
                  </div>

                  {/* Sample Basket Preview */}
                  <div className="mt-4 rounded-xl border border-slate-200 p-3 dark:border-slate-800">
                    <div className="flex items-center justify-between text-xs font-semibold text-slate-700 dark:text-slate-300">
                      <span>Optimized Basket (4 Items)</span>
                      <span className="text-orange-600">Total: ₹384 (Under ₹600)</span>
                    </div>
                    <div className="mt-2 space-y-1.5 text-xs text-slate-600 dark:text-slate-400">
                      <div className="flex justify-between">
                        <span>• Aashirvaad Select Maida (1 kg)</span>
                        <span className="font-medium text-slate-800 dark:text-slate-200">Aisle 3 • Bay 2</span>
                      </div>
                      <div className="flex justify-between">
                        <span>• Cadbury Rich Cocoa Powder</span>
                        <span className="font-medium text-slate-800 dark:text-slate-200">Aisle 3 • Bay 4</span>
                      </div>
                      <div className="flex justify-between">
                        <span>• Epigamia Greek Yogurt (High Protein)</span>
                        <span className="font-medium text-slate-800 dark:text-slate-200">Aisle 2 • Bay 1</span>
                      </div>
                    </div>
                  </div>

                  <div className="flex items-center justify-between rounded-lg bg-emerald-50 px-3 py-2 text-xs font-semibold text-emerald-800 dark:bg-emerald-950/40 dark:text-emerald-300">
                    <div className="flex items-center gap-1.5">
                      <Navigation className="h-3.5 w-3.5" /> Optimal Path: Aisle 2 → Aisle 3
                    </div>
                    <span>Est. 4 mins</span>
                  </div>
                </div>
              </div>
            </div>
          </div>
        </div>
      </section>

      {/* Google Tech Credibility Strip */}
      <section className="border-y border-slate-200 bg-white py-10 dark:border-slate-800 dark:bg-slate-900/50">
        <div className="mx-auto max-w-7xl px-4 sm:px-6 lg:px-8">
          <p className="text-center text-xs font-semibold uppercase tracking-wider text-slate-500">
            Powered by Google Cloud &amp; State-of-the-Art AI Tooling
          </p>
          <div className="mt-6 flex flex-wrap items-center justify-center gap-8 sm:gap-14 text-sm font-semibold text-slate-700 dark:text-slate-300">
            <div className="flex items-center gap-2">
              <Sparkles className="h-5 w-5 text-orange-500" />
              <span>Gemini 2.5 Flash</span>
            </div>
            <div className="flex items-center gap-2">
              <Bot className="h-5 w-5 text-indigo-500" />
              <span>Agno 3.1.3 Multi-Agent</span>
            </div>
            <div className="flex items-center gap-2">
              <Cpu className="h-5 w-5 text-emerald-500" />
              <span>pgvector &amp; Hybrid RRF</span>
            </div>
            <div className="flex items-center gap-2">
              <Layers className="h-5 w-5 text-blue-500" />
              <span>Cloud Run &amp; Vertex AI Ready</span>
            </div>
          </div>
        </div>
      </section>

      {/* 3-Step "How It Works" */}
      <section id="how-it-works" className="py-20 sm:py-28">
        <div className="mx-auto max-w-7xl px-4 sm:px-6 lg:px-8">
          <div className="text-center">
            <h2 className="text-xs font-semibold uppercase tracking-wider text-orange-600">Architecture &amp; Flow</h2>
            <p className="mt-2 text-3xl font-bold tracking-tight sm:text-4xl text-slate-900 dark:text-white">
              How OmniMission Works
            </p>
          </div>

          <div className="mt-14 grid gap-8 md:grid-cols-3">
            <div className="rounded-2xl border border-slate-200 bg-white p-8 shadow-sm dark:border-slate-800 dark:bg-slate-900">
              <div className="flex h-12 w-12 items-center justify-center rounded-xl bg-orange-100 text-orange-600 dark:bg-orange-950 dark:text-orange-400">
                <Mic className="h-6 w-6" />
              </div>
              <h3 className="mt-5 text-lg font-bold text-slate-900 dark:text-white">1. Multimodal Input</h3>
              <p className="mt-2 text-sm text-slate-600 dark:text-slate-400">
                Speak in Hindi or English, paste a natural query, or snap a photo of a pantry or shelf. Gemini decomposes your input into structured mission goals.
              </p>
            </div>

            <div className="rounded-2xl border border-slate-200 bg-white p-8 shadow-sm dark:border-slate-800 dark:bg-slate-900">
              <div className="flex h-12 w-12 items-center justify-center rounded-xl bg-emerald-100 text-emerald-600 dark:bg-emerald-950 dark:text-emerald-400">
                <ShieldCheck className="h-6 w-6" />
              </div>
              <h3 className="mt-5 text-lg font-bold text-slate-900 dark:text-white">2. Strict Catalog Grounding</h3>
              <p className="mt-2 text-sm text-slate-600 dark:text-slate-400">
                Zero hallucinations. Products, prices, and stock levels come exclusively from PostgreSQL hybrid search (pgvector + FTS + RRF) across physical stores.
              </p>
            </div>

            <div className="rounded-2xl border border-slate-200 bg-white p-8 shadow-sm dark:border-slate-800 dark:bg-slate-900">
              <div className="flex h-12 w-12 items-center justify-center rounded-xl bg-indigo-100 text-indigo-600 dark:bg-indigo-950 dark:text-indigo-400">
                <Navigation className="h-6 w-6" />
              </div>
              <h3 className="mt-5 text-lg font-bold text-slate-900 dark:text-white">3. In-Store Wayfinding</h3>
              <p className="mt-2 text-sm text-slate-600 dark:text-slate-400">
                The deterministic wayfinding engine compiles an ordered aisle-by-aisle traversal path, guiding shoppers to the exact bay and shelf for each item.
              </p>
            </div>
          </div>
        </div>
      </section>

      {/* Dual Persona Showcase */}
      <section id="personas" className="bg-slate-100/60 py-20 dark:bg-slate-900/40">
        <div className="mx-auto max-w-7xl px-4 sm:px-6 lg:px-8">
          <div className="grid gap-10 md:grid-cols-2">
            {/* Shopper */}
            <div className="rounded-3xl border border-slate-200 bg-white p-8 shadow-md dark:border-slate-800 dark:bg-slate-900">
              <div className="flex items-center gap-3">
                <span className="flex h-10 w-10 items-center justify-center rounded-xl bg-orange-600 text-white">
                  <ShoppingBag className="h-5 w-5" />
                </span>
                <div>
                  <h3 className="text-xl font-bold">For Shoppers</h3>
                  <p className="text-xs text-slate-500">Mobile-First PWA Experience</p>
                </div>
              </div>
              <ul className="mt-6 space-y-3 text-sm text-slate-600 dark:text-slate-300">
                <li className="flex items-center gap-2">
                  <CheckCircle2 className="h-4 w-4 text-orange-600" /> Multi-store select across nearby branches
                </li>
                <li className="flex items-center gap-2">
                  <CheckCircle2 className="h-4 w-4 text-orange-600" /> Dietary constraint filtering (eggless, gluten-free, vegan)
                </li>
                <li className="flex items-center gap-2">
                  <CheckCircle2 className="h-4 w-4 text-orange-600" /> Automated out-of-stock substitutions with trade-off rationale
                </li>
                <li className="flex items-center gap-2">
                  <CheckCircle2 className="h-4 w-4 text-orange-600" /> Live agent reasoning timeline streamed via SSE
                </li>
              </ul>
              <div className="mt-8">
                <Link
                  href="/login?redirect=/app"
                  className="inline-flex items-center gap-2 text-sm font-semibold text-orange-600 hover:text-orange-500"
                >
                  Explore Shopper Experience <ArrowRight className="h-4 w-4" />
                </Link>
              </div>
            </div>

            {/* Merchant */}
            <div className="rounded-3xl border border-slate-200 bg-white p-8 shadow-md dark:border-slate-800 dark:bg-slate-900">
              <div className="flex items-center gap-3">
                <span className="flex h-10 w-10 items-center justify-center rounded-xl bg-indigo-600 text-white">
                  <Store className="h-5 w-5" />
                </span>
                <div>
                  <h3 className="text-xl font-bold">For Store Merchants</h3>
                  <p className="text-xs text-slate-500">Store Operations Command Console</p>
                </div>
              </div>
              <ul className="mt-6 space-y-3 text-sm text-slate-600 dark:text-slate-300">
                <li className="flex items-center gap-2">
                  <CheckCircle2 className="h-4 w-4 text-indigo-600" /> Real-time demand radar tracking shopper queries
                </li>
                <li className="flex items-center gap-2">
                  <CheckCircle2 className="h-4 w-4 text-indigo-600" /> Predictive stockout alerts and days-of-cover velocity
                </li>
                <li className="flex items-center gap-2">
                  <CheckCircle2 className="h-4 w-4 text-indigo-600" /> Vision shelf audits detecting empty slots from photos
                </li>
                <li className="flex items-center gap-2">
                  <CheckCircle2 className="h-4 w-4 text-indigo-600" /> Automated restock task generation and kanban tracking
                </li>
              </ul>
              <div className="mt-8">
                <Link
                  href="/login?redirect=/merchant"
                  className="inline-flex items-center gap-2 text-sm font-semibold text-indigo-600 hover:text-indigo-500"
                >
                  Explore Merchant Command <ArrowRight className="h-4 w-4" />
                </Link>
              </div>
            </div>
          </div>
        </div>
      </section>

      {/* Footer */}
      <footer className="border-t border-slate-200 bg-white py-10 dark:border-slate-800 dark:bg-slate-950">
        <div className="mx-auto flex max-w-7xl flex-col items-center justify-between gap-4 px-4 text-center text-xs text-slate-500 sm:flex-row sm:text-left">
          <p>© 2026 OmniMission AI. Built for the Google AI Hackathon.</p>
          <div className="flex gap-6">
            <Link href="/login" className="hover:text-slate-900 dark:hover:text-white">Sign In</Link>
            <Link href="/register" className="hover:text-slate-900 dark:hover:text-white">Register</Link>
            <a href="https://cloud.google.com" target="_blank" rel="noreferrer" className="hover:text-slate-900 dark:hover:text-white">Google Cloud</a>
          </div>
        </div>
      </footer>
    </div>
  );
}
