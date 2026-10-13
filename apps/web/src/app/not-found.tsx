import Link from "next/link";
import { ArrowLeft, Search } from "lucide-react";

export default function NotFound() {
  return (
    <div className="flex min-h-screen flex-col items-center justify-center bg-slate-50 px-4 text-center dark:bg-slate-950">
      <div className="flex h-16 w-16 items-center justify-center rounded-2xl bg-orange-100 text-orange-600 dark:bg-orange-950/50 dark:text-orange-400">
        <Search className="h-8 w-8" />
      </div>
      <h1 className="mt-6 text-3xl font-bold tracking-tight text-slate-900 dark:text-white">
        Page Not Found
      </h1>
      <p className="mt-2 text-sm text-slate-500 max-w-sm">
        The mission or screen you are looking for does not exist or has been moved.
      </p>
      <div className="mt-6">
        <Link
          href="/"
          className="inline-flex items-center gap-2 rounded-xl bg-orange-600 px-5 py-2.5 text-sm font-semibold text-white shadow-md shadow-orange-600/30 hover:bg-orange-500"
        >
          <ArrowLeft className="h-4 w-4" /> Return to Home
        </Link>
      </div>
    </div>
  );
}
