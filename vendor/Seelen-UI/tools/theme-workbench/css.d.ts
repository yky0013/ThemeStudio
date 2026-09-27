declare module "*.module.css" {
  const classes: Record<string, string>;
  export default classes;
}
declare module "*.yml" {
  const source: string;
  export default source;
}
declare module "*.svelte" {
  import type { Component } from "svelte";
  const component: Component<Record<string, unknown>>;
  export default component;
}
