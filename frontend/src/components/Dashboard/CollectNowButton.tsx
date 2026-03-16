import { useState } from "react";
import { useMutation } from "@tanstack/react-query";
import { triggerCollectNow } from "@/services/pipeline.service";
import { cn } from "@/lib/utils";

type CollectState = "idle" | "collecting" | "done" | "failed";

/**
 * CollectNowButton — triggers an on-demand data collection pipeline run.
 *
 * Designed to sit in the PageHeader actions slot on the Home page.
 * Shows a spinner while the job is running and a brief status message
 * once it completes or fails.
 */
export function CollectNowButton() {
  const [collectState, setCollectState] = useState<CollectState>("idle");

  const mutation = useMutation({
    mutationFn: triggerCollectNow,
    onMutate: () => setCollectState("collecting"),
    onSuccess: () => setCollectState("done"),
    onError: () => setCollectState("failed"),
  });

  const isDisabled = collectState === "collecting";

  const label =
    collectState === "collecting"
      ? "Collecting…"
      : collectState === "done"
        ? "✓ Collected"
        : collectState === "failed"
          ? "✗ Failed"
          : "Collect Now";

  return (
    <button
      type="button"
      disabled={isDisabled}
      onClick={() => mutation.mutate()}
      aria-label="Collect now"
      className={cn(
        "rounded-md border px-3 py-1.5 text-sm font-medium transition-colors",
        collectState === "idle" &&
          "border-primary bg-primary/10 text-primary hover:bg-primary/20",
        collectState === "collecting" &&
          "cursor-wait border-muted bg-muted/50 text-muted-foreground",
        collectState === "done" &&
          "border-green-500 bg-green-500/10 text-green-600",
        collectState === "failed" &&
          "border-destructive bg-destructive/10 text-destructive",
      )}
    >
      {label}
    </button>
  );
}
