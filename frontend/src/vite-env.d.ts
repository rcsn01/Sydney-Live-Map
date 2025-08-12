/// <reference types="vite/client" />

interface ImportMetaEnv {
  readonly VITE_API_BASE?: string;
  // add more custom env vars here as needed
}

interface ImportMeta {
  readonly env: ImportMetaEnv;
}
