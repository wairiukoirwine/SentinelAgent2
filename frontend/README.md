# Dashboard

The React + TypeScript + Vite dashboard reads the local FastAPI service at `http://127.0.0.1:8000`. Set `VITE_API_URL` at build time only if the local backend uses another address. No client-side tool executor exists.

Install the locked dependency tree with `npm ci`, start with `npm run dev`, and check types/build output with `npm run build`.
