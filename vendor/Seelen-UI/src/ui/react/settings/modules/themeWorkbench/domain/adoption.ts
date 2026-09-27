export interface ProviderPolicy {
  decisions: {
    wallpaper: { status: string; provider: "seelen" | "windhawk" | "both" | null };
    taskbar: { status: string; provider: "seelen" | "windhawk" | "deferred" | null };
  };
}

export function adoptedSeelenComponents(policy: ProviderPolicy): string[] {
  const result: string[] = [];
  const { taskbar, wallpaper } = policy.decisions;
  if (taskbar.status === "chosen_by_user" && taskbar.provider === "seelen") result.push("@seelen/weg", "@seelen/fancy-toolbar");
  if (wallpaper.status === "chosen_by_user" && ["seelen", "both"].includes(wallpaper.provider || "")) result.push("@seelen/wallpaper-manager");
  return result;
}
