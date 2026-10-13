import { Loader2 } from "lucide-react";

export default function Loading() {
  return (
    <div className="flex min-h-screen items-center justify-center bg-slate-50 dark:bg-slate-950">
      <div className="flex flex-col items-center gap-3">
        <Loader2 className="h-8 w-8 animate-spin text-orange-600" />
        <p className="text-xs font-semibold uppercase tracking-wider text-slate-500">
          Loading OmniMission...
        </p>
      </div>
    </div>
  );
}
